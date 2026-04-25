# Design: --compare-synthetic-same-entry Mode

**Date:** 2026-04-25  
**Status:** Approved

## Problem

`--compare-synthetic` runs two fully independent simulations — one with real DB chains, one with BS synthetic chains. Because BS prices wings differently from the real market, the VIX-anchored R/R selection picks different center strikes on most days (29% match rate after the strike-grid fix). The resulting correlation (0.53) is noisy because it conflates two sources of divergence: entry selection and intraday pricing.

The question we actually want to answer is: **given a real trade we already own, how accurately does BS model the intraday trajectory?**

## Goal

Add `--compare-synthetic-same-entry` flag. When set, after the real simulation selects an entry, run a second synthetic pass using the **same center strike, wing width, direction, and entry price** as the real run. Only the intraday chain pricing is synthetic (BS). This isolates intraday BS pricing error from entry selection error.

## Non-Goals

- Replacing `--compare-synthetic` (both flags remain independent)
- Changing the real simulation path in any way
- Showing the BS entry price or entry price divergence (out of scope for this pass)

## Architecture

### 1. `SimulationEngine.simulate_day_from_entry()`

New method on `SimulationEngine` in `simulation_engine.py`:

```python
def simulate_day_from_entry(
    self,
    day: DayData,
    params: SimulationParams,
    entry_candidate: ButterflyCandidate,
    entry_price: float,
    entry_time: dt.datetime,
) -> DayResult
```

- Skips the entry-search loop entirely
- Populates `result` with the passed `entry_price`, `entry_time`, `center_strike`, `wing_width`, `direction`
- Runs the existing intraday monitoring loop verbatim (same drawdown thresholds, same EOD exit logic)
- Intraday chain: `load_chain_day` is already patched to `None` by `_force_synthetic_for_date` before this method is called, so the monitoring loop's fallback to `self.synth.generate_chain()` is automatic — no changes needed to the monitoring loop itself
- Returns a `DayResult` — same type as `simulate_day()`

No changes to `SimulationParams` or `simulate_day()`.

### 2. `run_backtest_db.py` changes

**New CLI flag:**
```
--compare-synthetic-same-entry   Run a BS-only intraday pass pinned to the real
                                  entry's center/width/price, for a clean intraday
                                  pricing accuracy comparison.
```

**Per-day loop** (inside `run_single`):
```python
same_entry_result = None
if args.compare_synthetic_same_entry and result.traded:
    restore_se = _force_synthetic_for_date(date)
    same_entry_result = engine.simulate_day_from_entry(
        d["day"], params,
        entry_candidate=chosen,             # ButterflyCandidate from real run
        entry_price=result.entry_price,     # real fill (chosen.cost + slippage)
        entry_time=result.entry_time,
    )
    restore_se()
```

The `chosen_candidate` is the `ButterflyCandidate` that the real run selected. This is already stored in `day_rows` as `row["chosen"]`.

**Row dict** gains a `"same_entry_result"` key.

### 3. Output

New function `_print_same_entry_comparison_table(day_rows)`, printed after the existing comparison table (if both flags are set) or instead of it (if only `--compare-synthetic-same-entry` is set).

**Per-day table layout** — same columns as the existing comparison table, but the label column shows `REAL` / `SE-SY` (same-entry synthetic). The entry$ column is identical for both rows by construction; this is intentional and makes it visually clear the comparison is apples-to-apples.

**Aggregate stats block:**

| Stat | Description |
|---|---|
| Trades | Count for each side (should always match) |
| Win rate | % days PnL > 0 |
| Total / Avg PnL/ct | Sum and mean |
| Sharpe | Annualised Sharpe on PnL series |
| PnL correlation | Pearson r between real and SE-synth PnL series |
| Exit match % | Days where exit reason matches |
| Avg peak divergence | Mean abs diff of peak_value (real vs SE-synth) |
| Avg exit divergence | Mean (real exit$ − SE-synth exit$) |

The last two stats are the core signal: they tell you how far off BS intraday pricing is from real market behavior.

## File Touchpoints

| File | Change |
|---|---|
| `src/butterfly_guy/backtest/simulation_engine.py` | Add `simulate_day_from_entry()` method |
| `src/butterfly_guy/scripts/run_backtest_db.py` | Add `--compare-synthetic-same-entry` flag, call new method, add `_print_same_entry_comparison_table()` |

No schema changes, no new dependencies, no config changes.

## Testing

Run:
```
.venv/bin/python -m butterfly_guy.scripts.run_backtest_db --asset SPX --compare-synthetic-same-entry
```

Verify:
1. Entry price is identical between REAL and SE-SY rows for every day
2. Center strike is identical between REAL and SE-SY rows for every day
3. Intraday prices differ (BS vs real market) — peak and exit will diverge
4. Aggregate PnL correlation is higher than `--compare-synthetic` (expected: >0.6, ideally >0.8)
5. Days where real run didn't trade show no SE-SY row
