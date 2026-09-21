# Reproduce the SPX exit-policy experiment

Read [REPORT.md](REPORT.md) for the decision. All timestamps in raw files include
UTC offsets; trading sessions and displayed clock times use America/New_York.
The inclusive development window is March 17–September 11, 2026. No later market
observations enter the experiment. Both directions are recorded long debit
butterflies; original lower/center/upper strikes, entry price, and quantity are
unchanged. All 108 quantities are one.

## Offline reproduction

From the repository root, using the existing locked project environment:

```bash
uv run python docs/research/spx-exits-2026-09-12/freeze.py
uv run python docs/research/spx-exits-2026-09-12/replay.py
uv run python docs/research/spx-exits-2026-09-12/diagnostics.py
uv run pytest docs/research/spx-exits-2026-09-12/test_replay.py -q
uv run ruff check .
```

The research used `.venv/bin/python` for the three offline scripts and
`uv run pytest` for validation. `environment.json` records Python and relevant
package versions; repository `uv.lock` supplies the dependency lock. The local
checkout was `e2ba77284370b7edc7c7e94d659fe707a226f834`.
No secret environment variable is required by the offline scripts.
They instantiate `ProfitManagementSettings` from the sanitized effective config,
and import the frozen deployed state machine, rather than calling `load_config()`.

`freeze.py` reconstructs 99 deployed Python files, verifies their hashes, and
writes the baseline and candidate YAML files. Their only policy difference is
`profit_management.strategy`. No protector parameters were tuned.
The archive's `.ruff.toml` excludes immutable deployed evidence from linting;
the research scripts and normal repository source remain checked.

## Acquisition actually performed

The initial checks were `tailscale status` (local daemon unavailable), then direct
read-only SSH to `billy@helios`. Host identity was `helios`, checkout
`/opt/butterflyguy`, free disk 16 GB, load averages 4.33/2.94/2.50.
Docker inspection was restricted to image, command, working directory, start time,
and revision label. No environments or credentials were exported.

These are the export commands, shown with **new filenames** so rerunning does not
overwrite the original evidence:

```bash
ssh -F /dev/null -o BatchMode=yes billy@helios \
  'docker exec -i butterfly_spx_app python -' \
  < docs/research/spx-exits-2026-09-12/acquire.py \
  > /tmp/spx-exits-new-export.jsonl
ssh -F /dev/null -o BatchMode=yes billy@helios \
  'docker exec -i butterfly_spx_app python -' \
  < docs/research/spx-exits-2026-09-12/acquire_monitor.py \
  > /tmp/spx-exits-new-monitor.jsonl
```

Each helper uses one read-only database transaction, a 25-second statement
timeout, and bounded per-trade queries. It does not call a broker API. Only
the held strikes are exported, not a full-chain database dump. Replay and
statistics run locally. `raw/export.jsonl` contains the effective baseline,
source text/hashes, sanitized ledger, then 108 collector quote records.
`raw/monitor.jsonl` has 108 monitoring records, including empty ones.
`manifest.json` supplies SHA-256 hashes of all raw files and acquisition context.
The baseline's `retrieved_utc` timestamps the extraction; raw files contain
approximately 126 MB of uncompressed JSON.

The prior review's ledger hash was
`69d21d7514e4610439d97abe4d65fb9163c74519df9e94ae465948e1c6a72515`.
All 108 IDs and compared entry/exit prices, timestamps, quantities, directions,
centers, P/L, and peak fields matched that prior extract. Peak fields are retained
only for identifying the requested six trades and auditing the ledger.

## Replay rules and costs

- Require exactly three same-timestamp held-strike rows with finite nonnegative
  bid/ask/mark and bid ≤ ask. Reject duplicate or incomplete groups; never carry
  a missing leg forward. Process post-entry observations chronologically, before
  the session close. No interpolation or recorded-peak seeding is permitted.
- Reconstruct spread mark from recorded leg marks, clamp negative spread mark to
  zero as the deployed position manager does, initialize peak at recorded entry,
  and run the deployed `ProfitStateMachine`. The harness asserts the deployed
  peak/quote gates are disabled or single-poll, so its direct peak tracking is
  equivalent for this frozen configuration. Upstream quote receipt timestamps,
  liquidity/size, and achievable complex-order fills are not available.
- Keep source paths separate. `best_available` chooses monitoring for any trade
  with monitoring rows, otherwise collector, **before examining its result**.
  It never splices sources within a trade or falls back after an unresolved exit.
  `quote_source` records the boundary. Summaries use the intersection of resolved
  trade IDs for the two policies in that source/stress/cohort.
- Charge the deployed exit commission: four contracts × $0.65 = $2.60, or 0.026
  option points, followed by the deployed two-decimal fill rounding. Retain
  entry prices, including their embedded commission. Do not subtract entry fees
  again for `mark_v1`. Legacy entry-fee attribution is uncertain; a separate
  sensitivity adds $2.60 to legacy trades only.
- Signal evaluation always uses the identical recorded mark path. Fill stresses
  deduct 25%, 50%, or 100% of `max(0, mark − synthetic spread bid)`, plus 0.05,
  0.05, or 0.10 points respectively, then commission. These span partial spread
  concession through legwise crossing; they are assumptions, not calibrated
  complex-order execution. Raw synthetic bids can be negative, making crossing
  exceptionally punitive. No hypothetical zero-price fill replaces such quotes.
- `next_quote_halfspread_005` waits for the next recorded observation after the
  signal. If none exists, censor the fill. Monitoring generally stops on the
  actual exit signal, making this test unusable for most baseline exits.
- If no exit fires, reuse a **recorded cash-settlement payoff** only for a trade
  actually settled and with quotes reaching within 120 seconds of session close.
  No exit commission is added, matching deployed paper settlement. This terminal
  ledger payoff is conditional evidence, not independently broker-attested
  settlement. Otherwise leave the trade censored; never liquidate at the final
  quote or infer a terminal value from a peak.
- Drawdown is realized/closed-trade dollar drawdown, sorted by exit time with
  initial equity P/L zero. Exposure is summed holding hours and mean hold minutes,
  not account exposure or intratrade marked drawdown. Account return and capital
  utilization cannot be established from this extract.

## Output map

- `results/recorded_trades.csv`, `recorded_summary.csv`: complete 108-trade ledger.
- `results/coverage.csv`: per-source/trade counts, first/last timestamps, invalid
  groups, entry lag, maximum gap, gaps over 120 seconds, mark/midpoint differences.
- `results/trade_results.csv`: every attempted policy/source/stress result,
  including unresolved status, signal/fill quote, exit, fees/drag, and exposure.
- `results/summary.csv`: all requested metrics by source, stress, full available
  paired sample, `mark_v1`, and month. Zero trade count means unavailable evidence.
- `results/paired_sensitivity.csv`: removes the **same baseline winner IDs** from
  both policies, in addition to policy-specific top-winner exclusions in summary;
  includes uncertain legacy fees and an additional $5.20/trade industry-fee stress.
- `results/baseline_parity.csv`, `parity_summary.json`, `signal_attribution.csv`:
  price, P/L, time, reason, signal-mark, and legacy-ladder diagnostics.
- `results/focus_trades.csv`, `six_trades.csv`, `focus_quote_windows.csv`: the six
  doubled losers and ten largest recorded winners, with chronological quote windows.
- `baseline.json`, `baseline.yaml`, `candidate.yaml`, `source-hashes.json`,
  `raw/deployment.txt`, `raw/checkout-source-hashes.json`, `config-history.txt`:
  attributable configuration and source evidence.

## Conditional end-to-end confirmation

Not run: the exit-only candidate fails on the validated cohort, so step 6's gate
is not met. For a future candidate that passes that gate, the current local
config-backed CLI supports this explicit direction/policy command:

```bash
uv run python src/butterfly_guy/scripts/run_backtest_db.py \
  2026-03-17 2026-09-11 --asset SPX --direction auto \
  --profit-strategy peakvaluetrailer --slippage 0.05
uv run python src/butterfly_guy/scripts/run_backtest_db.py \
  2026-03-17 2026-09-11 --asset SPX --direction auto \
  --profit-strategy profitprotector --slippage 0.05
```

Run it only in an isolated checkout with the frozen SPX YAML at
`configs/config.yaml` and a verified offline DB copy. It selects entries anew, so
it is a separate experiment. The CLI has no arbitrary `--config` override;
do not invent one or use `run_paper_replay.py`'s legacy defaults.
