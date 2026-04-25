# Real vs Synthetic Comparison Stats Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an aggregate stats block to `_print_comparison_table` so running `--compare-synthetic` also prints win rates, Sharpe, PnL correlation, trade match %, exit match %, and avg divergence for real vs synthetic.

**Architecture:** Single function modification in `run_backtest_db.py`. Collect per-side PnL lists and trade metadata during the existing loop, then print a stats section after the per-day table. Uses the existing `_sharpe` helper; correlation is computed inline with a manual Pearson formula (no new deps).

**Tech Stack:** Python, asyncpg, existing `_sharpe` from `butterfly_guy.backtest.metrics`

---

### Task 1: Add stats block to `_print_comparison_table`

**Files:**
- Modify: `src/butterfly_guy/scripts/run_backtest_db.py` — `_print_comparison_table` function (lines ~733–766)

- [ ] **Step 1: Write a unit test for the stats computation logic**

Create `tests/test_comparison_stats.py`:

```python
"""Tests for _print_comparison_table aggregate stats."""
import math
import io
import sys
import datetime as dt
from unittest.mock import MagicMock
from butterfly_guy.scripts.run_backtest_db import _print_comparison_table
from butterfly_guy.backtest.simulation_engine import DayResult


def _make_result(traded, pnl, center, exit_reason):
    r = DayResult(date=dt.date(2026, 3, 13))
    r.traded = traded
    r.pnl = pnl
    r.center_strike = center
    r.exit_reason = exit_reason
    r.entry_price = 1.0
    r.peak_value = 1.5
    r.exit_price = pnl + 1.0
    r.wing_width = 10
    r.direction = "CALL"
    return r


def _capture(day_rows):
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        _print_comparison_table(day_rows)
    finally:
        sys.stdout = old
    return buf.getvalue()


def test_stats_block_present():
    rows = [
        {"data": {"date": dt.date(2026, 3, 13)},
         "result": _make_result(True, 0.30, 5500.0, "end_of_day"),
         "synth_result": _make_result(True, 0.20, 5500.0, "end_of_day")},
        {"data": {"date": dt.date(2026, 3, 14)},
         "result": _make_result(True, -0.10, 5490.0, "drawdown_morning"),
         "synth_result": _make_result(True, -0.05, 5495.0, "drawdown_morning")},
    ]
    out = _capture(rows)
    assert "AGGREGATE COMPARISON STATS" in out
    assert "PnL correlation" in out
    assert "Trade match" in out
    assert "Exit match" in out
    assert "Avg divergence" in out


def test_perfect_correlation():
    rows = [
        {"data": {"date": dt.date(2026, 3, 13)},
         "result": _make_result(True, 0.30, 5500.0, "end_of_day"),
         "synth_result": _make_result(True, 0.30, 5500.0, "end_of_day")},
        {"data": {"date": dt.date(2026, 3, 14)},
         "result": _make_result(True, -0.10, 5490.0, "drawdown_morning"),
         "synth_result": _make_result(True, -0.10, 5490.0, "drawdown_morning")},
    ]
    out = _capture(rows)
    assert "1.00" in out  # perfect correlation


def test_no_trade_days_handled():
    rows = [
        {"data": {"date": dt.date(2026, 3, 13)},
         "result": _make_result(False, 0.0, 0.0, ""),
         "synth_result": _make_result(False, 0.0, 0.0, "")},
    ]
    out = _capture(rows)
    assert "AGGREGATE COMPARISON STATS" in out
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /opt/butterflyguy && .venv/bin/python -m pytest tests/test_comparison_stats.py -v 2>&1 | tail -20
```

Expected: 3 failures (stats block not yet added).

- [ ] **Step 3: Implement stats block in `_print_comparison_table`**

Replace the existing `_print_comparison_table` function in `src/butterfly_guy/scripts/run_backtest_db.py` with this:

```python
def _print_comparison_table(day_rows: list[dict]) -> None:
    w = 92
    print(f"\n{'='*w}")
    print(f"  REAL vs SYNTHETIC COMPARISON")
    print(f"{'='*w}")
    print(f"  {'Date':>10}  {'Run':>4}  {'W':>2}  {'Center':>7}  "
          f"{'Entry$':>7}  {'Peak$':>6}  {'Exit$':>6}  {'Exit Reason':<22}  {'PnL/ct':>8}")
    print("  " + "─" * (w - 2))

    real_total = 0.0
    synth_total = 0.0

    # Collect data for stats
    real_pnls: list[float] = []
    synth_pnls: list[float] = []
    real_wins = 0
    synth_wins = 0
    real_trades = 0
    synth_trades = 0
    trade_matches = 0      # same center strike
    exit_matches = 0       # same exit reason
    matched_days = 0       # days both sides traded

    for row in day_rows:
        d = row["data"]
        r = row["result"]
        sr = row["synth_result"]
        date = d["date"]

        for label, res in (("REAL", r), ("SYNT", sr)):
            if res is None or not res.traded:
                print(f"  {date!s:>10}  {label:>4}   -       -         -       -       -    "
                      f"{'NO TRADE':<22}")
            else:
                pnl_ct = res.pnl * 100
                if label == "REAL":
                    real_total += pnl_ct
                else:
                    synth_total += pnl_ct
                print(f"  {date!s:>10}  {label:>4}  {res.wing_width:>2}  {res.center_strike:>7.0f}  "
                      f"${res.entry_price:>6.2f}  ${res.peak_value:>5.2f}  ${res.exit_price:>5.2f}  "
                      f"{res.exit_reason:<22}  ${pnl_ct:>+7.2f}")

        # Accumulate stats
        r_traded = r is not None and r.traded
        s_traded = sr is not None and sr.traded

        if r_traded:
            real_trades += 1
            real_pnls.append(r.pnl * 100)
            if r.pnl > 0:
                real_wins += 1
        if s_traded:
            synth_trades += 1
            synth_pnls.append(sr.pnl * 100)
            if sr.pnl > 0:
                synth_wins += 1
        if r_traded and s_traded:
            matched_days += 1
            if abs(r.center_strike - sr.center_strike) < 0.5:
                trade_matches += 1
            if r.exit_reason == sr.exit_reason:
                exit_matches += 1

    print(f"\n  Real total: ${real_total:+.2f}  /  Synth total: ${synth_total:+.2f}")
    print(f"{'='*w}\n")

    # ── Aggregate stats block ────────────────────────────────────────────────
    sw = 60
    print(f"\n{'='*sw}")
    print(f"  AGGREGATE COMPARISON STATS")
    print(f"{'='*sw}")
    print(f"  {'':20}  {'REAL':>8}  {'SYNTH':>8}")
    print(f"  {'─'*56}")
    print(f"  {'Trades':20}  {real_trades:>8}  {synth_trades:>8}")

    real_wr = f"{real_wins/real_trades*100:.0f}%" if real_trades else "n/a"
    synth_wr = f"{synth_wins/synth_trades*100:.0f}%" if synth_trades else "n/a"
    print(f"  {'Win rate':20}  {real_wr:>8}  {synth_wr:>8}")

    real_tot = f"${real_total:+.2f}" if real_trades else "n/a"
    synth_tot = f"${synth_total:+.2f}" if synth_trades else "n/a"
    print(f"  {'Total PnL/ct':20}  {real_tot:>8}  {synth_tot:>8}")

    real_avg = f"${real_total/real_trades:+.2f}" if real_trades else "n/a"
    synth_avg = f"${synth_total/synth_trades:+.2f}" if synth_trades else "n/a"
    print(f"  {'Avg PnL/ct':20}  {real_avg:>8}  {synth_avg:>8}")

    from butterfly_guy.backtest.metrics import sharpe as _sharpe
    real_sh = f"{_sharpe([p/100 for p in real_pnls]):.3f}" if real_trades >= 2 else "n/a"
    synth_sh = f"{_sharpe([p/100 for p in synth_pnls]):.3f}" if synth_trades >= 2 else "n/a"
    print(f"  {'Sharpe':20}  {real_sh:>8}  {synth_sh:>8}")

    print(f"  {'─'*56}")

    # Pearson r on matched days
    if matched_days >= 2:
        r_series = [row["result"].pnl * 100 for row in day_rows
                    if row["result"] and row["result"].traded
                    and row["synth_result"] and row["synth_result"].traded]
        s_series = [row["synth_result"].pnl * 100 for row in day_rows
                    if row["result"] and row["result"].traded
                    and row["synth_result"] and row["synth_result"].traded]
        n = len(r_series)
        mean_r = sum(r_series) / n
        mean_s = sum(s_series) / n
        cov = sum((a - mean_r) * (b - mean_s) for a, b in zip(r_series, s_series)) / n
        std_r = (sum((a - mean_r) ** 2 for a in r_series) / n) ** 0.5
        std_s = (sum((b - mean_s) ** 2 for b in s_series) / n) ** 0.5
        corr = cov / (std_r * std_s) if std_r > 0 and std_s > 0 else 0.0
        corr_str = f"{corr:.2f}"
        avg_div = sum(a - b for a, b in zip(r_series, s_series)) / n
        div_str = f"${avg_div:+.2f}/ct"
    else:
        corr_str = "n/a"
        div_str = "n/a"

    trade_match_str = f"{trade_matches/matched_days*100:.0f}%" if matched_days else "n/a"
    exit_match_str = f"{exit_matches/matched_days*100:.0f}%" if matched_days else "n/a"

    print(f"  {'PnL correlation':20}  {corr_str:>8}  (matched days: {matched_days})")
    print(f"  {'Trade match %':20}  {trade_match_str:>8}  (same center strike)")
    print(f"  {'Exit match %':20}  {exit_match_str:>8}  (same exit reason)")
    print(f"  {'Avg divergence':20}  {div_str:>8}  (real − synth, matched)")
    print(f"{'='*sw}\n")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /opt/butterflyguy && .venv/bin/python -m pytest tests/test_comparison_stats.py -v 2>&1 | tail -20
```

Expected: 3 PASSED.

- [ ] **Step 5: Commit**

```bash
cd /opt/butterflyguy && git add tests/test_comparison_stats.py src/butterfly_guy/scripts/run_backtest_db.py
git commit -m "feat: add aggregate stats block to --compare-synthetic output"
```

---

### Task 2: Run the comparison on all available SPX dates

**Files:** None (execution only)

- [ ] **Step 1: Run the backtest**

```bash
cd /opt/butterflyguy && .venv/bin/python -m butterfly_guy.scripts.run_backtest_db --asset SPX --compare-synthetic 2>&1
```

Expected: per-day REAL/SYNT table for all ~30 SPX dates, followed by the aggregate stats block.

- [ ] **Step 2: Record key findings in memory**

After reviewing output, save a memory entry summarising:
- PnL correlation value
- Trade match %
- Avg divergence direction/magnitude
- Whether synthetic is worth using for dates without real data
