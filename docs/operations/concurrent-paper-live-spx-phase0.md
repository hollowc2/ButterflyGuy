# Concurrent paper + live SPX: Phase 0 verification

Read-only verification for `docs/operations/concurrent-paper-live-spx-prompt.md`, done
2026-11-17 between 09:40 and 10:40 PT. Code references are to `origin/main` at `ec4d2d0`. Helios was
read with `docker ps/inspect`, `psql` SELECTs, the metrics endpoint and the Prometheus API only.
Nothing on Helios was changed.

## 1. Background claims: confirmed, corrected, new

**Confirmed (file:line on `ec4d2d0`)**

| Claim | Evidence |
|---|---|
| One OPEN trade per underlying/day | `db/migrations/008_one_open_trade_per_underlying_day.sql:1-3` |
| One active ENTRY (and EXIT) intent per underlying/day | `009_broker_order_intents.sql:26,31` (unique partial indexes) |
| `daily_risk_state` keyed `(trade_date, underlying)` | `db/queries.py:570-618` |
| Weekly P&L and recent-loss reads use every SPX trade | `db/queries.py:621-653`; callers `risk/risk_engine.py:111,119` |
| Startup adopts `open_rows[0]` regardless of mode | `scripts/run_live.py:1196,1216-1217` |
| Live startup + 15 s runtime reconciler compare all OPEN SPX rows with the broker | `run_live.py:1197-1214`, `604`, `635-650`, `693-725`, `1338-1351` |
| Live freshness gate needs a collector snapshot in its own DB | `services/trade_service.py:231,778-815`; `max_chain_snapshot_age_seconds=180` (`core/config.py:55`) |
| No setting disables the collector | `run_live.py:1311` |
| Paper fill marker is the only mode marker | `execution/order_manager.py:464` (`paper_fill_model: mark_v1`); fills at mark `633,768` |
| EOD chart loop selects by underlying | `run_live.py:903-924`, `position_service.py:1405` |
| Pool `min_size=2, max_size=10` | `db/connection.py:38-39` |
| Account hash resolved once per client | `data/schwab_client.py:125,157` |
| `container_name`, port `127.0.0.1:8000`, `DATABASE__NAME: butterfly_guy` | `infra/docker-compose.yml:14,51,32` |

**Corrections**

- The override's env names are `EXECUTION__LIVE_TEST_DATE` and `EXECUTION__LIVE_TEST_MAX_DEBIT`
  (not `LIVE_TEST_*`). `LIVE_EXPECTED_SCHWAB_ACCOUNT_ID` is exported in the override's
  `command`, not in `environment`. The override also forces `SCHWAB_ACCESS_MODE: direct`,
  `SCHWAB_GATEWAY_SHADOW_READS: "false"`, `EXECUTION__RECORD_LIVE_EXECUTION: "true"` and
  `EXECUTION__LIVE_TEST_QUOTE_MAX_AGE_SECONDS: "10"`.
- The brief's line refs `activate-auto.sh:49-72`, `common.sh:9-36` don't match the local copies.
  The local `spx-live-test-2026-11-17/` is the **old 2472617 pilot** (BASE_IMG 172359a6, spx-charts
  override). The current material is the `b06cdb7` template and the Helios dir
  `/opt/butterflyguy-releases/spx-live-test-20261117-b06cdb7/`, which carries an `ON-HOLD` marker.
- Prometheus on Helios scrapes `butterfly_spx_app:8000` from `/opt/monitoring/prometheus.yml`,
  not `app_spx:8000` (the repo's `infra/prometheus.yml` says it is not the live config).

**New collisions the brief did not list**

1. **Chain JSONL journal.** The collector appends every snapshot to
   `data/chains/SPX/<date>.jsonl` (`data/collector.py:10,235` → `backtest/chain_cache.py:59-100`,
   `CHAIN_CACHE_DIR = data/chains`). `app_spx` bind-mounts `/opt/butterflyguy/data/chains`
   read-write; 11-13 was 49 MB, 11-16 37 MB. Two SPX collectors on the same bind would interleave
   ~100 KB appends into one file with no lock. The live service must not mount it, or must mount
   a separate directory.
2. **Postgres advisory locks are per-database.** The entry lock
   `butterfly_entry:SPX:<date>` (`trade_service.py:152-161`) would make one bot log
   `entry_lock_held` if both shared a DB. A separate DB removes this. The migration lock
   `810770001` is also per-DB.
3. **Alertmanager labels.** `AlertmanagerNotifier(url, underlying)` labels alerts by underlying
   only (`services/notifier.py:20-50`). Live startup resolves `reconciliation_failure`,
   `broker_ambiguity` and `settlement_failure` (`run_live.py:1206-1213`). A paper
   `settlement_failure` alert (`run_live.py:829-833`) would be cleared by a live restart, and the
   two bots' alerts would dedupe into one.
4. **Regime classification on a fresh DB.** `classify_market_regime` runs at startup from
   `daily_bars` (`run_live.py:927-945`). `daily_reset_loop` reclassifies at 09:45 ET, but only
   after first sleeping to the next midnight (`run_live.py:948-985`). A container started at
   06:35 PT on an empty DB classifies `UNKNOWN` for the whole session. **Today this has no
   trading effect**: `GapRegimeFilter` defaults to `bull_call_bias=False`, `min_gap_pct=None`
   (`strategy/gap_regime_filter.py:10-22`), and SPX config sets neither. Seeding `daily_bars`
   at bootstrap avoids the difference entirely.
5. **Live trade 415 is already in the paper record.** It has no `paper_fill_model`, so it
   shows as `legacy` in the public performance page (`generate_live_performance.py:44-55`, all
   CLOSED SPX trades), the weekend review (`weekend_review.py:223`), Grafana panels, and the
   monitor-cadence extraction SQL. A separate live DB stops this going forward; 415 itself
   stays in `butterfly_guy` unless the owner decides otherwise.

## 2. Query inventory

Legend: **L** live bot, **P** paper bot, **R** reporting/cron, **G** Grafana, **S** research/study.
"Mode filter" = filters by paper/live. None of the runtime queries do.

| Table | Query / helper (file:line) | Callers | Mode filter | If the other bot's rows are present |
|---|---|---|---|---|
| butterfly_trades | `get_open_trades` (`queries.py:353`) | L, P startup recovery; L reconciler | no | **Live: halts startup or marks broker unsafe** ("DB has OPEN SPX trade(s) but broker is flat", `run_live.py:604`). **Paper restart adopts the live trade** and monitors it at mark |
| butterfly_trades | `insert_trade` (`:295`) + index 008 | L, P | no | **Second bot's entry fails** on the unique index |
| butterfly_trades | `get_trades_for_date` (`:364`) → `sync_trade_count`, startup realized P&L (`run_live.py:1263-1272`) | L, P startup | no | Restart sets trade_count/realized P&L from both bots → wrong daily limits |
| butterfly_trades | `close_trade`, `update_peak_value`, `merge_metadata` (`:314-350`) | L, P by trade id | n/a (by id) | Safe by id, but only after a wrong adoption |
| butterfly_trades | `get_trades_pending_eod_chart` / `mark_eod_chart_sent` (`:375-400`) | L, P (Discord EOD chart) | no | One bot posts the other's chart; whichever runs first marks it sent |
| butterfly_trades | `get_weekly_pnl` (`:621`) | L, P risk engine | no | **Paper losses can halt live** (weekly $1,500 default, `config.py:165`) and vice versa |
| butterfly_trades | `get_recent_closed_pnls` (`:639`) | L, P | no | Consecutive-loss is a **warning only** (`risk_engine.py:118-141`); wrong warnings |
| butterfly_trades | `fetch_closed_trades` (`generate_live_performance.py:44`), `weekend_review.py:223` | R (cron 20:30/21:30 UTC weekdays; Sat 16:00 UTC) | cohort by `paper_fill_model` of the **latest** trade | Live trades show as `legacy`; a live trade last in order flips the cohort |
| butterfly_trades | `reconcile_paper_settlements.py:78` | R/manual | by `settlement_source` | Low; touches only provisional settlements |
| butterfly_trades | `report_spx_live_test.py:57`, `deployment-check-database.py` | pilot scripts | no | **Close-out mixes paper rows into live evidence; `db_flat` fails when paper is open** |
| butterfly_trades | Grafana `butterfly_trading`, `butterfly_trade_detail`, `performance` (16/18/15 rawSql) | G | only 4 panels filter `paper_fill_model` | Mixed P&L/charts |
| butterfly_trades | monitor-cadence extraction (`research/monitor-cadence-exit` plan §1, lines 12-13, 29) | S | no (plan says live is reported separately, by hand) | Live trades enter the extraction |
| broker_order_intents | `create_intent` (`:410`) + index 009 | L only (paper creates none) | no | Paper never writes; in a shared DB no conflict, but … |
| broker_order_intents | `active_intents`, `intents_for_day`, `active_broker_order_ids` (`:517-560`) | L reconciler, L account guard | no | Only live rows exist; safe |
| daily_risk_state | `get_or_create`, `increment_trade_count`, `update_pnl`, `set_halted` (`:570-618`), `sync_*` (`risk_engine.py:170-210`) | L, P | no | **Shared count/P&L/halt: a paper trade uses live's 1 trade/day; a paper loss can halt live** |
| daily_risk_state | Grafana `performance.json` | G | no | Mixed |
| monitoring_leg_quotes | `insert_quotes` (`:174`) | L, P monitor | by `trade_id` | Safe by id; `chart_data.py:43` reads by trade id |
| monitoring_leg_quotes | Grafana, `update_grafana_exit_trigger.py:69`, study SQL (plan §1 line 20: `where underlying='SPX'`) | G, S | no | Study pulls both bots' quotes |
| post_exit_leg_quotes | `insert_post_exit_quotes` (`:223`) | L, P | by trade id | Safe by id |
| decision_log | `log_event` (`:659`) | L, P | no (underlying only) | Reports reading by underlying/time mix two bots' events (`report_exit_mark_parity`, `report_trade_ladders`, `report_selection_parity`, Grafana) |
| butterfly_candidates | `bulk_insert` (`:743`); startup count (`run_live.py:1278-1290`) | L, P | no | Two scans per minute interleaved; metric seed mixed |
| option_chain_snapshots | `bulk_insert_snapshot` (`:18`) | L, P collector | no | **Duplicate rows per minute** (two collectors) → research/backtests that assume one snapshot per minute double-count |
| option_chain_snapshots | `get_latest_snapshot_time` (`:154`) | L freshness gate | no | Satisfied by either collector (would mask a dead live collector) |
| option_chain_snapshots | `get_nearest_snapshot_chain` (`:91`) | L, P selection-parity diag, position_service `:1558` | no | Diagnostic only |
| chain_snapshot_meta | `insert_snapshot_meta` (`:45`) | L, P collector (SPX, `record_timing`) | no | Duplicate timing rows |
| spot_prices (incl. `$VIX`) | `SpotQueries.insert` (`:260`); VIX read `trade_service.py:306-313` | L, P | no | Duplicates; VIX read takes latest of either |
| daily_bars | `bulk_upsert` (`:677`, ON CONFLICT); `_previous_close` `trade_service.py:836-845`; regime `run_live.py:937-941` | L, P | n/a | Upsert is idempotent; safe |
| tent_boundaries | `TentQueries.insert` (`:721`) | L, P monitor | no | Grafana mixes |

## 3. Entry and exit dependencies on DB data

| Read | Path | Fresh live DB satisfies it? |
|---|---|---|
| Chain snapshot ≤180 s old | live entry gate | Yes, once its own collector has run one minute |
| `$VIX` in `spot_prices` ≤300 s | entry, VIX method (`trade_service.py:306-345`) | Yes, collector writes `$VIX` each minute |
| Previous close from `daily_bars` (must be the prior trading day) | entry (`trade_service.py:830-880`) | Yes after the collector's first-snapshot refresh (1 month of daily bars, `schwab_client.py:408-419`). **Blocks entry until then** (`prev_close_unavailable`) |
| Session open | entry, from Schwab 1-min bars | No DB dependency |
| Regime (`daily_bars`, 5-day lookback) | startup + 09:45 ET (see §1 new item 4) | **No** on day one if started after midnight (UNKNOWN all day); no trading effect today |
| `daily_risk_state` today | risk engine | Yes, created on demand |
| Weekly P&L (7 days) | risk engine | Needs history to mean anything; empty = 0 |
| Last 10 closed P&Ls | risk engine (warning only) | Needs history; empty = no warning |
| `butterfly_trades` OPEN / intents | startup recovery, reconciler | Yes (empty = flat) |
| Monitor | broker chain per poll; writes only | No history needed |

## 4. Risk-check finding (today's behavior)

The live pilot's weekly-loss and consecutive-loss checks **count paper trades today**, and
paper's count the live trade. Query (`queries.py:621-636`) filters only `underlying='SPX'` and
`status='CLOSED'`.

- 2026-11-16 live session: the weekly window (11-10 … 11-16) held paper 11-10 +11, 11-11
  +220, 11-12 −110, 11-13 −217 = **−$96**. That is far from the $1,500 halt, so it had no effect.
- If the pilot ran on 2026-11-18: window 11-12 … 11-18 = paper −327 + live −70 = **−$397**
  (`SUM` over CLOSED SPX trades on Helios, DB `pnl` is pre-fee). There's still no effect,
  but a bad paper week (e.g. 11-03 … 11-06 had −$595 in four trades) can halt live at
  −$1,500 with no live loss at all.
- `daily_risk_state` was not shared in practice only because the pilot **replaced** paper for
  the day. For 11-17, `trade_count=1` from paper trade 417 (still OPEN at 10:12 PT).
- Only one bot-placed live SPX trade exists: **415** (the only SPX trade with broker order ids; 2 intents, FILLED).
  76 SPX trades lack `paper_fill_model`: 75 legacy paper trades before 2026-07-22, and 415.

## 5. Load and storage (Helios)

**Schwab requests per minute** (Prometheus `butterfly_schwab_api_calls_total`, 30-min rate).

| Bot | When | chain | quote | account snapshot | orders for day | total |
|---|---|---|---|---|---|---|
| SPX live pilot | 11-16 10:00 PT, position open | 22.5 | 1.95 | 8.1 | 8.1 | **40.7** |
| SPX paper | 11-17 09:00 PT, position open | 23.5 | 1.95 | — | — | **25.4** |
| Gateway upstream (NDX + XSP) | 11-16 10:00 PT / 11-17 09:00 PT | | | | | 16.9 / 10.4 |

- The collector accounts for 1 chain + 2 quotes (SPX, VIX) per minute, plus 2 daily-bar calls per day. The
  rest is the monitor (2 s poll, `config.py:204`) and, on live, the reconciler/account guard.
- **Concurrent estimate:** 40.7 + 25.4 + ~17 ≈ **83 req/min** across all consumers at peak, vs
  ~58 on 11-16. SPX paper and live are both `SCHWAB_ACCESS_MODE=direct` on the same app key.
  The repo doesn't document Schwab's limit (unverified).

**Storage** (`butterfly_guy`, 9.9 GB; 18 GB free on `/`)

- SPX snapshots, 11-16 session: **197,340 rows, 390 snapshots** (~506 rows each).
- The current uncompressed chunk is 832 MB for 2.93 M rows (≈ 285 B/row). That gives **≈ 56 MB per SPX session
  uncompressed**. Compressed chunks run ~6× smaller (1,209 MB → ~200 MB), so ≈ **9-10 MB per session after
  compression**.
- Compression is a **manually added** policy (job 1000, `compress_after 7 days`). It is not in
  the migrations, so a new DB created by migrations gets no compression unless the bootstrap adds it.
- Also: `chain_snapshot_meta` 390 rows/session, `spot_prices` 780 rows/session (SPX + VIX), and
  `data/chains/SPX/<date>.jsonl` 37-49 MB/session on disk.

**DB connections:** `max_connections=50`. There were 30 backends at 10:12 PT. Of the 13 on
`butterfly_guy`, 8 are Grafana (172.23.0.11), 1 each SPX/NDX/XSP, plus psql and the TimescaleDB
scheduler. Each other DB has 1 (TimescaleDB scheduler per DB). A live bot adds pool ≤10 plus 1
scheduler: worst case ≈ 41 against today's count. Peak during a session was not measured; there's no
Postgres exporter.

**CPU and RAM:** load 0.36 on 2 cores; 5.6 GB available.

## 6. Pilot script assumptions (template `b06cdb7` + 11-17 local copy)

1. `spx_containers()` counts `^butterfly_spx_app$`; activation requires exactly 1.
2. Activation **recreates `app_spx`** (`up -d --no-deps app_spx` with the live override). The
   paper container ID/image (`BASE_ID`, `BASE_IMG`) must match beforehand, and a rollback restores them.
3. Post-activation checks read `docker inspect/logs butterfly_spx_app` for the live env and image.
4. `broker_flat` runs `deploy_broker_flat_check.py` inside `butterfly_spx_app`. It checks **all
   three** underlyings at the broker, so running it in the paper container would still be valid (read-only).
5. `db_flat` runs `deployment-check-database.py` in `butterfly_spx_app` against
   `config.database.dsn` = **`butterfly_guy`**, requiring 0 OPEN SPX trades and 0 non-terminal
   SPX intents. With paper running, **paper's OPEN trade fails this gate.**
6. Close-out runs `report_spx_live_test.py` in `butterfly_spx_app`. It reads `butterfly_trades` and
   `broker_order_intents` by `underlying='SPX' AND trade_date` (`tools/report_spx_live_test.py:57-60`),
   which would mix in paper rows. It saves `docker logs butterfly_spx_app`.
7. `rollback()` recreates `app_spx` from `rollback-image.yml` and verifies `BASE_IMG`.
8. Close-out gate: "pilot running" means `butterfly_spx_app` image == `CAND`.
9. `notify.py` posts to `DISCORD_WEBHOOK_URL` from `/opt/butterflyguy/.env`, the same webhook the
   bot uses for trade posts.
10. `D`, `R11`, `CAND`, `BASE_*`, `COMPOSE` are hard-coded per date in `common.sh`.

## 7. Consumers of `butterfly_guy` SPX rows

- **Grafana:** `butterfly_trading` (16 SQL panels), `butterfly_trade_detail` (18),
  `performance` (15; 3 use the `$fill_model` variable). All select by `underlying`.
- **Discord, in-bot:** trade posts and the EOD chart (`DISCORD_WEBHOOK_URL`, SPX only, paper and live).
- **Cron (UTC, `cron_guard`):**
  - `daily_report_card` 21:30 Mon-Fri: reads the **broker account**, not the DB.
  - `live_performance` 20:30/21:30 Mon-Fri: public page, all CLOSED SPX.
  - `weekend_review` Sat 16:00: from `.releases/weekend-review-current`.
  - `realized_vs_implied` Mon 15:30: snapshots and `daily_bars`.
  - `runtime_config_check` daily; `gateway_minute_backfill` monthly; token keepalive and reminder; `weekly_calendar`.
- **Research:**
  - monitor-cadence plan §1: all CLOSED SPX trades and `monitoring_leg_quotes` by underlying. Its qualifying set is
    "paper SPX trades ≥ 2026-11-17, direct, as-live"; live is reported separately.
  - The exit-ladder plan uses the supervised live pilot as its confirmation evidence (plan §5 and
    Amendment 1). That evidence is read from `butterfly_guy` today.
  - `run_backtest_db`, research export and dataset, `run_paper_replay`, `report_*` read snapshots and trades.
- **Discord webhook names** in the SPX container env: `DISCORD_WEBHOOK_URL`,
  `DISCORD_DAILY_REPORT_CARD_WEBHOOK`, `DISCORD_WEEKEND_REVIEW_WEBHOOK`,
  `DISCORD_UPCOMING_WEEK_PREP_WEBHOOK`, `EQUITY_DISCORD_WEBHOOK_URL` (values not read).

## 8. Helios state (2026-11-17 ~10:15 PT)

- **Paper SPX:**
  - container `9f36b8d5…`, image `sha256:d05c4fc8…` = `butterflyguy:release-a283610`;
  - started 2026-11-16 16:36 PT, 0 restarts;
  - compose files `infra/docker-compose.yml` + `.rollbacks/spx-a283610-20261116/release-image.yml`;
  - `SCHWAB_ACCESS_MODE=direct`, `EXECUTION__*`/`RISK__*`/`LIVE_*` unset (paper defaults).
- **NDX/XSP:** `SCHWAB_ACCESS_MODE=gateway`. XSP and NDX mount configs from
  `.releases/collector-phases-a471069-20261021/`.
- **Checkout:** `/opt/butterflyguy` at `f5cf2aa9` (PR #81), behind `origin/main` `ec4d2d0`.
  Untracked `.releases/`, `.rollbacks/`, `infra/generated/`.
- **Live-test staging:** `/opt/butterflyguy-releases/spx-live-test-20261117-b06cdb7/` is `ON-HOLD`
  (mid_walk). Left untouched.
- **Prometheus** (`/opt/monitoring/prometheus.yml`): job `butterfly_spx` → `butterfly_spx_app:8000`,
  no extra labels. Alerts (`/opt/monitoring/prometheus-alerts/butterflyguy.yml`):
  - `up{job=~"butterfly_(spx|ndx|xsp)"} == 0`;
  - restart churn;
  - Schwab API errors and entry-loop errors (`job!="butterfly_spx_candidate"`).

  A new job named `butterfly_spx_live` would **not** match the `up`/restart regex, but **would**
  match the error alerts.
- **Token mount:** directory bind `/opt/butterflyguy-tokens` (rw), as the compose comment
  requires. Inode/digest check is deferred to Phase 3 (no new consumer yet).
