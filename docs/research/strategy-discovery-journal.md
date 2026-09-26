# Options strategy discovery journal

## 2026-07-14 — data audit and research design

### Verified data

- Live PostgreSQL 16 / TimescaleDB contains 18 public tables; nine are hypertables.
- Historical options are limited to 0-DTE SPX, NDX, and XSP chains. No SPY, QQQ,
  individual-equity, weekly, monthly, calendar, diagonal, or LEAPS history exists.
- `option_chain_snapshots` contains 55,401,575 rows (SPX 19,688,764; NDX 23,060,601;
  XSP 12,652,210) and occupies 3,573 MB including indexes and TOAST.
- Chain coverage: SPX 83 dates from 2026-03-13 through 2026-07-14; NDX 78 dates from
  2026-03-20; XSP 70 dates from 2026-04-01. Several early/incident days are partial.
- Stored fields are bid, ask, mark, last, volume, open interest, IV, delta, gamma,
  theta, vega, rho, bid/ask size, intrinsic/time value, moneyness, multiplier,
  theoretical value, symbol, strike, type, expiration, timestamp, and spot.
- Bid, ask, mark, IV, delta, gamma, theta, vega, volume, and open interest have no
  nulls. Bid/ask size is missing in 2,289,882 SPX rows and 1,105,884 NDX rows; XSP
  sizes are complete.
- `spot_prices` covers SPX, NDX, XSP, and VIX intraday. `daily_bars` has 92 SPX/NDX/XSP
  dates and 95 VIX dates beginning 2026-03-02. No breadth, futures, dealer positioning,
  or durable macro-event table was found.
- Relationships: `monitoring_leg_quotes.trade_id` cascades to `butterfly_trades.id`;
  `broker_order_intents.trade_id` sets null on trade deletion. Other market-data
  tables are related by symbol/date/time rather than foreign keys.

### Data limitations and leakage controls

- Four months is insufficient to demonstrate stability across multiple long-run
  regimes. SPX and XSP are the same economic exposure; NDX is correlated, so they
  are not three independent samples.
- The first pass uses only entry-time fields and rolling IV percentiles built from
  prior dates. Chronological 60/20/20 train/validation/test segments are reported.
- Every option leg buys at ask or sells at bid on entry, then sells at bid or buys
  at ask on exit. Round-trip commission is $0.65 per contract per side. Missing or
  illiquid entry quotes are rejected; no midpoint-fill assumption is used.

### Predeclared hypotheses (no tuning yet)

1. Long ATM straddle: realized intraday movement exceeds the crossed-spread premium.
2. Long 25-delta strangle: cheaper convexity improves long-vol expectancy.
3. Short iron fly: intraday decay exceeds tail and spread costs.
4. Short 20/5-delta iron condor: defined-risk volatility carry survives execution.
5. 55/25-delta debit spread following the 09:35–10:00 move: momentum continuation.
6. The same debit spread against that move: intraday mean reversion.
7. Strong-trend debit spread: momentum only after a 0.15% opening move.
8. Long ATM straddle only below the trailing IV 35th percentile.
9. Iron condor only above the trailing IV 65th percentile.

### First-pass result

- Volatility selling failed decisively. Iron fly and iron condor expectancy was
  negative on every underlying after crossing the recorded spread.
- Unconditional long straddles/strangles were mildly positive in some full samples,
  but chronological holdout performance changed sign across NDX and XSP.
- The filtered IV variants produced too few trades and contradictory segments; very
  high Sharpe values on three to eight observations were rejected as small-sample
  artifacts.
- Sensitivity at 09:45/10:00/10:30 entries and 15:15/15:30/15:45 exits did not
  preserve a long-vol edge across assets. SPX 10:30 trend debit reached full-sample
  Sharpe 2.06, but training Sharpe was -0.72 and NDX/XSP full samples were negative.
  It is regime-local, not robust.

### Second structural pass

Four fixed candidates were added before any additional result was inspected: ATM
butterfly, 25-delta directional butterfly, trend-following opposite-side credit
spread, and reversal-side credit spread. Wing distance for butterflies is 0.30% of
spot so the rule scales across SPX, NDX, and XSP.

All four failed: every full-sample butterfly result was negative, and neither credit
spread generalized across markets or chronological segments.

### Final data-driven pass

Two volatility hypotheses use fields not consumed by the structural pass:

1. Buy the ATM straddle only when its ask premium as a fraction of spot is below the
   trailing 20-session median absolute 10:00–15:45 underlying move.
2. Buy the ATM straddle only when entry gamma per absolute theta is at or above its
   trailing 65th percentile.

Both features are calculated from the current entry snapshot and prior sessions;
the current exit is appended to history only after that day's decision.

The filters also failed. At 10:00 the XSP variants exceeded Sharpe 2 on only 12–14
trades while their training segments were negative and NDX lost. Moving entry to
10:30 reversed the signs. This is regime/timing instability, not confirmation.

## 2026-07-14 — diminishing returns checkpoint

Fifteen fixed hypotheses were tested on three assets. Five nearby entry/exit timing
combinations were evaluated for the surviving families. Every additional structural
or feature filter either remained negative, reduced the sample to single digits, or
reversed sign across time/underlying. Further filtering would be in-sample curve
fitting, so research stops here pending materially more history.

The best observed result is the SPX 10:30 trend-following 55/25-delta debit spread,
but it is rejected: full Sharpe 2.06 and positive expectancy coexist with train
Sharpe -0.72, an April–May walk-forward Sharpe of -4.61, NDX Sharpe -2.17, XSP
Sharpe -0.12, and a bootstrap Sharpe 95% interval of -1.73 to 5.69.

Entry is 10:00 ET and exit is 15:45 ET. These values and delta targets are fixed for
the first pass. Only strategies with positive holdout expectancy and cross-underlying
support advance to sensitivity and robustness testing.

## 2026-09-20 — SPX cash-settlement parity correction

The frozen SPX database replay was rerun for 2026-03-13 through 2026-09-18 without
changing entries, strikes, widths, exit thresholds, confirmation polls, the trading
window, commissions, or slippage. Base commit and `origin/main` were both
`e2ba77284370b7edc7c7e94d659fe707a226f834`. The configuration was
`configs/config.yaml`, SHA-256
`d120b63fd4e12ed812cc2742d602f9e531a1f5ca38e28c30628ab149f5d1b397`.

The defect regression first failed because a held-to-close butterfly returned
`end_of_day` and used the last option mark. After the fix, it returns `cash_settled`
and uses `position_manager.fly_settlement_value`, the function called by the paper
runtime's position service, with the official same-session index close. The regression
also proves that absent settlement evidence returns `missing_settlement` with no trade
result. Legacy final-mark valuation is retained only
as the explicit `--legacy-end-of-day-mark` diagnostic.

### Frozen result

| Metric | Legacy final mark | Corrected cash settlement | Change |
|---|---:|---:|---:|
| Trades | 118 | 118 | 0 |
| Net P&L | $17,247.60 | $17,691.60 | +$444.00 |
| Expectancy | $146.17 | $149.93 | +$3.76 |
| Profit factor | 2.049 | 2.074 | +0.025 |
| Win rate | 18.6% (22/118) | 18.6% (22/118) | 0.0 pp |
| Median trade | -$134.20 | -$134.20 | $0.00 |
| Maximum drawdown | $3,613.00 | $3,618.00 | +$5.00 worse |
| MFE capture | 50.0% | 50.0% | 0.0 pp (rounded) |
| Held-to-close contribution | $31,066.80 | $31,510.80 | +$444.00 |
| Estimated commission drag | $613.60 | $556.40 | -$57.20 |

Legacy exit totals were 47 morning, 15 late-morning, 34 afternoon, and 22
`end_of_day`. Corrected totals were 47 morning, 15 late-morning, 34 afternoon, and
22 `cash_settled`. No corrected replay trade was excluded. The database lacked the
2026-09-18 official close, but that day's simulated trade exited intraday.

### Evidence, assumptions, and exclusions

The official Cboe SPX history download had SHA-256
`001099a8dd56f943335d67dbad271d4080a700334b758d1d6226133c052dcfd2`.
Cboe supplied 131 sessions in the replay window; production `daily_bars` supplied 130,
through 2026-09-17. Every available database close matched Cboe to the cent.

Five recorded paper settlements with explicit settlement evidence reconciled exactly
to the shared intrinsic function within cent rounding: trade IDs 139 (2026-06-22),
150 (2026-06-26), 184 (2026-07-17), 189 (2026-07-21), and 212 (2026-08-03).
Their source was `schwab_final_regular_session_1m_close`, so this establishes formula
parity rather than source parity with Cboe.

Twelve recorded `cash_settled` trades were excluded from recorded-trade reconciliation
because both settlement spot and source were missing: IDs 3 (2026-03-17), 4
(2026-03-18), 5 (2026-03-19), 6 (2026-03-20), 7 (2026-03-23), 8 (2026-03-26),
16 (2026-04-01), 19 (2026-04-02), 20 (2026-04-06), 61 (2026-05-06), 77
(2026-05-13), and 130 (2026-06-16). Their option exit marks were not used to infer
settlement.

Assumptions: SPXW positions are PM-settled; the official same-session SPX close is the
appropriate expiration settlement evidence; cash settlement has no closing fill,
slippage, or commission; and missing evidence remains missing data. The corrected
baseline remains highly dependent on held-to-close outcomes and is not deployment
evidence.

### Exact commands and implementation fingerprints

```bash
ssh -F /dev/null -o BatchMode=yes billy@helios 'docker exec butterfly_spx_app python -m butterfly_guy.scripts.run_backtest_db 2026-03-13 2026-09-18 --asset SPX'
ssh -F /dev/null -o BatchMode=yes billy@helios 'docker exec -i butterfly_spx_app python - 2026-03-13 2026-09-18 --asset SPX' < /tmp/corrected_replay_overlay.py | tee /tmp/spx_corrected_replay_20260313_20260918.log
UV_CACHE_DIR=/tmp/butterfly-spx-settlement-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/butterfly-spx-settlement-uv-python uv run pytest tests/test_backtest_research_integrity.py tests/test_run_backtest_db_defaults.py -q
UV_CACHE_DIR=/tmp/butterfly-spx-settlement-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/butterfly-spx-settlement-uv-python uv run pytest -q && UV_CACHE_DIR=/tmp/butterfly-spx-settlement-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/butterfly-spx-settlement-uv-python uv run ruff check .
```

The focused suite passed 21 tests. Full verification passed 670 tests with one skip,
and Ruff reported no errors.

Corrected source SHA-256 fingerprints:

- `src/butterfly_guy/backtest/data_loader.py`: `ce442a5a99dbfc73b06c8c23cdf1bb6bf0524097d7a9b5d541f615bd8e4516f9`
- `src/butterfly_guy/backtest/simulation_engine.py`: `57cc88ec0568144989dff1b182ed4bd4617e3af1f21e8960c4919e3c5336cf11`
- `src/butterfly_guy/scripts/run_backtest_db.py`: `39ebcbd25df3a4998c90e3fb37e1f46694c81994a4019f4882fe5441245152ab`

The bounded corrected-replay overlay was streamed through stdin only because the local
checkout's database password did not match the runtime credential. It changed only
settlement loading and held-to-close finalization, wrote no remote file, and did not
modify or restart a service.

## 2026-09-21 — SPX executable-side accounting on the settlement-correct replay

This was an accounting experiment on the settlement-parity implementation from commit
`3cf2df23224cdd29ad3664d08441f69a69f207b5`, not a strategy optimization. The
inclusive sample remained 2026-03-13 through 2026-09-18. Signals, entry window,
direction, VIX-bucket width selection, strikes, reward/risk filter, drawdown thresholds,
confirmation settings, profit-management policy, and exit timestamps were generated
once by the corrected-midpoint model and then frozen for both executable comparisons.
The checkout base was `ef13afb940a95f091f704965ec692200698dd60a`; the changes
described here were uncommitted. `configs/config.yaml` had SHA-256
`d120b63fd4e12ed812cc2742d602f9e531a1f5ca38e28c30628ab149f5d1b397`.

### Accounting models and deterministic data rules

- `corrected_midpoint` is the named comparison baseline. Entry and an intraday exit use
  the recorded composite midpoint with $0.65 per contract per executed side. A held
  position uses official same-session SPX intrinsic cash settlement, with no fabricated
  closing fill, closing commission, or slippage.
- `marketable` buys the lower and upper long contracts at their recorded asks and sells
  two center contracts at their recorded bid. An intraday exit uses the inverse sides:
  lower and upper bids and two center asks. Commission is $0.65 on each of the four
  contracts at entry and, when an exit order exists, on each of the four contracts at
  exit. Cash settlement remains a settlement event rather than an executable exit.
- `stressed_marketable` uses the same bid/ask model and moves every contract fill $0.05
  adversely. That is $20 additional entry cost per butterfly, another $20 reduction on
  an intraday exit, and no exit stress on cash settlement.
- Only a snapshot recorded at or before the already-frozen decision timestamp is
  eligible. No later snapshot is used. If any required leg or bid/ask field is absent,
  the fill is classified as missing; if any leg has bid greater than ask, it is classified
  as crossed. Either condition excludes the trade from that executable model at that
  timestamp. No midpoint, synthetic quote, later quote, or carried value substitutes for
  an executable fill.
- An incomplete monitoring observation is skipped: it cannot update MFE, trigger an exit,
  or advance an exit-confirmation count. The final no-imputation rerun produced the same
  decisions and aggregate results as the initial comparison.

### Data provenance and coverage

The source was the production TimescaleDB `option_chain_snapshots`, `spot_prices`, and
`daily_bars` data already used by the SPX database replay. It was read through the
existing `butterfly_spx_app` container on Helios with a non-persistent in-memory module
overlay approved for this experiment; no remote file, service, configuration, database,
or order state was changed. The final log completed at 2026-09-21T05:06:43Z and had
SHA-256 `d9443466da5c89f2bbed110c19a1949ae69da37de27c877489d4bfec314af8d4`.

- The database-qualified range contained 128 sessions, from 2026-03-13 through
  2026-09-18. Qualification requires at least 50 same-day 0-DTE chain snapshots.
- Two sessions, 2026-03-13 and 2026-03-16, lacked the full prerequisite data used by
  `load_date_data` and were excluded explicitly.
- Eight sessions had no qualifying entry in the frozen window: 2026-03-18, 2026-04-27,
  2026-05-04, 2026-05-18, 2026-06-02, 2026-06-12, 2026-08-25, and 2026-09-08.
- The remaining 118 sessions all traded. There were 96 intraday exits and 22 official
  cash settlements. All 118 entries and all 96 required executable exits had complete,
  uncrossed markets: missing entry 0, crossed entry 0, missing exit 0, crossed exit 0.
- The MFE path contained 21,904 recorded observations. Of those, 21,887 (99.9224%) had
  all three leg markets, 17 (0.0776%) were missing at least one leg, and zero were
  crossed. The 17 incomplete observations were skipped rather than imputed.

### Frozen result

| Metric | Corrected midpoint | Marketable | Marketable + $0.05/contract leg |
|---|---:|---:|---:|
| Trades | 118 | 118 | 118 |
| Net P&L | $17,691.60 | $14,170.60 | $9,890.60 |
| Expectancy | $149.93 | $120.09 | $83.82 |
| Profit factor | 2.074 | 1.724 | 1.422 |
| Win rate | 18.6% | 15.3% | 14.4% |
| Median trade | -$134.20 | -$167.70 | -$207.70 |
| Maximum drawdown | $3,618.00 | $5,266.00 | $7,566.00 |
| MFE capture | 50.0% | 52.4% | 54.8% |
| Top-three-trade concentration | 32.7% | 32.9% | 33.2% |

Crossing the recorded spread reduced net P&L by $3,521.00 relative to corrected
midpoint. The explicit stress reduced it by another $4,280.00, exactly 856 executed
contract sides multiplied by $5 adverse slippage per contract. Total commission was
$556.40 in every model: four contracts on 118 entries and four contracts on 96
intraday exits.

The result remains highly dependent on settlement outcomes. In the midpoint baseline,
the 22 cash-settled trades contributed $31,510.80 while the other 96 trades contributed
-$13,819.20. The negative median, low win rate, larger executable drawdowns, and this
exit-regime dependence remain material failure modes even though top-three concentration
is about one-third of gross wins.

### Exact commands and implementation fingerprints

Standard reproduction wherever the configured TimescaleDB is reachable:

```bash
UV_CACHE_DIR=/tmp/butterfly-execution-uv-cache uv run python src/butterfly_guy/scripts/run_backtest_db.py 2026-03-13 2026-09-18 --asset SPX --execution-accounting-report
UV_CACHE_DIR=/tmp/butterfly-execution-uv-cache uv run pytest tests/test_backtest_research_integrity.py tests/test_run_backtest_db_defaults.py -q
UV_CACHE_DIR=/tmp/butterfly-execution-uv-cache uv run pytest -q
UV_CACHE_DIR=/tmp/butterfly-execution-uv-cache uv run ruff check .
```

The approved Helios evaluation used the same four tested modules as an in-memory overlay:

```bash
python /tmp/build_execution_overlay.py 2026-03-13 2026-09-18 --asset SPX --execution-accounting-report | ssh -F /dev/null -o BatchMode=yes billy@helios 'docker exec -i butterfly_spx_app python -' | tee /tmp/spx_execution_accounting_20260313_20260918.log
```

Final source SHA-256 fingerprints:

- `src/butterfly_guy/backtest/data_loader.py`: `ce442a5a99dbfc73b06c8c23cdf1bb6bf0524097d7a9b5d541f615bd8e4516f9`
- `src/butterfly_guy/backtest/simulation_engine.py`: `b90195072a896f90b4cc7cf325463913dcdaa00ab280e3e9fb04d81188415851`
- `src/butterfly_guy/backtest/execution_accounting.py`: `247b5182876e21086eb1ab6138704ddd92ddeb8a4aa13cb9a0f688a4da648637`
- `src/butterfly_guy/scripts/run_backtest_db.py`: `d7ac3c0a4bf3034632164427024af41e7e738ab1ec55357e568a65bd647b4354`

Conclusion: an executable edge remains in this fixed historical sample. It remains
positive after recorded bid/ask crossing and after the additional $0.05 adverse move on
every contract fill: $9,890.60 net, $83.82 expectancy, and 1.422 profit factor in the
stress case. This is not a broad or stable-looking edge—the typical trade loses, drawdown
more than doubles under stress, and cash-settled outcomes supply all aggregate profit—but
the requested executable accounting does not eliminate the sampled edge.

### Reproduction under the roll-forward exit rule

The frozen table above was produced before `execution_accounting.py` began rolling an
unusable exit observation forward to the next monitoring time with a settlement
fallback. The whole sample was rerun on committed code
`b83c2a18427f07dc514841e9fe2957eb4e391d80` with a clean worktree, and every published
figure reproduced exactly: 118 trades from 128 qualified sessions, 22 cash-settled and
96 intraday, net P&L $17,691.60 / $14,170.60 / $9,890.60, expectancy $149.93 / $120.09 /
$83.82, profit factor 2.074 / 1.724 / 1.422, maximum drawdown $3,618 / $5,266 / $7,566,
MFE capture 50.0% / 52.4% / 54.8%, top-three concentration 32.7% / 32.9% / 33.2%, and
held-to-close contribution $31,510.80. Exit totals were 47 morning, 15 late-morning, 34
afternoon, and 22 cash-settled. The ten skipped sessions were unchanged: 2026-03-13 and
2026-03-16 for missing prerequisite data, and 2026-03-18, 2026-04-27, 2026-05-04,
2026-05-18, 2026-06-02, 2026-06-12, 2026-08-25, and 2026-09-08 for no qualifying entry.

The rule change is inert on this sample by construction. Roll-forward only engages when
an exit observation is unusable, and all 96 required executable exits had complete,
uncrossed markets. Path coverage was again 21,887 of 21,904 observations usable, with 17
incomplete and none crossed; those 17 fall on monitoring observations, not on exits. The
historical baseline and the prospective cohort therefore share one code path, which was
the point of the rerun rather than any expected change in the numbers.

The run log had SHA-256
`253a8b15431092a6dcd7f058718a9811ca241918a4d4ec432675d8c35b205724`.

### Pre-registered drawdown limit

The stressed-marketable rejection threshold for the first prospective cohort is $12,000
of drawdown on a single one-lot butterfly, chosen on 2026-09-21 before any prospective
session existed. It is about 1.6 times the $7,566 historical stressed drawdown. The
threshold asks whether the strategy degraded, not what loss is tolerable: the historical
figure is the maximum of one 118-trade path, and a fresh path of similar length drawn
from the same distribution would exceed it roughly half the time, so a limit set at the
historical maximum would reject a healthy strategy on sampling variation alone. A 14%
stressed win rate and a negative median trade make long losing runs the normal texture
of this strategy rather than evidence of failure.


## 2026-09-21 — prospective execution-validation cohort (pre-registration)

The 2026-03-13 → 2026-09-18 executable result above is an in-sample measurement on the
same history the strategy was developed against. This section pre-registers a
prospective validation study on genuinely unseen sessions. It is a validation study,
not a development cycle: no signal, timing, strike, width, confirmation, exit, or
settlement rule may change while a cohort is open.

### Pre-registered hypothesis

Primary: the frozen SPX strategy will produce positive net P&L and positive expectancy
over at least 120 untouched prospective trades under stressed-marketable accounting.

Secondary questions, registered before any prospective data exists:

- Does marketable accounting remain profitable in each chronological half of the cohort?
- Is the prospective edge still concentrated in cash-settled positions?
- Do three exceptional trades account for an unacceptable share of gross profits?
- Are quote gaps or crossed markets materially reducing executable coverage?

The primary result is always stressed-marketable. Corrected midpoint is retained only as
a named comparison baseline.

### Start and stopping rules

The cohort starts on the first complete trading session after its manifest is created;
`init` refuses an earlier start for a prospective cohort, and `update` refuses any
session before the recorded start date.

Sixty trades is an early-failure checkpoint, not a passing result. The registered
endpoint is reached only when all three conditions hold, whichever comes last:

- at least 120 eligible trades;
- at least 20 cash-settled trades;
- at least 15 stressed-marketable winners.

At 20 trades, only pipeline integrity and coverage are reviewed; no profitability
conclusion is drawn. At 60 trades, the cohort is rejected early only if stressed
marketable is clearly negative and the loss is not attributable to a documented
temporary data outage.

At the endpoint, an executable edge is declared only if stressed-market net P&L,
expectancy, and profit factor above 1.0 all hold; marketable P&L is positive in both
chronological halves; at least 95% of eligible entries are executable without
imputation; the top three trades contribute no more than 50% of gross profits; and
maximum drawdown stays under the dollar limit chosen at `init` time. Because the
historical profit came predominantly from settlement, the report separately classifies
the outcome as a general executable edge, a settlement-dependent edge only, or no
executable edge.

### Quote-handling rules

- Every leg and decision uses the latest quote whose timestamp is at or before the
  simulated decision time; the snapshot timestamp and its age in seconds are recorded
  per leg. A later quote is never selected.
- No midpoint, theoretical value, adjacent strike, prior-session data, or carried-forward
  bid/ask substitutes for a missing executable side.
- `ask < bid` is crossed. Absent, null, non-finite, or negative required sides are
  missing/invalid.
- An unavailable or crossed entry leg makes the trade unpriced and excludes it from P&L
  while keeping it in coverage.
- An incomplete or crossed exit observation is skipped and the exit rolls forward to the
  next recorded monitoring time; the count of skipped observations is recorded on the
  trade. If no executable exit remains before settlement, the settlement-correct value is
  used with no invented closing commission.
- Missing and crossed markets are recorded separately by entry/exit, side, leg, and date.

Note one deliberate change to `execution_accounting.py` relative to the historical study:
previously an unusable exit snapshot dropped the whole trade from P&L. Roll-forward plus
settlement fallback replaces that, so exit-side quote gaps no longer silently shrink or
bias the executable sample. Entry-side gaps still leave the trade unpriced.

### Ledgers and integrity

Each cohort lives in `reports/prospective_execution/<cohort-id>/` with an immutable
`manifest.json`, append-only `daily_runs.jsonl` and `trades.jsonl`, and regenerated
`summary.json` / `summary.md`. The manifest freezes the cohort boundaries, Git SHA and
dirty-worktree status, configuration path and SHA-256, per-file source hashes, every
resolved strategy parameter, fill-model definitions, commission and stress assumptions,
decision rules, database tables, quote rules, and the exact init command.

Every `update` validates current sources and configuration against the manifest and
refuses to append on drift, naming the changed artifact. Trade identity is the SHA-256 of
cohort ID, session date, decision time, direction, and strikes. Rerunning a recorded date
either reproduces the identical record and appends nothing, or raises an integrity error;
it never appends a duplicate. Sessions whose quotes or official settlement are still
incomplete are deferred rather than recorded, so the later complete run does not have to
amend history. Corrections for documented data errors must be explicit amendment records.

### Exact commands

```bash
uv run python src/butterfly_guy/scripts/run_prospective_execution.py init \
  --asset SPX \
  --target-trades 120 \
  --min-cash-settlements 20 \
  --min-stressed-winners 15 \
  --max-drawdown MAX_ACCEPTABLE_DOLLAR_DRAWDOWN

uv run python src/butterfly_guy/scripts/run_prospective_execution.py update \
  --cohort reports/prospective_execution/COHORT_ID \
  --through YYYY-MM-DD

uv run python src/butterfly_guy/scripts/run_prospective_execution.py report \
  --cohort reports/prospective_execution/COHORT_ID

uv run python src/butterfly_guy/scripts/run_prospective_execution.py verify \
  --cohort reports/prospective_execution/COHORT_ID

uv run pytest tests/test_prospective_execution.py tests/test_backtest_research_integrity.py tests/test_run_backtest_db_defaults.py -q
uv run pytest -q
uv run ruff check .
```

The historical plumbing rehearsal uses `init --dry-run-cohort --start <past date>` over
five already-known dates. Its results verify manifest validation, append-only behavior,
quote provenance, report generation, and repeat-run idempotency only, and are never
combined with a prospective sample.

### Implementation fingerprints at pre-registration

- `src/butterfly_guy/backtest/prospective_execution.py`: `a3dfc10d3fba6996527c4cf9070bdcea5a3e2e3c1b3c3ad0672176a5dd16274c`
- `src/butterfly_guy/backtest/execution_accounting.py`: `24d90f5ff56f9c3da38a6d56f701859c3f6e1814164afd6fc2b69c594be05cdc`
- `src/butterfly_guy/scripts/run_prospective_execution.py`: `e21f3c1086946d765f1ac83664bd0507ef5d88ff91151a71dea8f8d5387ac7a7`
- `tests/test_prospective_execution.py`: `b01908e23b055928213935ebf8d393bc7f81450122a3dd8e0984e45563c80a9b`

The runner and its tests were corrected after pre-registration and before any
cohort existed; their earlier hashes were
`4bb9db87d3d0320c919c0577baac7bd2bd1a3381916ff556b222d63b976c85cb` and
`74ff1f9b5e215e4b752f34f964325d9bbac69364995c72e926409ec7fe9d511a`. See the
start-date correction below. `prospective_execution.py` and
`execution_accounting.py` are unchanged.

These hashes describe the pre-registration state. The binding fingerprints for any cohort
are the ones inside that cohort's own `manifest.json`, recorded at `init` against a
committed worktree.

### Start-date correction before the first cohort

`init` derived the current date from UTC and then took the next weekday. Sessions are
Eastern, so UTC rolls over at 20:00 ET and an evening `init` treated the next morning's
session as already underway. Initializing at 17:05 PDT on 2026-09-21 produced a start of
2026-09-23 and silently discarded Tuesday 2026-09-22, whose opening bell was still
about thirteen hours away. The date is now resolved in `America/New_York`, the timezone
`CohortSpec` already declared and wrote into the manifest; the manifest's own
`created_at` remains UTC. A regression test pins Monday 2026-09-21 20:05 ET to a Tuesday start,
the post-session case to Wednesday, and Friday evening across the weekend. The defective
cohort directory was deleted before any session was recorded; no ledger ever contained a
record under the old behavior.

### Dry-run rehearsal

Two rehearsal cohorts were run outside the repository tree under `--root`, starting
2026-09-14 and 2026-09-17, and were never placed under `reports/`. They recorded five
and two sessions respectively over already-known history. Demonstrated properties:

- Manifest freeze: sixteen source hashes, the configuration SHA-256, resolved strategy
  parameters including `drawdown_confirmation_polls = [1]`, fill models, quote rules, and
  a clean committed SHA with `dirty=False`.
- Source drift refusal: appending one comment line to `execution_accounting.py` caused
  `update` to refuse and name the changed file.
- Tamper detection: mutating a single `net_pnl` field in `trades.jsonl` made `verify`
  report a record hash mismatch against the affected trade ID.
- Repeat-run idempotency: rerunning recorded dates appended nothing and left
  `trades.jsonl` byte-identical, completing in 14 seconds.
- Start guards: a real cohort refused a past start, and a cohort starting 2026-09-17
  recorded only 2026-09-17 and 2026-09-18 without reaching back.
- Report generation: coverage, chronological halves, settlement split, skipped exit
  observations, and settlement fallbacks all populated.

Rehearsal results are plumbing evidence only and are never combined with a real cohort.

### Registered cohort

- Cohort ID: `spx-prospective-2026-09-22`
- Manifest SHA-256: `1e6e82978d47d55782f2ae5b45e59fbd7f1eeae8010687e9cc930915c6d7b889`
- Frozen commit: `6ffbfe7c0884c5c1616b6c226eee586b93ac1be7`, clean worktree, pushed
- First eligible session: 2026-09-22
- Endpoint: 120 trades, 20 cash settlements, 15 stressed winners, $12,000 drawdown limit

Daily command:

```bash
uv run python src/butterfly_guy/scripts/run_prospective_execution.py update \
  --cohort reports/prospective_execution/spx-prospective-2026-09-22 --through YYYY-MM-DD
```

The replay database is reachable only from Helios, so research runs go through an SSH
tunnel (`ssh -f -N -L 15432:127.0.0.1:5432 billy@helios`) with `DATABASE__PORT` and
`DATABASE_PASSWORD` supplied through the gitignored `.env`. A three-session comparison
reproduced the container-side figures exactly, confirming the tunnel path is equivalent.
One session costs about two minutes; rerunning recorded dates costs seconds.

The append is automated rather than run by hand: `tools/cohort_daily_update.sh` under the
systemd user units in `infra/systemd/` fires weekdays at 18:30 PT, appends every completed
session, verifies ledger integrity before committing, and treats a failed push as a
warning so a locked ssh key cannot cost a session. Repeat and catch-up runs are safe
because recorded sessions are skipped and incomplete ones are deferred. The timer must be
stopped before any strategy work, since source drift makes `update` refuse to append.

### Checkpoint results

- Dry-run rehearsal: completed 2026-09-21; every integrity property above demonstrated.
- 20-trade integrity checkpoint: not yet reached.
- 60-trade early-failure review: not yet reached.
- Registered endpoint: not yet reached.
- Coverage statistics: none yet; no prospective session has been recorded.

Conclusion: pending. No prospective session has been evaluated, so this study makes no
claim yet about whether a stressed executable edge survives out of sample.

## 2026-09-25 — SPX idea sweep and low-VIX diagnosis (development data only)

This is exploratory development research on already-seen history, not a change to the
frozen strategy and not evidence about the open prospective cohort. No tracked source,
configuration, service, or cohort ledger was modified; the cohort's source hashes are
untouched. Base commit `f918c08c9f44a59597a2c6ec68cf113dc83cb54b`.

### Data and harness

A read-only, after-hours export from the Helios `butterfly_guy` database: SPX 0-DTE
`option_chain_snapshots` rows 09:30–16:00 ET with `abs(strike − spot_price) ≤ 200`
(8,152,966 rows, 133 sessions), `spot_prices` for SPX and `$VIX`, and `daily_bars` for SPX
and `$VIX`. SHA-256: chain `470169466260d009f748bbb74fcc4aea7aaf562a0aaa1876b017e219c08a0332`,
spot `8757f19f989061a15b1c4b294c61e1b74e48c3646266b76d47771ca1f7cf4862`, daily
`cb4247a0f190a29c89adc1aca747baca699f2f356b6afcb20a229f55e346b74d`.

A standalone numpy replay reimplements the frozen entry (gap direction, VIX bucket widths
and sigma anchors, ±15 center tolerance, RR ≥ 8, cost caps, first qualifying snapshot in
10:00–10:45 ET) and the 60/90/75% peak trailer. It uses the chain snapshot as its decision
clock rather than `spot_prices` bars. Accounting matches the 2026-09-21 models: midpoint;
marketable (outer asks, twice the center bid; inverse on exit); and stressed (+$0.05 per
contract per executed side), with $0.65 per contract and free cash settlement against the
official close. Parity against the frozen 2026-03-13 → 2026-09-18 replay: 118 trades
(22 settled, 96 trailed), midpoint $17,634.60 vs published $17,691.60, stressed $9,830.60 vs
$9,890.60. The residual (0.3%) is attributed to the decision-clock difference.

Sample for the sweep: 132 sessions, 2026-03-13 → 2026-09-24. Halves: H1 through
2026-06-18 (67 sessions), H2 from 2026-06-19 (65 sessions). The variant list was written
before any variant was run. Round 2 was written after round 1 and is labeled post-hoc.

### Sweep results (stressed net P&L)

| Variant | Trades | Net | H1 | H2 |
|---|---:|---:|---:|---:|
| E0 baseline replica | 122 | $10,424 | $17,031 | −$6,607 |
| X1 hold to settlement | 122 | $5,051 | $14,344 | −$9,293 |
| X2 / X3 take profit 3× / 2×, else settle | 122 | −$2,574 / −$3,079 | −$1,143 / −$2,431 | −$1,431 / −$647 |
| X4 50% stop, else settle | 122 | −$625 | $7,489 | −$8,114 |
| X5 trailer, flat at 15:00 | 122 | −$4,044 | $3,448 | −$7,493 |
| D1 opening-momentum direction | 123 | $2,505 | $11,208 | −$8,703 |
| D2 gap-fade direction | 123 | −$7,244 | −$2,416 | −$4,827 |
| D3 call and put fly daily | 245 | $3,181 | $14,615 | −$11,434 |
| D4 ATM fly, settle | 123 | −$19,272 | −$11,377 | −$7,895 |
| K1 skip wide entry spread (H1-median gate) | 48 | $11,560 | $15,474 | −$3,914 |
| G1 prior-session EV selector, any fly, settle | 112 | $12,221 | −$346 | $12,567 |
| G2 G1 at 13:00 | 112 | $10,084 | −$16,122 | $26,206 |
| R1 (post-hoc) skip VIX < 17 | 67 | $12,722 | $17,086 | −$4,364 |
| R3 E0 candidates ranked by EV, trailer | 106 | $4,617 | $10,193 | −$5,577 |

No variant met the registered bar of beating the baseline in both halves. The peak trailer
beat every simpler exit, and gap direction beat momentum and fade. Straddle-anchored centers
(C1/C2) and 11:30/13:00/14:30 entries (T1–T6) produced one to four trades each. This is
structural: the chain-implied remaining-session σ (1.25 × the 10:00 ATM straddle) is about
0.4× the VIX daily move, and RR ≥ 8 exists only about 1.5–2 σ out of the money. G1's total
is not comparable: it chose 50-point flies at about $860 of debit (about 4× baseline risk),
returned 12% on stressed debit versus the baseline's 25%, and its highest-EV quartile lost
$9,740. Hypothesis 2 of `SHARPE_RESEARCH.md` (rank by expected payoff) failed as R3.

### Low-VIX diagnosis

The baseline's stressed P&L by entry VIX: < 17, −$2,578 over 56 trades; 17–24.5, +$8,061
over 55; > 24.5, +$4,941 over 11. This is mostly confounded with time. In an OLS of
stressed dollars per trade on a VIX < 17 indicator and an H2 indicator, the VIX < 17
coefficient is −$54 (t −0.29) and the H2 coefficient is −$368 (t −2.00). 43 of the 56
low-VIX trades fall in H2, and within H2 the 17–24.5 bucket did worse per trade (−$218)
than VIX < 17 (−$52).

Ruled out: placement differs by regime (mean center distance 1.58 / 1.56 / 1.64 σ, width
0.88 / 0.89 / 0.92 σ), and low-VIX sessions moving less than priced (mean |close − 10:00
spot| of 0.79 / 0.79 / 0.76 σ). A market-wide grid of 10:00 flies at 0–2 σ on both sides
varies more between halves than between VIX buckets.

Two mechanisms remain:

- Cost drag is about flat per fly ($66.8 / $65.3 / $67.8 per trade), so it is 28.8% of a
  low-VIX debit versus 21.9% and 15.0%. Low-VIX midpoint expectancy is only +$20.8 per
  trade; costs flip it negative.
- At VIX < 17, favorable excursion after 10:00 is smaller upward than downward in both
  halves (up minus down −0.34 σ in H1, n = 14; −0.17 σ in H2, n = 45; both bootstrap 90%
  intervals include zero). It is the opposite at 17–24.5 (+0.11, +0.13). Low-VIX call flies
  lost in both halves (−$1,617 over 8 trades; −$3,633 over 27). Low-VIX put flies won in both
  (+$1,282 over 5; +$1,390 over 16).

### Hypothesis registered for a future forward cohort (not applied)

H-LV1: with every other frozen rule unchanged, skipping CALL-direction entries when entry VIX
is below 17.0 improves stressed-marketable expectancy relative to the frozen baseline on
untouched sessions. It was derived post-hoc from 13 H1 and 43 H2 low-VIX trades, 21 of them
puts, and is not validated. It must not be added to the open cohort
`spx-prospective-2026-09-22`. A separate test must begin after that cohort's endpoint, or
run in parallel as a shadow comparison from shared entries without touching the cohort's
source hashes.

### Why the baseline fails in H2

Every component except settlement landings is unchanged between halves: trailed-exit P&L
(−$10,539 H1, −$10,841 H2), average loss (−$253, −$213), cost drag ($66.1, $66.3 per trade),
entry spread (6.0%, 6.5% of mid debit), center distance (1.579 σ in both), calls share (59%,
60%), and direction accuracy (54%, 59%). The difference is settlement:
15 settled trades netting +$27,570 in H1 against 8 netting +$4,234 in H2. Wins over $1,000:
11 versus 3; average win $2,651 versus $760. The market-implied payout proxy (mid debit ÷
width) was 0.091 and 0.089. Realized settlement value ÷ width was 0.160 in H1 and 0.059 in
H2, so H1 flies paid 1.76× their price and H2 flies paid 0.66×.

The H1–H2 expectancy difference of $394 per trade has a one-sided permutation p = 0.007.
A 63-trade resample from the full-sample trade distribution nets −$6,607 or worse 3.2% of the
time. This is larger than ordinary lottery variance but is not yet a structural break.

Across all 130 sessions with a 10:00 straddle, measured after 10:00 in chain-implied σ units:

| | H1 | H2 |
|---|---:|---:|
| Mean entry VIX | 19.9 | 16.5 |
| RMS realized move ÷ implied | 1.02 | 0.92 |
| Mean \|move\| | 0.84 σ | 0.74 σ |
| Sessions with \|move\| > 1 σ | 38.5% | 23.1% |
| Rest of day follows the gap | 53.8% | 61.5% |
| corr(gap sign, move after 10:00) | 0.11 | 0.25 |
| Close lands 0.9–2.3 σ in the gap direction | 23.1% (15/65) | 12.3% (8/65) |
| Long ATM straddle held to close, mean points | +1.55 | −2.79 |

The strategy is a directional bet on tail realized volatility. It pays when the close lands
about 1–2.3 σ in the gap direction, which needs realized movement at or above what the
chain prices. H2's direction signal was better, but the moves were smaller than implied, so
fewer closes reached the tent and those that did landed near the wings. H1 was the half in
which realized movement slightly exceeded implied (a long straddle made money). Index
options usually carry a positive variance premium, so the H1 conditions may be the favorable
exception rather than the norm. The landing-rate difference alone is not significant
(Fisher p = 0.167); the P&L gap also reflects winners landing near the wings.

No pre-entry predictor was found. Squared daily realized/implied moves have lag-one
autocorrelation −0.002. Trailing 5-, 10- and 20-session realized/implied and trailing
landing rates had Spearman correlations with next-trade stressed P&L of −0.07 to −0.17
(no p below 0.08). Their H1 and H2 signs disagreed or were negative, and tercile P&L was
non-monotonic. A "trade only after high realized vol" filter is not supported.

Implication for the open cohort: its outcome depends mainly on whether realized 0-DTE
movement after 10:00 matches or exceeds the chain's price during the cohort window. H2's
regime produced a stressed loss of $105 per trade. The registered endpoint's 20-settlement
minimum is the right guard: fewer settlements are the failure mode. Nothing here changes
the cohort's rules.

Artifacts and reproduction: `docs/research/spx-idea-sweep-2026-09-25/` (harness, registry,
result JSON, and the export commands; data is re-exported, not committed). The analysis ran
with the project's locked `.venv`, and `uv run ruff check .` passes.

## 2026-09-25 — direction-rule tests, live/backtest selection parity, and gap-input fix (development data only)

Everything here was chosen after seeing the data. It is exploratory, not a registered test,
and nothing in it touches the open cohort `spx-prospective-2026-09-22`.

### Setup and accounting

Runs use `src/butterfly_guy/scripts/run_backtest_db.py` single-config mode with the live SPX
config (VIX-bucket widths, VIX anchor, 07:00–07:45 PT window, peak-value trailer), over
2026-03-13 → 2026-09-25 (all sessions with a recorded chain; 123–124 trades per run). P&L is
the script's default per-contract figure: entry at mark plus the configured paper
commission, no slippage. It is **not** the stressed-marketable accounting used in the idea
sweep above, and is more optimistic than it.

Two options were added:

- `--direction-ma N` (commit `deb32dd`): CALL if entry-time spot ≥ the N-day SMA of prior
  daily closes, else PUT; sessions without N prior closes are skipped.
- Official gap inputs (commit `67ba7ce`, see below).

SPX `daily_bars` starts 2026-03-02, too short for MA100–MA200. Earlier closes came from FRED
series `SP500`, injected by a scratch wrapper that replaces `get_recent_closes` (no DB
writes). FRED matched `daily_bars` on all 144 overlapping sessions and the Schwab gateway's
`/v1/history` daily bars on all 250 of its sessions (2025-09-26 → 2026-09-24) to the cent.
The gateway rejects `days_back` above 250, so May–Sept 2025 closes rest on FRED alone.

### Moving-average direction versus the gap rule

The MA rules do not read the open or prior close, so the gap-input fix does not change them.
The gap-rule row was rebuilt with official inputs by taking each session's call or put trade
from the runs above; a full rerun to confirm it was in progress when this was written.

| Rule | Trades | Total | Avg | Win% | Max DD | Calls/Puts | Side ≠ gap rule | Before 06-15 | From 06-15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Gap rule, snapshot inputs (old) | 123 | +18,459 | +150 | 20% | −3,739 | 73/50 | 5 | +19,100 | −641 |
| Gap rule, official inputs | 123 | +22,720 | +185 | 20% | −3,911 | 72/51 | — | +21,393 | +1,327 |
| MA20 | 124 | +14,266 | +115 | 19% | −7,817 | 81/43 | 51 | +20,150 | −5,883 |
| MA50 | 123 | +16,117 | +131 | 20% | −7,669 | 98/25 | 48 | +23,786 | −7,669 |
| MA100 | 123 | +14,574 | +118 | 20% | −6,933 | 107/16 | 53 | +21,507 | −6,933 |
| MA150 | 123 | +16,853 | +137 | 21% | −6,933 | 109/14 | 51 | +23,786 | −6,933 |
| MA200 | 123 | +15,279 | +124 | 20% | −6,933 | 111/12 | 49 | +22,212 | −6,933 |

Every MA rule trails the gap rule and roughly doubles its drawdown. Longer MAs are close to
"always CALL" in this sample. The MA rules led before mid-June and gave it back afterwards.
Each run's top three winners supply about $10.6–11.2k, so differences among MA lengths are
noise.

### Call-only entry filters

On any session the rule chooses CALL, the entry logic picks the same call fly regardless of
which rule chose it (verified: no conflicts across the six runs). So call-only filters were
evaluated on one pool of call trades: the six runs plus eight single-session `--direction
CALL` runs for sessions no run had traded as calls. All conditions use only information
available at entry. Gap here uses the old snapshot inputs, except the last row.

| Buy a call fly only if… | Trades | Total | Avg | Win% | Max DD | Without top 3 | Before 06-15 | From 06-15 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| every session | 123 | +16,129 | +131 | 20% | −6,933 | +6,203 | +23,062 | −6,933 |
| gap up | 73 | +15,824 | +217 | 26% | −3,170 | +5,898 | +18,994 | −3,170 |
| gap up ≥ 0.25% | 46 | +14,648 | +318 | 30% | −1,378 | +4,722 | +15,739 | −1,091 |
| up since open at entry | 73 | +15,689 | +215 | 25% | −3,705 | +6,419 | +19,393 | −3,705 |
| gap up & up since open | 40 | +12,299 | +307 | 30% | −1,447 | +3,028 | +13,433 | −1,134 |
| VIX below prior close | 62 | +17,358 | +280 | 24% | −4,521 | +7,433 | +21,879 | −4,521 |
| up since open & VIX below prior close | 39 | +15,588 | +400 | 28% | −2,848 | +6,318 | +18,436 | −2,848 |
| above MA20 & gap up | 50 | +12,683 | +254 | 28% | −1,971 | +3,929 | +14,114 | −1,431 |
| above MA50 & gap up | 61 | +14,047 | +230 | 26% | −2,935 | +4,665 | +16,981 | −2,935 |
| prior day down | 60 | +9,698 | +162 | 18% | −5,276 | −227 | +14,973 | −5,276 |
| above MA50 & 5-day return < 0 | 34 | +4,190 | +123 | 21% | −2,975 | −4,295 | +7,128 | −2,938 |
| VIX ≥ 17 | 69 | +18,790 | +272 | 25% | −2,666 | +8,864 | +21,455 | −2,666 |
| VIX ≥ 17 & gap up | 40 | +18,294 | +457 | 35% | −1,223 | +8,369 | +19,518 | −1,223 |
| VIX < 17 | 54 | −2,661 | −49 | 15% | −4,358 | −6,288 | +1,607 | −4,268 |
| VIX ≥ 17 & gap up (official gap inputs) | 40 | +20,368 | +509 | 35% | −1,361 | +10,443 | +21,729 | −1,361 |

Eighteen conditions on about 25 winning trades: the best row is expected to be flattering.
Two consistent observations: low-VIX calls lose in total (agreeing with H-LV1 above), and
dip-buying conditions are the weakest. Every condition is negative from mid-June. The
official-input improvement of VIX ≥ 17 & gap up (+$2,074) is almost entirely one session
(2026-04-09, +$2,211) that the fix reclassified as a gap up.

Applied to actual live paper fills (`butterfly_trades`, SPX, closed; `pnl` × 100), the
filter's sessions made more than all sessions overall but less since mid-June:

| Live paper | Trades | Total | Avg | Win% | Max DD | Without top 3 | From 06-15 |
|---|---:|---:|---:|---:|---:|---:|---:|
| all trades | 118 | +1,625 | +14 | 19% | −4,504 | −5,138 | +17 |
| VIX ≥ 17 & gap-up sessions only | 37 | +2,539 | +69 | 24% | −2,440 | −3,093 | −1,442 |

This is a variant of H-LV1 on the same development data. It is not validated and must not be
applied to the open cohort.

### Why the backtest and live paper disagree

On the 116 shared sessions the backtest's gap rule made +$16,897 and live paper +$2,013.
Causes, largest dollar effect first:

1. **Config drift before June.** The backtest applies today's config to every session. Live
   traded fixed 10/20/30-point wings until VIX buckets arrived (`5ae1190`, 2026-04-28), the
   buckets changed on 2026-05-14 (`ad0be47`), and live and backtest selection were unified on
   2026-05-29/30 (`a71a2cd`, `e47bf0a`). Before that, live centers could sit outside the
   current ±15-point tolerance (2026-05-15: 30 points from today's target). The backtest's
   large March–May winners were wide flies live never held. From 06-15 the two agree in
   total: live +$17, backtest −$539 over 67 sessions.
2. **Knife-edge width choice.** Width is the one whose reward/risk is closest to 10. On 51
   live sessions with at least two widths, a mark change on the winning fly under $0.05
   would flip the choice 41% of the time, and under $0.10 69% of the time. Live's own
   `entry_selection_parity` events show a median per-fly mark difference between the live
   chain and the DB snapshot of $0.09 when the snapshot is under 10 s old and $0.13 at 30–60
   s. Width matched on 39/63 events. Replaying at the live entry time, direction and VIX
   (`--selection-parity-report`) reproduced live's fly on only 16 of 61 sessions, about
   25–35% per month even after unification. When the same fly was chosen, P&L agreed
   closely (since 2026-05-15: live −$2,828 vs backtest −$2,530 over 35 sessions).
3. **Different candidate sets.** The same price noise moves flies across the
   reward/risk, cost-cap and center-tolerance cutoffs, so the two sides sometimes see
   different widths (2026-07-08: live one width, DB three).
4. **Direction inputs (fixed).** The backtest compared the first chain snapshot's spot after
   09:30 with the last spot tick before 16:00. Live compares Schwab's 09:30 candle open with
   the `daily_bars` close. The snapshot open differed by up to about $5 and the tick close by
   about $2. That flipped direction on 4 of 83 live sessions since 2026-05-15. `daily_bars.open`
   equals the gateway's 09:30 candle open to the cent on every session checked
   (2026-09-21 → 09-24). Commit `67ba7ce` reads both inputs from `daily_bars`, with the old
   values as fallback. After it, the backtest's direction matched live on all 73 sessions
   since 2026-05-30, and 2026-06-22 reproduces live's exact fly (live +$2,258, backtest
   +$2,010).

Implication: apart from item 4, neither side is wrong. The selector chooses among two or
three near-equivalent flies by noise, so a single backtest run samples one realization of
each session. Rule comparisons that differ by a few thousand dollars on about 120 trades,
including the MA and filter results above, are within that noise. A robustness check that
scores every near-tied fly per session, or a less brittle width rule, would be needed before
any selection change is judged.

### Reproduction

```bash
# MA runs (MA100+ need the FRED-close wrapper described above for pre-March history)
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2026-03-13 2026-09-25 --asset SPX --direction-ma 50
# gap-rule baseline and call-only gap-up pool
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2026-03-13 2026-09-25 --asset SPX
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2026-03-13 2026-09-25 --asset SPX --direction CALL --gap-filter 0.0
# selection parity
uv run python src/butterfly_guy/scripts/report_selection_parity.py 2026-05-15 2026-09-25 --asset SPX
uv run python src/butterfly_guy/scripts/run_backtest_db.py 2026-05-15 2026-09-25 --asset SPX --selection-parity-report
```

Filter evaluation and the live comparison were scratch scripts over these runs' per-session
output; they were not committed.
