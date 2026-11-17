# Concurrent paper + live SPX: design

Phase 1 of `docs/operations/concurrent-paper-live-spx-prompt.md`. Written 2026-11-17 (PT), from
the Phase 0 facts in `concurrent-paper-live-spx-phase0.md` (cited below as "P0 §n").

**Status: owner decisions recorded 2026-11-17 (§13). Waiting for design approval before Phase 2.**
Nothing here has been built or deployed.

## 1. Summary

- **Paper stays exactly where it is:** `app_spx`, `butterfly_spx_app`, DB `butterfly_guy`, port
  8000, `data/chains`, Prometheus job `butterfly_spx`. Its compose definition does not change.
- **Live becomes a new, separate thing**, used only on pilot days:
  - compose project `butterfly-spx-live`, file `infra/docker-compose.spx-live.yml`;
  - service `app_spx_live`, container `butterfly_spx_live_app`, `restart: "no"`;
  - DB `butterfly_guy_spx_live`, metrics on `127.0.0.1:8002`, chain journal in `data/chains-live`.
- **Isolation by database, not by a mode column.** No runtime query can see the other bot's
  rows, so no missed filter can become a live-safety bug.
- **A new opt-in env var, `BUTTERFLY_INSTANCE_ROLE`**, makes a misconfigured container refuse to
  start before any DB or Schwab write. It also tags Alertmanager alerts so the two bots' alerts
  stay apart. Unset, both behave exactly as today.
- **Pilot scripts v2** start and stop only the live container and prove paper was not touched.
- **A read-only paired report** compares the two bots trade-for-trade each pilot day.

Phase 0 found nothing that argues against separate databases. Every hard block (P0 §2) is a
query that filters by underlying only. A mode column would need a correct filter in about
30 runtime and reporting queries, plus Grafana and the studies. A separate DB needs none.

## 2. Why separate DBs instead of a mode column

| | Separate DB | Mode column |
|---|---|---|
| Unique indexes 008/009 | untouched | must be rebuilt per mode (migration on a live table) |
| Startup adoption, reconciler, risk state, EOD charts | correct with no code change | each needs a filter; a missed one halts or adopts a live trade |
| Advisory entry lock, migration lock | per-DB, no clash (P0 §1 new 2) | lock keys must include mode |
| Collector rows | each DB has exactly one snapshot per minute | duplicate snapshots per minute in `butterfly_guy`; research double-counts |
| Paper history, Grafana, studies | unchanged | every consumer needs a filter |
| Cost | ~10 MB/session compressed, ≤11 connections, one bootstrap | code and migration risk across the trading path |

## 3. Decision 1: which bot keeps `app_spx` / `butterfly_guy`

**Paper keeps it.** Reasons:
- It keeps paper history, Grafana and the public page.
- It keeps the monitor-cadence qualifying set ("paper SPX trades ≥ 2026-11-17") intact.
- It keeps collector continuity in `butterfly_guy` and the `data/chains/SPX` journal for research.

Live gets the new identity:

| Item | Paper (unchanged) | Live (new) |
|---|---|---|
| Compose | project `infra`, `infra/docker-compose.yml` | project `butterfly-spx-live`, `infra/docker-compose.spx-live.yml` |
| Service / container | `app_spx` / `butterfly_spx_app` | `app_spx_live` / `butterfly_spx_live_app` |
| Restart | `unless-stopped` | `"no"` |
| DB | `butterfly_guy` | `butterfly_guy_spx_live` |
| Metrics | `127.0.0.1:8000` | `127.0.0.1:8002` (free on Helios; 8000/8001/8003-8005/8011 are taken) |
| Chain journal | `/opt/butterflyguy/data/chains` | `/opt/butterflyguy/data/chains-live` |
| Role | unset now; `paper` if approved (§13 D4) | `live` |

**A separate compose project, not a profile in the base file.** This is a deliberate deviation
from the brief's suggestion:
- `infra/docker-compose.yml` doesn't change at all, so the rendered `app_spx` config is
  byte-identical by construction.
- No `docker compose -p infra …` command, including `--remove-orphans`, can stop, recreate or
  remove the live container.
- The live file can require its variables (`${SPX_LIVE_IMAGE:?}`) without breaking every
  `infra` compose command on days it isn't set. In the base file, `:?` interpolation fails the
  whole file even for an inactive profile.
- Cross-project DNS is already proven on `monitoring_net`: the `infra` apps resolve
  `schwab-gateway` from another project. So `timescaledb` and `alertmanager` resolve from the
  live project.

## 4. Decision 2: the live DB's contents (**OWNER**)

`butterfly_guy_spx_live` is created by the bootstrap (§10, step 4):
- the schema from the release image's migrations, run by the image itself with no token mount;
- the same TimescaleDB compression policies paper has;
- recent `daily_bars`;
- optionally, the prior live trade.

**Prior live history.** Phase 0 found exactly one bot-placed live SPX trade: **415** (2026-11-16,
−$70.00 pre-fee in `pnl`; −$79.76 with fees). It has 2 FILLED intents. The earlier October fills
were manual ToS orders and have no bot rows.

What the risk checks compute on the first concurrent live day:

| Choice | Weekly P&L (halt at −$1,500) | Consecutive-loss warning (needs 10) |
|---|---|---|
| **A. Empty** | $0 | none (0 trades) |
| **B. Copy 415** (recommended) | −$70 if the first session is on or before 2026-11-22, else $0 | none (1 trade) |
| *Today (shared DB)*, for comparison | −$397 on 11-18 (paper −$327 + 415) | counts paper trades |

Neither choice can halt or warn on day one. **B is recommended** because it gives the live DB a
complete real-money record. The weekly check and the paired report then always see real-money
history only, and the record stays continuous with the 11-16 evidence.

What B copies:
- trade 415 with its original id;
- its 2 intents;
- its `monitoring_leg_quotes`, `post_exit_leg_quotes` and `decision_log` rows (by `trade_id` and
  the session's time window).

All rows are CLOSED or terminal, so live startup recovery and the reconciler ignore them. The
copy runs once, at bootstrap, read-only on `butterfly_guy`.

**ID ranges (recommended, either choice).** The bootstrap restarts the live DB's
`butterfly_trades` and `broker_order_intents` sequences at **100000**. A trade id then names its
DB on sight in Discord, logs and the paired report. Paper ids are at 417, so ids can never collide.

**Trade 415 inside `butterfly_guy`** (P0 §1 new 5). It shows as a `legacy` paper trade in the
performance page, the weekend review and Grafana. Options:
- **(i) leave it** (recommended): one row, older than the monitor-cadence qualifying set, and
  the weekly-loss effect on paper ends 2026-11-22;
- (ii) tag it `metadata.execution_mode='live'` (one UPDATE on `butterfly_guy`) and teach the
  performance page and weekend review to exclude tagged rows;
- (iii) delete it: not recommended, because it destroys evidence and breaks joins.

## 5. Decision 3: the live collector (**OWNER**: retention)

**The collector stays on.** The live freshness gate requires a snapshot ≤180 s old in the live
bot's own DB (`trade_service.py:778-815`). There is no setting to turn the collector off.

- **Extra Schwab load:** 1 chain + 2 quotes per minute (3 req/min) plus 2 daily-bar calls a day.
  Most of the live bot's ~41 req/min is the monitor and reconciler, which it needs anyway (P0 §5).
- **Storage per session:**
  - `option_chain_snapshots` ~197k rows ≈ 56 MB uncompressed, ≈ 10 MB compressed;
  - `spot_prices` 780 rows; `chain_snapshot_meta` 390 rows;
  - `monitoring_leg_quotes`: a few MB per traded session (not compressed, same as paper);
  - the `data/chains-live/SPX/<date>.jsonl` journal: 37–49 MB on disk.
- **Retention (recommended):** keep everything and compress after 7 days. The bootstrap copies
  paper's policies (P0 §5: `option_chain_snapshots`, `spot_prices`, `tent_boundaries`,
  `butterfly_candidates`, with the same segmentby/orderby). The migrations don't add these.
  - At one pilot day a week that is about 0.5 GB DB and 2.5 GB journal per year, against 18 GB
    free. Review after 6 months.
  - Alternative: delete the live journal files after N days, since paper's journal already holds
    the same market data.
- **Rejected: "read snapshots from the paper DB."** The gate would then pass on paper's collector
  while the live bot's own market-data path is dead. That's weaker than today, so it isn't proposed.

## 6. Decision 4: instance role guard (new, opt-in)

`BUTTERFLY_INSTANCE_ROLE` ∈ {unset, `paper`, `live`, `live_rehearsal`}. Any other value refuses.

| Role | Refuses to start when |
|---|---|
| unset | never (today's behavior, no extra DB read) |
| `paper` | `execution.paper_trading` is false |
| `live` | `paper_trading` is true; `database.name == "butterfly_guy"`; the DB holds **any** `butterfly_trades` row carrying `metadata.paper_fill_model` |
| `live_rehearsal` | `paper_trading` is false; `database.name == "butterfly_guy"` |

- **Stricter than the brief on purpose.** The brief refused only an OPEN paper row; this design
  refuses any paper row in the live DB. A rehearsal or a misconfigured paper bot pointed at the
  live DB would otherwise leave CLOSED paper trades that count in live's weekly loss and the
  paired report.
- **`live_rehearsal` replaces a temporary override flag.** Phase 3 runs the live service in
  paper mode against a *separate* DB, `butterfly_guy_spx_live_rehearsal`. No flag exists that
  could weaken a real live start.

**Ordering in `run_live.main()`.** Fail closed, before any Schwab call or DB write:
1. `load_config()`;
2. the role checks that need only config;
3. `db.initialize()` (opens the pool; no writes);
4. the role check that reads the DB: a single SELECT that tolerates a missing table on a
   brand-new DB, using `to_regclass('butterfly_trades')`;
5. `run_migrations()`;
6. `SchwabClientWrapper(...)`.

A refusal logs `instance_role_refused` with the reason and exits with code 2. The
config-only checks run before the metrics server starts; the DB check runs after it (the
metrics server writes nothing).

**Tests:**
- every refusal case;
- unset makes no extra query;
- a refusal happens before the migration and Schwab constructors are called (mocked);
- a real-Postgres test of the paper-row check (CI `timescaledb` job).

## 7. Decision 5: connections

- **Today:** `max_connections=50` and 30 backends at 10:12 PT on 11-17. `butterfly_guy` had 13:
  Grafana 8, SPX/NDX/XSP 1 each, psql, and the TimescaleDB scheduler.
- **Live bot:** pool ≤10 plus 1 TimescaleDB scheduler for the new DB, so ≤11. The rehearsal DB
  adds 1 more scheduler while it exists.
- **Worst-case total ≈ 42 of 50.** A Grafana live datasource could add a few idle connections.
- **Recommendation: no pool change.** Making it configurable is a code path in the trading
  process, for a margin we don't need. If the rehearsal's measured peak exceeds 45, add an
  env-only `DATABASE__POOL_MAX_SIZE` (live = 5) in a follow-up PR.
- `max_connections` is not raised. That is the separate, queued change after the Phase 8 window.

## 8. Decision 6: metrics, alerts, Discord (**OWNER**: Discord)

**Prometheus.** In `/opt/monitoring/prometheus.yml` (not the repo copy), add:

```yaml
  - job_name: "butterfly_spx_live"
    static_configs:
      - targets: ["butterfly_spx_live_app:8000"]
        labels:
          instance_role: live
```

- The target is down on non-pilot days. That is harmless: the existing `up`/restart alerts use
  the anchored regex `butterfly_(spx|ndx|xsp)`, which does not match `butterfly_spx_live`.
- The API-error and entry-loop alerts already group `by (job)`, so they separate correctly.
- **No `up == 0` rule for the live job.** Prometheus can't tell a pilot day from any other
  day, so the rule would fire every non-pilot day. Liveness is owned by the activation script
  (+2 min check) and the 13:45 PT close-out, plus the bot's own critical alerts.
- Reload: edit with a timestamped backup (existing practice), then `docker kill -s HUP
  butterfly_prometheus`. Prometheus holds no token.

**Grafana Prometheus panels** select `{underlying="SPX"}` without a job (P0 §7), so they would
merge the two bots. Add `job="butterfly_spx"` to those SPX panels (PR 4).

**Alertmanager (closes P0 §1 new 3).**
- `send_alertmanager` gains an optional `instance_role` label, sent only when the role is set.
  Alert identity is the full label set, so live and paper alerts become distinct. A live
  restart's `resolve_critical` can then only resolve live alerts.
- With the role unset the payload is byte-identical to today; a test pins this.
- Routing is unchanged: everything goes to `infra-discord`, grouped by
  `project, alertname, severity`. A `[live]` alert now carries the label in its Discord text.

**Discord (OWNER).**
- **A. Separate webhook (recommended, no code).** Corey creates a channel/webhook and adds
  `DISCORD_WEBHOOK_URL_SPX_LIVE` to `/opt/butterflyguy/.env`; I never read its value. The live
  service sets `DISCORD_WEBHOOK_URL: ${DISCORD_WEBHOOK_URL_SPX_LIVE:?}`. Compose `environment`
  overrides `env_file`, and `run_live` reads the env first. The pilot scripts' `notify.py` takes
  the variable name as an argument and posts to the live channel too.
- **B. Same channel, `[LIVE]`/`[PAPER]` prefix.** A code change in every `DiscordNotifier`
  message builder (entry, exit, EOD chart, errors). Entry posts already show `` `PAPER` `` or the
  broker order id (`notifier.py:150-151`), but exits and charts don't.
- Telegram risk warnings (consecutive losses) say "SPX RISK WARNING". Under A, prefix them with
  the role (a one-line change in the same PR as the alert label). Under B, they get the same prefix.

## 9. Collisions not in the brief: how each is closed

| # | Collision (P0 §1) | Closed by | Code change? |
|---|---|---|---|
| 1 | Both collectors append to `data/chains/SPX/<date>.jsonl` with no lock | Live mounts `/opt/butterflyguy/data/chains-live:/app/data/chains`; the rehearsal uses `data/chains-live-rehearsal`. The bootstrap creates the dirs as `billy` (uid 1001 = container user). Activation asserts the live container's mount source is not `data/chains`. | No |
| 2 | Advisory entry/migration locks would clash | Per-database by Postgres design; separate DB removes it | No |
| 3 | Alertmanager alerts share labels; live restart resolves paper's alerts | `instance_role` label when the role is set (§8) | Yes, small (PR 1) |
| 4 | Fresh DB → regime `UNKNOWN` all day (no 09:45 reclassify on day one) | Bootstrap seeds 1 year of `$SPX`/`$VIX` `daily_bars` from `butterfly_guy`. **Every activation re-seeds** bars newer than the live DB's latest, before the container starts. Startup then classifies from the same closes paper uses, and the prior close exists before the collector's first refresh. | No (tooling only) |
| 5 | Live trade 415 counted as paper in reports | Future live trades never enter `butterfly_guy`; 415 handled per §4 (i/ii) | No (or PR 4 for ii) |

Two more found while designing:

- **Image skew.** The live service needs an image with the role guard, so its image is newer
  than paper's (`a283610`). A paired comparison should run identical code. **Recommended:**
  deploy the same release to `app_spx` at a normal off-hours paper deploy before Phase 4
  (§13 D4), which is also when `BUTTERFLY_INSTANCE_ROLE=paper` would be added.
- **Exit pricing.** The live service uses the config default `bid_ladder`. The mid_walk pilot
  stays ON HOLD. Enabling it later is one env line (`EXECUTION__EXIT_PRICING=mid_walk`) in a
  separate, owner-approved override, as the b06cdb7 template already does.

## 10. Pilot scripts v2

These live in the repo under `deploy/spx-live/` (new), copied per session to
`/opt/butterflyguy-releases/spx-live-<DATE>-<sha7>/`. Every script supports `DRY_RUN=1`, which
prints each docker/compose command instead of running it (tested in CI).

**`common.sh`**
- `DATE`, `D`, `REL` (release snapshot), `CAND` (live image digest).
- `LIVE=(docker compose --project-directory /opt/butterflyguy/infra -p butterfly-spx-live -f $REL/infra/docker-compose.spx-live.yml)`.
- `paper_fingerprint()`: `docker inspect -f '{{.Id}} {{.Image}} {{.State.StartedAt}} {{.RestartCount}} {{.State.Running}}' butterfly_spx_app`.
- `count '^butterfly_spx_app$'`, `count '^butterfly_spx_live_app$'` (running only).
- `live_db_check()`: runs `tools/spx_live_db.py check` in the release image with no token mount
  (`docker run --rm --network monitoring_net --env-file /opt/butterflyguy/.env -e
  DATABASE__NAME=butterfly_guy_spx_live $CAND python tools/spx_live_db.py check`). It prints
  JSON and exits 0 only when:
  - schema is at head (`schema_migrations` = the image's migration files and checksums);
  - 0 OPEN trades and 0 non-terminal intents;
  - 0 rows with `paper_fill_model`.
- `broker_flat()`: unchanged; `deploy_broker_flat_check.py` in `butterfly_spx_app`. It is
  read-only at the broker and checks all three underlyings, so the paper container is a valid
  place to run it.

**`activate.sh`** (06:35 PT, or by hand with Corey present). Gates, each aborting with paper untouched:
1. Date matches; no `ACTIVATED` marker.
2. Exactly 1 running `butterfly_spx_app`; its env has `DATABASE__NAME=butterfly_guy` and no
   `EXECUTION__PAPER_TRADING=false`. Record `P0=$(paper_fingerprint)`.
3. 0 running `butterfly_spx_live_app`.
4. `CAND` image present; `broker_flat`; `live_db_check`.
5. Token: host `stat -c '%i'` and `sha256sum` of `tokens.json` equal those seen inside
   `butterfly_spx_app`. I compare digests only and never print or copy the file.
6. `tools/spx_live_db.py seed-daily-bars` (collision 4).

Then `touch ACTIVATED` and
`SPX_LIVE_IMAGE=$CAND SPX_LIVE_TEST_DATE=$DATE "${LIVE[@]}" up -d --no-build --pull never app_spx_live`.

Verify at +120 s; any failure runs `stop_live` (never touches paper):
- image = `CAND`; running;
- env has `BUTTERFLY_INSTANCE_ROLE=live`, `DATABASE__NAME=butterfly_guy_spx_live`,
  `EXECUTION__PAPER_TRADING=false`, `EXECUTION__LIVE_TEST_DATE=$DATE`, and **every live limit
  equal to today's pilot values** (§11);
- mount source for `/app/data/chains` ends in `chains-live`;
- the token inode/digest inside the live container equals the host's;
- logs show `live_trading_starting` and no error/Traceback;
- `curl 127.0.0.1:8002/health` responds;
- counts are exactly 1 paper + 1 live;
- **`paper_fingerprint` == `P0`**.

**`closeout.sh`** (13:45 PT). If live is not running, exit. Otherwise:
1. export evidence with `report_spx_live_test.py` **in `butterfly_spx_live_app`**, so it reads
   the live DB only;
2. save `docker logs butterfly_spx_live_app`;
3. run the paired report (§12);
4. if `broker_flat && live_db_check`, run `stop_live`, else alert and leave it running (as today);
5. assert `paper_fingerprint` == `P0` and post the result.

**`stop_live` (the v2 rollback).** `"${LIVE[@]}" stop app_spx_live`. It never runs `rm`, so
the logs survive until the next activation, and it never mentions `app_spx`. It verifies 0
running live containers and an unchanged paper fingerprint.

**`notify.py`**: as today, plus a webhook-variable argument (§8 A).

**Every assumption from P0 §6, resolved:**

| P0 §6 | v2 |
|---|---|
| 1 one SPX container | 1 paper + 0→1 live, by exact names |
| 2 recreate `app_spx`, BASE_ID/IMG | never touches `app_spx`; fingerprint compared before/after |
| 3 inspect paper container | inspects live container |
| 4 broker check in paper container | kept (read-only, account-wide) |
| 5 `db_flat` on `butterfly_guy` | `live_db_check` on the live DB; paper's open trade is irrelevant |
| 6 evidence mixes paper rows | runs in the live container against the live DB |
| 7 rollback recreates paper | `stop_live` |
| 8 "pilot running" = paper image is CAND | live container running with image CAND |
| 9 shared webhook | live webhook (D6 A) |
| 10 per-date BASE_* edits | none: the paper fingerprint is captured at run time |

## 11. Compose for the live service (PR 2)

`infra/docker-compose.spx-live.yml` (abridged):

```yaml
name: butterfly-spx-live
networks:
  monitoring_net:
    external: true
services:
  app_spx_live:
    image: "${SPX_LIVE_IMAGE:?set reviewed immutable live image}"
    pull_policy: never
    container_name: butterfly_spx_live_app
    restart: "no"
    env_file: [../.env]
    command: [/bin/sh, -c, 'export LIVE_EXPECTED_SCHWAB_ACCOUNT_ID="$${SCHWAB_ACCOUNT_ID}"; exec python -m butterfly_guy.scripts.run_live --config configs/config.yaml']
    volumes:
      - "${SCHWAB_GATEWAY_TOKEN_DIR:?}:${SCHWAB_GATEWAY_TOKEN_DIR:?}"   # directory bind, as app_spx
      - ../configs/config.yaml:/app/configs/config.yaml
      - ../data/chains-live:/app/data/chains
    environment:
      BUTTERFLY_INSTANCE_ROLE: live
      SCHWAB_TOKEN_PATH: "${SCHWAB_GATEWAY_TOKEN_DIR:?}/tokens.json"
      DATABASE__HOST: timescaledb
      DATABASE__PORT: 5432
      DATABASE__NAME: butterfly_guy_spx_live
      DATABASE__USER: butterfly
      ALERTMANAGER_URL: http://alertmanager:9093
      DISCORD_WEBHOOK_URL: "${DISCORD_WEBHOOK_URL_SPX_LIVE:?}"     # D6 A
      # Live limits: identical to today's infra/docker-compose.spx-live-test.yml
      SCHWAB_ACCESS_MODE: direct
      SCHWAB_GATEWAY_SHADOW_READS: "false"
      EXECUTION__PAPER_TRADING: "false"
      EXECUTION__ALLOW_LIVE_TRADING: "true"
      ALLOW_LIVE_TRADING: "true"
      EXECUTION__LIVE_TEST_DATE: "${SPX_LIVE_TEST_DATE:?}"
      EXECUTION__LIVE_TEST_MAX_DEBIT: "4.0"
      EXECUTION__RECORD_LIVE_EXECUTION: "true"
      EXECUTION__LIVE_TEST_QUOTE_MAX_AGE_SECONDS: "10"
      RISK__MAX_POSITION_SIZE: "1"
      RISK__MAX_TRADES_PER_DAY: "1"
      LIVE_ACCOUNT_ALLOCATION: "20000"
      LIVE_MAX_ACCOUNT_DAILY_LOSS: "500"
    read_only: true
    tmpfs: [/tmp]
    security_opt: [no-new-privileges:true]
    cap_drop: [ALL]
    networks: [monitoring_net]
    ports: ["127.0.0.1:8002:8000"]
```

**`infra/docker-compose.spx-live-rehearsal.yml`** (applied last, Phase 3 only):
- `BUTTERFLY_INSTANCE_ROLE: live_rehearsal`, `EXECUTION__PAPER_TRADING: "true"`;
- `ALLOW_LIVE_TRADING` and `EXECUTION__ALLOW_LIVE_TRADING` `"false"`;
- `EXECUTION__LIVE_TEST_DATE: !reset null`, and the `LIVE_*` limits reset;
- `DATABASE__NAME: butterfly_guy_spx_live_rehearsal`;
- the volume `../data/chains-live-rehearsal:/app/data/chains`.

The rehearsal keeps the live webhook (D6 A), so routing is tested; its entry posts show `PAPER`.

**Validation (PR 2):**
- `docker compose config` for: base alone; base + `spx` profile; the live file; live + rehearsal.
- Diff the rendered `app_spx` before and after the PR: it must be identical, because the base
  file doesn't change.
- Diff the rendered live env against today's override: identical limits.

**DB tooling, `tools/spx_live_db.py`** (asyncpg, DSNs from config/env; run in the release image).
Each subcommand refuses when the target name is `butterfly_guy`.
- `bootstrap --db NAME [--copy-live-trade 415]` (idempotent):
  1. `CREATE DATABASE` if missing, via the `postgres` DB;
  2. run migrations;
  3. add compression settings and policies matching `butterfly_guy`;
  4. restart the sequences at 100000 (only if the table is empty);
  5. seed `daily_bars`;
  6. optionally copy 415 and its child rows.

  `butterfly_guy` is opened read-only (`SET default_transaction_read_only = on`).
- `seed-daily-bars --db NAME`: insert `$SPX`/`$VIX` bars newer than the target's latest.
- `check --db NAME`: the JSON gate in §10.
- `compare --date D`: the paired report (§12).

## 12. Paired comparison report

`tools/spx_live_db.py compare --date YYYY-MM-DD [--out DIR]` is read-only on both DBs and
writes Markdown + JSON. For each bot:

- **Entry:** time (PT), direction, strikes, width, VIX, RR; fill vs mark at entry (live: broker
  fill vs `entry_execution_diagnostics` mark; paper: fill = mark by convention); entry attempts.
- **Exit:** time (PT), reason, fill vs mark at the signal, ladder steps (live); `live_rule_estimate`
  on paper (PR #84).
- **P&L:** realized pre-fee and after fees (live: actual fees from intents/evidence; paper:
  $1.15/contract).
- **Flags:**
  - *one bot traded, the other didn't*, with each side's last `entry_blocked`/skip reason from
    `decision_log`;
  - *different fly*: shows both bots' top candidates at their selection minute from
    `butterfly_candidates`, with the RR gap. Near-tied flips are expected (memory: neighbor tie
    sets).
  - *different exit reason or time*, with the gap in minutes;
  - *live P&L minus paper P&L*, split into entry-fill, exit-fill and path differences.

It runs from the close-out and on demand. It reads no Schwab data.

## 13. Decisions for the owner

| # | Decision | Recommendation | Owner decision (2026-11-17) |
|---|---|---|---|
| D2 | Live DB history | **B**: copy trade 415 (+ intents and child rows); sequences start at 100000 | **Copy trade 415** (+ intents and child rows); sequences at 100000 |
| D2b | Trade 415 inside `butterfly_guy` | **(i) leave it** | Leave it (default, not separately asked) |
| D3 | Live snapshot retention | Keep all; compress after 7 days (paper's policies); live JSONL kept; review in 6 months | **Keep all, compress after 7 days** |
| D4 | `app_spx` env / image | At the next normal off-hours paper deploy, run the **same release** as live and add `BUTTERFLY_INSTANCE_ROLE=paper`; no separate recreate | **Yes**: same-release paper deploy with role=paper, normal off-hours deploy |
| D5 | Pool size | No change (worst case ≈ 42/50) | No change (default, not separately asked) |
| D6 | Discord | **A**: separate webhook `DISCORD_WEBHOOK_URL_SPX_LIVE` (Corey creates it and adds it to `.env`) | **Separate webhook** `DISCORD_WEBHOOK_URL_SPX_LIVE` |
| D6b | Grafana | Add datasource `TimescaleDB SPX Live` (uid `timescaledb-spx-live`, as the candidate precedent) plus a datasource variable on *Trade Detail*; add `job="butterfly_spx"` to SPX Prometheus panels | As recommended (default, not separately asked) |

## 14. Rollout and rollback

All Helios steps need explicit approval, one step at a time. Times are PT. Paper is never
recreated except in D4's normal deploy.

| Step | When | What (exact commands in the PR runbook section) | Rollback |
|---|---|---|---|
| 1. Merge PRs 1–4 | after review + CI | — | revert PRs |
| 2. Release snapshot + image | off-hours | Per `docs/live-runbook.md` Deploy §3: `git archive <sha>` → `/opt/butterflyguy/.releases/<sha7>-spx-live-XXXX`, `docker build -t butterflyguy:release-<sha7>`, record digest in `release.json`. **No container is started.** The checkout does **not** need a fast-forward: no config key changes (env only). | delete image tag (unused) |
| 3. Prometheus job | off-hours | backup `/opt/monitoring/prometheus.yml.pre-spx-live-<ts>`; add job; `docker kill -s HUP butterfly_prometheus`; check `/api/v1/targets` | restore backup + HUP |
| 4. Bootstrap rehearsal DB + dirs | off-hours | `mkdir data/chains-live-rehearsal`; `docker run --rm --network monitoring_net --env-file .env $CAND python tools/spx_live_db.py bootstrap --db butterfly_guy_spx_live_rehearsal` | leave (drop only with approval) |
| 5. Phase 3 rehearsal | one session, 06:25 PT start | `"${LIVE[@]}" -f …spx-live-rehearsal.yml up -d app_spx_live`; verify the §10 list; measure connections and Schwab rate; `compare`; `stop_live` after 13:15 PT | `stop_live` |
| 6. D4 paper deploy (if approved) | off-hours, flat | runbook Deploy §2–3 for `app_spx` with the new release + `BUTTERFLY_INSTANCE_ROLE=paper` | the step's `rollback.sh` (pinned previous digest) |
| 7. Bootstrap live DB | off-hours | `mkdir data/chains-live`; `bootstrap --db butterfly_guy_spx_live [--copy-live-trade 415]`; `check` | leave (drop only with approval) |
| 8. Grafana datasource (D6b) | off-hours | edit `/opt/monitoring/grafana/provisioning/datasources/datasources.yml` with backup; restart Grafana only | restore backup |
| 9. Phase 4 session | owner present | v2 `activate.sh` / `closeout.sh` | `stop_live` |

## 15. PR plan (Phase 2)

1. **Role guard + alert label.**
   - `core/instance_role.py`, called from `run_live.main()`;
   - `send_alertmanager(..., instance_role=None)`;
   - Telegram prefix (D6 A).
   - Tests per §6 and §8.
2. **Compose + DB tooling.** `infra/docker-compose.spx-live.yml`, the rehearsal override,
   `tools/spx_live_db.py` (`bootstrap`, `seed-daily-bars`, `check`), tests against Postgres, the
   compose-config validation, and the local two-instance rehearsal.
3. **Pilot scripts v2 + paired report.** `deploy/spx-live/*.sh` with `DRY_RUN`,
   `notify.py`, `spx_live_db.py compare`; tests.
4. **Grafana** (if D6b): job filters; Trade Detail datasource variable; provisioning snippet.

## 16. Downstream notes

- **Exit-ladder study:** its confirmation evidence (the supervised pilot) moves to
  `butterfly_guy_spx_live`. `report_spx_live_test.py` run in the live container reads it
  automatically. Any ad hoc SQL should target the live DB. Trade 415 stays readable in both
  DBs under D2 B.
- **Draft note for the monitor-cadence plan** (for that study's owner; not applied):
  > From the first concurrent session, live-pilot SPX trades are recorded in DB
  > `butterfly_guy_spx_live` (trade ids ≥ 100000), not `butterfly_guy`. Paper SPX trades remain
  > in `butterfly_guy`, so the §1 extraction (`underlying='SPX'`) now returns paper trades only,
  > which matches the qualifying set. Live trade 415 (2026-11-16) remains in `butterfly_guy` as a
  > `legacy` row and predates the set. Live trades, still reported separately, are read from the
  > live DB.
