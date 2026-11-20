# Implementation prompt: run paper SPX and the live SPX pilot at the same time

Written 2026-11-17. Paste everything below the line into a fresh Claude Code session at the
repository root.

---

## Goal

Make the paper SPX bot and the real-money SPX pilot able to run **side by side on Helios**,
so each live session can be compared trade-for-trade with paper on the same day. Today the
live pilot **replaces** the paper container for the day. This costs the paper record a
session and leaves no same-day comparison.

**This touches live trading infrastructure. A mistake can halt, mis-record or close a
real-money position.** Read `AGENTS.md` first and follow it. Work in phases. Each phase ends
at a **stop point: report to the owner (Corey) and wait**. Nothing is deployed to Helios,
and no live session runs, without explicit approval for that specific step.

| Phase | Content |
|---|---|
| 0 | Verification (read-only) |
| 1 | Design and decisions for the owner |
| 2 | Implementation in an isolated worktree, with tests |
| 3 | Rehearsal on Helios, paper only |
| 4 | First supervised concurrent session with the live pilot |

## Work in a separate area: do not disturb current work

Other work is in progress in this repository. Protect it:

- **Do not work in the main checkout.** It is on `research/direction-vix-oos` with many
  uncommitted and untracked files. Do not switch its branch, stash, reset, clean, or commit
  there.
- **Create a fresh worktree from `origin/main`:**
  ```
  git fetch origin
  git worktree add .worktrees/concurrent-paper-live -b feat/concurrent-paper-live origin/main
  ```
  Do all edits, tests and commits there. Each PR gets its own branch, cut from `origin/main`
  or stacked explicitly.
- **Hands off other worktrees and branches.** Do not modify anything under
  `.worktrees/monitor-cadence` (`research/monitor-cadence-exit`, a pre-registered study),
  `.worktrees/poll-interval-config`, the exit-pricing worktrees, or any other worktree.
  - The git stash stack is shared across worktrees and sessions. Never `git stash` / `pop`;
    use WIP commits.
- **Live pilot staging material is read-only input.** This means
  `reports/execution_audits/spx-live-test-*` (including `spx-live-test-template-b06cdb7`) and
  the main checkout's untracked `infra/docker-compose.spx-live-test.yml`.
  - Copy what you need into the worktree. Never edit the originals.
  - A mid_walk exit-pricing pilot is staged there **on hold**. Do not activate, rebuild or
    re-stage it.
- **Helios is read-only until Phase 3 approval.** Read-only means:
  - `ssh helios` reads: `docker ps`, `docker logs`, `psql` SELECTs, `df`, `free`.
  - Not allowed: recreating, restarting or stopping containers; editing files in
    `/opt/butterflyguy`; creating databases; running migrations; changing cron jobs.

## Hard constraints

- **Tokens:**
  - Never mint, refresh or re-authorize Schwab tokens.
  - Never restart or recreate an existing token consumer (SPX, NDX or XSP apps, gateway).
  - Never print, copy, commit or summarize `.env` or `tokens.json`.
  - A *new* container is a new consumer of the shared token directory. Confirm it only
    reads the file and refreshes access tokens the way existing consumers do. Before it
    starts, verify the host and container see the same inode and digest.
- **Live safety.** Do not change any of the following, except where this brief says so and
  the owner approves:
  - trading limits, account guards, `LIVE_*` limits, max debit, allocation, daily loss;
  - order routing or exit pricing;
  - paper/live mode;
  - NDX/XSP behavior.
- **Defaults reproduce today.** With no new settings, a single `app_spx` must behave
  exactly as it does now. New behavior is opt-in.
- **Configs are bind-mounted from the Helios checkout** and models use `extra="forbid"`. A
  new YAML key breaks every older image that reads that file. Prefer new settings through
  environment variables, or ensure every image reading a config understands a key before
  adding it.
- **Rate load:** count Schwab requests before adding any.
- **Times:** Pacific when talking to the owner; the DB and crontab are UTC.
- **No forward tests, shadows, cron jobs or timers beyond what this brief specifies.**
- **Merge only with the owner's approval.**

## Background (verified 2026-11-17 on `origin/main` and Helios; re-verify in Phase 0)

### How the live pilot runs today

- **Activation** (`reports/execution_audits/spx-live-test-2026-11-17/activate-auto.sh:49-72`,
  `common.sh:9-36`):
  - runs `docker compose -p infra -f infra/docker-compose.yml`, the release-image override,
    and `infra/docker-compose.spx-live-test.yml`, then `up -d --no-deps app_spx`;
  - this **recreates the same service and container** `butterfly_spx_app`;
  - it checks "exactly one SPX container".
- **Rollback** recreates `app_spx` as paper. **Close-out** runs
  `docker exec butterfly_spx_app`.
- **The override sets:**
  - `EXECUTION__PAPER_TRADING=false`, `ALLOW_LIVE_TRADING`;
  - `LIVE_EXPECTED_SCHWAB_ACCOUNT_ID`, `LIVE_TEST_DATE`, `LIVE_TEST_MAX_DEBIT=4.0`;
  - `RISK__MAX_POSITION_SIZE=1`, `RISK__MAX_TRADES_PER_DAY=1`;
  - `LIVE_ACCOUNT_ALLOCATION`, `LIVE_MAX_ACCOUNT_DAILY_LOSS`;
  - `restart: "no"`, and a pinned image.

  It mounts the same `configs/config.yaml`.

### Why the two can't share a database

Both bots would use DB `butterfly_guy` (`infra/docker-compose.yml`, `DATABASE__NAME`). No
table has a paper/live or instance column. The only marker is
`metadata.paper_fill_model='mark_v1'` on paper fills (`order_manager.py:~464`).

**Hard blocks:**

- **One open trade per day:** unique index `butterfly_trades (underlying, trade_date) WHERE
  status='OPEN'` (`migrations/008_one_open_trade_per_underlying_day.sql`, checked). The
  first bot to enter blocks the other.
- **One active entry intent per day:** `broker_order_intents` allows one active ENTRY intent
  per `(underlying, trade_date)` (`migrations/009_...`).
- **Shared daily risk state:** `daily_risk_state` is keyed `(trade_date, underlying)`
  (`queries.py:~570-618`). Trade count, realized P&L and the halt flag are shared. A paper
  loss could halt live, and a paper trade uses up live's one trade a day.
- **History-wide risk checks:** weekly P&L and consecutive-loss checks read every SPX trade
  (`queries.py:~621-653`). **Inference to verify:** today's live pilot may already count
  paper history in these checks.
- **Startup takeover:** `run_live.py:1196-1217` calls `get_open_trades(underlying)` and
  adopts `open_rows[0]` regardless of mode (checked). A restarted paper bot could adopt the
  live trade.
- **Live reconciliation:** at startup and every 15 s (`run_live.py:~413-633, 693`), live
  compares all OPEN SPX rows with the broker. A paper row reads as "DB has OPEN SPX trade(s)
  but broker is flat". That stops the bot at startup, or marks broker state unsafe and
  blocks entries.
- **Shared reporting:** the EOD chart loop (`run_live.py:~1371`,
  `position_service.py:~1405`) and most Grafana panels select by `underlying` only.

### The live bot needs its own collector

- Before a **live** entry, `TradeService._live_chain_snapshot_fresh`
  (`trade_service.py:778-815`, checked) requires a recent chain snapshot in **its own DB**,
  via `chain_queries.get_latest_snapshot_time`. Paper skips the check.
- There is no setting to disable the collector (`run_live.py:~1311`; `config.yaml:88`
  `snapshot_interval_seconds: 60`).
- So whichever DB the live bot uses must receive collector snapshots.

### Where the two bots don't interact

- **Broker:** the paper bot never places orders or reads positions.
  - Fills are at the mark (`order_manager.py:~633, 768`).
  - Reconciliation and the operator-close check are live only.
  - Every client does resolve the account hash once (`schwab_client.py:~125`).
- **Live account guards** look at all SPX option positions in the account
  (`order_manager.py:~554-576`). Paper has none, so paper can't trip them.

### Other collisions

- `container_name: butterfly_spx_app`.
- Host port `127.0.0.1:8000`. Prometheus scrapes only `app_spx:8000` (`prometheus.yml:12`)
  with `underlying=SPX` labels.
- Both bots would use the same `DISCORD_WEBHOOK_URL`.

### Capacity on Helios (2026-11-17)

- **CPU and memory:** 2 cores, load ~0.5. 7.8 GB RAM with 5.5 GB available. SPX app ~180 MB.
- **Disk:** 18 GB free (82% used). DB `butterfly_guy` is 9.9 GB:
  - `option_chain_snapshots` 7.0 GB
  - `monitoring_leg_quotes` 1.45 GB (all bots since June)
- **DB connections:** cap is **50** (compose flag). About 30 were in use at 09:50 PT, 12 of
  them from `butterfly_guy`. The app pool is `min_size=2, max_size=10`
  (`db/connection.py:38-39`).
- **Schwab load, 11-16:** SPX pilot ~40 req/min plus gateway ~17/min. A second SPX bot adds
  about 23 chain/min for its monitor, plus collector requests. Schwab's limit is not
  documented in the repo.

### Precedent

A legacy SPX candidate fleet ran separate DBs: `butterfly_guy_spx_candidate_*`, a
`spx_candidate_feed`, and evaluators with no token mount. See
`docs/archive/schwab-gateway/CODEX_STATE.md` (~lines 944-1930) and
`docs/ai/BRANCH_REVIEW_INTEGRATION_PLAN.md:241`. Learn from it; don't revive it.

## Phase 0: verify (read-only)

1. **Re-verify every Background claim** with file:line on `origin/main`, and on Helios
   (`ssh helios`; `uv` is at `/home/billy/.local/bin/uv`).
2. **Query inventory.** Grep every SQL statement and query helper that touches these
   tables:
   - `butterfly_trades`, `broker_order_intents`, `daily_risk_state`;
   - `monitoring_leg_quotes`, `post_exit_leg_quotes`, `decision_log`, `butterfly_candidates`;
   - `option_chain_snapshots` and any VIX/spot snapshot tables.

   For each, record:
   - who calls it: live, paper, both, reporting, Grafana, or research;
   - whether it filters by mode;
   - what goes wrong if the other bot's rows are present.

   This table is the core deliverable of Phase 0.
3. **Entry dependencies on DB data.** List every DB read on the entry and exit paths: chain
   freshness, VIX, gap, candidates, prior-day data, risk state. Say which ones a fresh live
   DB would satisfy, and which need history (for example weekly P&L, consecutive losses,
   prior close).
4. **Risk checks today.** Do the live pilot's weekly and consecutive-loss checks currently
   count paper trades? Show the query and today's effect. This is a finding in its own right.
5. **Collector load and storage.** Measure the collector's requests per minute and the SPX
   snapshot rows and bytes per session from the DB. Measure the monitor's request rate on
   paper and live from logs.
6. **Pilot scripts.** Read the activation, close-out, rollback and notify scripts in
   `reports/execution_audits/spx-live-test-template-b06cdb7/` and `spx-live-test-2026-11-17/`.
   List every assumption that there is a single SPX container or DB.
7. **Consumers of `butterfly_guy` SPX rows:**
   - Grafana dashboards;
   - the EOD Discord chart and weekend review;
   - daily reports and the `cron_guard` jobs;
   - research extractions (the monitor-cadence study's SQL is in
     `docs/research/monitor-cadence-exit-design-plan.md` section 1; read it on branch
     `research/monitor-cadence-exit`, don't edit it);
   - the exit-pricing study.
8. **Helios state:** the current release, image and checkout commit; a Prometheus scrape
   config snippet; Discord webhook *names* only, never values.

**Stop point 0:** report:
- facts and corrections;
- the query inventory;
- the entry-dependency list;
- the risk-check finding;
- load and storage numbers;
- the script assumptions.

Wait.

## Phase 1: design and decisions (write `docs/operations/concurrent-paper-live-spx-design.md`)

The recommended direction is **separate databases**, so that no query can see the other
bot's rows. Adding a mode column instead means every missed filter becomes a live-safety
bug. Argue against the recommendation if Phase 0 shows it is wrong.

Decide and justify each point:

1. **Which bot keeps `app_spx` / `butterfly_spx_app` / DB `butterfly_guy`?**
   - The recommendation is that **paper stays exactly where it is.** That keeps:
     - its history and Grafana;
     - the research extractions;
     - the monitor-cadence study's qualifying set ("paper SPX trades");
     - collector continuity.
   - **Live becomes a new service**, e.g. `app_spx_live` / `butterfly_spx_live_app` with DB
     `butterfly_guy_spx_live`, started only on pilot days with `restart: "no"`.
2. **The live DB's contents.** It needs schema from migrations, its own collector (required
   by the freshness gate), and any history the risk checks need.
   - Decide whether to copy prior live trades (415 and earlier pilot trades) so that weekly
     and consecutive-loss checks see real-money history only.
   - Show what those checks would compute on day one under each choice.
   - The owner decides.
3. **The collector on the live bot.** The default is to keep it on: the freshness gate
   needs it. State the extra requests per minute and the storage per session, and propose a
   retention policy for the live DB's snapshots.
   - A "read snapshots from the paper DB" option counts only if it keeps the freshness gate
     equally strict, and needs its own approval.
4. **Instance role guard (new, opt-in).** An env var such as `BUTTERFLY_INSTANCE_ROLE=
   paper|live`, unset by default. When set, startup refuses to run if:
   - role=paper and `paper_trading` is false;
   - role=live and `paper_trading` is true;
   - role=live and `DATABASE__NAME` equals the paper DB name;
   - role=live and the live DB contains any OPEN trade carrying `paper_fill_model`.

   It must fail closed, before any Schwab or DB write.
5. **Connections:**
   - Pool sizes per bot, and the peak total against the cap of 50.
   - Consider a smaller pool for the live bot.
   - Do not raise `max_connections` without owner approval; it means recreating
     TimescaleDB, a separate high-impact change.
6. **Metrics and alerts:**
   - a separate port (e.g. `127.0.0.1:8001`) and Prometheus job;
   - an instance label;
   - alert rules that don't mix the two bots;
   - a separate Discord webhook or a `[LIVE]`/`[PAPER]` prefix.

   The owner chooses.
7. **Pilot scripts v2.**
   - **Activation** starts only `app_spx_live`. Then:
     - assert exactly one paper SPX container and one live container;
     - assert paper is still paper and untouched (same container ID and start time before
       and after);
     - assert the live DB schema is at head.
   - **Close-out** targets the live container only.
   - **Rollback** stops `app_spx_live` and never recreates `app_spx`.
8. **Comparison report.** Define the same-day paired comparison: entry time, strikes, fill
   vs mark, exit time and reason, realized P&L. Flag any day the two bots chose different
   flies; entry-selection flips between near-tied candidates are known to happen. This is a
   read-only report over both DBs.
9. **Rollout plan and rollback** for each step, with the exact commands, following the
   `docs/live-runbook.md` "Deploy" procedure (release snapshot + pinned-image override). The
   latest example is `.rollbacks/spx-a283610-20261116/` on Helios.
10. **Downstream updates:**
    - Grafana datasource or dashboard changes for the live DB;
    - the exit-pricing study's data source;
    - a note for the monitor-cadence plan saying live trades now sit in their own DB. Draft
      it only; that study's owner decides whether to amend.

**Stop point 1:** the owner approves the design and makes the open decisions (2, 3, 6).

## Phase 2: implementation (isolated worktree, small PRs)

Suggested PR split; adjust to the approved design.

1. **Instance role guard, plus any env-only settings** (pool size if approved). Unit tests:
   - every refusal case;
   - no effect when unset;
   - the guard runs before Schwab init and before any DB write.
2. **Compose:** an `app_spx_live` service, behind a compose profile so a plain `up` never
   starts it. Requirements:
   - own container name, port, `DATABASE__NAME`, `BUTTERFLY_INSTANCE_ROLE=live`;
   - `restart: "no"`;
   - same hardening as `app_spx`: `read_only`, `cap_drop`, `no-new-privileges`, and the
     token *directory* bind;
   - `app_spx` gets `BUTTERFLY_INSTANCE_ROLE=paper`, only if the owner approves changing
     its env;
   - Prometheus job and labels;
   - a DB bootstrap script (create DB, run migrations), idempotent and never touching
     `butterfly_guy`.

   Validate with `docker compose config` for each file combination, and diff the rendered
   config of `app_spx` before and after: it must be unchanged except for approved lines.
3. **Pilot scripts v2** and the comparison report. Tests or dry-run modes that print the
   exact compose commands without executing them.
4. **Grafana and reporting changes**, if approved.

**Verification required for every PR:**

- Focused tests, `uv run pytest` (full suite), `uv run ruff check .`, and CI green
  (`validate` and `timescaledb`).
- **Local two-instance rehearsal** on this machine, never Helios:
  - start a throwaway TimescaleDB container with two scratch databases;
  - run both app configs **in paper mode** with `BUTTERFLY_INSTANCE_ROLE` set and **no
    Schwab tokens**, or a market-closed path that makes no Schwab calls;
  - show that migrations apply to each DB separately;
  - show that the guard refuses each misconfiguration;
  - show that rows land only in their own DB.
  - Do not mount the real token directory locally.
- **Live-DB guard tests against the real queries.** Seed the live DB with a paper-looking
  OPEN row and show startup refuses. Seed `butterfly_guy` with an OPEN paper trade and show
  the live bot's reconciliation, risk state and startup recovery never see it.
- **PR descriptions cover:** what, why, risk, rollback, and the request-load and connection
  arithmetic.

**Stop point 2:** PRs reviewed and green. The owner approves merging, then approves Phase 3.

## Phase 3: Helios rehearsal, paper only (needs explicit approval)

- **Preconditions.** Same rules as any SPX deploy:
  - market closed, or no open SPX trade and no non-terminal intents;
  - broker flat check passes;
  - release snapshot, pinned image and rollback directory prepared.
- **Fast-forward the Helios checkout** only to a commit whose configs every running image
  accepts (see the config-drift memory notes in AGENTS.md / the runbook).
- **Create `butterfly_guy_spx_live`** and run migrations on it alone.
- **Run `app_spx_live` for one session in paper mode** (`BUTTERFLY_INSTANCE_ROLE=live`, but
  `paper_trading=true`, so the live-role guard needs a documented, temporary rehearsal
  override). Alternatively, rehearse with a separate role value; decide in Phase 1.

  Verify:
  - `app_spx` untouched: same container ID, start time and image;
  - both bots trade into their own DBs;
  - no cross-DB rows;
  - the collector writes to both;
  - connections stay under the cap at peak;
  - Schwab request rate is measured and reported;
  - no token file changes beyond normal access-token refreshes;
  - metrics and alerts are separated;
  - the comparison report runs.
- **Stop the rehearsal container afterwards** and report.

**Stop point 3:** report the rehearsal. The owner decides whether to schedule a live session.

## Phase 4: first supervised concurrent live session (only when the owner schedules it)

- Use the v2 activation with the owner's chosen live limits, unchanged from the current
  pilot unless the owner says otherwise. The owner is present.
- Watch the first entry, any exit, close-out and rollback.
- Afterwards, produce the paired comparison and report any divergence or incident.
- **State the risk to the owner before activation:** this places real orders.

## Reporting

At every stop point, report in Pacific time:
- what was verified;
- what changed and where (worktree, branch, commit);
- what is still unverified;
- the exact next step that needs approval.

Never claim a step ran or passed without its output. Record durable decisions in the design
doc, not only in chat.
