# Proposed one-shot Helios capture — not activated

Prepared from a read-only observation at **2026-10-16 15:56:18 UTC**. NDX is
paper trading and trade **355 is OPEN**, entered at 14:00:15 UTC. This supersedes
the earlier zero-open-trade observation. Broker positions/orders were not queried
again; paper DB state does not establish current broker state. No gateway request,
capture, live DDL/grants, image transfer, secret provisioning or restart occurred.

The proposed [context](context.json) fixes the existing paper selection before any
new market-data request:

- Lower: `NDXP  261016P29310000`
- Center: `NDXP  261016P29410000`
- Upper: `NDXP  261016P29510000`

Session October 16; cash-market close **20:00 UTC**, as returned by the deployed
`core.time_utils` calendar helpers, not an independent exchange-calendar
attestation or option-settlement timestamp. The calendar identifier names that
source. The observation contains the deployed strategy config file's SHA-256;
it does not attest all environment overrides or running source. No economics,
account IDs or credential values were exported.

`build_sha256` is the tested observer's immutable Docker image ID, not the old
running strategy image or repository HEAD. `config_sha256` hashes the exact
[capture policy](capture-policy.json), which binds the selected trade, strategy
config file hash, resource limits and proposed connectivity. These are separate
identities. Unique request/record/pass/acquisition IDs are allocated once for this
proposal. No request has used them. Publication is prospective observation of
these selected contracts; it does not reconstruct the 14:00 entry quote or order.

## Concrete release proposal

[compose.yaml](compose.yaml) is a separate, disabled, manual-profile project,
using the locally tested image
`sha256:e55ee57b97aa8a1a624677876853574831fb83f8b6ea77bf1ca8228978669a99`.
It has no trading-service dependencies, published ports, trading config mount or
token file. It joins the existing `monitoring_net`; read-only Docker metadata
verified aliases `schwab-gateway` (exposed TCP 8011) and `timescaledb`. DNS/HTTP/DB
connectivity from the new image has not been exercised on Helios.

The proposed install directory is `/opt/ndx-observer-review/v1`. Transfer via
Docker save/load must record archive SHA-256 and verify the loaded image ID;
local tags and repository SHAs are insufficient. No registry push or rebuild of
active services is needed. The runtime build contract and enabled synthetic image
smoke remain in `../observer-runtime-v1/` and their closed evidence archives.

The proposed secret file is `/etc/butterflyguy/ndx-observer/observer.env`, root
owned mode 0600, read by Compose on the host. It must contain only
`NDX_OBSERVER_DATABASE_DSN` and `NDX_OBSERVER_GATEWAY_KEY`. No secret is supplied
in this package. Environment secrets remain visible to Docker administrators;
never render resolved Compose/environment output into evidence. Compose pins
`NDX_OBSERVER_ENABLED=false` independently of that file.

Proposed login `ndx_observer_capture` must be a dedicated, non-superuser,
non-owner, non-CREATEDB/non-CREATEROLE/non-replication role, with CONNECT to
`butterfly_guy` and membership only in `ndx_evidence_recorder`. Separately approved
schema installation uses the frozen `../postgres-v1/schema.sql` and
`../observer-v1/roles.sql`, outside automatic migrations. Inspect inherited and
PUBLIC privileges before accepting the login; the proposal does not establish
that this target lacks broad PUBLIC access. The gateway needs a dedicated
read-only market-data consumer key for `ndx-timescale-observer-v1`; exact supported
provisioning and permissions must be reviewed before creating it. Do not copy a
strategy's key, database login or shared token file. Provisioning is still pending.

## Admission and execution after separately scoped approval

**HOLD now:** an open paper trade is present, the new login/key/schema and loaded
image are unprovisioned, and storage/WAL headroom is not freshly measured. This
package does not authorize those changes. The Helios deployment skill requires
explicit approval for live changes after a concrete preflight; prior approvals
covered local tests and read-only audits.

1. At the intended execution time, reread service health, current image IDs,
   DB trades/intents and the appropriately scoped broker positions/orders.
   The prior broker audit covered only the current-day order query, not all GTC
   history. Review that gap before claiming flatness. Do not use this package
   while required deployment preflight is non-flat or otherwise fails.
2. Confirm the selection row's date and three symbols still match this context,
   the runtime remains paper NDX, and the approved calendar says the session is
   open. The trade may have closed since selection. **Expire this context at
   20:00 UTC October 16.** If no safe window exists, skip; prepare a new dated
   context from a later real selection. No rollover, polling, fallback contracts
   or historical-expiration request is allowed.
3. Measure the database/WAL filesystem, current WAL pressure and research
   relation sizes. Proposed free-space floor is **10 GiB**, an operator admission
   check requiring review, not a validated capacity model. Stop below it. The
   image's 512 MiB research relation pause is sampled and excludes a hard WAL or
   filesystem quota. Retain this one-shot; no automatic delete/retention job.
   The local same-container restore test is not an independent backup. An
   accepted backup/storage plan remains required before live DDL.
4. Only after named approval: provision the additive schema/roles/login/key,
   transfer/verify the image and install the hash-verified proposal and secrets.
   Verify restricted login privileges, schema SQL hash/installation identity,
   connectivity and default-disabled behavior. Record redacted counts/results.
5. Recheck context freshness immediately before a separately approved **single**
   invocation with `NDX_OBSERVER_ENABLED=true`. No scheduler or service `up` loop.
   Retain its exit code and categorical output. CLI exit zero alone is not
   acceptance: require quote success, `recording_status=published` and a
   journaled receipt; independently reconcile exactly one publication and
   acknowledgement for this acquisition. No automatic retry on uncertain commit.
6. Hash and preserve the received body/provenance/journal and receipt evidence,
   including clock/provider-age/build/cache unknowns and signed composites.
   Export only the research schema with a hash/installation manifest to the
   accepted archive, verify it and record the lack of an independent backup.
   Any corrective acquisition gets new identities and explicit lineage.

Rollback is stopping only this standalone observer, returning its flag to false,
and preventing new requests. Preserve committed research evidence and logs;
never drop the schema, truncate append-only tables, reset live source, restart
trading services or rotate shared broker tokens as rollback. Uncertain outcomes
require reconciliation before any retry. All historical replay, fills, P&L and
later NDX research gates remain unchanged.

## Verification performed

The new context validates through the existing `Acquisition` constructor. Its
policy digest, observed trade identity and built image source hashes reconcile.
Compose validation with `--no-env-resolution` passes without reading secrets or
starting containers. This is preparation/static verification; remote connectivity,
provisioning, transfer, live capture and retention acceptance were not run.
The [manifest](manifest.json) binds every package member except itself.
