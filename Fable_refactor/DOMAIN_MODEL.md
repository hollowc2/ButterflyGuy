# Domain Model and Ingestion Boundaries

This document records the current typed domain objects and data-ingestion boundaries in
Butterfly Guy. It is intended as a guardrail for future strategy, execution, risk, and
backtest changes.

The current implementation has typed domain objects for quotes, candidates, trades, bars,
and configuration. The option-chain strategy path generally converts untyped API or
database data into typed objects before selection and pricing logic runs. Some reporting,
trade recovery, and script paths still pass raw dictionaries across module boundaries.

## Core Domain Types

### OptionQuote

Source: `src/butterfly_guy/data/schemas.py`

`OptionQuote` is the canonical option-leg quote used by strategy and mark calculations.
It is currently a plain mutable dataclass, not a frozen dataclass or Pydantic model.

Fields:

| Field | Type | Notes |
| --- | --- | --- |
| `symbol` | `str` | Broker option symbol. |
| `underlying` | `str` | Asset such as `SPX`, `NDX`, or `XSP`. |
| `expiration` | `datetime.date` | Option expiration date. |
| `strike` | `float` | Strike price. |
| `option_type` | `Literal["CALL", "PUT"]` | Option side. |
| `bid` | `float` | Bid price. |
| `ask` | `float` | Ask price. |
| `mark` | `float` | Mark price. Paper fills and fly valuation use mark-price convention where relevant. |
| `last` | `float` | Last traded price, default `0.0`. |
| `volume` | `int` | Volume, default `0`. |
| `open_interest` | `int` | Open interest, default `0`. |
| `iv` | `float` | Implied volatility, default `0.0`. |
| `delta` | `float` | Delta, default `0.0`. |
| `gamma` | `float` | Gamma, default `0.0`. |
| `theta` | `float` | Theta, default `0.0`. |
| `vega` | `float` | Vega, default `0.0`. |
| `bid_size` | `int` | Bid size, default `0`. |
| `ask_size` | `int` | Ask size, default `0`. |
| `rho` | `float` | Rho, default `0.0`. |
| `intrinsic_value` | `float` | Intrinsic value, default `0.0`. |
| `time_value` | `float` | Time value, default `0.0`. |
| `in_the_money` | `bool` | ITM flag, default `False`. |
| `days_to_expiration` | `int` | DTE, default `0`. |
| `multiplier` | `float` | Contract multiplier, default `100.0`. |
| `theoretical_value` | `float` | Theoretical option value, default `0.0`. |

Related deterministic helper:

```python
fly_mark_value(lower, center, upper) = lower.mark - 2 * center.mark + upper.mark
```

### ButterflyCandidate

Source: `src/butterfly_guy/data/schemas.py`

`ButterflyCandidate` is the canonical strategy output for an entry candidate. It is
currently a plain mutable dataclass.

Fields:

| Field | Type | Notes |
| --- | --- | --- |
| `direction` | `Literal["CALL", "PUT"]` | Side selected for the fly. |
| `wing_width` | `int` | Distance from center strike to each wing. |
| `center_strike` | `float` | Short strike. |
| `lower_strike` | `float` | Lower long strike. |
| `upper_strike` | `float` | Upper long strike. |
| `cost` | `float` | Mark-based fly debit. |
| `max_profit` | `float` | `wing_width - cost`. |
| `reward_risk` | `float` | `max_profit / cost`. |
| `lower_be` | `float` | Lower breakeven. |
| `upper_be` | `float` | Upper breakeven. |
| `distance_from_spot` | `float` | Absolute distance between center and spot. |
| `spot_price` | `float` | Spot used for selection. |
| `ask` | `float` | Composite fly ask, default `0.0`. |
| `lower_symbol` | `str` | Lower leg symbol. |
| `center_symbol` | `str` | Center leg symbol. |
| `upper_symbol` | `str` | Upper leg symbol. |
| `lower_quote` | `OptionQuote | None` | Optional lower quote reference. |
| `center_quote` | `OptionQuote | None` | Optional center quote reference. |
| `upper_quote` | `OptionQuote | None` | Optional upper quote reference. |

### TradeRecord

Source: `src/butterfly_guy/data/schemas.py`

`TradeRecord` is the runtime representation of an entered trade. It is currently a plain
mutable dataclass.

Fields include trade id, trade date, direction, strikes, entry and exit prices, entry and
exit times, exit reason, PnL, peak value, option symbols, quantity, and status.

### EntrySelectionResult

Source: `src/butterfly_guy/strategy/entry_selection.py`

`EntrySelectionResult` is a frozen dataclass returned by shared live/backtest selection
logic.

Fields:

| Field | Type | Notes |
| --- | --- | --- |
| `candidate` | `ButterflyCandidate | None` | Final selected candidate. |
| `candidates` | `tuple[ButterflyCandidate, ...]` | All built candidates. |
| `active_widths` | `tuple[int, ...]` | Widths scanned for this pass. |
| `active_sigmas` | `tuple[float | None, ...]` | VIX sigma anchors for active widths. |
| `per_width_bests` | `tuple[ButterflyCandidate, ...]` | Best candidate per width. |
| `selection_method` | `str` | `VIX`, `TARGET_COST`, or `BEST_RR`. |

### MinuteBar and DayData

Source: `src/butterfly_guy/backtest/data_loader.py`

`MinuteBar` and `DayData` are backtest market-data containers. They are currently plain
mutable dataclasses.

`MinuteBar` fields:

| Field | Type |
| --- | --- |
| `ts` | `datetime.datetime` |
| `open` | `float` |
| `high` | `float` |
| `low` | `float` |
| `close` | `float` |
| `volume` | `int` |

`DayData` fields:

| Field | Type |
| --- | --- |
| `date` | `datetime.date` |
| `bars` | `list[MinuteBar]` |
| `vix` | `float` |
| `prev_close` | `float` |
| `vix_bars` | `list[MinuteBar]` |
| `recent_closes` | `list[float]` |

## Configuration Schemas

Source: `src/butterfly_guy/core/config.py`

Runtime configuration is modeled with Pydantic:

| Model | Purpose |
| --- | --- |
| `SchwabSettings` | Schwab API config and token path. |
| `VixWidthBucket` | VIX regime width buckets. |
| `StrategySettings` | Underlying, widths, RR limits, spot range, max costs. |
| `EntrySettings` | Entry window, timezone, strike-selection method, gap options. |
| `ExecutionSettings` | Price ladder, paper/live controls, paper fill controls. |
| `TimeRegime` | Profit-management regime window and drawdown settings. |
| `QuoteQualitySettings` | Exit quote quality constraints. |
| `PeakTrackingSettings` | Peak confirmation and jump filtering. |
| `ProfitProtectorSettings` | Profit lock and breakeven policy. |
| `ProfitManagementSettings` | Exit policy selection and regime config. |
| `RiskSettings` | Daily/weekly loss, trade count, buying power, fail-safe behavior. |
| `CollectorSettings` | Snapshot interval. |
| `DatabaseSettings` | Database connection settings. |
| `MonitoringSettings` | Metrics and logging settings. |
| `AppConfig` | Top-level settings container. |

## Database Shape

Sources:

- `src/butterfly_guy/db/migrations/001_initial.sql`
- `src/butterfly_guy/db/migrations/004_add_chain_fields.sql`
- Live TimescaleDB inspection on 2026-06-17 UTC

Primary relational sources for trading and strategy data:

| Table | Purpose |
| --- | --- |
| `option_chain_snapshots` | Time-series option chain rows, including bid/ask/mark, greeks, symbols, spot price, and extended quote fields. |
| `spot_prices` | Time-series spot prices for underlyings and `$VIX`. |
| `butterfly_trades` | Trade lifecycle records. |
| `decision_log` | JSONB event log for decisions and diagnostics. |
| `butterfly_candidates` | Scanned candidate history. |
| `daily_risk_state` | Daily risk counters and halt state. |

Live database tables also include `monitoring_leg_quotes`, `bars_1m`, `l2_book`,
`strategies`, `trades`, and Polymarket tables. The trading-domain evidence below focuses
on Butterfly Guy tables used by SPX, NDX, and XSP.

## Live Data Research Findings

These findings came from read-only queries against the live `butterfly_guy`
TimescaleDB on 2026-06-17 UTC.

### Option Chain Coverage

`option_chain_snapshots` currently holds 43,314,675 rows.

| Underlying | Rows | ET dates | First snapshot UTC | Latest snapshot UTC at query time | Expirations |
| --- | ---: | ---: | --- | --- | ---: |
| `NDX` | 18,305,053 | 61 | 2026-03-20 19:48:44.586213+00 | 2026-06-17 16:49:31.696318+00 | 61 |
| `SPX` | 15,918,604 | 66 | 2026-03-13 16:27:26.081079+00 | 2026-06-17 16:49:59.414682+00 | 66 |
| `XSP` | 9,078,020 | 53 | 2026-04-01 17:47:36.282312+00 | 2026-06-17 16:49:59.496245+00 | 53 |

All observed option-chain rows have non-null `bid`, `ask`, `mark`, and `symbol`.
Observed `option_type` values are only `CALL` and `PUT`.

| Underlying | CALL rows | PUT rows |
| --- | ---: | ---: |
| `NDX` | 9,152,153 | 9,152,900 |
| `SPX` | 7,959,302 | 7,959,302 |
| `XSP` | 4,539,010 | 4,539,010 |

### Latest Snapshot Shape

Latest snapshots queried around 2026-06-17 16:55 UTC were 0-DTE snapshots with
`multiplier = 100.00`.

| Underlying | Latest snapshot UTC | Rows | Expiration | Spot | Strike range | Distinct strikes | Min DTE | Max DTE |
| --- | --- | ---: | --- | ---: | --- | ---: | ---: | ---: |
| `NDX` | 2026-06-17 16:55:54.154008+00 | 914 | 2026-06-17 | 30077.12 | 15000 to 39500 | 457 | 0 | 0 |
| `SPX` | 2026-06-17 16:55:18.975762+00 | 540 | 2026-06-17 | 7511.66 near that query window | 3000 to 9800 | 270 | 0 | 0 |
| `XSP` | 2026-06-17 16:55:18.413214+00 | 560 | 2026-06-17 | 751.17 near that query window | 440 to 950 | 280 | 0 | 0 |

Observed strike increments in the latest snapshots:

| Underlying | Minimum step | Maximum gap | Observed small steps |
| --- | ---: | ---: | --- |
| `SPX` | 5.00 | 200.00 | 5, 10, 25, 75, 100 |
| `NDX` | 10.00 | 1000.00 | 10, 40, 50, 100 |
| `XSP` | 1.00 | 10.00 | 1, 2, 5, 10 |

### Actual Schwab Symbol Formats

Observed symbols are OCC-style Schwab strings with a padded root, YYMMDD date,
contract type, and an 8-digit strike encoding.

Examples from live latest snapshots:

| Underlying field | Symbol root in payload | Example symbol | Meaning |
| --- | --- | --- | --- |
| `SPX` | `SPXW` | `SPXW  260617C07510000` | SPX weekly CALL, 2026-06-17, 7510 strike |
| `SPX` | `SPXW` | `SPXW  260617P07510000` | SPX weekly PUT, 2026-06-17, 7510 strike |
| `NDX` | `NDXP` | `NDXP  260617C30080000` | NDX weekly CALL, 2026-06-17, 30080 strike |
| `NDX` | `NDXP` | `NDXP  260617P30080000` | NDX weekly PUT, 2026-06-17, 30080 strike |
| `XSP` | `XSP` | `XSP   260617C00751000` | XSP CALL, 2026-06-17, 751 strike |
| `XSP` | `XSP` | `XSP   260617P00751000` | XSP PUT, 2026-06-17, 751 strike |

Parsing rule for current data:

```text
root = symbol[0:6].strip()
yyMMdd = symbol[6:12]
contract_type = symbol[12]  # C or P
encoded_strike = symbol[13:21]
strike = Decimal(encoded_strike) / Decimal("1000")
```

Important domain note: the stored `underlying` is the strategy asset (`SPX`, `NDX`,
`XSP`), while the symbol root can be the Schwab/OCC option root (`SPXW`, `NDXP`, `XSP`).
Do not require `symbol_root == underlying`.

### Broker Mark Versus Computed Mid

The live DB stores Schwab's `mark` field. It is very close to `(bid + ask) / 2`, but it
is not always exactly equal after decimal rounding.

Latest-snapshot mark checks:

| Underlying | Rows | Mark equals 4dp mid | Avg absolute mark-mid delta | Max absolute mark-mid delta |
| --- | ---: | ---: | ---: | ---: |
| `NDX` | 914 | 742 | 0.000941 | 0.0050 |
| `SPX` | 540 | 314 | 0.002093 | 0.0050 |
| `XSP` | 560 | 441 | 0.001063 | 0.0050 |

Monitoring-leg quote checks across all stored monitor rows:

| Underlying | Option type | Rows | Trades | Null quote rows | Avg absolute mark-mid delta | Max absolute mark-mid delta |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `NDX` | CALL | 50,331 | 3 | 0 | 0.000012 | 0.0050 |
| `NDX` | PUT | 76,992 | 5 | 0 | 0.000405 | 0.0050 |
| `SPX` | CALL | 48,930 | 6 | 0 | 0.002289 | 0.0050 |
| `SPX` | PUT | 45,876 | 4 | 0 | 0.001448 | 0.0050 |
| `XSP` | CALL | 73,692 | 6 | 0 | 0.002694 | 0.0050 |
| `XSP` | PUT | 58,401 | 5 | 0 | 0.002378 | 0.0050 |

Answer for the strict domain model: store both values explicitly.

- `broker_mark`: the broker-provided `mark` from Schwab or the DB.
- `mid_price`: deterministic `(bid + ask) / 2` computed at ingestion.
- Strategy code should choose one canonical valuation field and name it clearly. If
  deterministic replay is the goal, use computed `mid_price` or a normalized
  `mark_for_model` derived at the adapter boundary.

### Trade Row Reality

`butterfly_trades` currently contains live and historical rows for all three assets.

| Underlying | Trades | Open | Closed | First trade | Latest trade |
| --- | ---: | ---: | ---: | --- | --- |
| `NDX` | 46 | 1 | 45 | 2026-03-30 | 2026-06-17 |
| `SPX` | 54 | 1 | 53 | 2026-03-17 | 2026-06-17 |
| `XSP` | 35 | 1 | 34 | 2026-04-02 | 2026-06-17 |

Observed trade directions and statuses:

| Underlying | Direction | Status | Count |
| --- | --- | --- | ---: |
| `NDX` | CALL | CLOSED | 31 |
| `NDX` | CALL | OPEN | 1 |
| `NDX` | PUT | CLOSED | 14 |
| `SPX` | CALL | CLOSED | 32 |
| `SPX` | CALL | OPEN | 1 |
| `SPX` | PUT | CLOSED | 21 |
| `XSP` | CALL | CLOSED | 20 |
| `XSP` | CALL | OPEN | 1 |
| `XSP` | PUT | CLOSED | 14 |

Observed trade widths and quantities:

| Underlying | Observed trade wing widths | Observed quantities |
| --- | --- | --- |
| `NDX` | 50, 80, 100 | 1 |
| `SPX` | 10, 20, 25, 30, 35, 40 | 1 |
| `XSP` | 1, 2, 3 | 1 |

Latest open trades at query time:

| Trade id | Underlying | Direction | Width | Strikes | Entry price | Status |
| ---: | --- | --- | ---: | --- | ---: | --- |
| 135 | `NDX` | CALL | 100 | 30110 / 30210 / 30310 | 18.8800 | OPEN |
| 134 | `SPX` | CALL | 30 | 7555 / 7585 / 7615 | 3.1300 | OPEN |
| 133 | `XSP` | CALL | 3 | 756 / 759 / 762 | 0.3300 | OPEN |

Trade metadata is JSONB and contains strategy/replay diagnostics such as
`selection_method`, `entry_strategy`, `entry_spot`, `entry_attempts`, `active_widths`,
`active_sigmas`, `per_width_bests`, `selection_parity`, `exit_mark_parity`,
`exit_ladder_steps`, `exit_mark_at_signal`, `exit_settlement_value`, and
`exit_signal_reason`.

### Monitoring Leg Quotes

`monitoring_leg_quotes` is the high-frequency quote table for open-position legs.

| Underlying | Rows | Trades | First timestamp UTC | Latest timestamp UTC | Null quote rows |
| --- | ---: | ---: | --- | --- | ---: |
| `NDX` | 127,311 | 8 | 2026-06-04 14:01:36.820902+00 | 2026-06-17 16:56:42.074865+00 | 0 |
| `SPX` | 94,791 | 10 | 2026-06-04 14:01:32.117125+00 | 2026-06-17 16:56:43.928794+00 | 0 |
| `XSP` | 132,075 | 11 | 2026-06-03 14:00:11.269651+00 | 2026-06-17 16:56:41.816991+00 | 0 |

`monitoring_leg_quotes` stores per-leg bid/ask/mark plus per-position state at that
timestamp: `fly_mark`, `peak_value`, and `drawdown_pct`.

### Candidate, Spot, and Daily Bars

Candidate scan rows:

| Underlying | Rows | Selected rows | First scan UTC | Latest scan UTC | Directions | Widths |
| --- | ---: | ---: | --- | --- | --- | --- |
| `NDX` | 1,030 | 79 | 2026-03-24 14:00:10.426519+00 | 2026-06-17 14:01:46.239411+00 | CALL, PUT | 25, 50, 75, 80, 100 |
| `SPX` | 18,367 | 298 | 2026-03-16 14:00:13.445123+00 | 2026-06-17 14:00:19.047049+00 | CALL, PUT | 10, 20, 25, 30, 35, 40 |
| `XSP` | 755 | 96 | 2026-04-02 14:00:04.783290+00 | 2026-06-17 14:00:19.822785+00 | CALL, PUT | 1, 2, 3, 4 |

Spot prices:

| Underlying | Rows | First timestamp UTC | Latest timestamp UTC | Sources |
| --- | ---: | --- | --- | --- |
| `$VIX` | 29,073 | 2026-03-16 16:59:34.919535+00 | 2026-06-17 16:56:21.380740+00 | schwab |
| `NDX` | 24,749 | 2026-03-20 19:48:44.586213+00 | 2026-06-17 16:56:57.808603+00 | schwab |
| `SPX` | 27,539 | 2026-03-13 13:30:07.941624+00 | 2026-06-17 16:56:21.380740+00 | schwab |
| `XSP` | 18,783 | 2026-04-01 17:45:56.835120+00 | 2026-06-17 16:56:21.221318+00 | schwab |

Daily bars:

| Underlying | Rows | First date | Latest date |
| --- | ---: | --- | --- |
| `$VIX` | 76 | 2026-03-02 | 2026-06-16 |
| `NDX` | 75 | 2026-03-02 | 2026-06-16 |
| `SPX` | 75 | 2026-03-02 | 2026-06-16 |
| `XSP` | 75 | 2026-03-02 | 2026-06-16 |

## Strict Typing Blueprint for Fable

The following blueprint is based on the live dataset above. It uses immutable dataclasses
and `Decimal` for money and strikes. It deliberately distinguishes broker mark from
computed mid because the database proves they are not always exactly equal.

```python
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Mapping, Optional, Tuple


OptionType = Literal["CALL", "PUT"]
Underlying = Literal["SPX", "NDX", "XSP"]
TradeStatus = Literal["OPEN", "CLOSED", "EXPIRED"]


@dataclass(frozen=True, slots=True)
class OptionContract:
    """Immutable representation of one option quote at one snapshot timestamp.

    Live Schwab symbols in this database are OCC-style padded strings:
    - SPX: "SPXW  260617C07510000"
    - NDX: "NDXP  260617C30080000"
    - XSP: "XSP   260617C00751000"

    The strategy underlying is not always the same as the symbol root:
    SPX uses SPXW contracts and NDX uses NDXP contracts.
    """

    symbol: str
    symbol_root: str
    underlying: Underlying
    expiration: date
    snapshot_time: datetime
    strike: Decimal
    contract_type: OptionType
    bid: Decimal
    ask: Decimal
    broker_mark: Decimal
    mid_price: Decimal
    last: Decimal = Decimal("0")
    volume: int = 0
    open_interest: int = 0
    bid_size: int = 0
    ask_size: int = 0
    multiplier: Decimal = Decimal("100")
    days_to_expiration: int = 0
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    iv: Optional[float] = None
    intrinsic_value: Optional[Decimal] = None
    time_value: Optional[Decimal] = None
    theoretical_value: Optional[Decimal] = None
    in_the_money: Optional[bool] = None

    @property
    def mark_for_model(self) -> Decimal:
        """Deterministic valuation field for strategy and replay math."""
        return self.mid_price


@dataclass(frozen=True, slots=True)
class ButterflySpread:
    """Immutable 3-leg same-expiration butterfly."""

    direction: OptionType
    long_low_leg: OptionContract
    short_mid_leg: OptionContract
    long_high_leg: OptionContract
    timestamp: datetime

    @property
    def wing_width(self) -> Decimal:
        return self.short_mid_leg.strike - self.long_low_leg.strike

    @property
    def total_cost(self) -> Decimal:
        return (
            self.long_low_leg.mark_for_model
            + self.long_high_leg.mark_for_model
            - (Decimal("2") * self.short_mid_leg.mark_for_model)
        )

    @property
    def broker_mark_cost(self) -> Decimal:
        return (
            self.long_low_leg.broker_mark
            + self.long_high_leg.broker_mark
            - (Decimal("2") * self.short_mid_leg.broker_mark)
        )

    @property
    def is_symmetrical(self) -> bool:
        lower_width = self.short_mid_leg.strike - self.long_low_leg.strike
        upper_width = self.long_high_leg.strike - self.short_mid_leg.strike
        return lower_width == upper_width

    @property
    def max_profit(self) -> Decimal:
        return self.wing_width - self.total_cost

    @property
    def reward_risk(self) -> Decimal:
        if self.total_cost <= 0:
            return Decimal("0")
        return self.max_profit / self.total_cost


@dataclass(frozen=True, slots=True)
class ButterflyCandidateModel:
    """Immutable strategy candidate derived from a ButterflySpread."""

    spread: ButterflySpread
    spot_price: Decimal
    lower_breakeven: Decimal
    upper_breakeven: Decimal
    distance_from_spot: Decimal
    composite_ask: Decimal


@dataclass(frozen=True, slots=True)
class TradeRecordModel:
    """Immutable runtime trade state reconstructed from butterfly_trades."""

    trade_id: int
    underlying: Underlying
    trade_date: date
    status: TradeStatus
    direction: OptionType
    quantity: int
    wing_width: Decimal
    lower_strike: Decimal
    center_strike: Decimal
    upper_strike: Decimal
    entry_price: Decimal
    entry_time: datetime
    lower_symbol: str
    center_symbol: str
    upper_symbol: str
    exit_price: Optional[Decimal] = None
    exit_time: Optional[datetime] = None
    exit_reason: Optional[str] = None
    pnl: Optional[Decimal] = None
    peak_value: Optional[Decimal] = None
    metadata: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class MonitoringLegQuote:
    """Immutable high-frequency quote for one monitored trade leg."""

    ts: datetime
    trade_id: int
    underlying: Underlying
    expiration: date
    strike: Decimal
    contract_type: OptionType
    bid: Decimal
    ask: Decimal
    broker_mark: Decimal
    mid_price: Decimal
    symbol: str
    spot_price: Optional[Decimal]
    fly_mark: Decimal
    peak_value: Decimal
    drawdown_pct: Decimal


@dataclass(frozen=True, slots=True)
class ChainSnapshot:
    """All option contracts for one underlying and expiration at one timestamp."""

    underlying: Underlying
    expiration: date
    snapshot_time: datetime
    spot_price: Decimal
    contracts: Tuple[OptionContract, ...]
```

Adapter rule for Fable:

```text
asyncpg.Record or Schwab JSON
  -> adapter validates and converts Decimal/date/datetime/Literal fields
  -> immutable domain object
  -> strategy and math code
```

Do not allow `dict`, `asyncpg.Record`, or raw Schwab payload fragments into
`ButterflyBuilder`, selection, exit mark calculation, risk, or replay math.

## Ingestion Boundaries

The intended boundary is:

1. External API or database returns untyped data.
2. Adapter code immediately converts it to typed domain objects.
3. Strategy, selection, mark, and simulation logic consume only typed domain objects.

The current implementation mostly follows this for option-chain strategy paths.

### Live Schwab Chain to Strategy

Source: `src/butterfly_guy/services/trade_service.py`

`TradeService._parse_chain_to_quotes()` maps Schwab option-chain response data into
`list[OptionQuote]`.

`TradeService.attempt_entry()` then passes those quotes into
`select_entry_candidate()`.

Boundary:

```text
Schwab chain response dict -> OptionQuote[] -> select_entry_candidate()
```

### Collector Schwab Chain to Database

Source: `src/butterfly_guy/data/collector.py`

`OptionChainCollector._parse_chain_response()` maps Schwab option-chain response data
into flat row dictionaries for storage in `option_chain_snapshots`.

This is a database-write boundary, not a strategy boundary. It currently stores dict rows
via `ChainQueries.bulk_insert_snapshot()`.

Boundary:

```text
Schwab chain response dict -> option_chain_snapshots row dicts -> database
```

### Database Chain Rows to Strategy

Source: `src/butterfly_guy/data/db_chain_quotes.py`

`rows_to_option_quotes()` converts `option_chain_snapshots` row dictionaries into
`list[OptionQuote]`.

Used by:

- `TradeService._entry_selection_parity_report()`
- `strategy/exit_mark_parity.py`

Boundary:

```text
option_chain_snapshots rows -> OptionQuote[] -> entry/exit parity math
```

### Backtest Database Chain Rows to Strategy

Sources:

- `src/butterfly_guy/backtest/db_loader.py`
- `src/butterfly_guy/scripts/run_backtest_db.py`

`DbDataLoader._load_chain_async()` converts asyncpg rows from `option_chain_snapshots`
into `list[OptionQuote]`.

`run_backtest_db.py` also manually converts database rows into `OptionQuote` in several
loader functions before selecting entries.

Boundary:

```text
option_chain_snapshots rows -> OptionQuote[] -> select_entry_candidate()
```

### Trade Rows to Runtime Objects

Sources:

- `src/butterfly_guy/scripts/run_live.py`
- `src/butterfly_guy/scripts/run_backtest_db.py`

Open trade recovery converts raw `butterfly_trades` rows into `TradeRecord` and
`ButterflyCandidate`.

`candidate_from_trade_row()` converts a trade row dict into a `ButterflyCandidate` for
live-pinned replay.

Boundary:

```text
butterfly_trades row dict -> TradeRecord / ButterflyCandidate
```

## Deterministic Strategy and Math Path

Sources:

- `src/butterfly_guy/data/schemas.py`
- `src/butterfly_guy/strategy/butterfly_builder.py`
- `src/butterfly_guy/strategy/entry_selection.py`
- `src/butterfly_guy/strategy/butterfly_selector.py`

The main deterministic path is:

```text
OptionQuote[]
  -> ButterflyBuilder.build_candidates()
  -> ButterflyCandidate[]
  -> ButterflySelector / select_cross_width_candidate()
  -> EntrySelectionResult
```

Important behavior:

- `ButterflyBuilder.build_candidates()` accepts `list[OptionQuote]`.
- It builds a strike lookup for the requested direction.
- It calculates mark-based fly cost with `fly_mark_value()`.
- It calculates composite fly ask as `lower.ask + upper.ask - 2 * center.bid`.
- It filters by configured minimum debit, maximum cost per width, and minimum reward/risk.
- It emits `ButterflyCandidate` objects.
- `select_entry_candidate()` is shared between live trading and DB backtests.

## Current Guardrail Gaps

The current codebase has useful typing, but it does not yet fully enforce strict immutable
domain boundaries.

Observed gaps:

1. Core trading domain objects are mutable dataclasses.
   - `OptionQuote`, `ButterflyCandidate`, and `TradeRecord` are not frozen.
   - `MinuteBar` and `DayData` are not frozen.

2. Core trading domain objects are not Pydantic schemas.
   - Configuration is Pydantic.
   - Trading domain data is dataclass-based.

3. Database query helpers often return raw dictionaries.
   - `ChainQueries.get_latest_chain()` returns `list[dict]`.
   - `ChainQueries.get_chain_at_time()` returns `list[dict]`.
   - `TradeQueries.get_open_trades()` returns `list[dict]`.
   - `TradeQueries.get_trades_for_date()` returns `list[dict]`.

4. Row-to-domain conversion is duplicated.
   - `data/db_chain_quotes.py` has `rows_to_option_quotes()`.
   - `backtest/db_loader.py` has its own asyncpg-row to `OptionQuote` conversion.
   - `scripts/run_backtest_db.py` has additional manual asyncpg-row to `OptionQuote`
     conversions.

5. Reporting and review paths still consume raw trade dictionaries.
   - Live performance reporting converts `dict[str, Any]` rows into report objects.
   - Weekend review formats and charts raw trade row dictionaries.

6. Some external API parsing still passes generic dictionaries until a downstream helper.
   - Schwab chain response parsing is localized, but the input type remains `dict`.
   - Intraday candle handling uses `list[dict]` in charting and entry helpers.

## Suggested Strict Boundary Target

Future changes that aim for stricter domain modeling should preserve this target:

```text
External API / asyncpg row / JSON cache
  -> adapter-specific parsing
  -> immutable domain object
  -> strategy, risk, execution, reporting, or simulation logic
```

Recommended model direction:

1. Make core domain dataclasses frozen or migrate them to strict Pydantic models.
2. Centralize database row conversion functions by table/domain object.
3. Keep raw `dict[str, Any]` inside adapter/query modules only.
4. Make strategy and math signatures reject raw dictionaries.
5. Add focused tests that prove DB/API rows become domain objects before strategy code runs.

High-impact candidates for first cleanup:

| Target | Reason |
| --- | --- |
| `OptionQuote` | It is the core input to fly math and selection. |
| `ButterflyCandidate` | It is the core output of selection and input to execution. |
| `TradeRecord` | It crosses recovery, position management, risk, and exit reporting. |
| `rows_to_option_quotes()` | Existing central adapter can be expanded and reused. |
| `ChainQueries` return types | Current raw dict returns allow strategy callers to skip domain conversion. |

## Current Status Summary

The option-chain calculation path is already mostly decoupled from raw database rows:

```text
DB/API quote data -> OptionQuote -> ButterflyBuilder -> ButterflyCandidate
```

The architectural gap is enforcement. The code relies on convention and scattered
conversion helpers rather than immutable schemas and adapter-level return types.
