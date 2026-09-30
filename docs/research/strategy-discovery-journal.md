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

### Robustness to fly choice (near-tied flies)

Because the selector's width and center choice turns on a few cents of mark, each rule was
rescored on every fly the selector could plausibly have chosen, not just the one it did.

Method: for each of 124 sessions and both directions, the entry bar was found exactly as
`run_backtest_db.py` finds it. Every candidate the selector considers was rebuilt: all widths
in the VIX bucket, centers within ±15 of each width's VIX target, and the `rr_max` filter.
Each candidate that a combined mark shift of at most $0.25 could promote over the winner was
simulated with the backtest's own `simulate_day_from_entry`. The shift is the
reward/risk-distance gap divided by both flies' reward/risk sensitivity to cost (width ÷
cost²). This averaged 2.1 flies per session-direction within $0.10 and 2.5 within $0.25.
Rules use the official gap inputs. The MA side is decided from spot at the entry bar.
Accounting is the same as above.

For each rule:

- **Tie-set avg:** each session's P&L is the mean over its tied flies.
- **Random draws:** 5,000 draws pick one tied fly per session uniformly. The same draw is
  used for a given session and direction in every rule, so comparisons are paired.
- **Beats gap rule:** the share of draws in which the rule's total exceeds the gap rule's.

Tie set = flies within **$0.10** of winning (about the measured live-vs-DB mark gap):

| Rule | Trades | Selected fly | Tie-set avg | Draw median | Draw 5%–95% | Tie-set avg from 06-15 | Beats gap rule |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gap rule (official inputs) | 123 | +22,720 | +22,846 | +22,787 | +20,766 to +25,093 | +1,174 | — |
| MA20 | 124 | +14,266 | +15,085 | +15,073 | +12,300 to +17,889 | −4,954 | 0% |
| MA50 | 123 | +16,354 | +16,173 | +16,174 | +14,495 to +18,005 | −6,864 | 0% |
| MA100 | 123 | +14,574 | +14,554 | +14,543 | +12,875 to +16,372 | −6,320 | 0% |
| MA150 | 123 | +16,853 | +16,717 | +16,708 | +15,025 to +18,547 | −6,320 | 0% |
| MA200 | 123 | +15,279 | +15,738 | +15,730 | +14,326 to +17,155 | −6,320 | 0% |
| Call only: VIX ≥ 17 & gap up | 39 | +20,499 | +20,135 | +20,136 | +19,562 to +20,699 | −1,346 | 1% |

Tie set = flies within **$0.25** of winning:

| Rule | Trades | Selected fly | Tie-set avg | Draw median | Draw 5%–95% | Tie-set avg from 06-15 | Beats gap rule |
|---|---:|---:|---:|---:|---:|---:|---:|
| Gap rule (official inputs) | 123 | +22,720 | +23,901 | +23,810 | +20,948 to +27,133 | +2,092 | — |
| MA20 | 124 | +14,266 | +16,974 | +16,995 | +13,243 to +20,875 | −4,061 | 0% |
| MA50 | 123 | +16,354 | +17,610 | +17,651 | +14,767 to +20,575 | −6,417 | 0% |
| MA100 | 123 | +14,574 | +16,044 | +16,079 | +13,196 to +19,057 | −5,842 | 0% |
| MA150 | 123 | +16,853 | +18,185 | +18,221 | +15,316 to +21,161 | −5,842 | 0% |
| MA200 | 123 | +15,279 | +17,265 | +17,270 | +14,499 to +19,998 | −5,842 | 0% |
| Call only: VIX ≥ 17 & gap up | 39 | +20,499 | +20,219 | +20,219 | +19,619 to +20,804 | −1,320 | 1% |

The selected-fly column reproduces the earlier runs except MA50 (+$16,354 vs +$16,117) and
the call filter (39 trades, +$20,499, vs 40 and +$20,368). Both come from one or two sessions
where the side or VIX was decided on a slightly different bar.

Findings:

- **Correction to the paragraph above.** Fly-choice noise moves a rule's total by about
  ±$2–3k (5–95%). That is smaller than the $6–8k by which every MA rule trails the gap rule.
  No MA rule beat the gap rule in any of 5,000 paired draws at either threshold, so the MA
  result is robust to fly choice. It is not robust to anything else: this measures only
  which near-tied fly was picked, not which sessions happened to occur.
- The gap rule's total rises slightly when tied flies are averaged in (+$126 at $0.10, +$1,181
  at $0.25). The selector's specific pick is not an edge.
- The call-only VIX ≥ 17 & gap-up filter barely moves (5–95% range about $1.1k wide). It
  still loses from mid-June in every tie definition, and it beats the gap rule's total in
  about 1% of draws with a third of the trades. Its standing is unchanged: a post-hoc variant
  of H-LV1, not validated.
- What this does not address: session sampling (a day-block bootstrap would), the selection
  of 18 filters and five MA lengths after seeing the data, flies that noise would push across
  the cost-cap or `rr_min` cutoffs (excluded, so tie sets are slightly too small), and
  stressed execution costs.

The harness (`robust.py`, one worker per four-week block) and scorer (`rb_eval.py`) were
scratch scripts built on `run_backtest_db.py`'s public functions; they were not committed.

## 2026-09-27 — unified research core, cohort runner move, and stage-2 research tooling (development data only)

This entry records infrastructure and reproductions. It does not change the frozen
strategy or the open cohort `spx-prospective-2026-09-22`, and nothing in it is evidence
about either. Everything below runs on development data the strategy was built on, except
the three-session cohort shadow, which is exploratory. Work is on branch
`research/unified-core`. Design and commands are in `docs/research/research-core.md`;
the motivation is in `docs/reviews/2026-09-27-research-pipeline-review.md`.

### Research core and data

`src/butterfly_guy/research/` replaces the idea sweep's standalone numpy harness as the
simulator for rule research. It uses the live selector and profit-policy functions,
2026-09-21 accounting, paired day-block bootstrap scoring, tie-set robustness by default,
and a hash-chained variant registry. `run_backtest_db.py` and `SimulationEngine` stay the
live-parity reference and are unchanged.

The data is a read-only, per-day-bounded export from the Helios database into a Parquet
cache outside Git:

- 133 sessions, 2026-03-13 → 2026-09-25;
- dataset hash `dd38a5ecb2cfb08df6e057167c9da06041569da20aab9c30d3bf333e348bc523`;
- every file hash-checked on read.

A settlement refresh on 2026-09-27 (`export --bars-only`) found 2026-09-25's official
close still absent from `daily_bars`. The manifest's new export history lists it as
pending, and the hash is unchanged.

### Parity

- **Frozen replay.** E0 under the `frozen_20260921` profile reproduces
  `run_backtest_db.py` at `b83c2a18` (the 2026-09-21 executable result) trade by trade:
  118 trades, midpoint $17,691.60, marketable $14,170.60, stressed $9,890.60, with half a
  cent per trade as the only tolerance.
- **Idea sweep.** Under the `sweep_20260925` profile, all 26 idea-sweep variants
  reproduce their published rows to the dime. That includes the 16 ported in this stage:
  C1/C2, D3, D4, T1–T6, K1, G1/G2 and R2–R4. There are three documented float32/float64
  ties:
  - D2, and D3's put leg, on 2026-07-09: a drawdown of exactly 60%, +$25 stressed.
  - G2 on 2026-09-23: a call and a put fly with identical stressed debit and payoff;
    stressed is unchanged, midpoint differs by $15.
- **Sweep inputs.** The published figures were confirmed against the original
  2026-09-25 export as well as the new cache.

**Correction: the parity residual was not the decision clock.** The 2026-09-25 entry
attributed the harness's residual to its decision clock. That residual was −$57 midpoint
and −$60 stressed ($17,634.60 / $9,830.60 against $17,691.60 / $9,890.60). Switching the
sweep profile's settings one at a time toward the frozen profile shows the clock was not
the cause:

- Exact timestamps instead of whole-second rounding move it to $17,603.60 / $9,805.60.
- Adding all strikes, the full-day bar clock and the first-bar open changes nothing.
- The frozen replay's prior close closes the rest: the last SPX tick at or before 16:00,
  instead of `daily_bars`. It flips gap direction on a few sessions.

So the residual came from the prior-close source, partly offset by the whole-second
rounding. The `live` profile (official `daily_bars` open and prior close, commit
`67ba7ce`) reproduces the 2026-09-25 official-input gap rule: 123 trades, +$22,720
midpoint.

### Variant registry

`reports/research/registry/spx_0dte.jsonl` was seeded with the 49 variant definitions
tried on this data before it existed, 28 of them post hoc:

- the 26 idea-sweep variants;
- the five MA direction rules;
- the 18 call-only entry filters from the 2026-09-25 entry. Four of these are placeholders:
  that entry says eighteen but lists fourteen.

The 16 variants ported in this stage are linked to their word-only backfill records by
`port` events. They inherit those records' stages (C1–G2 pre, R2–R4 post) and are not
counted twice.

Fitted rules record their fit window and fitted value in their definition:

- K1: 0.0504 over 59 H1 E0 entries;
- R2: 2.2275.

Both are fitted on H1 (2026-03-13 → 2026-06-18) and applied to every session, as
published, so H1 is in-sample for them. Only their H2 figures are out of sample:

- K1 H2: −$3,914, +$2,693 against E0;
- R2 H2: −$5,598, +$1,009 against E0.

The EV learners (G1/G2, R3/R4) are handed only sessions before the one they decide, and
a session's own settlement is observed only after every variant has decided it.

### Exit-latency stress

Every run now also prices intraday exits one decision-clock snapshot after the trigger,
still rolling forward past unusable markets and falling back to settlement. This is the
"delayed" model.

**Calibration.** It was made read-only from 67 recorded paper intraday exits
(`monitoring_leg_quotes` and `butterfly_trades`).

- Trigger-to-fill latency: median 0.9 s, p90 67.5 s.
- Measured in collector snapshots (about 62 s apart), fills landed before the next
  snapshot 49 times, one snapshot later 14 times and later still 4 times.
- p90 is one snapshot, so the fixed one-snapshot stress is the calibrated one.
- Paper exits fill on a simulated ladder, so live broker latency can only be longer.

**Effect on the frozen 118-trade sample.** Stressed $9,890.60 becomes $9,408.20 delayed
(−$482.40). Of the 96 intraday exits, 40 were worse, 40 better and 16 unchanged, averaging
−$5.03. The idea-sweep E0 moves from $10,424 to $9,947. The exit delay is a small cost
next to the $2–3k fly-choice noise and the settlement dependence already documented.

### Cohort shadow (exploratory, three sessions)

`shadow` reads the cohort ledger only with `git show` from
`origin/cohort/spx-prospective-2026-09-22` (`70ccb8e`) and verifies every record hash.
It scores variants paired against E0 on the cohort's recorded sessions, 2026-09-22 →
2026-09-24.

E0 reproduced all three cohort trades exactly: fly, entry time, exit reason and P&L in
all three models, stressed +$669.

| Session | E0 | H-LV1 (`HLV1`) | R1 |
|---|---:|---:|---:|
| 2026-09-22 | −$225 | $0 (low-VIX call skipped) | $0 |
| 2026-09-23 | +$1,164 | +$1,164 | $0 |
| 2026-09-24 | −$270 | −$270 | $0 |
| Total | +$669 | +$894 | $0 |

R1 skipped all three sessions (entry VIX below 17). Three sessions carry no information
about either rule. This is recorded only to establish the shadow pipeline. It must not
influence the cohort, whose rules stay frozen, and H-LV1 remains a hypothesis for a
separate test.

### Cohort runner move (2026-09-27) and a labeling note

The cohort's daily update had stopped on 2026-09-25: research commits to
`run_backtest_db.py` and to shared modules drifted its frozen source hashes. Since
2026-09-27 the update runs from a dedicated worktree,
`/mnt/Repos/Trading/Butterflyguy-cohort`, pinned at the frozen commit `6ffbfe7`. The
ledger is committed to branch `cohort/spx-prospective-2026-09-22` instead of `main`.
Research work no longer interrupts it.

Commit `f933117` on that branch is labeled as a systemd README note. It also contains
the 2026-09-24 session record (`daily_runs.jsonl` and `trades.jsonl`, trade
`b87c47309d12f05c`), which `git commit -a` swept in from a manual `update` run. The
record is genuine and verifies. Only the commit message is incomplete, and the branch
had already been pushed, so the history was left as is.

`main` still carries the old updater and a ledger ending 2026-09-24 until the cohort
branch is merged.

## 2026-09-28 — stage 3: event calendar, term-structure features, descriptive diagnostics, vendor readiness (development data only)

This entry records inputs and descriptive breakdowns. It evaluates no rule, registers
nothing, and does not touch the frozen strategy or the open cohort
`spx-prospective-2026-09-22`. Work is on branch `research/unified-core`; details and
commands are in `docs/research/research-core.md`.

### Housekeeping

- **Settlement refresh.** `export --bars-only` on 2026-09-27 found no change: Helios
  `daily_bars` still ends at 2026-09-24, so 2026-09-25's official close is still pending.
  The dataset hash stays `dd38a5ec…`. With nothing landed, parity and the sweep-port
  tests had nothing new to check; both pass in the full suite.
- **Cohort.** The ledger (`70ccb8e`, read with `git show`) still holds 2026-09-22 →
  09-24, so the E0/HLV1/R1 shadow was not re-run. The next cohort update is Monday
  2026-09-28 18:30 PT.

### Feature sources and coverage

- **Event calendar** (`market_events_v1.csv`, 313 rows, sha256 `3185297d…`, committed).
  - Coverage: FOMC statement days, CPI/NFP/PCE releases, monthly OPEX, quarter-ends and
    early closes, 2022 → 2026.
  - Each row carries its source and the date its schedule was public: prior-release
    notices, Fed schedule press releases, dated lapse notices, or the earliest archive
    capture, which is an upper bound.
  - An event is a feature only if it was published before the session and not withdrawn
    before it. Unscheduled events (the 2025-08-22 FOMC notation vote) are never
    features.
- **Volatility term structure.**
  - *Helios DB:* has none of it.
  - *Schwab gateway:* one-minute `$VIX`, `$VIX9D` and `$VIX3M` bars for only about the
    last 30 sessions, and nothing for `$VIX1D`. This probe was a read-only run inside the
    SPX app container, which uses the container's own key.
  - *Cboe public daily files:* cover everything (VIX1D from 2022-05-13).
  - *Added to `spx_0dte`* as separately hashed aux files (`aux_hash` `b6175510…`), with
    `dataset_hash` unchanged: Cboe daily for all four indices (prior-session closes for
    all 133 sessions) and gateway intraday for the last 30.
  - *Leakage rules:* features use prior-session closes only, anchored on the previous
    SPX session (Cboe prints VIX on some exchange holidays). Intraday values count only
    from bars complete at or before the decision.
- **Overnight ES (audit only).** Not in the DB. The gateway has 04:00–16:59 ET `/ES`
  minutes for about 25 sessions and no overnight Globex session. No licensed free source
  exists. Nothing was ingested.

### Descriptive E0 breakdowns (not evidence)

Run `90673e0c138b`, `sweep_20260925`, 2026-03-13 → 2026-09-24. It reproduces the
published E0 totals: 122 trades, stressed $10,424, H1 $17,031 / H2 −$6,607.

- **Sessions with no scheduled event:** 101 sessions, +$10,094 ($100 per session).
- **Sessions with any event:** 31 sessions, +$330 ($11 per session).
  - Losing event cells: FOMC −$961 (5 sessions), CPI −$1,594 (6), NFP −$976 (4) and
    OPEX −$1,549 (7). OPEX sessions had the smallest move after 10:00 (RMS 0.57σ against
    0.98σ overall).
  - PCE was +$2,472 (7 sessions) and quarter-end +$2,937 (2).
- **Term structure.**
  - Prior VIX1D/VIX terciles: low +$6,838, mid +$6,948, high −$3,361 (44 sessions each;
    the high tercile is −$4,303 in H2).
  - Prior VIX9D/VIX: low −$1,940, mid +$8,919, high +$3,446, which is not monotone.
  - Seven backwardation sessions (VIX/VIX3M ≥ 1), all in H1: +$1,856.
- **The delayed-exit model** moves no cell by more than $612 (the 125-session contango
  cell); the whole sample moves by $477.

These are cells of 2–44 sessions on the data the strategy was built on. One cash
settlement decides any event cell's sign, and the terciles are confounded with H1/H2 and
the VIX level. No rule is evaluated or implied. A feature rule must be registered before
it is tested; see the next section.

### Pre-registration draft (not registered)

`docs/research/next-sweep-preregistration-draft.md` drafts the next sweep on vendor
history. It is **not registered** and awaits the owner's decision.

- **Split:** development 2022-01-03 → 2024-06-28, holdout 2024-07-01 → 2026-03-12. The
  holdout is fixed before any vendor data is seen.
- **Hypotheses:** H-LV1, the σ-normalised selector H-SN1, the 08:30-release skip H-EV1,
  and the rich one-day-implied skip H-TS1.
- **Gate:** stressed P&L per session, paired against E0, with a 10-session block
  bootstrap and Bonferroni over k at family α 0.10, plus both halves, top-3-removed and
  delayed-model gates.

It was drafted before the diagnostics above were run and has not been changed since.

### Vendor readiness

`docs/research/history-vendor-readiness.md` compares ThetaData, Databento OPRA and Cboe
DataShop, specifies a `HistorySource` adapter onto the research Parquet schema, and sets
a validation plan with pass criteria fixed in advance.

- **No vendor is complete on its own.** Databento and DataShop lack the SPX index level
  (DataShop only with a Cboe index-feed licence) and intraday VIX, which the selector
  needs.
- **Mark.** In our Helios data, `mark` is exactly the bid/ask midpoint.
- **Nothing was bought or signed up for.**

## 2026-09-28 — stage 4: housekeeping, provider-independent vendor tooling, hypothesis rules (no vendor data)

This entry evaluates no rule and registers nothing. It does not touch the frozen strategy
or the open cohort `spx-prospective-2026-09-22`. Work is on branch `research/unified-core`
(stage 3 committed as `5038e0d` first). Details and commands are in
`docs/research/research-core.md`.

**No data provider was chosen.** The owner decided not to buy vendor history for now. So
this stage built everything that does not depend on a provider and marked the rest
"Data provider not chosen". There is no vendor dataset, no fidelity validation result, no
development-period coverage and no in-sample E0 on vendor data. Nothing was downloaded
from any vendor and no account was created.

> **[Correction, 2026-09-28, added before the stage-4 commit]** The paragraph above
> misstates the owner's decision. Nothing has been bought, but the owner did not decide
> against vendor history: they will likely buy ThetaData, from 2022 forward. Until the
> subscription is active, every vendor path stays stubbed and `history.SOURCES` stays
> empty. The rest of this entry stands as written.

### Housekeeping

- **Settlement.** `export --bars-only` found that 2026-09-25's official close had landed:
  SPX 7743.41 (equal to Cboe's published close) and `$VIX` 14.87.
  - Only `daily_bars.parquet` changed (292 → 294 rows).
  - Dataset hash `dd38a5ec…` → `b76dc6c9e1c77a4ca15aa2aa4be73bcc86e3c6e5e5314e634d9dacf839ae0f45`.
  - `parity` and the sweep-port tests pass unchanged. They end at 2026-09-18 and
    2026-09-24, so the new close does not enter them.
- **Cohort.** The ledger (local and remote `70ccb8e`, read-only) still holds 2026-09-22 →
  09-24, so the shadow was not re-run.
- **Aux inputs.** No change; `aux_hash` is still `b6175510…`.
  - The Cboe daily refresh revised nothing.
  - The re-run gateway dump is byte-identical to stage 3's (`699420d1…`).
  - The intraday ingest replaces the file rather than merging it. Once the gateway's
    retention passes 2026-08-12, a same-range dump would drop older bars, so merge before
    ingesting any later dump.

### Built (provider-independent, tested on synthetic data)

- **Vendor adapter framework** (`history.py`):
  - the `HistorySource` interface and every mapping rule of the readiness spec;
  - a `vendor_1m` profile (09:31 → 16:00 ET, 13:00 on early closes);
  - a request log in the manifest for every pull;
  - a cost stop for usage-billed vendors;
  - a per-session coverage report.

  `SOURCES` is empty, and `export-history` stops with "Data provider not chosen".
- **Sealed holdout** (`holdout.py`). Any request, cost preview, write or session load
  touching 2024-07-01 → 2026-03-12 raises. The only way in is a registry-verified unseal:
  a clean-tree `register` record made on development-only data.
- **Fidelity validation harness** (`validate.py`). It implements steps 1–4 with the
  readiness doc's criteria copied verbatim, and fixes the details the plan left open (see
  research-core).
  - Self-check with the Helios export on both sides (133 sessions): steps 1, 2 and 4 pass
    trivially, in 38 s.
  - Eight sessions lack a 10:00 ATM straddle, so step 1's region excludes them.

### Validation results (readiness doc steps 1–4)

| Step | Criterion | Result |
|---|---|---|
| 1 Quote level | ≥ 95% of pairs within $0.05 in the 1.0–2.5σ OTM region; best offset within 1 min | not run: no vendor data |
| 2 Replay on the Helios clock | same fly ≥ 90%; stressed within max(±5%, ±$750); every disagreement explained | not run: no vendor data |
| 3 Replay on the vendor clock | stressed total inside the Helios $0.10 tie-set draw band | not run: no vendor data |
| 4 Spot and settlement | official closes identical to `daily_bars` and Cboe | not run: no vendor data |

### Development coverage and in-sample E0

None. No development-period data exists. For comparison later, the Helios export's own
coverage is:
- a median of 154 strikes and 375 timestamps per session;
- median missing and crossed rates of 0 within ±200 of spot;
- official bars on all 133 sessions;
- VIX at 10:00 on 126 sessions.

### Hypothesis rules (implemented, not registered)

`HSN1` (`4589760a…`), `HEV1` (`9180c56d…`) and `HTS1` (`2ec8c008…`) are new catalog
entries. HLV1 is unchanged (`6ed12752…`).

> **[Correction, 2026-09-28 (stage 6)]** HTS1's definition hash is `fab8bf3e…`, not
> `2ec8c008…`. The committed code at `82aed43` already gave `fab8bf3e…`; the value above was
> never the hash of committed code. The other three are right.
- They were unit-tested on synthetic data only, and were not run on any real data.
- Their implementation choices for details the draft leaves open are listed in
  research-core for the owner to review before registering.
- `register` records now store `git_sha`, `git_dirty` and the dataset hash, which the
  unseal requires.

### What this means for the evidence plan

Without vendor history, the pre-registered sweep cannot run as drafted. The draft's split
and gate assume the 2022–2026 vendor sessions. The alternatives discussed with the owner
on 2026-09-28 were:
- **Record going forward.** Register hypotheses now and let the Helios recorder
  accumulate an unseen holdout. The power analysis's ~400 trades would take about 1.7
  years.
- **A free mechanism check.** Test whether realised SPX moves undershoot VIX1D on
  H-TS1's and H-EV1's sessions, using Cboe's public daily data on the development window
  only.
- **A one-month vendor subscription**, later, if either of those justifies it.

None of these was started.

## 2026-09-28 — stage 5: corrected data decision, housekeeping, ThetaData readiness (stubbed), H-TS1 mechanism check (development window, descriptive)

This entry evaluates no rule, registers nothing, and does not touch the frozen strategy or
the open cohort `spx-prospective-2026-09-22`. Work is on branch `research/unified-core`;
stage 4 was committed first as `82aed43`. Details and commands are in
`docs/research/research-core.md`.

### Data decision (corrected)

Stage 4's docs said the owner had decided not to buy vendor history. That was wrong.
**Nothing has been bought, and the owner will likely buy ThetaData, from 2022 forward.**
The stage-4 entry above carries a marked correction note, and `research-core.md` and the
draft's marked fact update were corrected before the stage-4 commit. Until the subscription
is active, every vendor path stays stubbed and `history.SOURCES` stays empty.

### Housekeeping

- **Settlement.** `export --bars-only` found nothing new; the dataset hash stays
  `b76dc6c9…`.
- **Cohort.** The ledger (local and remote `70ccb8e`, read-only) still holds 2026-09-22 →
  09-24, so the E0/HLV1/R1 shadow was not re-run.
- **Intraday ingest now merges.** `ingest_intraday` used to replace the file with the
  dump's rows, so a dump taken after the gateway's ~30-session retention rolled would have
  deleted older bars. It now keeps existing bars, adds new ones, records revised bars (old
  and new OHLC) in the history entry, raises on a `bar_seconds` clash, and refuses any write
  that would remove a row. Every dump is listed in the file's source. Tests cover kept,
  added, revised, never-removed and an idempotent re-ingest.
- **Gateway re-dump**, run as in stage 3 over 2026-08-03 → 2026-09-28 (sha256 `ccf781f6…`,
  no errors).
  - Retention still starts at 2026-08-12.
  - `$VIX1D` returned minute bars for the first time, for 2026-09-28 only.
  - The merge added 1,556 bars (2026-09-28, four indices), removed, revised and kept-only 0.
  - **`aux_hash` `b6175510…` → `cb12502b721efeda92f06f55f35273e26b101ecaa3a847e7339a628445144967`.**
    `dataset_hash` is unchanged, and no feature on the 133 exported sessions changed.

### ThetaData readiness (stubbed, nothing bought, nothing downloaded)

Public pages only, read 2026-09-28: no account, no sign-up, no terminal install. Sources are
listed in `history-vendor-readiness.md` (new section "ThetaData: public-docs findings and
purchase checklist").

- **Plans and prices.** Options Value $40, Standard $80, Pro $160; Indices Value $30,
  Standard $50, Pro $100 (per month).
  ([pricing](https://www.thetadata.net/pricing)).
- **History depth: the pricing page and the docs disagree.**
  - Options Value: "4 years" on the pricing page, 1-minute from 2020-01-01 in the
    [subscriptions doc](https://thetadata.net/docs/Articles/Getting-Started/Subscriptions.html).
  - Indices Standard: "3 years" against 2022-01-01.
  - Options Standard (2016 / 8 years) and Indices Pro (2017 / 7 years) reach 2022-01-03 under
    either reading, so the safe combination is $180/month, or $130/month if ThetaData
    confirms Indices Standard reaches 2022. The readiness doc's "Standard, since Value
    reaches only about 2022-09" holds under the pricing page's reading only.
- **Indices tier.** Intraday SPX and VIX, and an index EOD report (open, high, low, close)
  that ThetaData generates at 17:15 ET
  ([index EOD](https://thetadata.net/docs/operations/index_history_eod.html)). Whether its
  open and close equal the official values is to confirm at purchase.
- **Licence.** Individual plans are "Personal use only, no redistribution or business use".
  The [terms](https://thetadata.net/terms-and-conditions) also forbid archiving or
  downloading content (§2.1(i)) and require destroying all copies on termination, certified
  within 30 days (§12.2). **Whether a local research cache may outlive a cancelled
  subscription must be confirmed with ThetaData in writing before paying**; if it may not,
  the subscription must run for as long as the vendor data is used.
- **Endpoints** (Theta Terminal v3, `http://127.0.0.1:25503/v3`):
  - `/option/history/quote` with `interval=1m`: "the last quote at the interval's
    timestamp";
  - `/option/list/expirations` and `/option/list/strikes`;
  - `/index/history/price` (price at the exact timestamp) and `/index/history/eod`.
- **Limits.** Multi-day requests are capped at one month (option quotes must name an
  expiration); concurrency is account-wide (2/4/8); there is no rate limit.
- **Timestamps.** `YYYY-MM-DDTHH:mm:ss.SSS` with no offset; ThetaData's Python library types
  them `America/New_York`. To confirm at purchase on a DST-change day.
- **Credential.** The terminal holds it (API key by argument, environment variable or
  `.env`; or `creds.txt`). Requests to the local server carry none, so our code never reads
  it.
- **Sessions.** SPXW was quoted only Monday, Wednesday and Friday before 2022-05-16, so the
  development window has about 590 sessions; the draft's "about 625" carries a marked fact
  fix.
- **Built.** `research/thetadata.py`: `ThetaDataSource` implements `HistorySource`, every
  data method raises "ThetaData not purchased yet", and it is not in `SOURCES` (tested).
  Its docstring holds the per-session request plan (four calls per session, index prices
  per session so that no batch reaches the holdout, EOD in ≤1-month chunks) and the
  estimates: validation ~550 calls / 20–40 min, development ~2,420 / 1–2.5 h, holdout
  ~1,750 / 0.7–1.8 h.
- **Purchase checklist** (readiness doc): confirm the open questions in writing; choose
  the plans; the expected subscription length; then the order the holdout guard enforces:
  validation window and `validate-vendor`, the development window only if every step
  passes, registration, and only then the holdout with `--unseal-holdout`. A single
  "2022 → today" download is not allowed.

### H-TS1 mechanism check (DESCRIPTIVE — development window — not a rule evaluation)

Question: on sessions whose prior-close VIX1D/VIX is high, does SPX move less than VIX1D
implied? Inputs are Cboe's public `SPX_History.csv` and the Cboe VIX1D/VIX daily aux file,
cut to 2022-05-13 → 2024-06-28 before anything was computed; the range passed
`holdout.guard`, and no value dated 2024-07-01 or later entered any computation.

Decision rule, quoted as fixed before the run:

> Split sessions at the upper tercile of the prior VIX1D/VIX, numpy.quantile at 2/3 over
> the same sessions (top: ratio >= that value, as in HTS1). Statistic: mean r in the top
> tercile minus mean r in the other two. Moving-block bootstrap over sessions in date
> order: 10-session blocks, 10,000 reps, seed 1, tercile membership fixed per session. The
> mechanism is 'supported' only if the 90% interval (5th to 95th percentile) lies entirely
> below zero; otherwise 'not supported'. Both halves (split at 2023-06-01) and the tercile
> bounds are reported. Fixed 2026-09-28, before the first run.

with `r_t = |ln(SPX_close_t / SPX_close_{t-1})| / (VIX1D_close_{t-1} / 100 / sqrt(252))`.

**Result: not supported** (run `a2b54db81c49`; `SPX_History.csv` sha256 `cfab26ca…`,
in-window rows `3127b07d…`; vol file `048eb3de…`, aux_hash `cb12502b…`).

- 533 sessions, none excluded; tercile bounds 0.801 and 0.918.
- Top tercile mean r 0.741 (178 sessions) against 0.715 for the rest (355): difference
  +0.026, 90% interval [−0.058, +0.101].
- H1 (before 2023-06-01): +0.025 [−0.070, +0.132]. H2: +0.013 [−0.108, +0.142].
- Mean r over all sessions is 0.724, below the ≈0.80 of a move priced exactly by VIX1D: the
  one-day implied was rich on average, but not richer when VIX1D/VIX was high.

**Limits.** Close-to-close includes the overnight move and the morning before entry, so
this is a proxy for the 10:00 → close exposure, not a test of H-TS1. H-EV1, H-SN1 and H-LV1
cannot be checked with close-only index data. The result informs whether the owner
registers H-TS1; it changes nothing in the pre-registration draft, and no registry record
was written.

## 2026-09-28 — stage 6: forward housekeeping and the registration decision package (no vendor data)

This entry evaluates no rule, registers nothing, runs no hypothesis rule on any data, and does
not touch the frozen strategy or the open cohort `spx-prospective-2026-09-22`. Work is on
branch `research/unified-core`. Stage 5 (`0d440b8`) was confirmed on
`origin/research/unified-core`, with the branch's upstream pointing there, before starting.
Nothing has been bought: `thetadata.py` stays a stub and `history.SOURCES` stays empty.
Details and commands are in `docs/research/research-core.md`.

### Housekeeping

- **Export.** 2026-09-28 is the only session recorded since 2026-09-25. It was exported
  read-only through the tunnel after the close (376 snapshots × 158 strikes).
  - 134 sessions, 2026-03-13 → 2026-09-28.
  - **Dataset hash `b76dc6c9…` → `c7fff54a1ffa7c4ee368a6d341828e792d65f7da6cfe27cd40300fae9e625182`.**
  - Settlements landed: none. Pending: 2026-09-28, whose official close was not yet in Helios
    `daily_bars`. The `--bars-only` refresh straight after changed nothing.
  - `tests/test_research_features.py` pins the hash; it was updated, with a comment saying
    why. Landing 2026-09-28's close will change it again.
- **Parity.** `parity` reproduces the frozen replay unchanged: 118 trades, 0 mismatches,
  $17,691.60 / $14,170.60 / $9,890.60, 22 settled and 96 intraday.
  `tests/test_research_sweep_ports.py` passes unchanged. Neither window reaches the new
  session.
- **Cohort shadow: not run.** The ledger, read with `git show` only, is still `70ccb8e`
  locally and on the remote, with 2026-09-22 → 09-24 recorded. There is no session after
  2026-09-24 to shadow.
- **Gateway re-dump**, 2026-08-03 → 2026-09-28, as in stage 5.
  - The output is byte-identical to stage 5's (`ccf781f6…`, 164 records, no errors): no
    session had completed in between.
  - The merge ingest added, removed and revised 0 bars; `kept_not_in_dump` 0.
  - **`aux_hash` unchanged at `cb12502b721efeda92f06f55f35273e26b101ecaa3a847e7339a628445144967`.**
  - Retention still starts at 2026-08-12, so no dump yet lacks a bar the file holds.
- **VIX1D intraday.** Still for 2026-09-28 only. Whether it now arrives every session can't
  be judged until 2026-09-29 has closed; re-check at the next dump.
  - 2026-09-28 is now an exported session, so its 10:00 features include intraday VIX1D
    (7.88).
  - Coverage of the 134 sessions: prior closes 134, intraday VIX/VIX9D/VIX3M at 10:00 31,
    intraday VIX1D 1.

### Registration decision package (nothing registered)

`docs/research/registration-decision-2026-09.md` is written for the owner. For H-LV1,
H-SN1, H-EV1 and H-TS1 it gives:
- the claim and mechanism quoted from the draft;
- every implementation choice the definition hash freezes, with its alternative and effect;
- the development evidence so far, labelled 2026 descriptive, stage-5 mechanism check or
  shadow.

It ends with the owner's choices: which hypotheses to register, k and its Bonferroni level,
optional H-EV2, and a forward (Helios-only) holdout if ThetaData is not bought. The registry
still has no `register` event.

Findings that came up while writing it:
- **HTS1's hash was misdocumented.** Stage 4 recorded `2ec8c008…`; the committed code gives
  `fab8bf3e0ab10805d8b6d8ee19617df7013c0fa776ed6fbf86314c6238ff69c6`, identically at
  `82aed43` and `0d440b8`. The research-core table and the draft carry marked fact fixes, and
  the stage-4 entry above a correction note. A new test pins all four definition hashes.
- **What the hash does not cover.** Only the top-level rule class's source and parameters
  are hashed. E0's code, HLV1's predicate body, the feature and calendar code and
  `configs/config.yaml` are frozen only by the register record's `git_sha`.
- **H-EV1 and 10:00 releases.** Calendar v1 has four PCE releases at 10:00, all in the
  holdout (2024-11-27, 2025-04-30, 2025-12-05, 2026-01-22). H-EV1's strict "before 10:00"
  trades them.
- **H-SN1's noise secondary is not built.** The 1.48σ/1.68σ runs are not catalog entries,
  and the draft gives no statistic for the comparison.
- **H-TS1 under a forward holdout.** It cannot be fitted as defined without
  development-window sessions in the dataset; a forward holdout would need a redefined
  threshold (new hash).
- **H-TS1 threshold** (feature count only, no P&L): the development bound (≈0.918) flags 23
  of the 132 evaluable 2026 sessions (17 H1, 6 H2), against 44 for the 2026 tercile
  (0.828). The mechanism check stays "not supported".
- **H-EV1's 2026 release sessions** moved more after 10:00 (RMS 1.192σ) than no-event
  sessions (0.956σ). That is the opposite of its mechanism's direction; it is descriptive,
  from 17 sessions.

### Tooling hygiene

- `graphify` is not available on this machine: it is not on `PATH`, and the binary path in
  `AGENTS.md` (`/home/billy/.local/bin/graphify`) does not exist here. `graphify update .`
  was not run.
- `export-history --provider thetadata` still stops with "Data provider not chosen" and exit
  2. It stops in `history.get_source`, before any source is built or request made.
- `uv run pytest` and `uv run ruff check .` pass.

## 2026-09-29 — ThetaData development window: E0 baseline, drafted hypotheses, power (in-sample; nothing registered)

Everything in this entry is on the development window (2022-01-03 → 2024-06-28) and is
**in-sample**. Nothing was registered, the holdout was not touched, and sessions from 2026-03-13
onward were not used. Dataset `spx_0dte_thetadata` @ `93bbe58e`, profile `vendor_1m`, halves
split at 2023-04-26 (by session count, fixed before any result was read). Vendor results are
comparable only with other vendor results. The owner's package, with every table, is
`docs/research/registration-decision-2026-09-29.md`.

### Integrity

`verify` OK; `coverage`: 585 sessions, each with a real SPX level, a 10:00 VIX and official
bars. E0 replays 584. The one it cannot is 2023-07-03, an early close: its fly was still held
when the 13:00 clock ended, and the replay calls that `incomplete_data`.

### E0 loses on the development window

| | Stressed | Midpoint | Delayed | $0.10 tie-set 5–95% |
|---|---:|---:|---:|---|
| 584 sessions, 361 trades | −13,085 (−$36/trade) | +18,362 | −8,791 | −13,561 … −10,965 |
| 2022 / 2023 / 2024 H1 | +3,524 / −15,990 / −619 | | | |
| Gap up (CALL) / gap down (PUT) | +6,934 / −20,020 | | | |

At VIX < 17 the losses are the puts (−$14,216 over 96), not the calls (+$1,452 over 135), which
reverses the 2026 pattern behind H-LV1. E0 barely enters at VIX ≥ 24.5 (6 trades in 120
sessions).

### Hypotheses, paired with E0 (draft bootstrap: 10-session blocks, 10,000 reps)

| | Δ vs E0 | H1 / H2 | Delayed Δ | Fly-choice draws beating E0 | 97.5% lower bound |
|---|---:|---|---:|---:|---:|
| H-TS1 (threshold 0.9181935615930604, n = 528) | +9,960 | +6,075 / +3,885 | +7,815 | 100% | −1,071 |
| H-EV2 (FOMC days; 4 trades) | +3,831 | +3,831 / 0 | +1,771 | 100% | +135 |
| H-EV1 | +151 | +948 / −797 | +116 | 100% | −8,912 |
| H-LV1 | −1,452 | +273 / −1,725 | −1,787 | 0% | −15,116 |
| H-SN1 (Δ at 1.48σ / 1.68σ: −17,691 / −33,537) | −9,814 | −14,929 / +5,115 | −13,888 | n/a | −34,224 |

- **H-TS1** is the only rule beyond fly-choice noise. Caveats:
  - its threshold is fitted on these sessions;
  - the stage-5 mechanism check was not supported;
  - skipping 69 random E0 trades gains +$2.5k on average, and 6.6% of such skips gain as much;
  - about a quarter of its Δ comes from below-zero exits (next section);
  - its own net is still −$3,126.
- **H-EV2's** gain rests on four trades, one of them an artifact.
- **H-SN1** fails its noise secondary: the spread across centers is $23.7k, against E0's $2.6k
  band.

### Findings about the test itself

- **Stressed exits can be priced below zero.** Six E0 trades have them: −$5,476 stressed
  against −$514 midpoint. The worst is 2022-12-14 at 14:00 ET, the FOMC statement minute: a
  $1.75 fly lost $2,535. Flooring those exits at $0 (sensitivity only) gives E0 −$9,685 and
  H-TS1 Δ +$7,402.
- **Gate 1 over-passes on skip filters.** With the exact nested bootstrap at 358 sessions and
  no effect, H-TS1 passes gate 1 16% of the time at k = 1 (nominal 10%) and 7.3% at k = 4
  (nominal 2.5%).
- **With E0 negative,** a paired pass means "loses less than E0".

### Power (from development vectors; assumes 2022–24 is representative)

- **Holdout size:** 358 usable sessions (H1 204 / H2 154), or 421 with an Indices month.
- **H-TS1, all gates:**
  - 57% at k = 1 and 38% at k = 4 if the development effect is real;
  - 34% at k = 1 if the effect is half as large;
  - 421 sessions add about 2 points.
- **The other four** have no realistic power.

### Changes

- **Data (owner-approved):** Cboe daily VIX-family closes were added to the vendor dataset for
  H-TS1: aux_hash `eab136c9…`, dataset hash unchanged.
- **Where runs are recorded (owner-confirmed):** the development runs are in a separate
  registry, `reports/research/registry/development/spx_0dte_thetadata.jsonl`, because `register`
  refuses a definition already in the dataset's registry. It holds 8 distinct definitions, all
  post hoc.
- **Code (`a36b110`):** `EventDaySkipEntry` and the catalog entries `HEV2`, `HSN1_c148` and
  `HSN1_c168`. The four pinned hypothesis hashes are unchanged.
- **Runs:** `9eccee6a6aa5` and `da7a9163c0fa`.

### Recommendation for the owner

If registering now, register H-TS1 alone (k = 1) and drop the other four. Only what is
registered before the holdout pull can ever be tested on it, so not registering yet is a real
alternative (D1). Decide D2–D5 (pass
meaning, exit floor, gate-1 calibration, early closes) before any registration, because the
`git_sha` freezes them. D6 (Indices month) and D7 (ThetaData licence) stay open.

## 2026-09-29 (later) — owner's decisions: no registration yet; stressed exits floored at $0

Still in-sample on the development window, and nothing is registered. The package
`registration-decision-2026-09-29.md` was revised in place: its figures now use the floored
metric, and the first version's unfloored figures are kept for the record.

### Decisions

- **D1: do not register yet.**
- **D3: floor stressed exits at $0.** This is Revision 1 of the pre-registration draft, marked
  there as made after seeing the development results.

### How the floor is implemented (`7b1f229`)

- `--floor-stressed-exits` (`Costs.stressed_exit_floor = 0.0`) books a stressed or delayed
  intraday exit whose net proceeds are below $0 at $0.
- Such fills are marked `exit_floored` in `trades.jsonl`. The run meta records
  `accounting.stressed_exit_floor`, and the report says so.
- It is off by default, because Helios data has such exits too: 3 of the 118 frozen-parity
  trades and 40 exits across the idea-sweep catalog.
- With it off, `parity` is unchanged (118 trades, 0 mismatches, $17,691.60 / $14,170.60 /
  $9,890.60) and the parity `trades.jsonl` is byte-identical (`b5b732ad…`).
- The full suite passes (1033), as do the `research_data` parity and sweep-port tests.

### Re-run under the floor

Runs `7d7f91ad9ba5` and `9971c5db1313` (git `7b1f229`), recorded in the development registry.
It now holds 25 records; the variant count is still 8.

| | Floored | Unfloored (first version) |
|---|---:|---:|
| E0 stressed net (361 trades) | −9,685 | −13,085 |
| E0 $0.10 tie-set 5–95% | −10,150 … −9,345 | −13,561 … −10,965 |
| H-TS1 Δ (90% lower bound) | +7,402 (+859) | +9,960 (+3,011) |
| H-TS1 Δ, H1 / H2; delayed | +3,517 / +3,885; +7,317 | +6,075 / +3,885; +7,815 |
| H-EV2 Δ | +1,366 (fails gate 2) | +3,831 |
| H-EV1 / H-LV1 / H-SN1 Δ | +151 / −1,455 / −12,878 | +151 / −1,452 / −9,814 |

- Exits floored:
  - E0: 6.
  - H-TS1: 3.
  - H-EV2: 4.
  - H-SN1: 14.
- Under the floor, H-TS1 passes gate 1 in-sample only at k = 1. 13% of random 69-trade skips
  gain as much.
- Holdout power for H-TS1 alone (k = 1, 358 sessions, all gates):
  - 49% if the development effect is real, 33% if it is half as large;
  - a false-pass rate of 18% with no effect (nominal 10%);
  - an Indices month changes these by less than the simulation error.

### Still open

- D2: what a pass means against a losing E0.
- D4: gate-1 calibration on skip filters.
- D5: early closes.
- D6: Indices month.
- D7: ThetaData licence.
- D9 (new): no command can evaluate a registered rule on holdout sessions yet (`run` has no
  `--unseal-holdout`). It must be built and committed before any registration.

## 2026-09-29 (later) — D9: the pre-registered holdout evaluation command (built; nothing run)

Built at the owner's request. Nothing was registered, unsealed, pulled or evaluated, and no
holdout data was read. The command was exercised only on a synthetic vendor dataset in tests.

### The command

`holdout --unseal-holdout SEQ` (`protocol.py`, commit `6f02a86`) is the only command that
replays holdout sessions.
- **What it evaluates.** Exactly the variants registered up to `SEQ`, each paired with E0.
- **Fixed, not parameters:** `vendor_1m`, stressed exits floored at $0, 10-session blocks,
  10,000 reps, seed 1, halves split after 2025-04-30, k = number registered, and gates 1–4 as
  drafted.
- **Recording.** Every evaluation is recorded (scope `holdout`, k, gates, reproduction), and
  there is no `--no-registry`.

### Refusals, all before any holdout session is replayed

- the unseal does not verify;
- a registered definition no longer matches the catalog;
- E0 or H-SN1 is registered (gate 5 has no statistic);
- the tree is dirty, or `src/`/`configs/` changed since the registration commit;
- no holdout sessions have been pulled;
- a fitted rule's re-fit differs from its registered value;
- a second evaluation is not an exact reproduction of the first.

### Also changed

- **`register` records fitted values.** It now fits a fitted rule on its window before
  appending anything, and records `fitted` and `fit_profile` (`--profile`, default
  `vendor_1m`).
- **Checked on the real dataset, in-process, with nothing registered:** HTS1 fits to
  `{threshold: 0.9181935615930604, fit_n: 528}`, the frozen value.

### Readings the draft left open, now fixed in code, for the owner to review before registering

- **Gate 3:** "either arm" is the union of each arm's three largest sessions, removed from
  both.
- **"No re-runs after edits":** a second evaluation is allowed only as an exact reproduction,
  and it is recorded.

### Tests

- `tests/test_research_protocol.py`, 13 tests.
- A bug the tests caught: the recorded gate-1 level was rounded to 0.97 instead of 0.975
  (label only; the bound itself was right). Fixed.
- The full suite (1046) and ruff pass.

## 2026-09-29 (later) — D5: held trades settle on early closes (development re-run; nothing registered)

In-sample on the development window. Nothing registered, unsealed or pulled.

### Decision and change

- **Decision (owner): D5.** A trade held on an early close settles on that day's official
  close instead of dropping the session.
- **Change (`6891317`).**
  - The replay's end-of-data requirement is one hour before the session's scheduled close:
    15:00 on a regular day, which is `SimulationEngine`'s rule, pinned by a test, and 12:00
    on a 13:00 early close.
  - The scheduled close comes from the vendor dataset's `session_close_et`. Helios datasets
    have none, so their replays are unchanged: parity is 118 trades, 0 mismatches.
  - The full suite (1050) and the `research_data` tests pass.
- **Re-runs:** `7d7f91ad9ba5` and `9971c5db1313` at `6891317`. The ids are unchanged because
  a run id does not hash the commit; the registry holds both versions' results hashes. The
  development registry now holds 37 records, still 8 definitions. All 585 sessions replay.

### Results

| | Now | Floored, before the fix |
|---|---:|---:|
| E0 stressed net | −9,922 (362 trades) | −9,685 (361) |
| H-TS1 Δ (90% lower bound) | +7,639 (+1,078) | +7,402 (+859) |
| H-EV2 / H-EV1 / H-LV1 Δ | +1,366 / +151 / −1,455 | unchanged |
| H-SN1 Δ | −12,736 | −12,878 |

- E0 gained 2023-07-03, a held put that settled at −$238. H-TS1 had skipped that session, so
  its Δ rose by the same amount.
- H-SN1 gained 2022-11-25 (−$163).
- Holdout power for H-TS1 alone (k = 1, 358 sessions, all gates) is essentially unchanged:
  - 51% if the development effect is real, 33% if it is half as large;
  - a false-pass rate of 18% with no effect.
- The draft will carry D5 as Revision 3.

### Still open

- D2: what a pass means against a losing E0.
- D4: gate-1 calibration on skip filters.
- D6: Indices month.
- D7: ThetaData licence.

## 2026-09-29 (later) — D4: gate 1's level calibrated on development data (Revision 4; nothing registered)

In-sample, development window only. Nothing registered, unsealed or pulled.

### The calibration study (scratch, development data)

Simulated holdouts of 358 sessions, drawn in 10-session blocks from the development pairs.
For H-TS1 at k = 1:

| Gate-1 method | Passes with no effect (target 10%) | Power, development effect | Power, half effect |
|---|---:|---:|---:|
| Percentile bootstrap at the drafted 90% bound | 17–19% | 49–52% | 32–34% |
| Same test at the 97.5% bound | 9–11% | 31–33% | 17–20% |
| Bootstrap-t at the 90% bound | 14–16% | 35–39% | 23–27% |

- **Bootstrap-t has no advantage** at the same real false-pass rate.
- **A circular-shift skip test could not be validated.** The block resampling lines both series
  up on block boundaries only at the observed alignment, which biases the test. On clean
  synthetic data it is conservative.
- **One scenario of mine was wrong and was replaced.** Halving every paired difference cannot
  change a sign-based test.

### Decision and change

- **Decision (owner): D4, the calibrated level.**
- **Change (`b18ca94`, `c59e6bd`).**
  - At registration, `register` replays E0 and each rule on the development window under the
    protocol's settings, and shifts each paired difference to mean zero.
  - It resamples that difference to the planned holdout size and runs the percentile test on
    a grid of levels: 2,000 simulated holdouts, 10,000 reps each, seed 1.
  - For each k = 1..5 it records the loosest level with a simulated false-pass rate of at most
    0.10/k, never looser than 0.10/k.
  - `holdout` uses the recorded level. It refuses a registration without one, or one whose
    target could not be reached for its k.
  - Marked in the draft as Revision 4.
  - Tests: 1052 pass, ruff is clean.

### What it gives on the real dataset (in-process, nothing registered)

| | k = 1 | k = 2 | k ≥ 3 |
|---|---:|---:|---|
| H-TS1, 358 sessions | 2.5% (97.5% bound) | 0.25% | cannot be calibrated |
| H-TS1, 421 sessions | 4.0% | 0.5% | cannot be calibrated |
| H-EV1 / H-LV1 / H-EV2 (358) | 5% / 6% / 10% | 1.5% / 2.5% / 5% | |

### Consequences

- **Power for H-TS1 alone (k = 1, all gates):**
  - 33% if the development effect is real, 20% if it is half as large;
  - 10.6% with no effect, against a 10% target;
  - with an Indices month: 40% and 22%. Under calibration the month now buys power.
- **In-sample, H-TS1 would fail gate 1 at its calibrated level:** its 97.5% bound is −$2,916.
- **The negative-baseline effect (D2) remains.** A no-mechanism skip passes about 15% of the
  time while E0 loses.

### Still open

- D2: what a pass means against a losing E0.
- D6: Indices month; register with `--holdout-sessions 421` if bought.
- D7: ThetaData licence.

## 2026-09-29 (later) — D2: a pass must also make money (gate 6, Revision 5; nothing registered)

In-sample, development window only. Nothing registered, unsealed or pulled.

### Study before the decision

Scratch simulation, H-TS1 alone, k = 1, calibrated gate 1, 358 sessions. Two candidate gates:

| Scenario | Gates 1–4 | + own P&L > 0 | + beats a random skip |
|---|---:|---:|---:|
| Development effect | 36% | 18% | 36% |
| Half the effect | 27% | 8% | 27% |
| No mechanism, E0 losing | 16% | 4.7% | 16% |
| No mechanism, E0 breaking even | 13% | 13% | 13% |

- **"Beats a random skip" changed no verdict.** The calibrated gate 1 already requires the
  skipped trades to be much worse than average.
- **With gate 1 calibrated, trading less adds only about 2.5 points** of false passes.
- **So D2 was a choice of meaning.**

### Decision and change

- **Decision (owner): D2, gate 6.** A registered rule's own stressed P&L over the evaluated
  holdout sessions must be above zero.
- **Change (`362a728`).** `protocol.gates` adds `gate6`, and the holdout verdict shows G6.
- Marked in the draft as Revision 5.
- Tests: 1052 pass, ruff is clean.

### Consequences for H-TS1 alone (k = 1)

- **A pass now means it beat E0 and made money on the holdout.**
- **Power with all gates:**
  - 18% if the development effect is real, 8% at half;
  - 22% and 10% with an Indices month;
  - a no-mechanism rule passes about 5% of the time while E0 loses.
- **In-sample it fails gate 6:** its own net is −$2,283. It also fails gate 1 at its calibrated
  level.

### Still open

- D6: Indices month.
- D7: ThetaData licence.

## 2026-09-29 (later) — D6: no Indices month

- **Decision (owner): no more data will be bought.**
- **The holdout is 358 usable sessions** (H1 204 / H2 154). The 63 sessions from 2025-12-10 to
  2026-03-12 have no SPX/VIX minute data, and the no-derived-data rule skips them.
- **Registration uses `--holdout-sessions 358`,** the default. H-TS1's calibrated gate 1 is then
  the 97.5% bound.
- **Power for H-TS1 alone, all gates:** about 18% if the development effect is real.
- **The intraday VIX cross-check stays undone.** It is a known limitation, and it does not
  affect H-TS1.
- **Still open:** D7, the ThetaData licence.
