"""First-pass, leakage-safe discovery across structurally different 0-DTE trades.

This intentionally uses a small, fixed hypothesis set. Every leg crosses the
recorded spread and pays round-trip commission; selection uses entry-time data
only. Run from the host with DATABASE__HOST=127.0.0.1 when TimescaleDB is in
Docker.
"""

from __future__ import annotations

import argparse
import asyncio
import csv
import datetime as dt
import json
import math
import random
import statistics
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

import asyncpg

from butterfly_guy.scripts.run_backtest_db import resolve_db_dsn

EASTERN = ZoneInfo("America/New_York")
DEFAULT_ENTRY_TIME = dt.time(10, 0)
DEFAULT_EXIT_TIME = dt.time(15, 45)
COMMISSION = 0.65
RISK_FRACTION = 0.01


@dataclass(frozen=True)
class Quote:
    symbol: str
    strike: float
    option_type: str
    bid: float
    ask: float
    mark: float
    delta: float
    iv: float
    volume: int
    open_interest: int
    spot: float
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0


@dataclass(frozen=True)
class Leg:
    quote: Quote
    quantity: int


@dataclass(frozen=True)
class Trade:
    strategy: str
    underlying: str
    date: dt.date
    pnl: float
    max_risk: float
    r_multiple: float
    entry_cost: float
    entry_spot: float
    open_to_entry: float
    atm_iv: float
    iv_percentile: float | None
    vix: float
    duration_minutes: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover simple 0-DTE option strategies")
    parser.add_argument(
        "--assets", default="SPX,NDX,XSP", help="Comma-separated subset of SPX,NDX,XSP"
    )
    parser.add_argument("--entry-time", type=dt.time.fromisoformat, default=DEFAULT_ENTRY_TIME)
    parser.add_argument("--exit-time", type=dt.time.fromisoformat, default=DEFAULT_EXIT_TIME)
    parser.add_argument("--report-strategy", choices=STRATEGIES)
    parser.add_argument("--output-dir", type=Path, default=Path("reports/strategy_discovery"))
    return parser.parse_args()


def liquid(quote: Quote) -> bool:
    spread = quote.ask - quote.bid
    return (
        quote.bid > 0
        and quote.ask >= quote.bid
        and quote.open_interest >= 10
        and spread <= max(0.25, quote.mark * 0.50)
    )


def closest_delta(quotes: Iterable[Quote], option_type: str, target: float) -> Quote | None:
    eligible = [q for q in quotes if q.option_type == option_type and liquid(q)]
    return min(eligible, key=lambda q: abs(abs(q.delta) - target), default=None)


def atm_pair(quotes: Iterable[Quote], spot: float) -> tuple[Quote, Quote] | None:
    by_strike: dict[float, dict[str, Quote]] = defaultdict(dict)
    for quote in quotes:
        if liquid(quote):
            by_strike[quote.strike][quote.option_type] = quote
    strikes = [strike for strike, pair in by_strike.items() if {"CALL", "PUT"} <= pair.keys()]
    if not strikes:
        return None
    pair = by_strike[min(strikes, key=lambda strike: abs(strike - spot))]
    return pair["CALL"], pair["PUT"]


def vertical(
    quotes: list[Quote], direction: str, long_delta: float = 0.55, short_delta: float = 0.25
) -> list[Leg] | None:
    long = closest_delta(quotes, direction, long_delta)
    short = closest_delta(quotes, direction, short_delta)
    if long is None or short is None or long.symbol == short.symbol:
        return None
    if direction == "CALL" and long.strike >= short.strike:
        return None
    if direction == "PUT" and long.strike <= short.strike:
        return None
    return [Leg(long, 1), Leg(short, -1)]


def iron_fly(quotes: list[Quote], spot: float) -> list[Leg] | None:
    pair = atm_pair(quotes, spot)
    long_call = closest_delta(quotes, "CALL", 0.10)
    long_put = closest_delta(quotes, "PUT", 0.10)
    if pair is None or long_call is None or long_put is None:
        return None
    short_call, short_put = pair
    if long_call.strike <= short_call.strike or long_put.strike >= short_put.strike:
        return None
    return [Leg(short_call, -1), Leg(short_put, -1), Leg(long_call, 1), Leg(long_put, 1)]


def iron_condor(quotes: list[Quote]) -> list[Leg] | None:
    short_call = closest_delta(quotes, "CALL", 0.20)
    long_call = closest_delta(quotes, "CALL", 0.05)
    short_put = closest_delta(quotes, "PUT", 0.20)
    long_put = closest_delta(quotes, "PUT", 0.05)
    if None in {short_call, long_call, short_put, long_put}:
        return None
    assert short_call and long_call and short_put and long_put
    if long_call.strike <= short_call.strike or long_put.strike >= short_put.strike:
        return None
    return [Leg(short_call, -1), Leg(long_call, 1), Leg(short_put, -1), Leg(long_put, 1)]


def credit_spread(quotes: list[Quote], option_type: str) -> list[Leg] | None:
    short = closest_delta(quotes, option_type, 0.20)
    long = closest_delta(quotes, option_type, 0.05)
    if short is None or long is None or short.symbol == long.symbol:
        return None
    if option_type == "CALL" and long.strike <= short.strike:
        return None
    if option_type == "PUT" and long.strike >= short.strike:
        return None
    return [Leg(short, -1), Leg(long, 1)]


def butterfly(
    quotes: list[Quote], spot: float, option_type: str, directional: bool
) -> list[Leg] | None:
    same_type = [quote for quote in quotes if quote.option_type == option_type and liquid(quote)]
    center = (
        closest_delta(same_type, option_type, 0.25)
        if directional
        else min(same_type, key=lambda quote: abs(quote.strike - spot), default=None)
    )
    if center is None:
        return None
    target_width = spot * 0.003
    lower = min(
        (quote for quote in same_type if quote.strike < center.strike),
        key=lambda quote: abs(quote.strike - (center.strike - target_width)),
        default=None,
    )
    upper = min(
        (quote for quote in same_type if quote.strike > center.strike),
        key=lambda quote: abs(quote.strike - (center.strike + target_width)),
        default=None,
    )
    return [Leg(lower, 1), Leg(center, -2), Leg(upper, 1)] if lower and upper else None


def make_legs(
    strategy: str,
    quotes: list[Quote],
    spot: float,
    open_to_entry: float,
    iv_percentile: float | None,
) -> list[Leg] | None:
    pair = atm_pair(quotes, spot)
    if strategy in {
        "long_atm_straddle",
        "low_iv_straddle",
        "underpriced_straddle",
        "high_gamma_straddle",
    }:
        if strategy == "low_iv_straddle" and (iv_percentile is None or iv_percentile > 0.35):
            return None
        return [Leg(pair[0], 1), Leg(pair[1], 1)] if pair else None
    if strategy == "long_25d_strangle":
        call = closest_delta(quotes, "CALL", 0.25)
        put = closest_delta(quotes, "PUT", 0.25)
        return [Leg(call, 1), Leg(put, 1)] if call and put else None
    if strategy == "short_iron_fly":
        return iron_fly(quotes, spot)
    if strategy in {"short_iron_condor", "high_iv_condor"}:
        if strategy == "high_iv_condor" and (iv_percentile is None or iv_percentile < 0.65):
            return None
        return iron_condor(quotes)
    direction = "CALL" if open_to_entry >= 0 else "PUT"
    if strategy == "atm_butterfly":
        return butterfly(quotes, spot, "CALL", directional=False)
    if strategy == "trend_butterfly":
        return butterfly(quotes, spot, direction, directional=True)
    if strategy == "trend_credit_spread":
        return credit_spread(quotes, "PUT" if direction == "CALL" else "CALL")
    if strategy == "reversal_credit_spread":
        return credit_spread(quotes, direction)
    if strategy == "reversal_debit":
        direction = "PUT" if direction == "CALL" else "CALL"
    if strategy == "strong_trend_debit" and abs(open_to_entry) < 0.0015:
        return None
    return vertical(quotes, direction)


def entry_cost(legs: list[Leg]) -> float:
    return sum(
        leg.quantity * (leg.quote.ask if leg.quantity > 0 else leg.quote.bid)
        for leg in legs
    )


def exit_value(legs: list[Leg], exits: dict[str, Quote]) -> float | None:
    if any(leg.quote.symbol not in exits for leg in legs):
        return None
    return sum(
        leg.quantity
        * (exits[leg.quote.symbol].bid if leg.quantity > 0 else exits[leg.quote.symbol].ask)
        for leg in legs
    )


def max_risk_points(legs: list[Leg], cost: float) -> float | None:
    if cost > 0:
        return cost
    credit = -cost
    widths: list[float] = []
    for option_type in ("CALL", "PUT"):
        longs = [
            leg.quote.strike
            for leg in legs
            if leg.quote.option_type == option_type and leg.quantity > 0
        ]
        shorts = [
            leg.quote.strike
            for leg in legs
            if leg.quote.option_type == option_type and leg.quantity < 0
        ]
        if longs and shorts:
            widths.extend(abs(long - short) for long in longs for short in shorts)
    risk = max(widths, default=0.0) - credit
    return risk if risk > 0 else None


def price_trade(
    strategy: str,
    underlying: str,
    date: dt.date,
    legs: list[Leg],
    exits: dict[str, Quote],
    open_to_entry: float,
    atm_iv: float,
    iv_percentile: float | None,
    vix: float,
    duration_minutes: int,
) -> Trade | None:
    cost = entry_cost(legs)
    value = exit_value(legs, exits)
    risk_points = max_risk_points(legs, cost)
    if value is None or risk_points is None:
        return None
    fees = sum(abs(leg.quantity) for leg in legs) * COMMISSION * 2
    pnl = (value - cost) * 100 - fees
    max_risk = risk_points * 100 + fees
    return Trade(
        strategy=strategy,
        underlying=underlying,
        date=date,
        pnl=pnl,
        max_risk=max_risk,
        r_multiple=pnl / max_risk,
        entry_cost=cost,
        entry_spot=legs[0].quote.spot,
        open_to_entry=open_to_entry,
        atm_iv=atm_iv,
        iv_percentile=iv_percentile,
        vix=vix,
        duration_minutes=duration_minutes,
    )


def percentile(value: float, history: list[float], minimum: int = 20) -> float | None:
    if len(history) < minimum:
        return None
    return sum(item <= value for item in history) / len(history)


def drawdown(returns: list[float]) -> tuple[float, list[float]]:
    equity = peak = 1.0
    max_dd = 0.0
    curve: list[float] = []
    for value in returns:
        equity *= 1 + value
        peak = max(peak, equity)
        dd = equity / peak - 1
        curve.append(dd)
        max_dd = min(max_dd, dd)
    return max_dd, curve


def summarize(trades: list[Trade], session_count: int) -> dict[str, object]:
    if not trades:
        return {"trade_count": 0}
    pnls = [trade.pnl for trade in trades]
    returns = [trade.r_multiple * RISK_FRACTION for trade in trades]
    mean = statistics.mean(returns)
    stdev = statistics.stdev(returns) if len(returns) > 1 else 0.0
    downside = math.sqrt(statistics.mean([min(value, 0.0) ** 2 for value in returns]))
    max_dd, _ = drawdown(returns)
    equity = math.prod(1 + value for value in returns)
    years = max((trades[-1].date - trades[0].date).days / 365.25, 1 / 365.25)
    cagr = equity ** (1 / years) - 1 if equity > 0 else -1.0
    wins = [pnl for pnl in pnls if pnl > 0]
    losses = [pnl for pnl in pnls if pnl < 0]
    gross_loss = abs(sum(losses))
    return {
        "trade_count": len(trades),
        "start": trades[0].date.isoformat(),
        "end": trades[-1].date.isoformat(),
        "cagr": cagr,
        "sharpe": mean / stdev * math.sqrt(252) if stdev else 0.0,
        "sortino": mean / downside * math.sqrt(252) if downside else 0.0,
        "calmar": cagr / abs(max_dd) if max_dd else 0.0,
        "profit_factor": sum(wins) / gross_loss if gross_loss else math.inf,
        "win_rate": len(wins) / len(pnls),
        "expectancy": statistics.mean(pnls),
        "max_drawdown": max_dd,
        "recovery_factor": (equity - 1) / abs(max_dd) if max_dd else 0.0,
        "average_trade": statistics.mean(pnls),
        "average_winner": statistics.mean(wins) if wins else 0.0,
        "average_loser": statistics.mean(losses) if losses else 0.0,
        "exposure": len(trades) / max(session_count, 1) * trades[0].duration_minutes / 390,
        "total_pnl": sum(pnls),
        "ending_equity": equity,
    }


def split_metrics(trades: list[Trade], all_dates: list[dt.date]) -> dict[str, dict[str, object]]:
    dates = sorted(all_dates)
    train_end = dates[max(1, int(len(dates) * 0.60)) - 1]
    validation_end = dates[max(1, int(len(dates) * 0.80)) - 1]
    segments = {
        "train": [trade for trade in trades if trade.date <= train_end],
        "validation": [trade for trade in trades if train_end < trade.date <= validation_end],
        "test": [trade for trade in trades if trade.date > validation_end],
        "full": trades,
    }
    return {name: summarize(rows, len(dates)) for name, rows in segments.items()}


async def load_asset(
    conn: asyncpg.Connection,
    underlying: str,
    entry_time: dt.time,
    exit_time: dt.time,
) -> tuple[dict[dt.date, dict[str, list[Quote]]], dict[dt.date, float]]:
    rows = await conn.fetch(
        """
        WITH targets(label, target_time) AS (
            VALUES ('open', time '09:35'), ('entry', $2::time), ('exit', $3::time)
        ), dates AS (
            SELECT date AS trade_date FROM daily_bars WHERE underlying = $1
        ), chosen AS (
            SELECT d.trade_date, t.label, snapshot.snapshot_time
            FROM dates d CROSS JOIN targets t
            JOIN LATERAL (
                SELECT MAX(snapshot_time) AS snapshot_time
                FROM option_chain_snapshots
                WHERE underlying = $1 AND expiration = d.trade_date
                  AND snapshot_time BETWEEN
                      ((d.trade_date + t.target_time) AT TIME ZONE 'America/New_York')
                          - interval '2 minutes'
                      AND ((d.trade_date + t.target_time) AT TIME ZONE 'America/New_York')
            ) snapshot ON snapshot.snapshot_time IS NOT NULL
        )
        SELECT c.trade_date, c.label, o.symbol, o.strike, o.option_type, o.bid, o.ask,
               o.mark, o.delta, o.iv, o.volume, o.open_interest, o.spot_price,
               o.gamma, o.theta, o.vega
        FROM chosen c
        JOIN option_chain_snapshots o
          ON o.underlying = $1 AND o.expiration = c.trade_date
         AND o.snapshot_time = c.snapshot_time
        ORDER BY c.trade_date, c.label, o.strike, o.option_type
        """,
        underlying,
        entry_time,
        exit_time,
    )
    snapshots: dict[dt.date, dict[str, list[Quote]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        snapshots[row["trade_date"]][row["label"]].append(
            Quote(
                symbol=row["symbol"] or f"{row['option_type']}_{row['strike']}",
                strike=float(row["strike"]),
                option_type=row["option_type"],
                bid=float(row["bid"] or 0),
                ask=float(row["ask"] or 0),
                mark=float(row["mark"] or 0),
                delta=float(row["delta"] or 0),
                iv=float(row["iv"] or 0),
                volume=int(row["volume"] or 0),
                open_interest=int(row["open_interest"] or 0),
                spot=float(row["spot_price"] or 0),
                gamma=float(row["gamma"] or 0),
                theta=float(row["theta"] or 0),
                vega=float(row["vega"] or 0),
            )
        )
    vix_rows = await conn.fetch(
        """
        SELECT d.date, v.price
        FROM (SELECT date FROM daily_bars WHERE underlying = $1) d
        JOIN LATERAL (
            SELECT price FROM spot_prices
            WHERE underlying = '$VIX'
              AND ts <= ((d.date + $2::time) AT TIME ZONE 'America/New_York')
              AND ts >= ((d.date + $2::time) AT TIME ZONE 'America/New_York')
                  - interval '2 minutes'
            ORDER BY ts DESC LIMIT 1
        ) v ON true
        """,
        underlying,
        entry_time,
    )
    return snapshots, {row["date"]: float(row["price"]) for row in vix_rows}


STRATEGIES = (
    "long_atm_straddle",
    "long_25d_strangle",
    "short_iron_fly",
    "short_iron_condor",
    "trend_debit",
    "reversal_debit",
    "strong_trend_debit",
    "low_iv_straddle",
    "high_iv_condor",
    "atm_butterfly",
    "trend_butterfly",
    "trend_credit_spread",
    "reversal_credit_spread",
    "underpriced_straddle",
    "high_gamma_straddle",
)


def research_asset(
    underlying: str,
    snapshots: dict[dt.date, dict[str, list[Quote]]],
    vix: dict[dt.date, float],
    duration_minutes: int,
) -> tuple[list[Trade], dict[str, dict[str, dict[str, object]]]]:
    trades: list[Trade] = []
    iv_history: list[float] = []
    realized_move_history: list[float] = []
    gamma_efficiency_history: list[float] = []
    usable_dates: list[dt.date] = []
    for date, day in sorted(snapshots.items()):
        if not {"open", "entry", "exit"} <= day.keys() or date not in vix:
            continue
        entry = day["entry"]
        pair = atm_pair(entry, entry[0].spot)
        if pair is None or not day["open"]:
            continue
        atm_iv = statistics.mean([pair[0].iv, pair[1].iv])
        iv_pct = percentile(atm_iv, iv_history)
        straddle_cost_fraction = (pair[0].ask + pair[1].ask) / entry[0].spot
        realized_forecast = (
            statistics.median(realized_move_history[-20:])
            if len(realized_move_history) >= 20
            else None
        )
        gamma_efficiency = (pair[0].gamma + pair[1].gamma) / max(
            abs(pair[0].theta) + abs(pair[1].theta), 1e-9
        )
        gamma_percentile = percentile(gamma_efficiency, gamma_efficiency_history)
        open_spot = day["open"][0].spot
        open_to_entry = entry[0].spot / open_spot - 1
        exits = {quote.symbol: quote for quote in day["exit"]}
        usable_dates.append(date)
        for strategy in STRATEGIES:
            if strategy == "underpriced_straddle" and (
                realized_forecast is None or straddle_cost_fraction >= realized_forecast
            ):
                continue
            if strategy == "high_gamma_straddle" and (
                gamma_percentile is None or gamma_percentile < 0.65
            ):
                continue
            legs = make_legs(strategy, entry, entry[0].spot, open_to_entry, iv_pct)
            if legs is None:
                continue
            trade = price_trade(
                strategy,
                underlying,
                date,
                legs,
                exits,
                open_to_entry,
                atm_iv,
                iv_pct,
                vix[date],
                duration_minutes,
            )
            if trade:
                trades.append(trade)
        iv_history.append(atm_iv)
        realized_move_history.append(abs(day["exit"][0].spot / entry[0].spot - 1))
        gamma_efficiency_history.append(gamma_efficiency)
    metrics = {
        strategy: split_metrics(
            sorted([trade for trade in trades if trade.strategy == strategy], key=lambda t: t.date),
            usable_dates,
        )
        for strategy in STRATEGIES
    }
    return trades, metrics


def write_outputs(
    output_dir: Path,
    trades: list[Trade],
    metrics: dict[str, dict[str, dict[str, dict[str, object]]]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "trades.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(trades[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(trade) for trade in trades)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2, allow_nan=True))


def period_returns(trades: list[Trade], period: str) -> dict[str, float]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for trade in trades:
        key = trade.date.strftime("%Y-%m" if period == "month" else "%Y")
        grouped[key].append(trade.r_multiple * RISK_FRACTION)
    return {key: math.prod(1 + value for value in values) - 1 for key, values in grouped.items()}


def bootstrap_report(trades: list[Trade], simulations: int = 5000) -> dict[str, object]:
    rng = random.Random(20260714)
    r_values = [trade.r_multiple for trade in trades]
    boot_means: list[float] = []
    boot_sharpes: list[float] = []
    ending_equities: list[float] = []
    maximum_drawdowns: list[float] = []
    ruin_count = 0
    for _ in range(simulations):
        sample = [rng.choice(r_values) for _ in r_values]
        boot_means.append(statistics.mean(sample))
        sample_stdev = statistics.stdev(sample) if len(sample) > 1 else 0.0
        boot_sharpes.append(
            statistics.mean(sample) / sample_stdev * math.sqrt(252) if sample_stdev else 0.0
        )
        path = [rng.choice(r_values) * RISK_FRACTION for _ in range(252)]
        equity = peak = 1.0
        path_max_dd = 0.0
        for value in path:
            equity *= 1 + value
            peak = max(peak, equity)
            path_max_dd = min(path_max_dd, equity / peak - 1)
        ending_equities.append(equity)
        maximum_drawdowns.append(path_max_dd)
        ruin_count += path_max_dd <= -0.50
    boot_means.sort()
    boot_sharpes.sort()
    ending_equities.sort()
    maximum_drawdowns.sort()
    lo = int(simulations * 0.025)
    hi = int(simulations * 0.975)
    return {
        "seed": 20260714,
        "simulations": simulations,
        "mean_r_95_ci": [boot_means[lo], boot_means[hi]],
        "sharpe_95_ci": [boot_sharpes[lo], boot_sharpes[hi]],
        "probability_positive_expectancy": sum(value > 0 for value in boot_means) / simulations,
        "monte_carlo_252_trade_ending_equity_95_ci": [
            ending_equities[lo],
            ending_equities[hi],
        ],
        "monte_carlo_252_trade_max_drawdown_95_ci": [
            maximum_drawdowns[lo],
            maximum_drawdowns[hi],
        ],
        "risk_of_ruin_50pct_drawdown": ruin_count / simulations,
    }


def candidate_charts(output: Path, trades: list[Trade]) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    returns = [trade.r_multiple * RISK_FRACTION for trade in trades]
    equity: list[float] = []
    value = 1.0
    for item in returns:
        value *= 1 + item
        equity.append(value)
    _, drawdowns = drawdown(returns)
    rolling_sharpe: list[float] = []
    for index in range(len(returns)):
        window = returns[max(0, index - 19) : index + 1]
        if len(window) < 20:
            rolling_sharpe.append(math.nan)
            continue
        stdev = statistics.stdev(window) if len(window) > 1 else 0.0
        rolling_sharpe.append(
            statistics.mean(window) / stdev * math.sqrt(252) if stdev else 0.0
        )
    fig, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes[0, 0].plot([trade.date for trade in trades], equity)
    axes[0, 0].set_title("Equity curve (1% risk/trade)")
    axes[0, 1].fill_between([trade.date for trade in trades], drawdowns, 0)
    axes[0, 1].set_title("Drawdown")
    axes[0, 2].plot([trade.date for trade in trades], rolling_sharpe)
    axes[0, 2].axhline(2, color="grey", linestyle="--")
    axes[0, 2].set_title("Rolling 20-trade Sharpe")
    for axis in axes[0]:
        axis.tick_params(axis="x", rotation=30)
    axes[1, 0].hist([trade.r_multiple for trade in trades], bins=15)
    axes[1, 0].set_title("Distribution of R returns")
    axes[1, 1].hist([trade.pnl for trade in trades], bins=15)
    axes[1, 1].set_title("P/L histogram ($)")
    axes[1, 2].hist([trade.duration_minutes for trade in trades], bins=10)
    axes[1, 2].set_title("Trade duration (minutes)")
    fig.suptitle(f"{trades[0].underlying} {trades[0].strategy}")
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def write_candidate_report(output_dir: Path, trades: list[Trade], strategy: str) -> None:
    selected = sorted(
        [trade for trade in trades if trade.strategy == strategy], key=lambda trade: trade.date
    )
    if not selected:
        raise SystemExit(f"No trades generated for --report-strategy {strategy}")
    chunk_size = max(1, len(selected) // 4)
    walk_forward = [
        summarize(selected[start : start + chunk_size], chunk_size)
        for start in range(0, len(selected), chunk_size)
    ]
    report = {
        "strategy": strategy,
        "underlying": selected[0].underlying,
        "execution": {
            "fills": "buy ask / sell bid on entry; reverse on exit",
            "commission_per_contract_per_side": COMMISSION,
            "risk_fraction": RISK_FRACTION,
        },
        "metrics": summarize(selected, len(selected)),
        "annual_returns": period_returns(selected, "year"),
        "monthly_returns": period_returns(selected, "month"),
        "walk_forward_quarters": walk_forward,
        "bootstrap_and_monte_carlo": bootstrap_report(selected),
    }
    (output_dir / "candidate_report.json").write_text(json.dumps(report, indent=2))
    candidate_charts(output_dir / "candidate_charts.png", selected)


async def main() -> None:
    args = parse_args()
    assets = [asset.strip().upper() for asset in args.assets.split(",")]
    if not assets or set(assets) - {"SPX", "NDX", "XSP"}:
        raise SystemExit("--assets must contain only SPX, NDX, XSP")
    conn = await asyncpg.connect(resolve_db_dsn())
    all_trades: list[Trade] = []
    all_metrics: dict[str, dict[str, dict[str, dict[str, object]]]] = {}
    try:
        duration_minutes = (
            dt.datetime.combine(dt.date.min, args.exit_time)
            - dt.datetime.combine(dt.date.min, args.entry_time)
        ).seconds // 60
        if not 0 < duration_minutes <= 390:
            raise SystemExit("--exit-time must be after --entry-time in the same session")
        for asset in assets:
            print(f"Loading {asset} entry/exit snapshots...")
            snapshots, vix = await load_asset(conn, asset, args.entry_time, args.exit_time)
            trades, metrics = research_asset(asset, snapshots, vix, duration_minutes)
            all_trades.extend(trades)
            all_metrics[asset] = metrics
            print(f"{asset}: {len(snapshots)} chain dates, {len(trades)} candidate trades")
    finally:
        await conn.close()
    if not all_trades:
        raise SystemExit("No trades generated")
    write_outputs(args.output_dir, all_trades, all_metrics)
    if args.report_strategy:
        write_candidate_report(args.output_dir, all_trades, args.report_strategy)
    for asset in assets:
        print(f"\n{asset} full-sample first pass")
        ranked = sorted(
            all_metrics[asset].items(),
            key=lambda item: float(item[1]["full"].get("sharpe", 0)),
            reverse=True,
        )
        for strategy, segments in ranked:
            full = segments["full"]
            test = segments["test"]
            print(
                f"  {strategy:22} n={full.get('trade_count', 0):>2} "
                f"sh={full.get('sharpe', 0):>6.2f} exp=${full.get('expectancy', 0):>8.2f} "
                f"test_sh={test.get('sharpe', 0):>6.2f}"
            )
    print(f"\nWrote {args.output_dir / 'metrics.json'} and {args.output_dir / 'trades.csv'}")


if __name__ == "__main__":
    asyncio.run(main())
