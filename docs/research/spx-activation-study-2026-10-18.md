# SPX activation filters — retrospective study, 2026-10-18

**Decision: refine; insufficient evidence for an activation change.** Wide entry
spreads and prior-day volatility structure identify costly baseline opportunities
while retaining most winning dollars. None of the 16 fixed filters passed the
development-period selection criteria. Runtime strategy, risk, configuration,
credentials and services were unchanged.

The self-contained local report is
[`report.html`](../../reports/research/spx-activation-20261018/report.html).
It contains execution-cost and drawdown charts, annual comparisons, every tested
filter, threshold sensitivities and a selectable period view. Its private,
gitignored companion directory preserves the pre-analysis plan, canonical replay
journals, session features, full metrics and provenance. PNG charts are available
beside the report for export.

## Coverage and baseline

Fresh canonical research-core replays use current main `2ed5282c71e5`, checked-in
SPX configuration, `vendor_1m`, and the existing E0 entry and peak-trailer exits.
The three immutable local datasets were hash-verified:

- `spx_0dte_local_durable_development_20261001`: 585 sessions, 2022-01-03
  through 2024-06-28; hash `98434ab47077456d812a17be785e98d2cfc2c94819c986b0c83df6518a4f6b63`.
- `spx_0dte_local_durable_spent_holdout_20261003`: 357 sessions, 2024-07-01
  through 2025-12-09; hash `8dabf04a35d0c75696eedc0ee81088962e29d642b7ca5a815c185234e9ea49ef`.
- `spx_0dte_local_durable_validation_20261001`: 128 sessions, 2026-03-17
  through 2026-09-25; hash `0f1fbcc08fda0059c044532308871fb6434396d5d73e76f4b9f5d919c276e4d5`.

There are 1,070 eligible sessions, 823 E0 trades and 247 eligible no-trade days.
All E0 and diagnostic X1 positions resolve; there are no additional replay
exclusions or unpriced trades. Missing periods are not no-trade decisions. The
source gap from December 2025 to March 2026 remains explicit. The development
replay reproduces the earlier frozen baseline's E0 trade records.

Totals are dollars across independent one-fly opportunities, without a capital,
compounding, buying-power or account-risk simulation. Midpoint with fees earns
$31,011. Crossing recorded leg bid/ask with fees loses $10,279. Adding $0.05
adverse slippage per contract per executed side loses $39,319, with $53,430 maximum
realized cumulative drawdown. One-minute delayed stressed exits lose $34,112.
Commission is $0.65 per contract; there are four contracts per executed side;
cash settlement has no closing commission or slippage.

Under the primary stressed model, win rate is 13.1%, expectancy −$47.78 per trade,
profit factor 0.786, average win $1,333, and average loss −$256. Mean expectancy
is −0.1241 entry-stressed-debit units. Average exposure is about 181 minutes per
trade, with 149,139 fly-minutes in total. Nominal commissions total $3,775.

The largest observed realized drawdown runs from the 2022-12-12 peak to the
2026-03-25 trough, spanning 748 subsequent eligible observations. This is not a
continuously observed account or intraday mark-to-market drawdown.

## Conditions worth refining

- **Entry ask-minus-mid / mid at least 20%:** skips 43 trades, avoids $22,722
  of losses and misses $3,385 of wins. It retains 97.6% of gross winning dollars
  and all ten largest winners. Remaining stressed net is −$19,981; realized
  drawdown is $38,879. Improvement is positive in each sampled year and at the
  prespecified 15% and 25% neighbors. Its midpoint improvement is only $90:
  most of the benefit is execution cost avoidance.
- **Prior-session VIX/VIX3M at least one:** skips 29 trades, retains 99.6% of
  winning dollars and every top-ten winner, and improves stressed net by $13,156.
  Remaining net is −$26,163. No baseline trades meet this skip condition in the
  development window, so that window cannot validate its benefit.
- **Prior-session VIX1D/VIX at least one:** skips 84 trades, retains 94.7% of
  winning dollars and all ten largest winners, and improves stressed net by
  $20,537. Remaining net is −$18,782. Twenty-seven traded sessions have missing
  inputs and retain their baseline opportunity; no missing value is imputed.
- **Scheduled FOMC statement day:** skips 16 traded sessions, all losing in this
  sample, and saves $6,701 without missing an observed winner. The count is traded
  event days, not all scheduled meetings. Remaining net is −$32,619. This small,
  retrospectively inspected sample does not establish a reliable rule.

All-session paired ten-session moving-block bootstrap 90% intervals for improvement
are +$9,997 to +$29,467 for spreads, +$4,983 to +$23,362 for backwardation, and
+$3,017 to +$11,884 for FOMC. These are exploratory, unadjusted intervals across
26 rule/threshold comparisons, conditional on observed data and modeled fills.
An interval for improvement is not an interval establishing positive strategy P&L.

Matched-count random trade skipping is another benchmark. Low-VIX and small-gap
rules look ordinary against it, despite large dollar improvements on a losing
baseline. Cash, with zero trading P&L, also beats every individual primary filter
except the retrospective drawdown pause.

## Filters that sacrifice the desired upside

Skipping VIX below 17 removes 460 of 823 trades and 44.7% of winning dollars.
Requiring the opening half-hour to agree with the gap removes six of the ten
largest winners. Skipping fast openings makes stressed total P&L worse.

The $5,000 drawdown pause appears profitable: +$4,924 with $7,078 realized
drawdown. But it skips 621 trades and misses 62.9% of winning dollars, including
two top-ten winners. It mostly pauses through 2023–25 and fails the frozen
development criteria. It tracks a virtual always-running E0 while paused and
resets after missing-history gaps longer than seven calendar days. The 2026
restart is therefore a research assumption; this is not a validated restart rule.

## Periods and exit diagnostic

E0 stressed net is +$3,524 in 2022, −$16,228 in 2023, −$9,562 in 2024,
−$23,137 in 2025, and +$6,084 in the available 2026 period. These are unequal
coverage windows, not full comparable calendar-year returns.

The same entries held to settlement, existing variant X1, improve aggregate
stressed net to +$1,575, versus −$39,319 for E0. But X1 still loses $17,588 in
July 2024–December 2025. It is an exit/cost diagnostic, not a viable replacement
established by this study. Entry selection and exit triggers in the existing
accounting models remain based on midpoint decisions; repriced cash flows do
not feed executable costs back into those decisions.

## Procedure and limitations

The study froze 16 primary filters and ten specified neighboring thresholds before
the new runs. The plan's “12 neighbors” was a count typo; its listed bounds specify
ten. No combinations or further threshold searches were tried. Primary conditions
cover VIX levels, volatility structure, gap size, opening behavior, VIX/straddle
comparison, entry spread, scheduled releases/FOMC, and prior virtual E0 losses.

Daily ratios use the preceding SPX session. Opening features stop at 10:00 ET;
all entries occur at or after that time. Events obey the existing public-before-date
calendar rule. A veto removes that baseline opportunity without a later retry or
replacement. Missing feature values retain E0 and are counted. Closing moves are
descriptive only and never activation inputs.

Development selection uses 2022–June 2024, split at 2023-03-31. It requires positive
stressed net, at least 20% lower drawdown, at least 80% winning-dollar retention,
eight of ten top winners retained, and improvement in both halves. None qualify.
An expanding-history half-year selector using earlier sessions only mostly selects
E0; it briefly selects the spread rule in 2023 H2, when no entries meet its skip
condition. Its aggregate improvement is zero. This fallback is a study convention,
not advice to activate E0.

All historical windows were already inspected. These are retrospective stability
checks, not fresh holdout validation. Original SPX/VIX minute CSV provenance remains
unknown. Existing quality approvals cover the normalized inputs, with the recent
Q5 timing check unevaluable on irregular recorded index ticks. One-minute leg NBBO
does not prove complex-order fills, queue priority or intraminute trigger paths.

The unfloored stressed model pays to close some long butterflies. A derived
zero-net-exit-floor sensitivity removes $5,337 across 18 trades but still loses
$33,982. Some marketable entries also cost far more than their selection midpoint.
Neither cost assumption should be confused with demonstrated limit-order fills.

VIX is a 30-day expected-volatility measure, whereas the same-day ATM-straddle
proxy describes a different horizon. The tested ratio is a heuristic, not directly
observed mispricing. [Cboe's explanation](https://www.cboe.com/tradable-products/volatility-trading/).

The next bounded experiment should freeze execution-aware eligibility and
volatility-structure vetoes separately, retain winner-preservation gates, validate
actual fill behavior, and reserve future observations for the promotion decision.
This study does not justify changing activation or exit behavior.

## Reproduce

From the repository root, run the three canonical replays into a **new** study
directory. The recorded artifacts use `reports/research/spx-activation-20261018`.
All run commands use `--no-registry` and preserve existing evidence:

```bash
STUDY=reports/research/spx-activation-20261018-reproduction
CACHE=reports/thetadata_completion/2026-10-01/thetadata-cache
mkdir -p "$STUDY"
cp reports/research/spx-activation-20261018/plan.json "$STUDY/plan.json"

uv run --no-sync python -m butterfly_guy.research --cache "$CACHE" \
  --dataset spx_0dte_local_durable_development_20261001 run --variants E0,X1 \
  --profile vendor_1m --start 2022-01-03 --end 2024-06-28 --split 2023-03-31 \
  --no-registry --no-tieset --out "$STUDY/replays"
uv run --no-sync python -m butterfly_guy.research --cache "$CACHE" \
  --dataset spx_0dte_local_durable_spent_holdout_20261003 run --variants E0,X1 \
  --profile vendor_1m --start 2024-07-01 --end 2025-12-09 --split 2024-12-31 \
  --no-registry --no-tieset --out "$STUDY/replays"
uv run --no-sync python -m butterfly_guy.research --cache "$CACHE" \
  --dataset spx_0dte_local_durable_validation_20261001 run --variants E0,X1 \
  --profile vendor_1m --start 2026-03-13 --end 2026-09-25 --split 2026-06-18 \
  --no-registry --no-tieset --out "$STUDY/replays"

uv run --no-sync python tools/research_studies/activation_study.py --out "$STUDY"
uv run --no-sync python tools/research_studies/render_activation_report.py --out "$STUDY"
```

The analysis requires the preserved `plan.json` before execution. The two scripts
read offline inputs only. Alternate study output directories are supported by the
scripts' `--out` arguments.
The metadata contains exact commands, Git/config/source/environment fingerprints,
dataset identities, and output hashes. The full session-level output is retained.
