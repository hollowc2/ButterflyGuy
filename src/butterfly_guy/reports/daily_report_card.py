"""Daily report card — parse Schwab account data into structured report."""

from __future__ import annotations

import datetime as dt
from collections import deque
from dataclasses import dataclass, field
from typing import Any

from butterfly_guy.core.time_utils import EASTERN
from butterfly_guy.reports.daily_report_card_config import DailyReportCardSettings

CASH_TRANSACTION_TYPES = frozenset({
    "ACH_RECEIPT",
    "ACH_DISBURSEMENT",
    "CASH_RECEIPT",
    "CASH_DISBURSEMENT",
    "ELECTRONIC_FUND",
    "WIRE_OUT",
    "WIRE_IN",
    "JOURNAL",
    "DIVIDEND_OR_INTEREST",
    "MARGIN_CALL",
})


@dataclass(frozen=True)
class AccountBalances:
    starting_liquidation: float
    ending_liquidation: float
    buying_power: float
    available_funds: float
    maintenance_requirement: float
    day_trading_buying_power: float
    account_type: str

    @property
    def net_change(self) -> float:
        return self.ending_liquidation - self.starting_liquidation

    @property
    def net_change_pct(self) -> float:
        if self.starting_liquidation <= 0:
            return 0.0
        return self.net_change / self.starting_liquidation * 100.0


@dataclass(frozen=True)
class TradeResult:
    label: str
    pnl: float
    order_id: str | None = None
    time: dt.datetime | None = None


@dataclass(frozen=True)
class TradeLeg:
    symbol: str
    label: str
    quantity: float
    net_amount: float
    position_effect: str | None
    time: dt.datetime | None
    order_id: str | None


@dataclass(frozen=True)
class OpenPosition:
    symbol: str
    asset_type: str
    quantity: float
    market_value: float
    open_pnl: float
    is_zero_dte: bool


@dataclass(frozen=True)
class CashMovement:
    label: str
    amount: float


@dataclass(frozen=True)
class ActivitySummary:
    trade_count: int
    winners: int
    losers: int
    breakeven: int
    realized_pnl: float
    win_rate: float


@dataclass(frozen=True)
class DailyReportCard:
    report_date: dt.date
    generated_at: dt.datetime
    balances: AccountBalances
    activity: ActivitySummary
    top_winners: list[TradeResult]
    top_losers: list[TradeResult]
    open_positions: list[OpenPosition]
    rejected_order_count: int
    cash_movements: list[CashMovement]
    problems: list[str] = field(default_factory=list)


def transfer_total(card: DailyReportCard) -> float:
    return sum(m.amount for m in card.cash_movements)


def effective_start_balance(card: DailyReportCard) -> float:
    """Balance after transfers, before today's trading P&L.

    Schwab's initialBalances is pre-transfer; when cash moved intraday we
    derive the meaningful start from ending value minus realized trade P&L.
    """
    if card.cash_movements:
        if card.activity.trade_count:
            return card.balances.ending_liquidation - card.activity.realized_pnl
        return card.balances.starting_liquidation + transfer_total(card)
    return card.balances.starting_liquidation


def effective_pnl(card: DailyReportCard) -> float:
    """Day P&L relative to effective start (matches trading when transfers present)."""
    if card.activity.trade_count:
        return card.activity.realized_pnl
    return card.balances.ending_liquidation - effective_start_balance(card)


def effective_pnl_pct(card: DailyReportCard) -> float:
    start = effective_start_balance(card)
    if start <= 0:
        return 0.0
    return effective_pnl(card) / start * 100.0


def _float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _parse_time(value: Any) -> dt.datetime | None:
    if not value:
        return None
    if isinstance(value, dt.datetime):
        return value.astimezone(EASTERN) if value.tzinfo else value.replace(tzinfo=EASTERN)
    text = str(value)
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d+%H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(text, fmt)
            return parsed.astimezone(EASTERN)
        except ValueError:
            continue
    try:
        parsed = dt.datetime.fromisoformat(text.replace("Z", "+00:00"))
        return parsed.astimezone(EASTERN)
    except ValueError:
        return None


def parse_account_balances(account_data: dict[str, Any]) -> AccountBalances:
    acct = account_data.get("securitiesAccount", account_data)
    initial = acct.get("initialBalances", {})
    current = acct.get("currentBalances", {})
    return AccountBalances(
        starting_liquidation=_float(initial.get("liquidationValue")),
        ending_liquidation=_float(current.get("liquidationValue")),
        buying_power=_float(
            current.get("buyingPower")
            or current.get("buyingPowerNonMarginableTrade")
            or acct.get("buyingPower")
        ),
        available_funds=_float(current.get("availableFunds")),
        maintenance_requirement=_float(
            current.get("maintenanceRequirement") or acct.get("maintenanceRequirement")
        ),
        day_trading_buying_power=_float(
            current.get("dayTradingBuyingPower") or acct.get("dayTradingBuyingPower")
        ),
        account_type=str(acct.get("type", "UNKNOWN")),
    )


def _is_currency_instrument(instrument: dict[str, Any]) -> bool:
    asset_type = instrument.get("assetType", "")
    symbol = instrument.get("symbol", "")
    return asset_type == "CURRENCY" or symbol == "CURRENCY_USD"


def _instrument_label(instrument: dict[str, Any]) -> str:
    if _is_currency_instrument(instrument):
        return ""
    symbol = instrument.get("symbol") or instrument.get("underlyingSymbol") or "?"
    asset_type = instrument.get("assetType", "")
    if asset_type == "OPTION":
        put_call = instrument.get("putCall", "")
        strike = instrument.get("strikePrice")
        exp = instrument.get("expirationDate") or instrument.get("maturityDate")
        exp_str = ""
        if exp:
            exp_str = str(exp)[:10]
        parts = [symbol]
        if put_call:
            parts.append(put_call)
        if strike is not None:
            parts.append(f"${strike:g}")
        if exp_str:
            parts.append(exp_str)
        return " ".join(parts)
    return symbol


def _extract_order_id(txn: dict[str, Any], transfer_items: list[dict[str, Any]]) -> str | None:
    order_id = txn.get("orderId")
    if order_id:
        return str(order_id)
    for item in transfer_items:
        item_order = item.get("orderId")
        if item_order:
            return str(item_order)
    return None


def _extract_trade_leg(txn: dict[str, Any]) -> TradeLeg | None:
    transfer_items = txn.get("transferItems") or []
    if not transfer_items and "transactionItem" in txn:
        transfer_items = [txn["transactionItem"]]

    instrument_item: dict[str, Any] | None = None
    for item in transfer_items:
        instrument = item.get("instrument", {})
        if instrument and not _is_currency_instrument(instrument):
            instrument_item = item
            break
    if instrument_item is None:
        return None

    instrument = instrument_item["instrument"]
    symbol = instrument.get("symbol") or instrument.get("underlyingSymbol") or "?"
    return TradeLeg(
        symbol=symbol,
        label=_instrument_label(instrument),
        quantity=abs(_float(instrument_item.get("amount"))),
        net_amount=_float(txn.get("netAmount")),
        position_effect=instrument_item.get("positionEffect"),
        time=_parse_time(txn.get("time") or txn.get("tradeDate")),
        order_id=_extract_order_id(txn, transfer_items),
    )


def _parse_trades_without_position_effect(
    transactions: list[dict[str, Any]],
) -> list[TradeResult]:
    """Fallback when Schwab omits OPENING/CLOSING (e.g. some option closes)."""
    trades: list[TradeResult] = []
    by_order: dict[str, TradeResult] = {}

    for txn in transactions:
        leg = _extract_trade_leg(txn)
        if leg is None:
            continue
        if leg.order_id and leg.order_id in by_order:
            existing = by_order[leg.order_id]
            by_order[leg.order_id] = TradeResult(
                label=existing.label,
                pnl=existing.pnl + leg.net_amount,
                order_id=leg.order_id,
                time=existing.time or leg.time,
            )
        elif leg.order_id:
            by_order[leg.order_id] = TradeResult(
                label=leg.label,
                pnl=leg.net_amount,
                order_id=leg.order_id,
                time=leg.time,
            )
        else:
            trades.append(
                TradeResult(label=leg.label, pnl=leg.net_amount, time=leg.time)
            )

    trades.extend(by_order.values())
    return trades


def _match_round_trips_fifo(legs: list[TradeLeg]) -> list[TradeResult]:
    """Pair OPENING and CLOSING legs into round-trip realized P&L."""
    open_queues: dict[str, deque[dict[str, float]]] = {}
    round_trips: list[TradeResult] = []
    sorted_legs = sorted(
        legs,
        key=lambda leg: leg.time or dt.datetime.min.replace(tzinfo=EASTERN),
    )

    for leg in sorted_legs:
        if leg.position_effect == "OPENING":
            if leg.quantity <= 0:
                continue
            open_queues.setdefault(leg.symbol, deque()).append(
                {"qty": leg.quantity, "net_amount": leg.net_amount}
            )
            continue

        if leg.position_effect != "CLOSING" or leg.quantity <= 0:
            continue

        remaining = leg.quantity
        pnl = leg.net_amount
        queue = open_queues.setdefault(leg.symbol, deque())

        while remaining > 0 and queue:
            lot = queue[0]
            matched = min(remaining, lot["qty"])
            if lot["qty"] > 0:
                fraction = matched / lot["qty"]
                pnl += lot["net_amount"] * fraction
                lot["qty"] -= matched
                lot["net_amount"] -= lot["net_amount"] * fraction
                remaining -= matched
            if lot["qty"] <= 1e-9:
                queue.popleft()

        round_trips.append(
            TradeResult(
                label=leg.label,
                pnl=pnl,
                order_id=leg.order_id,
                time=leg.time,
            )
        )

    return round_trips


def parse_trade_transactions(transactions: list[dict[str, Any]]) -> list[TradeResult]:
    """Parse TRADE transactions into round-trip realized P&L."""
    legs: list[TradeLeg] = []
    fallback_txns: list[dict[str, Any]] = []

    for txn in transactions:
        if txn.get("type") != "TRADE":
            continue
        leg = _extract_trade_leg(txn)
        if leg is None:
            continue
        if leg.position_effect in ("OPENING", "CLOSING"):
            legs.append(leg)
        else:
            fallback_txns.append(txn)

    trades = _match_round_trips_fifo(legs)
    trades.extend(_parse_trades_without_position_effect(fallback_txns))
    return trades


def parse_cash_movements(transactions: list[dict[str, Any]]) -> list[CashMovement]:
    movements: list[CashMovement] = []
    for txn in transactions:
        txn_type = txn.get("type", "")
        if txn_type not in CASH_TRANSACTION_TYPES:
            continue
        amount = _float(txn.get("netAmount"))
        label = txn_type.replace("_", " ").title()
        desc = txn.get("description")
        if desc:
            label = f"{label}: {desc}"
        movements.append(CashMovement(label=label, amount=amount))
    return movements


def _is_zero_dte_option(instrument: dict[str, Any], report_date: dt.date) -> bool:
    if instrument.get("assetType") != "OPTION":
        return False
    exp_raw = instrument.get("expirationDate") or instrument.get("maturityDate")
    if not exp_raw:
        return False
    exp_date = dt.date.fromisoformat(str(exp_raw)[:10])
    return exp_date == report_date


def parse_open_positions(
    account_data: dict[str, Any],
    report_date: dt.date,
) -> list[OpenPosition]:
    acct = account_data.get("securitiesAccount", account_data)
    positions = acct.get("positions") or []
    open_positions: list[OpenPosition] = []
    for pos in positions:
        instrument = pos.get("instrument", {})
        long_qty = _float(pos.get("longQuantity"))
        short_qty = _float(pos.get("shortQuantity"))
        quantity = long_qty - short_qty
        if quantity == 0:
            continue
        symbol = _instrument_label(instrument)
        open_positions.append(
            OpenPosition(
                symbol=symbol,
                asset_type=str(instrument.get("assetType", "")),
                quantity=quantity,
                market_value=_float(pos.get("marketValue")),
                open_pnl=_float(
                    pos.get("longOpenProfitLoss") or pos.get("shortOpenProfitLoss")
                ),
                is_zero_dte=_is_zero_dte_option(instrument, report_date),
            )
        )
    return open_positions


def summarize_activity(trades: list[TradeResult]) -> ActivitySummary:
    if not trades:
        return ActivitySummary(0, 0, 0, 0, 0.0, 0.0)
    winners = sum(1 for t in trades if t.pnl > 0)
    losers = sum(1 for t in trades if t.pnl < 0)
    breakeven = sum(1 for t in trades if t.pnl == 0)
    realized = sum(t.pnl for t in trades)
    win_rate = winners / len(trades) * 100.0 if trades else 0.0
    return ActivitySummary(
        trade_count=len(trades),
        winners=winners,
        losers=losers,
        breakeven=breakeven,
        realized_pnl=realized,
        win_rate=win_rate,
    )


def count_rejected_orders(orders: list[dict[str, Any]]) -> int:
    return sum(1 for o in orders if o.get("status") == "REJECTED")


def detect_problems(
    *,
    balances: AccountBalances,
    activity: ActivitySummary,
    trades: list[TradeResult],
    open_positions: list[OpenPosition],
    rejected_order_count: int,
    cash_movements: list[CashMovement],
    settings: DailyReportCardSettings,
) -> list[str]:
    problems: list[str] = []
    thresholds = settings.thresholds

    # Large-loss check uses effective start when transfers exist (see effective_* helpers).
    if activity.trade_count:
        eff_start = (
            balances.ending_liquidation - activity.realized_pnl
            if cash_movements
            else balances.starting_liquidation
        )
        trading_pnl = activity.realized_pnl
    else:
        xfer = sum(m.amount for m in cash_movements)
        eff_start = balances.starting_liquidation + xfer if cash_movements else balances.starting_liquidation
        trading_pnl = balances.ending_liquidation - eff_start
    trading_pct = trading_pnl / eff_start * 100.0 if eff_start > 0 else 0.0
    if trading_pct <= -thresholds.large_loss_day_pct:
        problems.append(
            f"Down {trading_pct:.1f}% on trades (${trading_pnl:+,.2f})"
        )

    if trades:
        worst = min(trades, key=lambda t: t.pnl)
        if worst.pnl <= -thresholds.large_single_loss:
            problems.append(f"Worst trade: {worst.label} ${worst.pnl:+,.2f}")

    zero_dte = [p for p in open_positions if p.is_zero_dte]
    if zero_dte:
        for pos in zero_dte[:3]:
            problems.append(f"Open 0-DTE position: {pos.symbol} (qty {pos.quantity:g})")
        if len(zero_dte) > 3:
            problems.append(f"{len(zero_dte) - 3} more open 0-DTE positions")

    if balances.buying_power < thresholds.low_buying_power:
        problems.append(f"Low buying power: ${balances.buying_power:,.2f} remaining")

    if rejected_order_count:
        noun = "order" if rejected_order_count == 1 else "orders"
        problems.append(f"{rejected_order_count} {noun} REJECTED today")

    if not cash_movements and activity.trade_count:
        unexplained = balances.net_change - activity.realized_pnl
        if abs(unexplained) > 50:
            problems.append(
                f"Balance change differs from trade P&L by ${unexplained:+,.2f}"
            )

    return problems


def rank_trades(
    trades: list[TradeResult],
    *,
    top_n: int,
) -> tuple[list[TradeResult], list[TradeResult]]:
    if not trades:
        return [], []
    sorted_trades = sorted(trades, key=lambda t: t.pnl, reverse=True)
    winners = [t for t in sorted_trades if t.pnl > 0][:top_n]
    losers = sorted(
        [t for t in trades if t.pnl < 0],
        key=lambda t: t.pnl,
    )[:top_n]
    return winners, losers


def build_daily_report_card(
    *,
    report_date: dt.date,
    generated_at: dt.datetime,
    account_data: dict[str, Any],
    transactions: list[dict[str, Any]],
    orders: list[dict[str, Any]],
    settings: DailyReportCardSettings,
) -> DailyReportCard:
    balances = parse_account_balances(account_data)
    trades = parse_trade_transactions(transactions)
    activity = summarize_activity(trades)
    top_winners, top_losers = rank_trades(
        trades,
        top_n=settings.thresholds.top_trades_count,
    )
    open_positions = parse_open_positions(account_data, report_date)
    cash_movements = parse_cash_movements(transactions)
    rejected_order_count = count_rejected_orders(orders)
    problems = detect_problems(
        balances=balances,
        activity=activity,
        trades=trades,
        open_positions=open_positions,
        rejected_order_count=rejected_order_count,
        cash_movements=cash_movements,
        settings=settings,
    )
    return DailyReportCard(
        report_date=report_date,
        generated_at=generated_at,
        balances=balances,
        activity=activity,
        top_winners=top_winners,
        top_losers=top_losers,
        open_positions=open_positions,
        rejected_order_count=rejected_order_count,
        cash_movements=cash_movements,
        problems=problems,
    )
