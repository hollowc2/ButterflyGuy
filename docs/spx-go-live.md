# SPX go-live readiness

Owner: Corey. Spec dated 2026-10-20. Scope: frozen SPX E0, one contract,
one trade/day, $500 daily loss limit, $20,000 allocation. NDX, XSP and prospective
cohort v2 remain paper. Quantity support stays in the execution code; sizing up
requires a separate review and guard change.

Status: **NO-GO pending evidence and operational sign-off.** This checklist is
not deployment approval. See the [decision record](research/spx-go-no-go-2026-10-20.md)
and [live runbook](live-runbook.md#spx-live-one-contract).

## Gate A: ready for the first live order

Edge and frozen rules:

- [x] Resolve the deferred 2026-10-19 session in the dedicated frozen v2 checkout.
  Retry recorded the twelfth trade; ledger verification passes. The scheduled
  updater subsequently committed the evidence as `2eaf522` and deferred October 20.
- [x] Verify the current append-only ledgers under the existing updater lock.
  Rechecked `2eaf522`: 12 trades, $1,158 stressed net, four settlements,
  October 20 deferred. Frozen sources and manifest remain intact (evidence below).
- [ ] Complete the registered 20-trade integrity review; 12 trades do not close it.
- [ ] Merge an owner-reviewed go/no-go record reconciling the recent cohort with
  losing 2023–2025 replays. The initial decision in this branch is NO-GO.
- [ ] Confirm SPX rules still match the registered E0 configuration hash. A rule
  change requires a new cohort and resets this gate. Current main has collector
  timing additions and a higher paper fee; the raw hash differs. Review the
  differences below without changing the frozen cohort or its assumptions.
- [ ] Assign continued monitoring of the registered 60-trade early-failure review.
  Completing 60 trades is not a first-order gate; failure returns live to paper.
  Keep the original 120-trade/20-settlement/15-winner study endpoint unchanged.

Order path:

- [ ] Confirm Schwab accepts SPX butterfly limits on the $0.05 increment (M4):
  supported order preview, or first approved supervised order, with redacted evidence.
- [ ] Review the retained `entry.live_require_leg_bids=false` choice in the runbook.
- [ ] Check the frozen 4 × $0.10 / 20-second / 300-second ladder against actual
  entry-time SPX spreads and cancellation/fill latency.
- [ ] Prove post-close cash settlement reconciles without manual DB edits (M10).
- [x] Pass synthetic live-mode partial-fill, cancel-pending, missing/unknown
  parent/child status, and unconfirmed cancellation tests on the reviewed code.
  These checks must pass again on the exact deployment release.

Market data and credentials:

- [x] Validate actual Compose merging: base, gateway-paper, then SPX live;
  SPX alone becomes direct/live, NDX/XSP remain gateway/paper, independent
  account pin required, SPX restart disabled and image pinned.
- [ ] Verify authenticated direct/live startup on the approved release.
- [ ] Measure the combined shared-credential request budget: gateway traffic
  for paper NDX/XSP and other consumers plus SPX direct collection, scanning,
  position polling, accounts/orders, token checks and broker reconciliation.
  Run the gateway load test in its approved test environment, compare protected
  latency and 429s before/after, and retain measurement duration and headroom.
  Gateway load tests alone do not measure the direct SPX load. If insufficient,
  stay paper and separately review force-fresh chains; do not bypass the guard.
- [x] Verify the shared token-expiry rule is loaded: Helios Prometheus reports
  `SchwabGatewayRefreshTokenExpiring`, health `ok`, state `inactive`.
- [ ] Put Saturday 10:00 Pacific reauthorization on the operator's calendar and
  verify the expiry alert route reaches the supervision phone.

Operations and release:

- [ ] Review and rehearse the SPX runbook, halt command, targeted paper rollback
  and manual SPX flatten. Preserve the July 16 XSP evidence as historical proof only.
- [ ] Test critical-alert delivery to the actual supervision phone and record receipt.
- [ ] Verify account approval for index spreads, $20,000 allocation, independent
  expected-account pin, and named supervisor for the whole holding window.
- [x] Run local full tests, Ruff, actual three-overlay Compose validation and
  isolated TimescaleDB smoke testing; see the verification record below.
- [ ] Require CI and Database Smoke on the final PR head, a reviewed immutable
  deployment image, and a freshly verified rollback baseline.
- [x] Exercise synthetic startup rejection for a wrong account ID, wrong loss cap,
  oversized launch, missing supervision, NDX live and gateway live market data.
  Account approval and an independently reviewed real account pin remain open.
- [ ] Prove DB/broker flatness before the first session, including
  `deploy_broker_flat_check.py` exit 0, no open DB trades, no active/unknown
  intents, no monitored trade and no duplicate live runtime.
- [ ] Obtain explicit approval of the named Helios SPX release and first live session.

Some acceptance facts (the first actual broker limit acceptance and actual
cash settlement) cannot be manufactured in offline tests. If no preview exists,
mark limit acceptance as conditional for the first approved supervised order;
failure aborts Stage 1. Synthetic settlement tests do not close the broker M10 gate.

## Implementation review and evidence — October 20 Pacific

Review `26554d8` (substantive launch controls) separately from `8e8d35c`
(four generated graph files only). The generated graph is navigation evidence,
not execution or strategy proof. Follow-up `8d6d5cd` fixes supervision expiry
during an active position, retries broker-halt persistence after reconciliation
recovers, and releases the entry lock on failed risk/supervision checks.
`40aa172` adds startup rejection and expiry-during-monitoring regressions.
`402d0c7` rejects a FILLED parent with a WORKING child in polling,
post-cancel checking and startup fill repair; the captured parent executions
alone cannot establish that the entire order tree is safe.
Main `fe4dbd0` was merged before final validation; no runtime config changes are
part of this PR relative to that base.

Execution review: explicit `EXECUTION__PAPER_TRADING` and
`EXECUTION__ALLOW_LIVE_TRADING` override YAML in both directions and take
precedence over the legacy allow-live flag. Invalid values fail validation.
Live account, allocation, loss, size, supervision and direct-data guards stay
enforced. Unknown/missing statuses stop before another submit; cancel acceptance
alone does not permit a retry, and every child must also be terminal canceled
unless a complete broker fill is validated. Operational halt and audit insert
are transactional and do not fabricate P&L. Supervision expiry is checked while
holding a position, including after close, and under the entry lock before each
attempt. Expiry latches entries; monitoring and reconciliation continue.
Synthetic tests preserve active monitoring across broker, manual and supervision
entry halts. Phone reachability still requires an operator drill.

Frozen checkout verification used its own pinned CLI:

```bash
flock -n ~/.local/state/butterfly-cohort-v2/update.lock \
  env UV_CACHE_DIR=/tmp/butterfly-cohort-verify-cache \
  uv run --locked --no-sync python -m butterfly_guy.scripts.run_prospective_execution \
  verify --cohort reports/prospective_execution/spx-prospective-v2-2026-10-02
```

Run from `/mnt/Repos/Trading/Butterflyguy/.worktrees/spx-prospective-v2` at
`2eaf522`; result: ledger integrity OK, all 39 registered source/lock hashes
match, registered config hash matches. The previous `08fed21` manifest is
byte-identical; daily/trade/deferral ledgers retain the previous bytes as prefixes.
The checkout was clean before and after verification. No update was requested.
The existing updater's last result was success/exit 0, service inactive, timer
active with next run October 21 at 18:32:44 Pacific. Any later retry must use
this same lock and frozen CLI, leave the timer intact, and append evidence only.

Verified SHA-256 values:

- Manifest: `ce7144c24d3f0620b45501b224eaf55d5c0431be81285a5df11bcebe87d779db`
- Daily ledger: `880ac7a80dbd601e1d780ab207a7eff4a9cc89e0b19f278c45af52d4ed404918`
- Trade ledger: `10bc2e5d8a8ad9b53b8453a0b914431dcf2076cdaeb4be9e6328b099b9eb2efb`
- Deferral ledger: `a9a59be16c6ddb183f7b21bcc15aadecb5c297f40a5f54bb67814969191d1804`
- Frozen config: `d120b63fd4e12ed812cc2742d602f9e531a1f5ca38e28c30628ab149f5d1b397`
- Current-main/launch config: `05e188ca6aac95b3cdaa9b40bf982d241b428b197147425d5b9035c8fe673c25`

Parsed config comparison finds only the existing collector timing fields
(`record_timing`, `align_to_minute`, `align_offset_seconds`) and main's explicit
`execution.paper_commission_per_contract=1.15` versus the registered/default
0.65. Entry, strategy, profit-management and risk sections match. This is not
raw-config identity, and collector cadence can affect observations. Reconcile
that provenance and main's all-in fee evidence in the owner review; do not
rewrite the v2 manifest, ledgers or registered 0.65 cost assumption. A separately
labeled cost sensitivity may supplement the review without replacing v2.

Read-only Helios checks found one running app per SPX/NDX/XSP, each
`paper=true`, `allow_live=false`, market data `gateway`, restart count zero,
and HTTP 200 from `/health` and `/ready`. SPX's current image was
`sha256:4771356b52d76788c1e5766b54c6a146ab5600d1e5eac7c2c04c2c98199cad0d`;
NDX `sha256:1fbc1ab3aed0aec85bcccab9e5009679789baab10fc333cfd0e4636ef1e7cc61`;
XSP `sha256:df144a93aaa2b71d8f773820acc8f11af85acaaa135f873c86967794f5fd4f35`.
These are observation-time baselines, not deployment or rollback approval.

### Verification record

Local validation of substantive code commit `402d0c7` (after merging
`fe4dbd0`): **1,422 passed, 36 skipped, three warnings**. The full suite ran
with `CI_DATABASE_URL` pointing only to a fresh task-owned local database,
`butterfly_review_child_guard`, in `timescale/timescaledb:2.30.1-pg16`
(image `sha256:f495f2bc25ca7596ca8e1606c6241ca250ccc56a0c082b9f2ec0d290e0126cd9`).
It includes the real `tests/integration/test_database_smoke.py` migration,
weekly-P&L and durable asset-scoped halt/audit checks; that test did not skip.
No production DSN or database was used. Focused launch/order/trade/runtime
tests: **183 passed**. Ruff and `git diff --check` passed.

Commands used `UV_CACHE_DIR=/tmp/butterfly-launch-uv-cache uv run --locked
--no-sync` followed by `pytest -q -rs`, the focused test filenames, or
`ruff check .`. Full output is retained locally at
`/tmp/spx-launch-review-verified-pytest.log`. The actual three-overlay Compose
regression passed separately after the final fix (`pytest -q
tests/test_spx_live_launch.py -k combined_compose`); it invokes Docker Compose
with synthetic interpolation values and `config --no-env-resolution --format
json`, and checks the merged service fields and missing-account rejection.
It does not start services, load production env files, authenticate or prove
broker acceptance. CI and Database Smoke must also pass on the final PR head;
only documentation/generated graph changes follow the locally tested source.

Remaining skips: **30** isolated NDX PostgreSQL tests require
`NDX_POSTGRES_BIN`; **six** NDX baseline/continuation/execution-audit/provenance/
quote-fidelity tests require private snapshots. The Timescale smoke does not
substitute for those NDX tests. The three warnings are a websockets legacy
deprecation and two multiprocessing fork warnings. No broker write, real alert,
credential renewal, calendar installation or load test was performed.

The required AST-only graph refresh ran with graphifyy 0.9.93 and
`GRAPHIFY_BACKEND=none`; no semantic/LLM extraction ran. Its JSON has 11,034
unique nodes and 24,730 edges, with all edge endpoints present. Generated files
belong in their own commit. Extraction reports 27 SQL files omitted because
the optional `tree_sitter_sql` parser is absent and three code/data files with
no modeled symbols. The graph does not validate runtime behavior or refresh
semantic documentation evidence.

## Next checks before any operational approval

- **Broker:** first inventory the existing redacted SPX fill evidence referenced
  by main's fee change; confirm exact $0.05 limit acceptance rather than assuming
  it from the fill price. Determine whether a supported read-only preview exists.
  Prepare the exact one-contract order and redacted evidence fields for owner
  review; submit nothing here. Separately collect broker cash transactions,
  intent/trade IDs, execution times, and settlement amounts to close M10 through
  normal reconciliation without manual DB changes. Keep ladder and wing-bid
  policy review open until spread/latency evidence and owner review are attached.
- **Request budget:** use SchwabGateway's
  `docs/runbooks/full-session-load-test.md` to prepare an immutable driver/profile,
  session date, operator, existing consumers, baseline and stop thresholds. Include
  direct SPX collector, scan, two-second held-position reads, accounts/orders,
  reconciliation and token work alongside gateway NDX/XSP/other consumers.
  Retain the runbook's chain p95 <1.5s / p99 <2s, other-read p95 <1s,
  zero protected timeouts/rejections, zero restart deltas and token errors.
  Require zero credential-wide 429s; inventory total upstream requests/minute
  against the application budget and agree minimum remaining headroom before
  the approved measurement. Retain request timestamps and duration, including
  entry bursts and overlapping monitor windows.
  Do not run a production load test or change consumers as preparation.
- **Credentials:** owner installs the Saturday 10:00 Pacific calendar slot;
  verify shared token-directory mounts, file permissions and read-only direct
  authentication after the established interactive renewal. The loaded expiry
  rule is verified; actual routing/receipt and live-direct startup are not.
- **Alert delivery:** inspect the loaded Alertmanager route and receiver without
  exposing secrets; prepare a single critical drill with session date, phone,
  operator, expected receipt deadline and missed-alert stop action. Obtain
  explicit approval to send it, then retain receipt/acknowledgment timestamps.
  No real alert was sent in this review.
- **Account:** owner supplies a redacted independent account record, index-spread
  approval and $20,000 allocation evidence. Compare the account pin by equality
  without printing it. Name the supervisor and coverage through settlement;
  exercise mismatches synthetically before any approved authenticated startup.
- **Rehearsal/release:** conduct an offline SPX halt/rollback/manual-control
  tabletop, record operator and pass/fail for each step. Before a later deployment
  request, pin the tested image and exact three-overlay argv; capture current
  image/mounts and targeted paper rollback argv. Run read-only
  `tools/deploy_broker_flat_check.py` inside SPX (require exit 0), count OPEN DB
  trades and nonterminal/unknown intents, inspect active monitor logs and verify
  runtime uniqueness. Recheck those facts immediately before the approved
  session; this review does not certify future flatness. Require final-head CI,
  Database Smoke, the 20-trade decision and all other Gate A evidence first.

No operational approval is being sought while these gates remain open. Keep
launch NO-GO, the registered 60-trade review assigned before any launch, and
the original 120-trade/20-settlement/15-winner endpoint intact.

## Gate B: ten supervised trades

Corey supervises all ten. Each trade uses one contract and the frozen rules.
Retain broker execution IDs/timestamps and prices, DB trade/intent references,
settlement evidence, notifications and a cost comparison. Require all ten to
reconcile, no manual DB edits, zero unknown statuses at session end and no
unresolved incidents. Sign and date the gate record before routine Stage 2.

## Gate C: twenty further routine trades

Continue the same one-contract limits with a reachable operator throughout each
holding window. Gate C completes the launch after thirty clean live SPX trades
in total: ten Stage 1 and twenty Stage 2. Every trade must reconcile, zero
unknown orders may remain, and average fill cost must not exceed the registered
stressed model. Write up every stop-rule event and update the runbook to match
what actually happened. Sizing above one contract remains a separate decision.

Any stop-rule trip in either stage latches entries, hands broker control to the
operator, reconciles and returns to paper. Re-entry restarts that stage's count.
Use an append-only stage log recording stage, trade ID, release SHA, date,
clean/incident status, reconciliation evidence, cost comparison and reviewer.
Never count paper trades, historical canaries or manual DB repairs toward a gate.
