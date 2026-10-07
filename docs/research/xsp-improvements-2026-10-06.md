# XSP improvements — sequential work record, October 6, 2026

This work follows the isolated review. Runtime trading parameters and services
remain unchanged. Each economic experiment uses only XSP evidence; shared
mechanics retain their live defaults.

## 1. Risk accounting — existing fix verified

The initial review's double-booking hypothesis needs a more precise explanation.
Before September 26 (`c0b229e`), startup put an open trade's debit into realized
risk P&L as a worst-case reserve. On settlement the full loss was then added.
For the September 1 and 24 XSP debits this produces exactly −$66 and −$78 instead
of −$33 and −$39. The historical snapshot is consistent with this known defect;
we do not have the old restart logs to prove each occurrence independently.

The existing fix keeps open exposure separate from realized P&L. Deployed
`run_live.py` and `risk_engine.py` hash-match the fixed local implementation.
Deployed `TradeQueries.close_trade` also has the OPEN-only guard. No new risk
posting redesign is warranted from these two old observations alone.

Added regressions for both exact XSP amounts: recover an open trade, settle it
worthless, record one loss, retain no committed exposure, and avoid a false $50
halt. Existing recovery, risk, guarded-close and settlement targets: **93 passed**.
Corrected the stale dollar-unit comment in XSP config without changing its value.

Historical ledger rows and halt flags were not rewritten. Those flags could
include manual halts; a data correction must not infer permission to clear them.
Trade-based performance already uses the correct losses.

## 2. XSP exit replay — baseline established before tuning

`python -m butterfly_guy.scripts.replay_xsp_exits` consumes read-only exported
trade JSONL and high-frequency held-leg monitor CSV. It calls the actual
PositionManager and ProfitStateMachine using the recorded observation clock,
retains per-regime hold times, quality gates and peak/drawdown confirmations.
Live valuation defaults remain unchanged. IV-based tent geometry is omitted
because monitor recordings do not contain leg IV; no current exit rule uses it.

The September 1–October 6 baseline has exact accepted-peak and exit-policy parity
on 18 of 20 trades. September 9 and 10 contain incomplete held-leg records and
are explicitly refused. Records contain neither quote event age nor unsuccessful
polls; exact agreement on recorded polls does not establish complete feed parity.
Observed telemetry gaps remain visible, including a roughly 34-minute gap on
September 11. There is no interpolation or fabricated liquidation during gaps.

## 3. Earlier trailer — experiment fixed before execution

- Development evidence: the already-inspected September 1–October 6 sessions.
  No independent holdout or promotion claim.
- Baseline: current XSP management on the same observed entries.
- Benchmark: hold to the recorded cash-settlement outcome.
- Single candidate: drawdown threshold **0.50 in each regime**; all other
  peak acceptance, quality gates, confirmation counts and hold times unchanged.
- Eligible sessions: exact baseline accepted-peak/exit parity and terminal
  monitor coverage; exclude incomplete held-leg sessions. Report large gaps.
- Fixed execution assumptions: recorded marketable entry estimate; hypothetical
  exit at component-leg bid less existing paper fee and slippage, rounded to cents
  and floored at zero with floor usage reported. Settlement has no closing fee.
  These are estimates, not broker fills. Quote age and complex-book execution
  are unavailable. Cash settlement remains a recorded market-data proxy.
- Primary comparison: paired net dollars, trade-close drawdown, average win/loss,
  expectancy, top-three-removed results. Candidate must beat the paired benchmark
  without greater drawdown and retain an advantage after removing three largest
  wins. Passing is only a reason for new forward evidence, not activation.
- Do not expand the threshold search after viewing results. Any later parameter
  change requires a separately recorded experiment.

Artifacts: `reports/research/xsp-improvements-2026-10-06/`. Outputs are exclusive
create: reruns use a new filename rather than overwrite earlier evidence.

### Result: refine; do not activate this candidate

On 18 parity-matched sessions, the component-price estimate improves from
**+$72 to +$136**, while trade-close drawdown falls from $193 to $115.
Twelve sessions exit early. The three-largest-wins-removed result remains
negative: baseline −$424, candidate −$205. An extra five cents of adverse exit
pricing reduces the candidate total to $76, almost eliminating its $64 advantage.

**Post-hoc coverage diagnostic, not an independent evaluation:** on the 12
sessions with no recorded gap above 60 seconds, baseline earns $72 and the
candidate earns only $13. With another three cents of adverse exit pricing,
the candidate loses $14. This reversal is sufficient reason not to change
the live strategy. Do not try additional trailer thresholds on this inspected
sample until data/settlement quality and a new evaluation protocol are established.
The candidate reduces some losses but also changes September 23 from an
estimated $81 winner to a $7 loser. A higher win rate alone is insufficient.

No strategy parameter was changed. The legacy minute-based backtest remains
available with its known limitations; the new monitor replay supplies verified
fixed-entry exit evidence rather than silently changing that simulator globally.

## 4. Independent width policy — no recent behavioral difference

All 20 recorded September-onward entries have exactly one per-width eligible
candidate. Removing the first-width preference would therefore change **none**
of these entries. The SPX-era rationale in the helper is stale, but the recent
evidence does not support changing the policy for profit.

Fourteen entries also contain DB/live selection comparisons: no cross-width
ranking flip is recorded; 11 match center, while three stored snapshots yield
no eligible DB candidate although the live observation finds one.
This makes observation timing and within-width selection more useful research
targets than an immediate first-width override. Six entries lack that comparison.
Alternate widths also lack high-frequency held-leg observations after entry;
those cannot be synthesized as if they were captured live. Freeze the current
width policy pending a sufficiently covered, separately specified comparison.

## 5. Execution and settlement evidence — proxy discrepancy measured

Retained the existing fee and component-price estimates, and stressed only
early exits additionally. Neither midpoint wins nor component prices establish
complex-order fill quality. Peak-quality and sellability safeguards are retained.

A read-only crosscheck found completed Schwab daily closes for 19 of the 20
sessions; October 6 was not yet available in daily_bars at extraction. The
recorded final-minute XSP settlement spot differs from daily SPX close divided
by ten by up to **0.45 XSP points**. Using that alternative closing proxy changes
September 23's settlement P&L by $25.70. It can therefore materially affect
results near the tent boundary.

The daily-close comparison comes from the same provider, not independent Cboe
settlement verification. It is a sensitivity analysis, not authorization to
overwrite trade results or relabel SPX intraday data as XSP. On the 17
parity-matched sessions with daily closes, baseline/candidate totals are
$108/$172 using recorded settlements, versus $128/$174.50 using scaled daily
SPX closes. The latter still does not rescue the coverage-dependent candidate.

Next prerequisite for another economic experiment: an attributed finalized XSP
settlement observation and explicit monitor coverage eligibility, registered
before inspecting the next cohort. Preserve proxy and official observations
separately; missing official evidence must remain missing.

## Reproduce

The quote export ran in an explicit read-only transaction and selected only
XSP September 1–October 6 observations. Extraction SQL, raw quote CSV, recorded
entry-selection metadata, and both settlement inputs are preserved locally.
Replay command (choose a new output filename):

```bash
UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run python -m butterfly_guy.scripts.replay_xsp_exits \
  --trades reports/research/xsp-review-2026-10-06/evidence.jsonl \
  --quotes reports/research/xsp-improvements-2026-10-06/monitor-quotes.csv \
  --output /tmp/xsp-replay-new.json --earlier-trailer
```

Omit `--earlier-trailer` for the frozen baseline. The report records input hashes,
source hashes, full profit-policy settings, per-trade exclusions and hypothetical
exits. No credentials or broker APIs are involved.

Final verification: **1,187 passed, one skipped**; the skipped real-DB smoke test
requires `CI_DATABASE_URL`, which is not configured locally. Ruff and
`git diff --check` pass. Graphify's AST update completed; SQL extraction remains
unavailable because the installed Graphify environment lacks tree_sitter_sql.
