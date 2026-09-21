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
- `src/butterfly_guy/scripts/run_prospective_execution.py`: `4bb9db87d3d0320c919c0577baac7bd2bd1a3381916ff556b222d63b976c85cb`
- `tests/test_prospective_execution.py`: `74ff1f9b5e215e4b752f34f964325d9bbac69364995c72e926409ec7fe9d511a`

These hashes describe the pre-registration state. The binding fingerprints for any cohort
are the ones inside that cohort's own `manifest.json`, recorded at `init` against a
committed worktree.

### Checkpoint results

- Dry-run rehearsal: not yet run.
- 20-trade integrity checkpoint: not yet reached.
- 60-trade early-failure review: not yet reached.
- Registered endpoint: not yet reached.
- Coverage statistics: none yet; no prospective session has been recorded.

Conclusion: pending. No prospective session has been evaluated, so this study makes no
claim yet about whether a stressed executable edge survives out of sample.
