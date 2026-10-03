# F2 prospective shadow registration — 2026-10-02

F2 is the best candidate from the 2026-10-02 edge search. This file freezes its
definition and its pass/fail rules before it has seen any prospective data. F2
places no orders and changes no runtime configuration. It is scored from the live
strategy's own recorded entries.

## Definition

- **Entry:** exactly the live strategy's entry (`configs/config.yaml`, sha256
  `d120b63f…`). That means the gap direction, the 10:00–10:45 ET window, VIX-bucket
  widths and live fly selection, as recorded by the frozen v2 prospective cohort
  `spx-prospective-v2-2026-10-02`.
- **Filter:** take the entry only when the latest `$VIX` at the decision time is
  at least **16.0** and no older than the config's `max_vix_age_seconds` (300 s).
- **Exit:** none. Hold to cash settlement against the official SPX close
  (`daily_bars`), valued with the runtime's `fly_settlement_value`.
- **Accounting:** the cohort's own entry fills for each model. Settlement has no
  closing order or fee. **Stressed marketable** is the primary model.

## How it is scored

`tools/f2_shadow_report.py` reads the v2 cohort's `trades.jsonl` and looks up
the VIX and official close in the Helios TimescaleDB. It then writes
`reports/f2_shadow/{ledger.jsonl,summary.json,summary.md}`. The ledger is derived
data, rebuilt in full on every run. Sessions start on **2026-10-02**; nothing
from v1 or from earlier dates counts. A session with no settlement close yet is
`pending_settlement` and is scored on a later run.

The scored row is checked against the cohort itself. On sessions where the live
trade was cash-settled, F2 equals the cohort's E0 `net_pnl` exactly, under every
model. This was verified on the v1 sessions from 2026-09-22 to 09-29, with the
VIX floor lowered for that dry run only.

## Endpoint and gates (fixed now, judged only at the endpoint)

- **Endpoint:** 60 F2 trades, with at least 8 stressed winners.
- **Early stop:** F2 stressed drawdown above **$8,000**.
- **Pass requires all of:**
  1. F2 stressed net P&L > 0
  2. F2 stressed profit factor > 1
  3. F2 beats E0 on the same entries (stressed)
  4. Top-3 winners < 50% of gross stressed profit
  5. Max stressed drawdown ≤ $8,000

There are no interim decisions before the endpoint other than the early stop.
Changing the rule, the floor, the gates or the scoring makes a new study, and its
count starts again.

## Evidence that motivated it (all in-sample or partly used)

Stressed P&L, one-lot:

| Window | E0 (live) | F2 |
|---|---:|---:|
| ThetaData 2022-01-03 → 2024-06-28 (search window) | −$13,323 | +$18,645 |
| ThetaData 2026-03-17 → 09-25 (checked once) | +$6,084 | +$11,668 |
| Schwab DB 2026-03-13 → 09-28 | +$14,537 | ≈ +$14.9k (estimate; the trailer won here) |

Cause: the trailer exits about 80% of trades, at roughly $40 each in spread and
fees. It salvages $120–$140 on most of them. Holding wins only through the rarer
late reversals to the center: 31 of 283 exits in 2022–24. In 2026 those
reversals were fewer, and they depended on the quote source. That is why this
needs a prospective test. Expect about 0.7 F2 trades per session when VIX ≥ 16,
and none while VIX stays below 16.

## Operation

Checkout: `/mnt/Repos/Trading/Butterflyguy/.worktrees/f2-shadow` on branch
`research/f2-shadow-2026-10-02`. Timer: `butterfly-f2-shadow.timer`, weekdays at
19:30 Pacific, after the v2 cohort update at 18:30. It reuses the existing
database tunnel and protected `.env`. Run it by hand with:

```bash
uv run --locked python tools/f2_shadow_report.py
```
