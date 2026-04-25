# Real vs Synthetic Backtest Comparison — Design Spec

**Date:** 2026-04-25  
**Status:** Approved

## Goal

Run the existing `--compare-synthetic` flag on all available SPX dates and add an aggregate stats block so we can answer: *does synthetic (BS-generated) option data faithfully replicate real-data backtest outcomes, and is it worth using for dates where we have no real chain data?*

## Scope

Single change: add a summary stats block at the bottom of `_print_comparison_table` in `src/butterfly_guy/scripts/run_backtest_db.py`. No new files, no new flags.

## Stats Block

Appended automatically after the per-day table whenever `--compare-synthetic` is used.

```
═══════════════════════════════════════════════════════════
  AGGREGATE COMPARISON STATS
═══════════════════════════════════════════════════════════
                    REAL      SYNTH
  Trades          :   28        26
  Win rate        :  57%       50%
  Total PnL/ct    : +$842     +$310
  Avg PnL/ct      : +$30.1   +$11.9
  Sharpe          :  1.84      0.72
  ──────────────────────────────────────────────────────
  PnL correlation :  0.61
  Trade match %   :  82%   (same center strike)
  Exit match %    :  71%   (same exit reason)
  Avg divergence  : +$18.2/ct  (real − synth, traded days only)
═══════════════════════════════════════════════════════════
```

**Metrics defined:**
- **Trades**: days where a trade was executed (real / synth independently)
- **Win rate**: fraction of traded days with PnL > 0
- **Total / Avg PnL**: in $/contract (×100 from internal units)
- **Sharpe**: using the existing `_sharpe()` helper (annualised on daily PnL series)
- **PnL correlation**: Pearson r on days where *both* sides traded; measures whether synthetic and real move together
- **Trade match %**: fraction of all days where both sides chose the same center strike
- **Exit match %**: fraction of days where both sides exited for the same reason
- **Avg divergence**: mean of (real_pnl − synth_pnl) per contract on matched trading days

## Implementation

- Modify `_print_comparison_table(day_rows)` to collect per-side PnL arrays after the existing loop, then compute and print the stats block
- Use the existing `_sharpe` helper from `butterfly_guy.backtest.metrics`
- Correlation: manual Pearson formula (no new deps) using only days both sides traded
- ~40 lines total

## Run Command

```bash
.venv/bin/python -m butterfly_guy.scripts.run_backtest_db --asset SPX --compare-synthetic
```

Covers all 30 available SPX dates (2026-03-13 → 2026-04-24).
