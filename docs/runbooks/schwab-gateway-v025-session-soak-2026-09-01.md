# SchwabGateway order-book release full-session acceptance — 2026-09-01

## Scope and freeze boundary

This runbook validates only the exact production SchwabGateway container on
Helios. It does not cut over a ButterflyGuy strategy, build a candidate image,
change an order path, or enable live trading.

The active SPX, NDX, and XSP services remain PAPER runtimes on direct Schwab
market data. This gateway acceptance run is therefore isolated from their
trading path. Candidate gateways, feeds, and evaluator fleets are retired from
the active market-open scope and must not be started to satisfy an older
checklist.

The acceptance target:

- container: `schwab_gateway_live`;
- endpoint: `http://127.0.0.1:8011`;
- Docker healthcheck override:
  `docs/runbooks/schwab-gateway-soak-health.override.yml`, SHA-256
  `2f998db4ff20a0a8640122419742f74db74edc03f3b9ea86a58e30d902b49cbf`.

The production gateway moved off the `aa9d6e6` order-book build on 2026-09-03 and
is now on the 0.4.x strict-priority scheduler line. Identity captured
**2026-09-04 00:01 UTC** (stable, no restart in the prior 3 h, warm):

- release tag: `schwab-gateway:0.4.2-efee41f`;
- container ID:
  `1a2dfa27c6a19ae72c13a87a9fe9ce2d5d42b9f20eb82179c1774fba6b4e433d`;
- image ID:
  `sha256:c8540b5c4eb2ab3d0dfa00d85d75a6fb774bcf22ca1d352b38b68507edb17dcd`;
- revision label: **absent** (`docker inspect` reports `<no value>`; the `0.4.1` /
  `0.4.2` release builds do not stamp `org.opencontainers.image.revision`, so pass
  `--expected-revision '<no value>'` verbatim — the real revision `efee41f` is
  preserved in the tag and evidence path);
- started at: `2026-09-03T22:57:45.300059462Z`;
- restart count `0`, status `running`, health `healthy`, gateway process count `1`.

Re-capture and update the launch command below if the gateway is restarted before
the baseline:

```bash
C=schwab_gateway_live
docker inspect --format '{{.Id}} {{.Image}} {{index .Config.Labels "org.opencontainers.image.revision"}} {{.State.StartedAt}} {{.RestartCount}} {{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}' "$C"
docker image inspect --format '{{.RepoTags}}' "$(docker inspect --format '{{.Image}}' "$C")"
```

`0.4.1` gates live readiness on one successful Schwab round-trip at startup, so a
freshly redeployed gateway serves `503 gateway_not_ready` until it is warm. The
build must stay deployed and warm (`/ready` returns 200 with `token_state: ready`)
through the 06:22 PDT baseline and must not be redeployed afterward. Any Docker,
container, or gateway restart after the baseline invalidates the run.

The harness aborts full-session credit if the container ID, image ID, revision,
start time, restart count, health, or process count changes mid-session.

Retired candidate services are outside this soak and should remain stopped.
AfterHours Lab containers may change or restart without invalidating the
production soak, but must not route to port 8011 or change the production
container, production consumer key, shared token file, or protected priority
policy. The harness records any AfterHours container state as background
context but does not freeze it.

## Credential lineage

The shared token (observed 2026-09-04 00:01 UTC):

- expiry: on or after `2026-09-05T21:20:16Z` — the token was re-refreshed several
  times on 2026-09-03 during the gateway 0.4.x rollout; `token_state: ready` and
  3 successful refreshes since the current container started;
- host file mode/owner: `0600`, `1001:1001`;
- host inode: `42448`;
- active token mounts: production gateway, SPX, NDX, and XSP all bind the same
  host token directory and agree on inode `42448`.

This lineage covers the full 2026-09-04 session. Reauthorization is not part of
the preflight. The preflight must still prove host/container inode and
truncated-fingerprint agreement for those four active consumers without printing
token contents. Do not start a retired candidate service for token-agreement
evidence.

## EquityScanner coexistence boundary

EquityScanner may use the existing production endpoint on
`http://127.0.0.1:8011` with its existing scanner-owned key and a URL-only
runtime override. The key is accepted for read-only quote/history capability
and is classified by the production gateway as `background`; do not copy,
rewrite, rotate, or print it. Do not start a second gateway on port 8012.

Background admission does not create upstream parallelism. The deployed live
provider holds one exclusive shared-token transaction per Schwab call and
serializes every gateway read, so an unbounded 1,917-symbol history phase could
extend into the open and interfere with the protected soak and direct PAPER
consumers.

The ButterflyGuy reference still uses the direct Schwab client. Run the two
captures sequentially so that direct token refresh and gateway traffic cannot
overlap:

- 09:00 ET: ButterflyGuy reference with
  `/opt/equity-scanner/parity/2026-09-01/input/equity_scan.reference.yaml` and
  the six frozen universe/metadata files in that same directory; the wrapper
  hard-stops it at 09:09 ET. It issues 20 sequential quote batches of at most
  100 symbols, skips broad RVOL, movers, and news, and fetches history for at
  most 72 unique selected symbols with concurrency four. Direct-client retries
  are bounded at three attempts per request.
- 09:10 ET: EquityScanner candidate through port 8011 with its existing
  background key; it hard-stops at 09:20 ET, uses at most 72 unique history
  symbols with concurrency four, and uses one attempt per gateway request.
- 09:22 ET: establish the final harness baseline after rechecking shared-token
  agreement, gateway identity, process uniqueness, and flatness. No Docker,
  gateway, PIA, or PAPER-service restart is permitted after this point.

The 09:45 ET comparison is offline and makes no gateway call. Because the live
captures are sequential, its explicit skew-aware mode gates stable fields and
records all dynamic capture differences plus both timestamps and capture skew;
strict zero-skew comparison remains the default for fixtures.

## Prepared read-only tools

Stage these versioned files on Helios without replacing any service file:

- `schwab_gateway_session_soak_20260904_v7.py` SHA-256
  `d8ede4fa9939849863c10bfe6c75535a74b46df668c888a1239318d1c2fb901a`;
- `gateway_cutover_flatness_audit_20260828.py` SHA-256
  `9f215ecd3f6cd1cba048ea1921821da0730ad44a32cbb859fc468fbb443427f0`.

The `v5` soak tool replaced `v4` (used for the 2026-09-02 run). Its only
behavioural change was in the cached option-chain comparison: `canonical_market_data`
now also drops the reevaluated `stale` field and the `stale` /
`stale_contracts_present` quality flags at every nesting level, so per-contract
freshness re-stamping in the sub-second gap between the two chain reads no longer
reports `cache_semantic_mismatch`. `cache_consistency_result` records the ignored
freshness-only difference paths. Independent freshness gating is unchanged:
`validate_chain` still runs on the cached body, so a genuinely stale or too-old
cached response still fails `aggregate_stale` / `too_old_for_consumer`. Verified
against the 2026-09-02 evidence: all recorded `cache_semantic_mismatch`
checkpoints resolve to `semantic_equal=true` with zero market-field drift.

The `v6` soak tool replaces `v5` and carries `v5`'s cache change unchanged. It
adds tiered adjudication for bounded, recovered upstream non-200s, mirroring the
opening-warmup partition:

- A checkpoint no longer fails outright on a `likely_three_second_upstream_timeout`
  (504 at the gateway's ~3 s upstream deadline) or `admission_rejection` (429)
  once retries are exhausted; it records the surface to `checkpoint["transient_non_200"]`.
  Every other non-200 stays gating at the checkpoint — 401/403, non-504 5xx
  (`gateway_or_upstream_server_error`), `client_or_transport_error`,
  `unexpected_http_status`, and invalid JSON on a 200.
- After the checkpoint loop, `main()` adjudicates the accumulated transients:
  a surface that returns 200 at the immediately following checkpoint becomes a
  `transient_observations` entry (not a violation); 2+ consecutive failed
  checkpoints for one surface, or transients on `>= max(3, ceil(0.10 * checkpoints))`
  checkpoints, are promoted to gating; a transient at the final checkpoint is
  confirmed by a single post-close probe of only those surfaces (200 =>
  observation, else gating).
- `manifest["transient_observations"]` and `manifest["transient_policy"]` record
  the outcome and thresholds. The exit code is still
  `0 if not manifest["violations"] else 1`; bounded/recovered 504s simply no
  longer land in `violations`.
- Defense in depth: `REQUEST_MAX_ATTEMPTS` 2 -> 3 and
  `REQUEST_RETRY_BACKOFF_SECONDS` 0.25 -> 0.5 (attempts at 0 / +0.5 s / +1.5 s);
  every raw attempt is still persisted.

Replayed against the 2026-09-02 evidence: the three `session_*_regular` 504s at
checkpoint 10 move to `transient_observations` (recovered at checkpoint 11) and
the run's `violation_count` goes to 0.

The `v7` soak tool carries the `v5`/`v6` changes unchanged and makes the harness
aware of the gateway 0.4.x strict-priority scheduler:

- Non-200s are classified from the stable `error.code` in the JSON body, not
  from status code plus elapsed wall time (queue wait now inflates elapsed, so
  the old `504 and 2500 <= elapsed_ms <= 4000` heuristic was unsafe). A bare 504
  with no error body still classifies as an upstream timeout.
- `503 gateway_queue_timeout` (`queue_wait_timeout`) joins
  `likely_three_second_upstream_timeout` and `admission_rejection` (429 /
  `gateway_capacity_exceeded`) as a bounded transient — designed backpressure,
  adjudicated across checkpoints exactly like the 504s. `503 gateway_not_ready`,
  `503 upstream_unavailable`, and `502 upstream_malformed` stay gating.
- `METRIC_RE` now allowlists `schwab_gateway_scheduler_*`, so every checkpoint's
  `metrics_before` / `metrics_after` capture queue depth, queue-wait and
  execution histograms, dispatch, capacity-rejection, queue-timeout,
  upstream-timeout and cancellation counters as evidence for the "bounded 504"
  review bar. Filtered logs retain `priority_class` / `queue_wait_ms` /
  `outcome`. The manifest carries a `scheduler_policy` block; pass
  `--expected-consumer-priority protected` (the soak key's registered class).

The soak tool has no Docker lifecycle, database, broker-account, token-write, or
order capability. It reads the scoped gateway key without printing it, sends a
maximum of three requests concurrently, and writes new evidence files with mode
`0600`. The flatness tool performs database and authenticated broker reads and
prints only counts and status names; it does not print account, order, position,
or option identifiers. Its audit-only status matrix treats historical Schwab
`REPLACED` nodes as terminal without changing runtime reconciliation behavior.

Verify the two local and remote hashes agree before use. Do not run a tool whose
hash differs.

## Tuesday preflight — final gate at 06:20-06:29 PDT

1. Confirm the host clock says Friday 2026-09-04 and it is a normal session.
2. Confirm the token is ready and all four active consumers agree on the
   then-current host token inode and approved truncated fingerprint without
   printing token contents. (Captured 2026-09-04 00:01 UTC: inode `42448`, mode
   `0600`, owner `1001:1001`, all four consumers agree.)
3. Confirm production identity matches the values in "The acceptance target"
   above, health and readiness return 200, token state is ready, restart count is
   zero, and there is exactly one gateway process. If the gateway was restarted
   since the 00:01 UTC capture, re-capture and update the launch command; on the
   0.4.x line a freshly redeployed gateway serves `503 gateway_not_ready` until
   warm — if `/ready` is not 200 with `token_state: ready`, wait, do not start.
4. Confirm the evidence target does not exist:
   `/opt/butterflyguy-gateway-evidence/2026-09-04-session-soak-v0.4.2-efee41f`.
5. From `/opt/butterflyguy`, run the redacted flatness gate:

```bash
.venv/bin/python \
  /opt/butterflyguy-gateway-acceptance-tools/gateway_cutover_flatness_audit_20260828.py \
  --config configs/config.yaml --date 2026-09-04
```

Require `flat: true`, database OPEN trades `0`, database nonterminal intents
`0`, SPX/NDX/XSP broker option-position counts `0`, active order nodes `0`,
missing and unmapped statuses `0`, and duplicate order IDs `0`. Historical
`REPLACED` counts are recorded separately and do not satisfy any active-order
category.

Do not start the soak if a production invariant or flatness gate fails.
AfterHours changes alone are not failures. A retired candidate service being
stopped is expected, not a failure.

## Start the full-session harness

The launcher sleeps until 06:22 PDT so it cannot establish its baseline while a
parity process is still allowed to run. Start it beforehand in a durable `tmux`
session; it must establish a clean baseline no later than 06:29 PDT. The process
waits for the 06:30 PDT / 09:30 EDT open, samples every 15 minutes through the
13:00 PDT close, then performs the post-close check at 13:10 PDT.

Identity below was captured 2026-09-04 00:01 UTC. Re-verify at preflight; if the
gateway was restarted, re-capture and update the four `--expected-*` values.

```bash
ssh -F /dev/null -o BatchMode=yes billy@helios
tmux new -s gateway-session-soak
cd /opt/butterflyguy
.venv/bin/python \
  /opt/butterflyguy-gateway-acceptance-tools/schwab_gateway_session_soak_20260904_v7.py \
  --session-date 2026-09-04 \
  --evidence-dir /opt/butterflyguy-gateway-evidence/2026-09-04-session-soak-v0.4.2-efee41f \
  --expected-container-id 1a2dfa27c6a19ae72c13a87a9fe9ce2d5d42b9f20eb82179c1774fba6b4e433d \
  --expected-image-id sha256:c8540b5c4eb2ab3d0dfa00d85d75a6fb774bcf22ca1d352b38b68507edb17dcd \
  --expected-revision '<no value>' \
  --expected-started-at 2026-09-03T22:57:45.300059462Z \
  --expected-consumer-priority protected
```

Detach with `Ctrl-b d`; do not interrupt the process. Do not use cron, systemd,
Compose, or a container recreation for this harness.

Each checkpoint exercises SPX/NDX/XSP concurrent spot, uncached and cached
same-day chains, minute history, regular session history, and VIX spot. It
checks freshness using the existing 30-second current-data and 180-second
minute-history consumer limits; chain counts, sides, symbols, strikes, prices,
sizes, timestamps, normalization metadata, cache equivalence, selected metrics,
health, readiness, token state, production identity, restart count, and process
uniqueness are recorded. Post-close it validates the bounded empty extended
session contract for each index and captures filtered production logs from the
recorded UTC boundary.

## Post-close decision

An exit code of zero is necessary but not sufficient. Require all of the
original acceptance criteria and review:

- manifest `complete: true`, 27 expected checkpoints, and no violations;
- exact production identity unchanged through the final check;
- health/ready 200, token ready, restart zero, and one process throughout;
- no protected 429, authentication failure, readiness flap, unexplained gap,
  stale required surface, incomplete chain, invalid market, or cache mismatch;
- every non-200 classified from the preserved response `error.code` and the
  metrics/log boundary;
- any bounded backpressure (504 `upstream_timeout`, 429
  `gateway_capacity_exceeded`, 503 `gateway_queue_timeout`) shown to be bounded
  and non-compromising rather than merely ignored: under `v7` a recovered
  single-window occurrence is adjudicated into `manifest["transient_observations"]`
  (with its `checkpoint_index`, `recovered_at_index`, `error_code`,
  classification, and attempt count) against the thresholds in
  `manifest["transient_policy"]`; a run passes with a non-empty
  `transient_observations` as long as `violations` is empty. Confirm each entry
  recovered at the next checkpoint (or the post-close probe), cross-check the
  `schwab_gateway_scheduler_*` counters in the surrounding `metrics_before` /
  `metrics_after` snapshots, and confirm no `sustained_upstream_failure`,
  `gateway_too_flaky`, or `unconfirmed_final_checkpoint_transient` entry reached
  `violations`. `gateway_not_ready`, `upstream_unavailable`, and
  `upstream_malformed` are never tolerated;
- SPX and XSP no-regression evidence;
- NDX normalized contracts retain both endpoints, `bid <= mark <= ask`, retain
  chain counts, and expose both contract and aggregate normalization flags;
- final flatness gate still passes.

If no live NDX crossed market occurs during the session, do not manufacture an
event or claim the live normalization criterion passed. Record the operational
soak result, but keep the NDX normalization acceptance item `INCOMPLETE` until
audible production evidence exists. Unit tests and counters support readiness;
they do not replace the requested live event evidence.

The evidence root and every raw file are append-only by construction. Record the
printed manifest SHA-256 and remote paths. Do not overwrite a failed or partial
run.

## Work allowed only after a full PASS

Only after the evidence review passes may Phase 5 begin: select a clean exact
ButterflyGuy commit containing the normalized-cross metadata consumer fix, rerun
the focused/full tests and Ruff, update graphify, and build an immutable image
without recreating a running strategy. Then prepare separate approval requests
in XSP, SPX, NDX order. No strategy recreation or cutover is authorized by this
runbook.
