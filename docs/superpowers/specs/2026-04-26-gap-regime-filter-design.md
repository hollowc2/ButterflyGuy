# Gap Regime Filter — Design Spec

**Date:** 2026-04-26
**Status:** Approved

## Problem

Two statistically validated signals are unused in the live trading path:

1. **BULL regime + gap-down → reversal bias.** In bull markets, gap-down days mean-revert 59.5% of the time (z=-7.20, the strongest signal in a 25-year dataset). The current direction filter places PUT butterflies on those days, systematically trading against the highest-confidence signal in the dataset.

2. **Small gaps (< 0.25%) have zero edge.** Gaps below 0.25% show no statistically significant continuation or reversal bias in either direction. The system currently trades these as coin flips.

Neither signal exists in the live trading path. A backtest-only implementation exists (`--gap-filter`, `--strategy-f`) but uses duplicated inline logic that can't be shared with live.

## Solution

A new `GapRegimeFilter` class in `strategy/gap_regime_filter.py` encapsulates both signals behind two toggleable parameters. The same class is used identically in live (`TradeService`) and backtest (`run_backtest_db.py`).

## Components

### 1. `strategy/gap_regime_filter.py` (new file)

```python
@dataclass
class GapRegimeFilter:
    bull_call_bias: bool = False
    min_gap_pct: float | None = None

    def apply(
        self, spot: float, prev_close: float, regime: Regime
    ) -> tuple[Literal["CALL", "PUT"] | None, str | None]:
        ...
```

**Return type:** `(direction_override, skip_reason)`

- `skip_reason` non-None → skip this day entirely (direction_override will be None)
- `direction_override` non-None → use this direction instead of the normal filter
- `(None, None)` → no-op, fall through to existing direction logic

**Logic (applied in order):**

1. Compute `gap_pct = (spot - prev_close) / prev_close`
2. If `min_gap_pct` is set and `abs(gap_pct) < min_gap_pct` → return `(None, "gap_below_min")`
3. If `bull_call_bias` is True and `regime == Regime.BULL` and `gap_pct < 0` → return `("CALL", None)`
4. Otherwise → return `(None, None)`

**Design notes:**
- Step 2 (skip) runs before step 3 (override) so a tiny gap-down in a bull regime is skipped, not flipped.
- The filter is a no-op when both params are at their defaults (`False`, `None`), so existing behavior is unchanged unless explicitly enabled.
- `abs(gap_pct)` is used for the skip check so the threshold applies symmetrically to gap-ups and gap-downs.

### 2. `core/config.py` — `EntrySettings`

Two new fields, following the existing `use_bias_filter` pattern:

```python
bull_call_bias: bool = False   # Override to CALL in BULL regime on gap-down days
min_gap_pct: float | None = None  # Skip days where |gap| < this (e.g. 0.0025 = 0.25%)
```

Both default to `False`/`None` so no live behavior changes unless set in `config.yaml`.

### 3. Live path

**`trade_service.py`:**

Two new `__init__` params:
- `regime: Regime = Regime.UNKNOWN`
- `gap_regime_filter: GapRegimeFilter | None = None`

In `attempt_entry()`, inserted before the existing direction block:

```python
if self.gap_regime_filter:
    override, skip_reason = self.gap_regime_filter.apply(
        spot_price, previous_close, self.regime
    )
    if skip_reason:
        await self.decision_queries.log_event(
            "gap_regime_skip", {"reason": skip_reason, "spot": spot_price}, ...
        )
        log.info("gap_regime_skip", reason=skip_reason)
        return None
    if override:
        direction = override
        log.info("gap_regime_override", direction=direction)

# The existing direction-filter block must be wrapped so it only runs
# when direction is still unset (i.e., no override from gap_regime_filter):
if direction is None:
    if self.config.entry.use_bias_filter:
        ...
    else:
        direction = self.direction_filter.get_direction(spot_price, previous_close)
```

**`run_live.py`:**

Regime classification (currently ~30 lines after `TradeService(...)`) is moved before `TradeService` construction. Then:

```python
gap_regime_filter = GapRegimeFilter(
    bull_call_bias=config.entry.bull_call_bias,
    min_gap_pct=config.entry.min_gap_pct,
)

trade_service = TradeService(
    ...
    regime=regime,
    gap_regime_filter=gap_regime_filter,
)
```

### 4. Backtest path (`run_backtest_db.py`)

Two new CLI args:

```
--bull-call-bias      Override to CALL in BULL regime on gap-down days
--min-gap-pct FLOAT   Skip days where |gap| < FLOAT (e.g. 0.0025)
```

In the day loop, a single `GapRegimeFilter` is constructed from args at the top of `run_single` / `run_sweep` and called via `.apply()` — identical to the live path. The existing `--gap-filter` and `--strategy-f` flags are left unchanged for backward compatibility.

## Config YAML (optional)

To enable in `config.yaml` or `config_ndx.yaml`:

```yaml
entry:
  bull_call_bias: true
  min_gap_pct: 0.0025
```

Both fields are optional; omitting them keeps the defaults (`false` / `null`).

## Testing

- Unit tests for `GapRegimeFilter.apply()` covering all four branches: skip (gap too small), override (bull+gap-down), gap-up in bull (no-op), any regime in non-bull (no-op).
- Existing `TradeService` and backtest tests should pass unchanged (filter is `None` by default, no-op path).

## What This Does Not Change

- The `BiasScoreFilter` path (`use_bias_filter: true`) is unaffected.
- The simple `DirectionFilter` fallback is unaffected.
- Existing backtest flags (`--gap-filter`, `--strategy-f`, `--vix-max`) are unaffected.
- BEAR and CHOP regimes get no direction override — only BULL regime triggers the call bias.
