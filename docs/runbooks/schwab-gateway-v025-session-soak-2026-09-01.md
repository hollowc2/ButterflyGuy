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

The acceptance target is frozen at:

- container: `schwab_gateway_live`;
- endpoint: `http://127.0.0.1:8011`;
- container ID:
  `ccd2b0d2d2b3dc928bdfba46ba80a73ab6831cb6e955582ec50df5c1f9b39768`;
- image ID:
  `sha256:f1d287294864c05b00ca201d1d86f8344f0d6f61121074982f92667468fec7f0`;
- revision: `aa9d6e65a91c14eadf70df1c3da15101fb84d3f9`;
- release tag: `gateway-order-book-aa9d6e6`;
- started at: `2026-08-31T03:26:25.514589924Z`;
- baseline restart count: `0`;
- gateway process count: `1`;
- Docker healthcheck override:
  `docs/runbooks/schwab-gateway-soak-health.override.yml`, SHA-256
  `2f998db4ff20a0a8640122419742f74db74edc03f3b9ea86a58e30d902b49cbf`.

This freeze supersedes the pre-rebuild `383f5fb` / `d11b61e` target. The
production gateway was intentionally rebuilt on 2026-08-29 while other Helios
work was in progress, then recreated on 2026-08-30 PDT with the same immutable
image and the healthcheck-only override above. A later Docker/containerd recovery
preserved the container ID but advanced `StartedAt` to the value frozen above.
PIA VPN was restored at `2026-08-31T03:34:28Z`, after which Docker, the gateway,
and all three PAPER services were revalidated. The failed earlier evidence at
`2026-08-31-order-book-aa9d6e6` is preserved and records only
`production_started_at_changed`; do not overwrite or reuse it. Any subsequent
Docker, container, or gateway restart invalidates the new freeze.

The harness aborts full-session credit if the container ID, image ID, revision,
start time, restart count, health, or process count changes.

Retired candidate services are outside this soak and should remain stopped.
AfterHours Lab containers may change or restart without invalidating the
production soak, but must not route to port 8011 or change the production
container, production consumer key, shared token file, or protected priority
policy. The harness records any AfterHours container state as background
context but does not freeze it.

## Credential lineage

The shared token currently records:

- creation: `2026-08-29T21:20:16Z` (`14:20:16 PDT`);
- expiry: `2026-09-05T21:20:16Z` (`14:20:16 PDT`);
- host file mode/owner: `0600`, `1001:1001`;
- host inode observed after final infrastructure recovery: `60948`;
- active token mounts: production gateway, SPX, NDX, and XSP all bind the same
  host token directory.

This lineage is valid through the full Tuesday session. Reauthorization is not
part of the Tuesday preflight. The preflight must still prove host/container
inode and truncated-fingerprint agreement for those four active consumers
without printing token contents. Do not start a retired candidate service for
token-agreement evidence.

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

- `schwab_gateway_session_soak_20260903_v5.py` SHA-256
  `5c214fabb33ba137b8c23ff53ab19ba6ec24ffdd29aebbe32fce2d07bd331c82`;
- `gateway_cutover_flatness_audit_20260828.py` SHA-256
  `9f215ecd3f6cd1cba048ea1921821da0730ad44a32cbb859fc468fbb443427f0`.

The `v5` soak tool replaces `v4` (used for the 2026-09-02 run). Its only
behavioural change is in the cached option-chain comparison: `canonical_market_data`
now also drops the reevaluated `stale` field and the `stale` /
`stale_contracts_present` quality flags at every nesting level, so per-contract
freshness re-stamping in the sub-second gap between the two chain reads no longer
reports `cache_semantic_mismatch`. `cache_consistency_result` records the ignored
freshness-only difference paths. Independent freshness gating is unchanged:
`validate_chain` still runs on the cached body, so a genuinely stale or too-old
cached response still fails `aggregate_stale` / `too_old_for_consumer`. Verified
against the 2026-09-02 evidence: all recorded `cache_semantic_mismatch`
checkpoints resolve to `semantic_equal=true` with zero market-field drift.

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

1. Confirm the host clock says Tuesday 2026-09-01 and it is a normal session.
2. After both parity processes have stopped, confirm the refreshed token is ready
   and all four active consumers agree on the then-current host token inode and
   approved truncated fingerprint without printing token contents.
3. Confirm production identity exactly matches the frozen values above, health
   and readiness return 200, token state is ready, restart count is zero, and
   there is exactly one gateway process.
4. Confirm the evidence target does not exist:
   `/opt/butterflyguy-gateway-evidence/2026-09-01-order-book-aa9d6e6-refreeze-032625`.
5. From `/opt/butterflyguy`, run the redacted flatness gate:

```bash
.venv/bin/python \
  /opt/butterflyguy-gateway-acceptance-tools/gateway_cutover_flatness_audit_20260828.py \
  --config configs/config.yaml --date 2026-09-01
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

```bash
ssh -F /dev/null -o BatchMode=yes billy@helios
tmux new -s gateway-order-book-soak
cd /opt/butterflyguy
.venv/bin/python \
  /opt/butterflyguy-gateway-acceptance-tools/schwab_gateway_session_soak_20260903_v5.py \
  --session-date 2026-09-01 \
  --evidence-dir /opt/butterflyguy-gateway-evidence/2026-09-01-order-book-aa9d6e6-refreeze-032625 \
  --expected-container-id ccd2b0d2d2b3dc928bdfba46ba80a73ab6831cb6e955582ec50df5c1f9b39768 \
  --expected-image-id sha256:f1d287294864c05b00ca201d1d86f8344f0d6f61121074982f92667468fec7f0 \
  --expected-revision aa9d6e65a91c14eadf70df1c3da15101fb84d3f9 \
  --expected-started-at 2026-08-31T03:26:25.514589924Z
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
- every non-200 classified from the preserved response and metrics/log boundary;
- any 504 shown to be bounded and non-compromising rather than merely ignored;
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
