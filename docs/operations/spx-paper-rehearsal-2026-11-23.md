# SPX paper rehearsal and verification on November 23 2026

As of 08:49 PT / 16:49 UTC, the SPX rehearsal completed a simulated entry and
induced exit, recovered its position monitor across restarts, and received Discord
acceptance for the exit notification. Verification covered six areas: 230 checks
passed and two regression probes failed, confirming unresolved defects. These
counts include repeated baseline cases; the packet contains 196 unique test cases.
Actual end-of-session close-out remained pending at this checkpoint.

**Corey's authorization for this session was paper simulation only. No live trades
were authorized or submitted.** The manually opened broker butterfly remained
under Corey's control and was not adopted or modified by the rehearsal. This
record does not authorize a future live session or deployment.

## Evidence and release identity

- [Verification manifest](../../data/rehearsals/SPX/2026-11-23/verification-20261123T1640Z/verification-manifest.json):
  results by scenario, source hashes, safeguards, limitations, and artifact hashes.
- [Confirmed findings](../../data/rehearsals/SPX/2026-11-23/verification-20261123T1640Z/findings.json).
- [Reproduction probes](../../data/rehearsals/SPX/2026-11-23/verification-20261123T1640Z/reproduction-probes.tar.gz):
  isolated probes and the runner that disables real Python network connections.
- [Latest local market capture](../../data/rehearsals/SPX/2026-11-23/capture-20261123T164731Z/manifest.json):
  40,014 chain rows, 432 held-position leg rows, 2,631 post-exit leg rows,
  spot observations, decisions, trade/risk ledgers, and sanitized runtime logs.
  These are point-in-time counts; the remote recorder continued collecting.

Local checkout: `b3150ad75fdc01a7080e6bad42b9445bbc4c3a89`.
Runtime release: `4a3c3515637a0d5346c49d640d386da3e678c27d`; its Python source
matches the checkout. Image:
`sha256:6da41417101b27cd429dffb55b1768da0fbf2259c656d2cc2acf0594721c6739`.
No application source changes were deployed during verification.

The local evidence directory is currently untracked Git content. The operations
record and index addition are also uncommitted; nothing was pushed.

## Why the prepared test did not start

The original November 23 plan used `OBSERVE=1`: run live startup reconciliation,
broker reconciliation, collection, health, and alerting with every entry blocked.
It did not exercise order submission or exit fills. The 06:35 PT activation
attempt aborted because `butterfly_guy_spx_live` lacked
`013_account_monitor.sql`. Later, Corey's manual SPX position would also prevent
the normal live flatness/reconciliation gates from passing.

The authorized workaround was the existing paper rehearsal on
`butterfly_spx_live_app`, role `live_rehearsal`, database
`butterfly_guy_spx_live_rehearsal`, port 8002, beside the unchanged regular paper
SPX container. Both live-allow flags were false and paper trading was true.
Migration 013 was applied only to the rehearsal database after backing it up.
The real-money live database was not migrated or changed to make its gates pass.

## Paper trade and induced events

Trade `100001` was one SPX call butterfly: long 7320, short two 7360, long 7400,
expiring November 23. The paper entry occurred at 08:00:29 PT / 16:00:29 UTC.
The observed entry mark was about 3.70 and recorded fill was 3.75.

Three changes affected only the separate rehearsal configuration for this date:

1. Extended the entry cutoff from 07:45 to 08:30 PT.
2. Widened center tolerance from 15 to 100 points to obtain an otherwise valid
   candidate. The one-trade limit and cost/risk limits were retained.
3. Changed `profit_management.exit_before_close_minutes` from 0 to 300 to induce
   the normal `end_of_day` exit path early. This was a mechanics test, not a
   naturally triggered profit exit.

The exit occurred at 08:07:29 PT / 16:07:29 UTC. Signal mark was 3.43, paper fill
3.38, and the closed trade and daily-risk ledger both recorded a $37 loss.
`mark_v1` embeds modeled commissions in the fill prices: four contracts at $1.15
per side produce 0.046 option points per side before two-decimal rounding.
Do not subtract those commissions again. Configured slippage is diagnostic-only
in this model. The entry/exit adjustments here were commissions and rounding,
not simulated slippage.

A quoting error in the temporary launcher initially prevented the entry Discord
post. It was corrected before the exit. A diagnostic wrapper around the existing
Discord transport recorded `rehearsal_discord_receipt`, `kind=exit`,
`accepted=true` at 16:07:29.524 UTC. This proves HTTP acceptance, not that a human
read the notification. The wrapper did not manufacture an exit message or change
the transport's return value.

The normal on-disk rehearsal config was restored after the exit. The existing
process retained its loaded test settings until stopped; its one-trade limit
blocked further entries. Its launcher selects the separate config only on
November 23, and post-exit quote recording continued without a further restart.

## Verification results

1. **Exit-alert failure handling — defect confirmed.** An isolated rejection
   reached `PositionService.monitor_loop`: the trade closed once, one notification
   attempt occurred, and `exit_secondary_work_pending` was set false despite failed
   delivery. No duplicate exit was submitted. See `01-alert-delivery.xml`.
2. **Profit exits — simulation passed.** Replaying 845 actual observations through
   unchanged profit rules produced no natural trailing exit. A separately labeled
   synthetic mark path triggered `drawdown_morning` and reached a paper fill with
   no broker submission. See `02-observed-market-replay.json`,
   `02-induced-profit-exit.json`, and the profit-exit JUnit files.
3. **Quote outages — simulation passed.** Removing each of the three actual SPX
   leg quotes prevented valuation, degraded readiness, and recorded an outage.
   Restoring complete quotes recovered readiness. Isolated stale-quote,
   prolonged-outage, warning-rate-limit, and entry-freshness tests also passed.
   See `03-quote-outages.xml`, `03-entry-freshness.xml`, and the missing-leg traces.
4. **Manual takeover — isolated fixtures passed.** Both an operator working order
   and an operator cancellation/edit of a bot order persisted ownership across
   restart. The simulated bot did not resume exits after the operator order was
   canceled and adopted the eventual manual fill once. No actual manual trade was
   read or changed by these fixtures. See `04-manual-takeover.xml` and its traces.
5. **Settlement/accounting — one-lot checks passed; quantity defect confirmed.**
   Today's fills reconciled to the configured commission model and risk ledger.
   A hypothetical intrinsic-value grid for the actual SPX strikes passed, as did
   isolated settlement, missing-close, true-up, and dollar-conversion cases.
   A two-lot paper probe exposed incorrect fee scaling. Actual official closing
   data was not available yet. See `05-settlement-accounting.xml` and its traces.
6. **Close-out — isolated tests passed; actual session outcome pending.** Tests
   covered export/stop when flat, refusing unsafe stops, retaining health after a
   failed stop, task cleanup, and post-exit recording. The running rehearsal
   remained healthy and the regular paper container fingerprint was unchanged.
   See `06-closeout.xml`.

Network guards reported zero attempted real Python network connections during
the isolated suites. Broker interactions in manual-takeover and incident tests
were fixtures. This does not establish live broker fill, cancellation, partial
fill, or rejection behavior. The induced entry and exit are not strategy-return
evidence.

## Unresolved defects and next implementation work

**Exit alert delivery can be forgotten.**
[`DiscordNotifier.notify_exit`](../../src/butterfly_guy/services/notifier.py)
discards the transport's failure result, and
[`PositionService`](../../src/butterfly_guy/services/position_service.py) can clear
notification work afterward. The persisted pending flag also has no retry
consumer in the current source. Fix acceptance-aware delivery and restart-safe
retry without ever resubmitting a filled exit. Test rejection, timeout, recovery,
restart, and duplicate-delivery boundaries. At-least-once delivery may produce
duplicates after an acknowledgment is lost; do not claim exactly-once delivery.

**Multi-lot paper commission scales twice.**
[`OrderManager._commission`](../../src/butterfly_guy/execution/order_manager.py)
scales the fee with quantity before adding/subtracting it inside the per-spread
fill price; later P&L is multiplied by quantity again. At mark 3.43, one lot
received a per-spread paper exit fill of 3.38, while two lots received 3.34.
Fix and verify per-spread versus aggregate fee units for both entry and exit.
The running quantity-one limit was never increased, and today's ledger was
unaffected by this defect.

Both defects are reproduced but unfixed. The archived probes import helpers from
this checkout's `tests/` directory. To rerun them, extract to a scratch directory,
run from the repository root, and direct their `OUT` constants and JUnit outputs
to a new directory rather than overwriting this evidence. Preserve the Python
network guard and use no real broker credentials or order APIs.

## Helios handoff and pending end of day evidence

Host: `billy@helios`.
Session scripts: `/opt/butterflyguy-releases/spx-live-20261123-fe051d6/`.
Test working directory beneath that session:
`paper-entry-20261123T075056/`.
It contains `entry-window-effective.json`, the date-specific config, original
launcher/config copies, induced-event records, capture scripts, and timestamped
`capture-*` directories. The earlier `rehearsal-20261123T154753Z/` directory holds
the pre-migration rehearsal DB dump and the stopped-container baseline.

Scheduled for November 23 only:

- **13:10 PT / 21:10 UTC:** `spx-rehearsal-evidence-20261123.timer` exports a fresh
  full-session snapshot after market close.
- **13:15 PT / 21:15 UTC:** existing `spx-live-closeout-20261123.timer` invokes the
  guarded rehearsal close-out. It stops only when the applicable gates pass.
- **13:20 PT / 21:20 UTC:** `spx-rehearsal-postclose-audit-20261123.timer` captures
  the ledger, quotes, logs, and deliberate-stop status. It tolerates the expected
  stopped HTTP endpoint and does not place orders or stop services itself.

On resumption, inspect those timer/service results and the newest remote
`capture-*/manifest.json` and `capture-*/session-status.json`.
`deliberate_closeout_verified=true` requires the session's `STOPPED` marker, a
stopped container, and the recorded test trade closed. A failed gate must remain
visible; do not force a stop or enable live trading to make a test pass. Copy the
new snapshots into `data/rehearsals/SPX/2026-11-23/`, verify their manifest hashes,
and append the actual end-of-day outcome here. The scheduled exports stay on
Helios until explicitly copied; they do not update this local record themselves.

## Readiness investigation follow-up: November 23, still intraday

This section supersedes the earlier **unfixed** classifications for the local
candidate only. The running image has not changed. See the
[deployment/migration/rollback plan](spx-readiness-deployment-2026-11-23.md) and
[new evidence packet](../../data/rehearsals/SPX/2026-11-23/readiness-fixes-20261123/).
The assessment remains **NO-GO for a supervised real-money canary**. The market
session was still open during this investigation; actual close-out remains pending.
No orders were submitted, replaced, canceled, adopted or managed at the broker.
No runtime was restarted/deployed and no production migration was applied.

### Reproduction and local fixes

The archived probes were extracted under `/tmp`, with every `OUT` redirected to
fresh scratch directories. Their original packet's 28 artifact hashes still
match. Before changes, the current source reproduced both failures (2 failed,
9 passed): rejected alert marked complete and quantity-two exit at 3.34 rather
than the one-lot 3.38. Before/after artifacts are retained separately in the new
packet. The original inline-alert probe's one-immediate-attempt expectation is
superseded by the independent delivery worker; its failure is not relabeled a pass.

`TradeQueries.close_trade()` now atomically adds `exit_notification_status=pending`
and the instance role to the guarded OPEN→CLOSED update. `ExitNotifications`, an
independent supervised task in `run_live`, consumes CLOSED rows even outside market
hours and after restart. It also recognizes legacy CLOSED rows with
`exit_secondary_work_pending=true` and no notification status. It reconstructs
prices, P&L, quantity, peak, entry/exit timestamps and manual-fill context from the
persisted trade. Retries run while the owning process is running; a deliberately stopped session
retains its backlog until its next authorized start. Do not keep/restart a trading
service just to deliver an alert: supervision must track outstanding receipts.
The original secondary-work flag continues to describe monitor
bookkeeping/audit work; clearing it no longer clears notification work. The worker
does not replay accounting or hide a persisted secondary-work error.

Discord rejection, rate limiting and timeout are failures. Only transport return
`True` records `sent`. Retry is once per minute, with a persisted retry deadline.
One transaction locks the selected closed row with `FOR UPDATE SKIP LOCKED`
through its bounded request and receipt update, so competing workers skip it.
The HTTP request has a 10-second total timeout and the worker adds a 15-second
outer delivery deadline. Shutdown cancellation releases ownership. Position
monitoring does not await exit HTTP delivery. No exit-order, risk or metrics APIs
exist on the retry worker. A lost HTTP acknowledgment or receipt commit can
produce a duplicate message: **delivery is at least once, not exactly once**.

SPX paper uses the paper webhook. Declared live/rehearsal roles and standalone
live mode require the dedicated live webhook, with no paper-channel fallback.
The persisted role prevents another declared role consuming its messages; legacy
untagged rows rely on the existing isolated-DB/role startup guards. Exit messages
include the declared role and original execution time. Missing configuration
remains `pending/unconfigured`; intentional asset-level disabling (NDX/XSP) is
recorded as `disabled`, never as accepted delivery. Transport exception details
are redacted for these sends; no URLs, tokens or account identifiers are logged.

The paper fee is now `.046` **option points per spread per side**, independent of
quantity: four contracts × $1.15 / 100. Hand-calculated one-, two- and three-lot
entry/exit tests all produce per-spread fills **3.75 / 3.38**, preserving one-lot
`mark_v1` rounding. Their aggregate dollar P&Ls are **-$37 / -$74 / -$111**.
Raw aggregate modeled fees per side are $4.60 / $9.20 / $13.80; two-decimal fill
rounding embeds $5 / $10 / $15 per side for this example. Fees are already in
fills and must not be subtracted again. Quantity remains in the persisted trade;
position/risk/metric/notification dollars multiply per-spread P&L by 100 × quantity
once. Slippage remains diagnostic-only, and intrinsic cash settlement gains no
modeled exit commission. Runtime quantity limits were not changed.

### Additional verification and evidence limits

Focused PostgreSQL tests use new UUID-named databases on local disposable
TimescaleDB instances, never the live, rehearsal or regular paper DBs. They cover
failure→acceptance, restart from persisted work, successful receipt suppression,
concurrent ownership, timeouts, legacy pending rows, missing/disabled configuration,
manual/cash-settled message reconstruction and role isolation. Lost acknowledgments
and receipt-write failure deliberately demonstrate duplicate-delivery boundaries.
A monitor-to-real-DB test at quantities 1/2/3 verifies exactly one exit submission
fixture and one risk update despite failed then successful notification delivery.

Useful archived probes are now repository regressions in
`tests/test_spx_rehearsal_regressions.py`: each held leg missing/recovery, operator
ownership through two restarts and order cancellation, and intrinsic payoff on the
actual strikes. Its three input quote rows have recorded provenance in the fixture.
All operator actions use isolated broker fixtures; none targeted Corey's position.
Existing persistence-failure/repeated-ownership-warning tests remain in place.

Replaying **2,489** recorded held/post-exit mark observations through unchanged
normal baseline profit rules produced **58 repeated `drawdown_late_morning`
evaluations**, first at 17:47:52 UTC, peak 3.98 and mark 0.37. This is a
**counterfactual hold-through replay** of observed quotes after the actual trade
had already closed at 16:07; it is not 58 trades, an observed bot profit exit, or
profitability evidence. The archived sensitivity replay supplies a running maximum
peak directly; full-monitor peak acceptance/confirmation and restart-state tests
are separate checks. A distinct, labeled synthetic 3.75→7.50→12→4.50 path triggers
`drawdown_morning` and an isolated paper fill. Neither changes baseline rules.

Missing/incomplete/stale/unavailable quote checks retain degraded readiness,
rate-limited warning, recovery and no-valuation/no-exit behavior. The recorded
three-leg removal probe applies to **SPX direct data**. Gateway forced recovery
and its quiet-window behavior are **paper XSP-specific**; they are not evidence
that direct SPX uses the gateway recovery path. Profit peaks/confirmation state,
manual takeover persistence, settlement final-bar requirements, provisional
settlement, broker true-up, early closes and calendar boundaries are covered by
the shared suites. Hypothetical closing spots remain explicitly synthetic. No
official November 23 closing/settlement value was available during this review.
The rehearsal trade had already exited, so it does not provide an actual
expiration/true-up example.

### Read-only runtime, broker and schema observations

A fresh [17:54:37 UTC capture](../../data/rehearsals/SPX/2026-11-23/capture-20261123T175437Z/manifest.json)
was copied from Helios into a new local directory. All 13 file hashes match.
Trade **100001 remains CLOSED**, one lot, entry 3.75 / exit 3.38, **-$37**, matching
the day's risk row (trade count 1). It contains 87,048 chain rows, 432 held-leg rows
and 7,035 post-exit-leg rows. The latter form 2,345 complete three-leg observations,
16:07:30–17:54:36 UTC, largest interval 6.224491 seconds; two gaps exceed five
seconds and none exceed ten. Held observations have two gaps over ten seconds,
maximum 10.767226 seconds. This is partial-session coverage, not a complete-close
export. See `capture-reconciliation.json` for exact ranges and counts.

The extended read-only account audit found **zero nonzero account positions,
zero active orders and zero unknown/missing order-status nodes** at its recorded
observation time. Order history spans September 25–November 23; SPX nodes include
3 canceled, 11 filled and 9 historical replaced statuses. Bot ownership was
matched against live intents in memory; identifiers were not exported. There was
no manual position remaining to attribute at that snapshot. This does not turn a
flat paper DB into brokerage-flat proof, establish earlier manual trade ownership,
or replace reconciliation immediately before a future activation. The shared
paper DB's open simulated NDX trade is not a live broker position.

The 18:14:51 UTC ledger audit also found no unresolved intents, unlinked filled
entries or provisional settlements in either dedicated DB. November 19 live P&L
reconciles at -$379.79; November 23 rehearsal P&L reconciles at -$37. The November
16 live history has -$70 with no historical daily-risk row. This is the documented
bootstrap copy of trade 415: `copy_live_trade()` copies trade/intents/quotes/decisions,
not shared paper daily risk. Its economic fields match the original shared-DB
trade, as recorded in `history-copy-audit.json`; it is an explained seed-history
difference, not a new missing close or a reason to manufacture a risk row. No
trading records were edited.

The live DB still ends at **012**; all installed checksums match the intended
release. Public columns/indexes match a fresh 001–012 database. Only migration
**013_account_monitor.sql** is missing. Rehearsal 001–013 matches completely.
The shared paper DB has unrelated tables and extra indexes, preserved untouched.
A scratch 012→013 migration and full logical dump/restore passed on PG16.11 /
TimescaleDB **2.25.2**, matching the deployed extension. The tested scratch dump
has no populated/compressed production chunks; restoring the actual backup into
an isolated copy remains a pre-migration gate. Migration SQL/hash, impact,
compatibility, backup/restore, validation and rollback commands are in the plan.
No schema gate/checksum was weakened.

### Actual end-of-day status: pending, not inferred success

The runtime-service receipts record the original activation failed at 14:35–14:36
UTC. The **21:10 export**, **21:15 guarded close-out** and **21:20 post-close audit**
timers are active/waiting. Their service records have no execution-start timestamp;
`Result=success` on an unrun inactive unit is not proof they ran. No after-close
capture or STOPPED marker existed. The rehearsal container was still running as
expected, not unexpectedly continuing after an attempted close-out.

`deliberate_closeout_verified` is currently false. The capture script computes it
from STOPPED marker existence, a non-running container, and `all()` exported trade
rows being CLOSED. It does **not** validate timer success, risk reconciliation,
hashes, completeness or broker state; `all([])` would even be true for an empty
trade export. Future acceptance must independently require exactly trade 100001,
its closed row, reconciled risk, file hashes, complete coverage/gap analysis and
the actual unit results. Do not use that boolean alone as proof.

The regular paper SPX container's ID, image, start time, restart count and running
state still match the session's stored `paper.fingerprint`. No source fix was
copied into either runtime. Preserve normal collection until the existing guarded
close-out; copy and review the later captures after the scheduled jobs actually
execute. No stop, migration, restart, real-money enablement or new timer is
requested as part of this investigation.


### Final local verification receipt

On the final unchanged source, the full suite passed **2,270 tests**, with **36
skipped**, no failures and three existing dependency/process-fork deprecation
warnings. All **45 integration cases** passed; **36 use actual PostgreSQL** and
nine are isolated collector/order-preview checks. The database cases used fresh
local PG16 / TimescaleDB 2.25.2 scratch databases. The skips require private NDX snapshots or the
separate `NDX_POSTGRES_BIN` infrastructure; they are not asserted as tested.
The network-blocked shared/scenario run passed **335 checks**, with zero network
attempts. The final routing/fee subset passed 15 checks and the PostgreSQL exit
notification subset passed 14. Counts overlap; do not sum them as unique cases.

One intermediate full rerun reused the first scratch database and failed its
existing weekly-P&L smoke test because a second seeded -$250 row yielded -$500.
That run is retained, explained and superseded by the full run against a new
scratch database; no trading database or production record was involved.

`uv run ruff check .`, runtime-config validation and `git diff --check` passed.
The final clean-base candidate built locally as
`sha256:568eb8a15a58b6587f6e5e8312ea7aed68421887db0794adbc501825683448b1`.
A Python **3.12.15** import/hash check ran in it with networking disabled and no
credentials or token mounts; all packaged changed sources match the candidate
manifest. Full pytest ran on local Python **3.13.13**, not inside that image.
The reviewed code/test patch applies cleanly to the base commit. No CI run for a
new release commit or real-channel rejection/recovery exercise is claimed.

`graphify update .` completed through `uv tool run --from graphifyy graphify`
(the documented `/home/billy` executable is absent on this host). Its SQL-parser
warning and pending community labels are retained in the log; no SQL changed and
no semantic/LLM relabel was run. A complete pre-update graph archive preserves the
pre-existing modified output. Unrelated research files and the existing docs
index modification were not edited.

The final [evidence manifest](../../data/rehearsals/SPX/2026-11-23/readiness-fixes-20261123/verification-manifest.json)
binds source/config hashes, image identity, checks, runtime receipts and artifact
hashes. The [code/test patch](../../data/rehearsals/SPX/2026-11-23/readiness-fixes-20261123/source-changes.patch)
is reviewable independently of unrelated workspace changes. The dated supervised
canary remains **NO-GO**: live schema 013, actual after-close results, a reviewed
release/CI, approved deployment and paper validation, fresh broker reconciliation,
normal settings and explicit dated owner approval remain required. Do not relax
entry criteria or raise limits to obtain a fill.


## Actual after-close review and authorized release, 22:05 UTC onward

Corey resumed the push/merge/deployment work after the earlier hold. This authorizes
release of the fixes in paper mode and preparation of the stopped live/rehearsal
release; it does not authorize a real-money session or broker order operations.
The separately recorded 012→013 migration plan is included in the authorized
release scope, with backup/restore and read-only flatness checks before applying it.

The scheduled **21:10 export completed at 21:10:56 UTC**. Guarded close-out ran
21:15:02–21:15:30; its log reports schema-at-head, no open SPX trades, no nonterminal
intents and no unlinked filled entries, then a confirmed stop. Container finish
was **21:15:29.164642527 UTC**. The **21:20 audit completed at 21:20:27 UTC**.
The transient systemd units have since unloaded; their journal receipts, actual
capture output, close-out completion log and stopped-container state are retained
in `release-20261123T2205Z`. No success is inferred from an unexecuted timer.

Both new capture manifests verify all 13 artifact hashes. Trade **100001 remains
CLOSED**, quantity one, at **-$37**, matching the one-trade daily-risk state.
The 21:10 and 21:20 exports agree: **216,918 chain rows**, **432 held-leg rows**,
and **19,248 post-exit-leg rows**. Post-exit coverage has **6,416 complete three-leg
observations** from 16:07:30.240518 through **20:59:59.650018 UTC**, immediately
before the 21:00 regular close. Maximum interval was 6.224491 seconds; three gaps
exceed five seconds, none exceed ten, and no observation is missing a leg. The
held phase retains the two previously documented gaps over ten seconds.
This recording establishes coverage, not an official index settlement value.

The post-close `deliberate_closeout_verified=true` is independently corroborated:
STOPPED exists, the container is exited, exactly trade 100001 was exported closed,
P&L reconciles, hashes match and the close-out log confirms the guarded stop.
The regular paper SPX fingerprint remained unchanged through this close-out.
A fresh broker read found zero account positions, active orders or unknown status
nodes; all three databases have zero open trades. Real-money readiness remains
NO-GO until the remaining release/schema/routing/supervision gates and a dated
owner approval are satisfied.

Raw captures remain intact locally and on Helios. Compact `capture-*.tar.gz`
archives and adjacent manifests preserve them for reproduction without presenting
hundreds of thousands of raw rows as source changes. The pre-existing graph
backup remains private/local; unrelated research and current graph edits are not
part of this release commit. The Database Smoke workflow now explicitly runs the
new durable-exit Postgres regression suite on every relevant PR/main build.


## Completed merge, migration and paper deployment

[PR #104](https://github.com/hollowc2/ButterflyGuy/pull/104) merged as
`b7ee64a1e2c743c68aa36a5a3563b3bcfc596d39`. Both
[CI](https://github.com/hollowc2/ButterflyGuy/actions/runs/45282310852) and
[Database Smoke](https://github.com/hollowc2/ButterflyGuy/actions/runs/45282310795)
passed on that merge commit. Database Smoke now includes all 14 new durable-exit
Postgres regressions.

The live database's complete 8,319,624-byte backup was restored into an isolated
copy on PG16.11 / TimescaleDB 2.25.2. All table counts and the 001–012 ledger match;
all six restored background jobs are disabled. Source jobs were untouched. The
approved **013_account_monitor.sql** migration then applied to
`butterfly_guy_spx_live`; its schema/flatness gate passes with no open trades,
unresolved intents, unlinked fills or paper rows. The backup and restore copy are
retained privately on Helios; no dump or credentials were published.

Regular paper SPX (`infra/app_spx`, `butterfly_spx_app`) was recreated with image
`sha256:568eb8a15a58b6587f6e5e8312ea7aed68421887db0794adbc501825683448b1`.
At **22:53:23 UTC**, `/health` and `/ready` both returned **200**. All **165**
packaged Python/SQL files match the merged source snapshot. Role is `paper`, data
is direct, paper trading is true, both live-allow flags are false, and the
one-contract/one-trade limits remain unchanged. The account monitor is enabled
and ticking. Mounts, ports, restart policy and effective runtime environment were
preserved; a new unused equity-webhook env-file key was explicitly left absent,
as it was in the original container, without changing its secret or the env file.

The exact before/after fingerprints prove **NDX, XSP and the stopped live/rehearsal
container are unchanged**. No real-money runtime was started. The same release
source/image is staged for a future explicitly approved session; the old November
23 session artifacts/nudges were not reused or rewritten. The host checkout was
fast-forwarded and synchronized; runtime configs validate. Rollback argv pinning
the prior image is saved in the release's `deployment/prepared-deployment.json`.
No rollback was needed.

A **22:58:58 UTC** stability check still showed health/ready 200, a fresh account
monitor heartbeat and zero restarts after more than six minutes.

The **22:53:52 UTC** read-only reconciliation again found zero account positions,
zero active/unknown orders, and zero open rows in all three databases. Trade 100001
and its -$37 risk reconciliation remain intact. Nothing was edited to force a gate.

[Release receipt](../../data/rehearsals/SPX/2026-11-23/release-20261123T2205Z/release-receipt.json)
binds CI, image/source, migration, actual close-out, backup/restore and deployment
receipts. Earlier intraday manifests remain historical: their pending close-out
and missing-schema classifications are superseded by this section. Their test
count label is also corrected here: 45 integration cases comprise 36 real-DB and
nine isolated cases, not 45 real-DB cases.

A supervised one-contract live canary is **still NO-GO without a dated owner
approval**, fresh broker/intent reconciliation, normal session settings, fixed
runtime paper exit-receipt confirmation and session-specific monitoring/stop/
rollback checks. No live broker order was placed, replaced or canceled; no manual
position was adopted or managed; no real-money session was scheduled.
