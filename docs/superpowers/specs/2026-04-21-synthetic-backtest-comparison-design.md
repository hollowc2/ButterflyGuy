# Synthetic vs Real Backtest Comparison

**Date:** 2026-04-21  
**Status:** Approved

## Goal

Add a `--compare-synthetic` flag to `run_backtest_db.py` (single-config mode only) that runs each date twice — once with real DB chain data, once with Black-Scholes synthetic chains — and prints a side-by-side comparison table. The purpose is to measure how accurately the synthetic chain model approximates real market behavior.

## Approach

Option A: patch-based. The existing `_patch_chain_cache` mechanism already controls which chain data the `SimulationEngine` sees. For the synthetic run, a new helper `_force_synthetic_for_date(date)` patches `load_chain_day` in both `chain_cache` and `simulation_engine` to return `None` for the target date, triggering the engine's existing BS fallback. No changes to `SimulationEngine` or `SimulationParams`.

## Changes

**File: `src/butterfly_guy/scripts/run_backtest_db.py`**

### 1. New CLI flag

```
--compare-synthetic   Run a second synthetic-only pass and print side-by-side comparison.
                      Only applies in single-config mode; ignored with --sweep.
```

### 2. New helper function

```python
def _force_synthetic_for_date(date: dt.date):
    """Patch load_chain_day to return None for `date`, forcing BS synthetic fallback.
    Returns a restore callable."""
```

Mirrors `_patch_chain_cache` exactly — patches both `chain_cache.load_chain_day` and
`simulation_engine.load_chain_day` — but the patched function returns `None` for the target date
(and delegates to the original for all other dates).

### 3. Modified `run_single` per-date loop

When `--compare-synthetic` is set, each date runs twice with the same `SimulationParams`:

1. **Real run:** `_patch_chain_cache(full_chains, date)` → `engine.simulate_day(day, params)` → `real_result`
2. **Synthetic run:** `_force_synthetic_for_date(date)` → `engine.simulate_day(day, params)` → `synth_result`

Both use the same direction, wing width, drawdown thresholds, and slippage. The only difference is the chain data source. Fixing these structural parameters is intentional — it isolates the chain source as the single variable under test, making the comparison a clean A/B.

### 4. Output

The existing per-day table prints normally (real results only, unchanged).

After it, a second comparison table is printed with two rows per date:

```
==========================================================================================
  REAL vs SYNTHETIC COMPARISON
==========================================================================================
  Date        Run   W  Center    Entry$  Peak$   Exit$   Exit Reason            PnL/ct
  ─────────────────────────────────────────────────────────────────────────────────────
  2026-04-20  REAL  10   5580   $1.45   $3.20   $2.10   drawdown_late_morning  +$65.00
  2026-04-20  SYNT  10   5580   $1.52   $2.85   $1.90   drawdown_afternoon     +$38.00
```

If a run didn't trade (no qualifying butterfly found), its row shows `NO TRADE`.

A summary block follows showing total PnL for each run:
```
  Real total: +$X.XX  /  Synth total: +$X.XX
```

## Edge Cases

- **Real trades, synthetic doesn't (or vice versa):** non-trading row shows `NO TRADE` with dashes. No skip.
- **No real chain data in DB for date:** date is skipped entirely (same as today's behavior). The synthetic leg does not run solo — comparison requires both sides.

## Out of Scope

- Sweep mode support (deferred)
- Time-series plots of mark value over the day
- Forcing synthetic to pick the same butterfly as the real run
