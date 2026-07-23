"""Immutable normalized market snapshots shared by candidate evaluators."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, replace
from types import MappingProxyType
from typing import Any, Iterable, Literal, Mapping

from butterfly_guy.data.schemas import OptionQuote

UTC = dt.timezone.utc


def _aware_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        raise ValueError("snapshot timestamps must be timezone-aware")
    return value.astimezone(UTC)


@dataclass(frozen=True, order=True)
class SnapshotIdentity:
    instance: str
    sequence: int

    def __post_init__(self) -> None:
        if not self.instance:
            raise ValueError("snapshot instance is required")
        if self.sequence < 1:
            raise ValueError("snapshot sequence must be positive")


@dataclass(frozen=True)
class MarketSnapshot:
    """One atomically published, replayable view of candidate market data."""

    identity: SnapshotIdentity
    captured_at: dt.datetime
    expiration: dt.date
    spot: float
    vix: float
    session_open: float
    previous_close: float
    quotes: tuple[OptionQuote, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "captured_at", _aware_utc(self.captured_at))
        object.__setattr__(self, "quotes", tuple(self.quotes))
        if min(self.spot, self.vix, self.session_open, self.previous_close) <= 0:
            raise ValueError("snapshot context prices must be positive")
        seen: set[tuple[str, float, str]] = set()
        for quote in self.quotes:
            if quote.expiration != self.expiration:
                raise ValueError("quote expiration does not match snapshot")
            key = (quote.symbol, quote.strike, quote.option_type)
            if key in seen:
                raise ValueError(f"duplicate normalized quote: {key}")
            seen.add(key)

    @property
    def instance(self) -> str:
        return self.identity.instance

    @property
    def sequence(self) -> int:
        return self.identity.sequence

    def age_seconds(self, now: dt.datetime | None = None) -> float:
        current = _aware_utc(now or dt.datetime.now(UTC))
        return max(0.0, (current - self.captured_at).total_seconds())

    def require_fresh(
        self,
        max_age_seconds: float,
        now: dt.datetime | None = None,
    ) -> MarketSnapshot:
        age = self.age_seconds(now)
        if age > max_age_seconds:
            raise StaleSnapshotError(age, max_age_seconds)
        return self

    def by_symbol(self) -> Mapping[str, OptionQuote]:
        return MappingProxyType({quote.symbol: quote for quote in self.quotes})

    def by_strike_type(self) -> Mapping[tuple[float, str], OptionQuote]:
        return MappingProxyType(
            {(quote.strike, quote.option_type): quote for quote in self.quotes}
        )

    def leg_quotes(self, symbols: Iterable[str]) -> MarketSnapshot:
        wanted = {symbol for symbol in symbols if symbol}
        if not wanted:
            raise ValueError("at least one leg symbol is required")
        selected = tuple(quote for quote in self.quotes if quote.symbol in wanted)
        if {quote.symbol for quote in selected} != wanted:
            missing = sorted(wanted - {quote.symbol for quote in selected})
            raise KeyError(f"snapshot is missing leg quotes: {missing}")
        return replace(self, quotes=selected)

    def to_dict(self) -> dict[str, Any]:
        quotes = []
        for quote in sorted(
            self.quotes,
            key=lambda item: (item.option_type, item.strike, item.symbol),
        ):
            row = asdict(quote)
            row["expiration"] = quote.expiration.isoformat()
            quotes.append(row)
        return {
            "instance": self.instance,
            "sequence": self.sequence,
            "captured_at": self.captured_at.isoformat(),
            "expiration": self.expiration.isoformat(),
            "spot": self.spot,
            "vix": self.vix,
            "session_open": self.session_open,
            "previous_close": self.previous_close,
            "quotes": quotes,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> MarketSnapshot:
        expiration = dt.date.fromisoformat(str(payload["expiration"]))
        quotes: list[OptionQuote] = []
        for raw in payload.get("quotes", []):
            row = dict(raw)
            row["expiration"] = dt.date.fromisoformat(str(row["expiration"]))
            row["strike"] = float(row["strike"])
            for key in (
                "bid",
                "ask",
                "mark",
                "last",
                "iv",
                "delta",
                "gamma",
                "theta",
                "vega",
                "rho",
                "intrinsic_value",
                "time_value",
                "multiplier",
                "theoretical_value",
            ):
                if key in row:
                    row[key] = float(row[key] or 0)
            for key in (
                "volume",
                "open_interest",
                "bid_size",
                "ask_size",
                "days_to_expiration",
            ):
                if key in row:
                    row[key] = int(row[key] or 0)
            quotes.append(OptionQuote(**row))
        return cls(
            identity=SnapshotIdentity(
                instance=str(payload["instance"]),
                sequence=int(payload["sequence"]),
            ),
            captured_at=dt.datetime.fromisoformat(str(payload["captured_at"])),
            expiration=expiration,
            spot=float(payload["spot"]),
            vix=float(payload["vix"]),
            session_open=float(payload["session_open"]),
            previous_close=float(payload["previous_close"]),
            quotes=tuple(quotes),
        )


class SnapshotUnavailableError(RuntimeError):
    """No complete snapshot is currently available."""


class StaleSnapshotError(SnapshotUnavailableError):
    def __init__(self, age_seconds: float, max_age_seconds: float) -> None:
        self.age_seconds = age_seconds
        self.max_age_seconds = max_age_seconds
        super().__init__(
            f"snapshot is stale ({age_seconds:.3f}s > {max_age_seconds:.3f}s)"
        )


LeaseKind = Literal["entry", "position"]
