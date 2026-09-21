# SPX frozen baseline: cash-settlement correction

Date: 2026-09-20

Replay window: 2026-03-13 through 2026-09-18

Asset: SPX

Base commit: `e2ba77284370b7edc7c7e94d659fe707a226f834` (`origin/main`)

Config: `configs/config.yaml`

Config SHA-256: `d120b63fd4e12ed812cc2742d602f9e531a1f5ca38e28c30628ab149f5d1b397`

## Result

The legacy replay valued 22 held-to-close butterflies from their last option marks. The
corrected replay values those positions from the official same-session SPX close using
`position_manager.fly_settlement_value`, the intrinsic-value function called by the paper
runtime's position service. Entry selection, strikes, widths, exit thresholds, confirmation
polls, trading window, commissions, and slippage were unchanged.

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

Legacy exit reasons were 47 `morning_profit`, 15 `late_morning_profit`, 34
`afternoon_profit`, and 22 `end_of_day`. Corrected exit reasons were the same first three
totals and 22 `cash_settled`. No replay trade was excluded for missing settlement evidence.
The 2026-09-18 official close was absent from the database, but that date's simulated trade
exited intraday and did not require settlement.

The corrected result remains concentrated in held-to-close outcomes and is a research
baseline, not deployment evidence.

## Settlement evidence and reconciliation

Official comparison file:
`https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv`

Downloaded file SHA-256:
`001099a8dd56f943335d67dbad271d4080a700334b758d1d6226133c052dcfd2`

For 2026-03-13 through 2026-09-18, Cboe supplied 131 sessions and production
`daily_bars` supplied 130, through 2026-09-17. Every available database close matched the
Cboe close to the cent. The corrected replay therefore uses the same-session
`daily_bars.close` as the official settlement evidence.

Five recorded paper trades had explicit `settlement_spot` and `settlement_source` evidence.
All five reconciled exactly to `fly_settlement_value` within cent rounding: trade IDs 139
(2026-06-22), 150 (2026-06-26), 184 (2026-07-17), 189 (2026-07-21), and 212
(2026-08-03). Their recorded source was `schwab_final_regular_session_1m_close`; this proves
intrinsic-calculation parity, not source parity with the official Cboe daily close.

Twelve recorded `cash_settled` trades lacked both settlement spot and source and were
excluded from recorded-trade reconciliation rather than inferred from their option marks:

- ID 3 — 2026-03-17
- ID 4 — 2026-03-18
- ID 5 — 2026-03-19
- ID 6 — 2026-03-20
- ID 7 — 2026-03-23
- ID 8 — 2026-03-26
- ID 16 — 2026-04-01
- ID 19 — 2026-04-02
- ID 20 — 2026-04-06
- ID 61 — 2026-05-06
- ID 77 — 2026-05-13
- ID 130 — 2026-06-16

## Reproduction commands

Legacy frozen replay:

```bash
ssh -F /dev/null -o BatchMode=yes billy@helios 'docker exec butterfly_spx_app python -m butterfly_guy.scripts.run_backtest_db 2026-03-13 2026-09-18 --asset SPX'
```

Corrected frozen replay used a bounded stdin-only overlay against the same read-only
production database because the local checkout's database credential did not match the
runtime credential. The overlay changed only settlement loading and held-to-close
finalization; it did not write a remote file or modify a service:

```bash
ssh -F /dev/null -o BatchMode=yes billy@helios 'docker exec -i butterfly_spx_app python - 2026-03-13 2026-09-18 --asset SPX' < /tmp/corrected_replay_overlay.py | tee /tmp/spx_corrected_replay_20260313_20260918.log
```

Regression and defaults tests:

```bash
UV_CACHE_DIR=/tmp/butterfly-spx-settlement-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/butterfly-spx-settlement-uv-python uv run pytest tests/test_backtest_research_integrity.py tests/test_run_backtest_db_defaults.py -q
```

Full verification:

```bash
UV_CACHE_DIR=/tmp/butterfly-spx-settlement-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/butterfly-spx-settlement-uv-python uv run pytest -q && UV_CACHE_DIR=/tmp/butterfly-spx-settlement-uv-cache UV_PYTHON_INSTALL_DIR=/tmp/butterfly-spx-settlement-uv-python uv run ruff check .
```

Result: 670 passed, 1 skipped; Ruff passed.

## Corrected implementation fingerprints

- `src/butterfly_guy/backtest/data_loader.py`: `ce442a5a99dbfc73b06c8c23cdf1bb6bf0524097d7a9b5d541f615bd8e4516f9`
- `src/butterfly_guy/backtest/simulation_engine.py`: `57cc88ec0568144989dff1b182ed4bd4617e3af1f21e8960c4919e3c5336cf11`
- `src/butterfly_guy/scripts/run_backtest_db.py`: `39ebcbd25df3a4998c90e3fb37e1f46694c81994a4019f4882fe5441245152ab`

## Assumptions

- SPXW positions are PM-settled; the official same-session SPX close is the appropriate
  expiration settlement evidence for this replay.
- A cash settlement has no executable closing option order, so no exit slippage or closing
  commission is charged.
- Missing settlement evidence is missing data. It is never replaced by a final option mark.
- The former mark-based behavior is available only through the explicitly named
  `--legacy-end-of-day-mark` diagnostic mode.
