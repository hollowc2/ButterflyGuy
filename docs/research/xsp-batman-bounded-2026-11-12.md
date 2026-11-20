# XSP quiet iron and mixed Batman — bounded study, November 12, 2026

**Quiet ATM iron: insufficient evidence for new validation. Batman: reject the
eight exact frozen cells.** No paper-trade candidate or activation recommendation.
Research only; runtime configuration, services, tokens and orders were untouched.

Read the [standalone HTML report](../../reports/research/xsp-batman-2026-11-12/index.html)
for payoff diagrams, full trial results, costs, chronological/monthly metrics,
matched-date comparisons, raw-cash examples, embedded journals and reproduction.
The [small versionable receipt](xsp-batman-2026-11-12.summary.json) retains decisions
and hashes if private local artifacts are unavailable.

## Scope and genuinely new work

First read the [independent study](xsp-independent-research-2026-11-12.md),
[quiet-day study](xsp-quiet-flies-2026-11-12.md), and Batman discovery-journal entry.
Earlier CALL/CALL, PUT/PUT and IRON/IRON pairs were not exact mixed Batman tests.
This study prices the lower PUT and upper CALL legs together using genuine XSP
minute component quotes and transaction-needed displayed sizes.

The coverage audit precedes the frozen specification. All local quote kinds
(quotes, OHLC, open interest, EOD) end September 28, 2026: 1,437 files each,
including 185 dates in 2026. Native published XSP settlements cover all 185.
Recorded SPX/10 supplies 122 first-hour prefixes; 63 dates are excluded.
Canonical support has SPX/VIX, no native intraday XSP. No newer joint cohort,
per-leg age evidence or demonstrated complex fills was found. Older quote files
are not automatically validated signal/settlement cohorts. No download or remote
runtime access was performed. Every January–September date is development data.

The exact prior quiet four-point iron policy is preserved, including its signal,
warmup, entry, sizes, costs, settlement and missing-data rules. Its 30 outcomes
remain +$405 stressed, −$171.20 after the top three wins, and −$44.40 before the
fixed May 15 split. No new quiet threshold, width or exit was evaluated. Its
earlier exact-policy rejection remains; genuinely fresh validation is unavailable.

## Frozen matrix and lifecycle

Eight new cells: two geometries × two gates × two exits. Two imported unchanged
IRON width-four benchmark cells make ten total cells including benchmarks.
No outcome-led expansion. Fixed width four, one fly per side, eight gross units.

- Body-only: target bodies at SPX/10 ± half the 10:29 ATM XSP straddle midpoint;
  wings can cross the proxy and overlap.
- Every-strike OTM: target bodies at SPX/10 ± (four + half that straddle).
  Upper put wing must remain below the proxy; lower call wing above it.
- Bodies use nearest listed strike on the required side, lower tie, with listed
  wings and no alternative search. Recheck geometry against the last completed
  SPX minute at entry. Native intraday XSP OTM status remains unobserved.
- Entry: first usable simultaneous snapshot strictly after 10:30 through 10:32
  ET, using a completed >=54/59 minute first-hour prefix with <=120-second gaps
  and an exact 10:29 observation. Each fly must have a debit strictly in (0,4).
- Gate: unconditional versus efficiency >=0.30 and absolute first-hour drift
  >=half the straddle. This is a provisional continuation/movement hypothesis,
  not the quiet filter. Ten dates signal before quote admission.
- Exit: native published settlement versus the first later completed SPX/10
  observation inside the entry-fixed combined positive expiry-net interval.
  The latter attempts a strictly later full-pair quote within two minutes,
  capped at close minus 15 minutes. A body touch is not a fill.
- First failed fill window or signal-prefix outage irrevocably settles both
  flies. No recovery retry. No trigger means an exact cutoff close attempt,
  then settlement if unavailable. Missing settlements remain unresolved.
- All component transactions cross bid/ask, with needed sizes, signed payable
  closes, $0.65/gross contract/transaction and $5 adverse stress/fly/transaction.
  Midpoints are diagnostic. Additional broker/exchange/exercise charges and
  actual complex-order execution remain unverified. No partial fills modeled.

Combined expiry cash is the sum of two tents. Net subtracts both debits and
opening costs. Maximum expiry loss is total debits ×100 +$15.20; component
liquidation plus closing costs may lose more. Profitable zones are finite;
staying in a central gap, overshooting wings or reversing before exit can lose.
One accepted body-only trade has no positive expiry zone at its actual cost
and is retained with its outcome. No retrospective profit-feasibility filter.

## Results and decisions

Stressed totals, completed combined positions per alternative:

- Body-only unconditional: settlement −$5,042.80 (119); zone exit −$11,383.20 (119).
- Body-only movement: settlement −$776.60 (8); zone exit −$656.20 (8).
- All-strikes unconditional: settlement −$2,313.20 (121); zone exit −$4,820 (121).
- All-strikes movement: settlement +$414 (10); zone exit −$169.80 (10).

The positive settlement cell has 60% wins, $41.40 expectancy, PF1.85, $285.40
terminal-outcome drawdown, mean initial risk $120.60 and mean trade +0.4614R.
It has +$344.60 / +$69.40 in fixed chronological halves, but **−$202.40** after
the top three winners. It fails the frozen screen. The 10-entry zone-exit policy
has four combined closes and six explicit settlement fallbacks; it loses in
the second half and after top-three removal. All eight cells are rejected.

All-strikes movement reaches an entry-specific expiry-profit zone on 7/10
complete sampled proxy paths versus 72/105 other complete paths (70% vs68.6%).
Only four signal dates reach a zone on the original drift side. This does not
establish useful forecast skill. Body-only zones commonly overlap around entry,
so frequent early reaches do not validate a later moderate-move hypothesis.
All eight body-only movement zone exits lose after modeled costs.

Full monthly, split, net expectancy, win rate, profit factor, initial risk/R,
cost drag, terminal drawdown and top-three sensitivity are in the report and
summary. Drawdown is sampled once at terminal trade outcome, never intraday.
Matched comparisons retain unequal exposure: one iron fly versus two Batman
flies. Participation zeros apply only to valid no-signals. Exclusions and
unresolved positions are never zeroed. No funded-account return is claimed.

## Evidence and verification

- [Coverage before freeze](../../reports/research/xsp-batman-2026-11-12/coverage-01/coverage.json).
- [Frozen rules](../../reports/research/xsp-batman-2026-11-12/run-01/specification.json).
- [All results](../../reports/research/xsp-batman-2026-11-12/run-01/summary.json).
- [Complete journal](../../reports/research/xsp-batman-2026-11-12/run-01/journal.jsonl):
  1,850 date/cell rows, including no-signals and exclusions.
- [Independent cash ledger receipt](../../reports/research/xsp-batman-2026-11-12/run-01/cash-review/review.json):
  all 648 completed records, 173 liquidations and 475 settlements, zero errors.
  Direct raw option-side cash and individual-option intrinsic, independent of
  simulator pricing/account functions. All raw sides are retained.
- [Decision](../../reports/research/xsp-batman-2026-11-12/run-01/decision.json).
- [Final artifact/hash receipt](../../reports/research/xsp-batman-2026-11-12/evidence-manifest.json).

Source copies, hashes, original dirty-tree patch, commands, library versions and
input receipts live in the fresh run directory. Existing graph evidence was
backed up before the required AST update. Focused tests: **59 passed**; full Ruff
passed. Graphify completed with the existing missing `tree_sitter_sql` warning;
no SQL changed. Browser checks and final validation receipts accompany the HTML.

Reproduce from repository root with audited private inputs available:

```bash
uv run python -m tools.research_studies.xsp_independent.batman --out /tmp/xsp-batman-coverage-new --audit
uv run python -m tools.research_studies.xsp_independent.batman --out /tmp/xsp-batman-new --coverage /tmp/xsp-batman-coverage-new/coverage.json --freeze
uv run python -m tools.research_studies.xsp_independent.batman --out /tmp/xsp-batman-new --run
uv run python -m tools.research_studies.xsp_independent.review_batman --run /tmp/xsp-batman-new
uv run python -m tools.research_studies.xsp_independent.render_batman_report --run /tmp/xsp-batman-new --out /tmp/xsp-batman-new/report.html
uv run pytest tests/test_xsp_batman.py tests/test_xsp_quiet_flies.py tests/test_xsp_settlement_data.py -q
uv run ruff check .
graphify update .
```

Stop this matrix here. Next quiet evidence must use the unchanged policy on a
new joint cohort or observed full-cost complex executions. A redesigned Batman
requires a materially specified hypothesis and a fresh, separately frozen study.
Do not promote or activate either idea from a positive retrospective subset.
