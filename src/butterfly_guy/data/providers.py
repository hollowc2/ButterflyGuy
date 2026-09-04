"""Narrow read-only provider boundaries for Schwab market data."""

from __future__ import annotations

import asyncio
import datetime as dt
import math
from collections.abc import Awaitable, Callable
from typing import Any, Protocol
from zoneinfo import ZoneInfo

from schwab_gateway_sdk.client import (
    GatewayCapacityError,
    GatewayMarketDataClient,
    GatewayTimeoutError,
    GatewayUnavailableError,
)

from butterfly_guy.core.metrics import clear_readiness, set_readiness
from butterfly_guy.core.time_utils import MARKET_OPEN, market_close_time
from butterfly_guy.data.schwab_client import SchwabClientWrapper

EASTERN = ZoneInfo("America/New_York")
MINUTE_HISTORY_LIVE_MAX_AGE_SECONDS = 180.0
MINUTE_HISTORY_POST_CLOSE_MAX_AGE_SECONDS = 8 * 60 * 60.0
SESSION_CLOSE_BAR_TOLERANCE = dt.timedelta(minutes=5)
GATEWAY_REQUIRED_SURFACES = frozenset({"spot", "option_chain", "minute_history"})
TRANSIENT_GATEWAY_ERRORS = (
    GatewayCapacityError,
    GatewayTimeoutError,
    GatewayUnavailableError,
)


def _now_eastern() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).astimezone(EASTERN)


class GatewayMarketDataError(RuntimeError):
    """Gateway data cannot safely be consumed by a trading strategy."""


def _same_symbol(left: str, right: str) -> bool:
    return left.strip().upper().lstrip("$") == right.strip().upper().lstrip("$")


def _finite_number(value: object, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise GatewayMarketDataError("gateway returned a non-numeric value")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise GatewayMarketDataError("gateway returned a non-numeric value") from exc
    if not math.isfinite(number) or (positive and number <= 0):
        raise GatewayMarketDataError("gateway returned an out-of-range value")
    return number


def _nonnegative_integer(value: object, *, field: str) -> int:
    if value is None:
        return 0
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise GatewayMarketDataError(
            f"gateway option contract {field} must be a nonnegative integer"
        )
    return value


def _optional_number(
    value: object,
    *,
    default: float,
    field: str,
    nonnegative: bool = False,
    positive: bool = False,
) -> float:
    if value is None:
        return default
    number = _finite_number(value, positive=positive)
    if nonnegative and number < 0:
        raise GatewayMarketDataError(
            f"gateway option contract {field} must be nonnegative"
        )
    return number


def _require_usable_observation(
    observation: Any,
    *,
    operation: str,
    max_age_seconds: float | None = None,
    allow_stale: bool = False,
    allowed_quality_flags: frozenset[str] = frozenset(),
) -> None:
    if observation.stale and not allow_stale:
        raise GatewayMarketDataError(f"gateway {operation} data is stale")
    if observation.age_seconds is None and not allow_stale:
        raise GatewayMarketDataError(f"gateway {operation} freshness is unknown")
    if (
        max_age_seconds is not None
        and observation.age_seconds is not None
        and observation.age_seconds > max_age_seconds
    ):
        raise GatewayMarketDataError(f"gateway {operation} data is too old")
    fatal_flags = set(observation.data_quality_flags) - allowed_quality_flags
    if allow_stale:
        fatal_flags.discard("stale")
    if fatal_flags:
        raise GatewayMarketDataError(
            f"gateway {operation} data failed quality checks: "
            f"{','.join(sorted(fatal_flags))}"
        )


class SpotPriceProvider(Protocol):
    async def get_spot_price(self, symbol: str = "$SPX") -> float: ...


class OptionChainProvider(Protocol):
    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]: ...


class PriceHistoryProvider(Protocol):
    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]: ...

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]: ...

    async def get_daily_bars(
        self, symbol: str, days_back: int = 10
    ) -> list[dict]: ...


class EquityQuoteProvider(Protocol):
    async def get_equity_quotes(
        self, symbols: list[str], *, batch_size: int = 150
    ) -> dict[str, dict[str, Any]]: ...


class MarketMoversProvider(Protocol):
    async def get_market_movers(
        self,
        index: str,
        *,
        sort_order: str = "PERCENT_CHANGE_UP",
        frequency: int | None = None,
    ) -> list[dict[str, Any]]: ...


class CollectorMarketDataProvider(
    SpotPriceProvider,
    OptionChainProvider,
    PriceHistoryProvider,
    Protocol,
):
    """The read-only surface required by ``OptionChainCollector``."""


class GatewayAuthoritativeMarketDataProvider:
    """Adapt the standalone gateway's typed contracts to existing strategy inputs.

    The adapter deliberately has no direct-client fallback. Once gateway mode is
    selected, an unavailable, stale, mismatched, or malformed response raises and
    the caller's existing fail-safe path skips collection/entry/valuation.
    """

    def __init__(
        self,
        client: GatewayMarketDataClient,
        *,
        max_current_age_seconds: float = 30.0,
        max_attempts: int = 2,
        retry_backoff_seconds: float = 0.25,
    ) -> None:
        if max_current_age_seconds <= 0:
            raise ValueError("max_current_age_seconds must be positive")
        if max_attempts < 1:
            raise ValueError("max_attempts must be at least one")
        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds must be nonnegative")
        self._client = client
        self._max_current_age_seconds = max_current_age_seconds
        self._max_attempts = max_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._required_surfaces_ready: set[str] = set()
        self.begin_readiness_tracking()

    def begin_readiness_tracking(self) -> None:
        self._required_surfaces_ready.clear()
        clear_readiness("gateway_market_data_unavailable")
        set_readiness("gateway_market_data_warming")

    def _required_surface_succeeded(self, surface: str) -> None:
        self._required_surfaces_ready.add(surface)
        if self._required_surfaces_ready == GATEWAY_REQUIRED_SURFACES:
            clear_readiness("gateway_market_data_warming")
            clear_readiness("gateway_market_data_unavailable")

    def _required_surface_failed(self) -> None:
        self._required_surfaces_ready.clear()
        clear_readiness("gateway_market_data_warming")
        set_readiness("gateway_market_data_unavailable")

    async def _transient_read(
        self,
        operation: Callable[[], Awaitable[Any]],
    ) -> Any:
        for attempt in range(1, self._max_attempts + 1):
            try:
                return await operation()
            except TRANSIENT_GATEWAY_ERRORS:
                if attempt == self._max_attempts:
                    raise
                await asyncio.sleep(
                    self._retry_backoff_seconds * (2 ** (attempt - 1))
                )
        raise AssertionError("gateway retry loop exhausted")

    async def _required_read(
        self,
        surface: str,
        operation: Callable[[], Awaitable[Any]],
    ) -> Any:
        try:
            result = await self._transient_read(operation)
        except Exception:
            self._required_surface_failed()
            raise
        self._required_surface_succeeded(surface)
        return result

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        return await self._required_read("spot", lambda: self._get_spot_price(symbol))

    async def _get_spot_price(self, symbol: str) -> float:
        response = await self._client.get_spot(symbol)
        spot = response.spot
        _require_usable_observation(
            spot,
            operation="spot",
            max_age_seconds=self._max_current_age_seconds,
        )
        if not _same_symbol(spot.symbol, symbol):
            raise GatewayMarketDataError("gateway spot symbol does not match request")
        return _finite_number(spot.price, positive=True)

    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]:
        return await self._required_read(
            "option_chain",
            lambda: self._get_option_chain(symbol, expiration),
        )

    async def _get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]:
        response = await self._client.get_option_chain(symbol, expiration)
        chain = response.option_chain
        _require_usable_observation(
            chain,
            operation="option-chain",
            max_age_seconds=self._max_current_age_seconds,
            allowed_quality_flags=frozenset(
                {
                    "crossed_markets_normalized",
                    "stale_contracts_present",
                    "missing_contract_event_timestamp",
                }
            ),
        )
        if not _same_symbol(chain.symbol, symbol):
            raise GatewayMarketDataError("gateway option-chain symbol does not match request")
        if chain.expiration != expiration:
            raise GatewayMarketDataError(
                "gateway option-chain expiration does not match request"
            )
        underlying_price = _finite_number(chain.underlying_price, positive=True)

        maps: dict[str, dict[str, list[dict[str, Any]]]] = {
            "callExpDateMap": {},
            "putExpDateMap": {},
        }
        expiration_key = f"{expiration.isoformat()}:0"
        seen_symbols: set[str] = set()
        contract_counts = {"CALL": 0, "PUT": 0}
        strikes: set[float] = set()
        for contract in chain.contracts:
            contract_flags = set(contract.data_quality_flags)
            omittable_flags = {"stale", "missing_event_timestamp"}
            usable_flags = {"crossed_market_normalized"}
            fatal_flags = contract_flags - omittable_flags - usable_flags
            if fatal_flags:
                raise GatewayMarketDataError(
                    "gateway option contract failed quality checks: "
                    f"{','.join(sorted(fatal_flags))}"
                )
            usable_contract = (
                not contract.stale
                and contract.age_seconds is not None
                and contract.age_seconds <= self._max_current_age_seconds
                and not (contract_flags & omittable_flags)
            )
            if contract.expiration != expiration:
                raise GatewayMarketDataError(
                    "gateway option contract expiration does not match request"
                )
            option_type = str(contract.option_type).upper()
            if option_type not in {"CALL", "PUT"}:
                raise GatewayMarketDataError("gateway option contract type is invalid")
            contract_symbol = str(contract.symbol).strip()
            if not contract_symbol or contract_symbol in seen_symbols:
                raise GatewayMarketDataError(
                    "gateway option chain has missing or duplicate symbols"
                )
            seen_symbols.add(contract_symbol)
            strike = _finite_number(contract.strike, positive=True)
            contract_counts[option_type] += 1
            strikes.add(strike)
            if contract.bid is None or contract.ask is None or contract.mark is None:
                raise GatewayMarketDataError(
                    "gateway option contract is missing bid, ask, or mark"
                )
            bid = _finite_number(contract.bid)
            ask = _finite_number(contract.ask)
            mark = _finite_number(contract.mark)
            if min(bid, ask, mark) < 0 or bid > ask:
                raise GatewayMarketDataError(
                    "gateway option contract has an invalid market"
                )
            last = _optional_number(
                contract.last,
                default=0.0,
                field="last",
                nonnegative=True,
            )
            total_volume = _nonnegative_integer(
                contract.total_volume,
                field="total_volume",
            )
            open_interest = _nonnegative_integer(
                contract.open_interest,
                field="open_interest",
            )
            bid_size = _nonnegative_integer(contract.bid_size, field="bid_size")
            ask_size = _nonnegative_integer(contract.ask_size, field="ask_size")
            days_to_expiration = _nonnegative_integer(
                contract.days_to_expiration,
                field="days_to_expiration",
            )
            in_the_money = contract.in_the_money
            if in_the_money is None:
                in_the_money = False
            if not isinstance(in_the_money, bool):
                raise GatewayMarketDataError(
                    "gateway option contract in_the_money must be boolean"
                )
            option = {
                "symbol": contract_symbol,
                "bid": bid,
                "ask": ask,
                "mark": mark,
                "last": last,
                "totalVolume": total_volume,
                "openInterest": open_interest,
                "volatility": _optional_number(
                    contract.volatility,
                    default=0.0,
                    field="volatility",
                    nonnegative=True,
                ),
                "delta": _optional_number(
                    contract.delta, default=0.0, field="delta"
                ),
                "gamma": _optional_number(
                    contract.gamma, default=0.0, field="gamma"
                ),
                "theta": _optional_number(
                    contract.theta, default=0.0, field="theta"
                ),
                "vega": _optional_number(
                    contract.vega, default=0.0, field="vega"
                ),
                "bidSize": bid_size,
                "askSize": ask_size,
                "rho": _optional_number(contract.rho, default=0.0, field="rho"),
                "intrinsicValue": _optional_number(
                    contract.intrinsic_value,
                    default=0.0,
                    field="intrinsic_value",
                    nonnegative=True,
                ),
                "timeValue": _optional_number(
                    contract.time_value,
                    default=0.0,
                    field="time_value",
                    nonnegative=True,
                ),
                "inTheMoney": in_the_money,
                "daysToExpiration": days_to_expiration,
                "multiplier": _optional_number(
                    contract.multiplier,
                    default=100.0,
                    field="multiplier",
                    positive=True,
                ),
                "theoreticalOptionValue": _optional_number(
                    contract.theoretical_option_value,
                    default=0.0,
                    field="theoretical_option_value",
                    nonnegative=True,
                ),
            }
            if not usable_contract:
                continue
            map_key = "callExpDateMap" if option_type == "CALL" else "putExpDateMap"
            strike_key = str(int(strike)) if strike.is_integer() else str(strike)
            strike_map = maps[map_key].setdefault(expiration_key, {})
            strike_map.setdefault(strike_key, []).append(option)

        if not seen_symbols or not maps["callExpDateMap"] or not maps["putExpDateMap"]:
            raise GatewayMarketDataError(
                "gateway option chain must contain calls and puts"
            )
        expected_counts = {
            "CALL": _nonnegative_integer(
                chain.call_contract_count,
                field="call_contract_count",
            ),
            "PUT": _nonnegative_integer(
                chain.put_contract_count,
                field="put_contract_count",
            ),
        }
        expected_strikes = _nonnegative_integer(
            chain.strike_count,
            field="strike_count",
        )
        if contract_counts != expected_counts or len(strikes) != expected_strikes:
            raise GatewayMarketDataError(
                "gateway option-chain counts do not match delivered contracts"
            )
        return {
            "symbol": chain.symbol,
            "underlyingPrice": underlying_price,
            **maps,
        }

    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]:
        return await self._required_read(
            "minute_history",
            lambda: self._get_intraday_bars(symbol, days_back),
        )

    async def _get_intraday_bars(
        self, symbol: str, days_back: int
    ) -> list[dict]:
        response = await self._client.get_history(
            symbol,
            frequency="minute",
            days_back=days_back,
        )
        allow_stale, max_age_seconds = self._minute_history_freshness(
            response.history
        )
        return self._history_bars(
            response.history,
            symbol,
            operation="intraday-history",
            allow_stale=allow_stale,
            max_age_seconds=max_age_seconds,
        )

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]:
        today = _now_eastern().date()
        if day > today:
            raise ValueError("session-history day cannot be in the future")
        sessions = ("regular", "extended") if include_extended_hours else ("regular",)
        responses = await asyncio.gather(
            *(
                self._transient_read(
                    lambda session=session: self._client.get_session_history(
                        symbol,
                        day,
                        session=session,
                    )
                )
                for session in sessions
            )
        )
        historical = day < today
        all_bars: list[dict] = []
        for response in responses:
            history = response.session_history
            if history.date != day or history.session not in sessions:
                raise GatewayMarketDataError(
                    "gateway session-history contract does not match request"
                )
            allow_empty = history.session == "extended"
            if historical:
                allow_stale = True
                max_age_seconds = None
            elif history.candles:
                allow_stale, max_age_seconds = self._minute_history_freshness(
                    history,
                    bar_field="candles",
                )
            else:
                # A symbol can legitimately have no extended-hours candles. The
                # empty-session validator below still requires exactly the bounded
                # no-bars/stale flags and never permits an empty regular session.
                allow_stale = history.session == "extended"
                max_age_seconds = None
            all_bars.extend(
                self._history_bars(
                    history,
                    symbol,
                    operation=f"{history.session}-session-history",
                    allow_empty=allow_empty,
                    bar_field="candles",
                    allow_stale=allow_stale,
                    max_age_seconds=max_age_seconds,
                )
            )
        by_timestamp: dict[int, dict] = {}
        for bar in all_bars:
            prior = by_timestamp.get(bar["datetime"])
            if prior is not None and prior != bar:
                raise GatewayMarketDataError(
                    "gateway session-history returned conflicting candles"
                )
            by_timestamp[bar["datetime"]] = bar
        candles = [by_timestamp[key] for key in sorted(by_timestamp)]
        if not candles:
            raise GatewayMarketDataError("gateway session-history returned no candles")
        return candles

    @staticmethod
    def _minute_history_freshness(
        history: Any,
        *,
        bar_field: str = "bars",
    ) -> tuple[bool, float]:
        bars = tuple(getattr(history, bar_field))
        if not bars:
            return False, MINUTE_HISTORY_LIVE_MAX_AGE_SECONDS

        now = _now_eastern()
        latest = max(bar.timestamp for bar in bars).astimezone(EASTERN)
        close_at = dt.datetime.combine(
            now.date(),
            market_close_time(now.date()),
            tzinfo=EASTERN,
        )
        latest_close_candidate = close_at - SESSION_CLOSE_BAR_TOLERANCE
        if (
            now >= close_at
            and latest.date() == now.date()
            and latest >= latest_close_candidate
        ):
            seconds_since_close = max(0.0, (now - close_at).total_seconds())
            return True, min(
                MINUTE_HISTORY_POST_CLOSE_MAX_AGE_SECONDS,
                seconds_since_close + SESSION_CLOSE_BAR_TOLERANCE.total_seconds(),
            )

        if now.time() < MARKET_OPEN:
            return False, MINUTE_HISTORY_LIVE_MAX_AGE_SECONDS
        return False, MINUTE_HISTORY_LIVE_MAX_AGE_SECONDS

    async def get_daily_bars(
        self, symbol: str, days_back: int = 10
    ) -> list[dict]:
        response = await self._transient_read(
            lambda: self._client.get_history(
                symbol,
                frequency="daily",
                days_back=days_back,
            )
        )
        return self._history_bars(
            response.history,
            symbol,
            operation="daily-history",
            allow_stale=True,
        )

    @staticmethod
    def _history_bars(
        history: Any,
        symbol: str,
        *,
        operation: str,
        allow_empty: bool = False,
        bar_field: str = "bars",
        allow_stale: bool = False,
        max_age_seconds: float | None = None,
    ) -> list[dict]:
        if not _same_symbol(history.symbol, symbol):
            raise GatewayMarketDataError(
                f"gateway {operation} symbol does not match request"
            )
        raw_bars = tuple(getattr(history, bar_field))
        if not raw_bars and allow_empty:
            flags = set(history.data_quality_flags)
            allowed_flags = {"no_bars_returned"}
            if allow_stale:
                allowed_flags.add("stale")
            if "no_bars_returned" not in flags or flags - allowed_flags:
                raise GatewayMarketDataError(
                    f"gateway {operation} returned invalid empty-session flags"
                )
            if history.stale and not allow_stale:
                raise GatewayMarketDataError(f"gateway {operation} data is stale")
            return []
        _require_usable_observation(
            history,
            operation=operation,
            allow_stale=allow_stale,
            max_age_seconds=max_age_seconds,
        )
        candles: list[dict] = []
        last_timestamp: int | None = None
        for candle in raw_bars:
            timestamp = int(candle.timestamp.timestamp() * 1000)
            if last_timestamp is not None and timestamp <= last_timestamp:
                raise GatewayMarketDataError(
                    f"gateway {operation} candles are not strictly ordered"
                )
            last_timestamp = timestamp
            open_price = _finite_number(candle.open, positive=True)
            high = _finite_number(candle.high, positive=True)
            low = _finite_number(candle.low, positive=True)
            close = _finite_number(candle.close, positive=True)
            volume = _finite_number(candle.volume)
            if high < max(open_price, low, close) or low > min(open_price, high, close):
                raise GatewayMarketDataError(
                    f"gateway {operation} returned invalid OHLC values"
                )
            if volume < 0:
                raise GatewayMarketDataError(
                    f"gateway {operation} returned negative volume"
                )
            candles.append(
                {
                    "datetime": timestamp,
                    "open": open_price,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                }
            )
        if not candles and not allow_empty:
            raise GatewayMarketDataError(f"gateway {operation} returned no candles")
        return candles


class DirectSchwabMarketDataProvider:
    """Delegate to the current client without owning its lifecycle or changing data."""

    def __init__(self, client: SchwabClientWrapper) -> None:
        self._client = client

    async def get_spot_price(self, symbol: str = "$SPX") -> float:
        return await self._client.get_spot_price(symbol)

    async def get_option_chain(
        self, symbol: str, expiration: dt.date
    ) -> dict[str, Any]:
        return await self._client.get_option_chain(symbol, expiration)

    async def get_intraday_bars(
        self, symbol: str = "$SPX", days_back: int = 1
    ) -> list[dict]:
        return await self._client.get_intraday_bars(symbol, days_back)

    async def get_intraday_bars_for_day(
        self,
        symbol: str,
        day: dt.date,
        *,
        include_extended_hours: bool = True,
    ) -> list[dict]:
        return await self._client.get_intraday_bars_for_day(
            symbol,
            day,
            include_extended_hours=include_extended_hours,
        )

    async def get_daily_bars(
        self, symbol: str, days_back: int = 10
    ) -> list[dict]:
        return await self._client.get_daily_bars(symbol, days_back)

    async def get_equity_quotes(
        self, symbols: list[str], *, batch_size: int = 150
    ) -> dict[str, dict[str, Any]]:
        return await self._client.get_equity_quotes(symbols, batch_size=batch_size)

    async def get_market_movers(
        self,
        index: str,
        *,
        sort_order: str = "PERCENT_CHANGE_UP",
        frequency: int | None = None,
    ) -> list[dict[str, Any]]:
        return await self._client.get_market_movers(
            index,
            sort_order=sort_order,
            frequency=frequency,
        )
