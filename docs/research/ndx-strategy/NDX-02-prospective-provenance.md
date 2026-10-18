# NDX prospective provenance v1 — offline specification

Status: **proposed recording contract; offline implementation only**. This is
NDX-provenance-v1, not a replacement for the frozen causal-minute proposal or an
active runtime eligibility rule. The versioned [contract](provenance-v1/contract.json)
links the fidelity run-01, accounting run-02, continuation run-01 and baseline
run-03. Their hashes, original manifests, required membership and source pins
must pass before the checker relies on them. All 17 historical paths retain
false R0-continuation and minute-replay eligibility. No strategy P&L is computed.

## Intended consumer and demonstrated boundary

The primary proposed consumer is `db-research`: an offline NDX minute-evidence
reader using an immutable complete-snapshot manifest and exact snapshot ID.
This fits the existing collector → TimescaleDB → research path. It is a proposed
reader protocol, not a claim that current DB queries implement publication.
`ChainQueries.get_latest_chain` selects MAX(snapshot_time); `get_nearest_snapshot_chain`
selects the timestamp and then rows in separate queries. Neither records the
consumer receipt interval or proves an atomic join to complete provenance.

The secondary `collector-direct` channel is an in-process research observer of
the normalized response returned by collection, before persistence. It is useful
for testing the causal boundary in isolation. It is not the order manager, live
monitor or a replacement trading channel. A collector's fetch completion does
not prove even this observer received a response; record its explicit read and
receipt. DB receipt and direct receipt are different records and clocks.

Local architecture evidence (source hashes are pinned in the new source lock):

- `data/collector.py`, `_collect_timed_snapshot`: pass-start stamp, request wrapper,
  response/observation, parsing and storage; `_store_chain` stores quotes and cache;
  `_store_meta` is a separate operation whose failure leaves quote success intact.
- `data/providers.py`, gateway adaptation: validates and forwards provider mark,
  event time and reported age; may omit contracts and default auxiliary fields,
  including multiplier. Per-contract and chain-wide metadata are different.
  Direct observed adapter has no constituent clocks.
- `data/schwab_client.py`, `get_option_chain`: returns response JSON; original
  response bytes and precision are not preserved by that return value alone.
- `db/queries.py`, `bulk_insert_snapshot` and `insert_snapshot_meta`: quote COPY
  and separate metadata INSERT, with metadata conflicts ignored. Neither stores
  commit/consumer timestamps or immutable publication IDs. Price columns use
  numeric(10,4); they cannot recover original JSON lexical precision.

These are current local source observations, not historical deployment identity.
The frozen runtime bundle does not include collector/provider/DB write source.
SchwabGateway receipt clock, provider event meaning, age calculation/cache policy
and intermediate transformations require upstream build/source and clock evidence.
No other repository was modified and no remote acquisition is needed to establish
that uncaptured original responses and consumer receipts are missing historically.

Proposed sequence: scheduled deadline → pass start → request start → optional
upstream gateway receipt → local response receipt → fetch wrapper completion →
normalization completion. A direct observer then records read start/end and actual
receipt. The DB path additionally records transaction/insert start → a local
post-COMMIT acknowledgement → publication acknowledgement of immutable complete
manifest → consumer query/read start/end → actual receipt of that exact snapshot.
A future potential decision must follow receipt under its own frozen policy;
a potential later fill needs a separately observed eligible quote/order record.
This checker creates neither. Gateway/constituent events need not follow pass
start; events after pass start but before fetch completion are legitimate.

## Field dictionary and claims

The [JSON Schema](provenance-v1/record.schema.json) is generated from strict
Pydantic models in `research/ndx_provenance.py`. Extra fields and coercion are
refused. All fields are required keys; `null` means unobserved/unavailable and
never zero. Unsupported historical fields stay null. The following dictionary
specifies units, ownership and observation points in addition to schema types.
Every field's provenance is the enclosing evidence kind and acquisition ID,
unless explicitly attributed to a clock owner, response or build below.

- `schema_version` is the literal NDX-provenance-v1. `evidence_kind` is synthetic,
  historical or prospective; fixtures, including the historical-shaped case, are
  all synthetic. `record_id`, `snapshot_id`, positive integer `version`,
  `acquisition_id`, `pass_id`, `request_id` are nonempty opaque collector-issued
  identities, not timestamps. `parent_record_sha256` is nullable lowercase SHA-256
  of the previous immutable record for corrections/recovery. `channel` identifies
  one consumer boundary; version changes never silently overwrite a publication.
- `session` is ISO local trading date; `close_utc` is an explicitly calendar-sourced
  session close with UTC offset. Synthetic fixtures stipulate the calendar.
  Neither identifies official settlement or XQC. `expected_symbols` is the
  consumer's predeclared exact three-leg universe, not the entire chain or a
  universe inferred from whatever happened to arrive.
- Each `legs` item identifies exact OCC `symbol`, literal `root=NDXP`, ISO `expiry`,
  CALL/PUT `option_type`, decimal-string `strike` in index points and decimal-string
  positive `multiplier` in dollars per point. Collector normalization must retain
  the supplied value and attribution of any default; a default is not provider
  evidence. Encoded date/type/strike must agree with fields and session.
- Leg `bid`, `ask`, `provider_mark` are nullable decimal strings in option points,
  preserving lexical precision. Sizes are nullable nonnegative integers in
  provider-reported contracts; zero is a real display, not missing. `source` is
  nullable upstream source identity; `flags` are the leg's delivered strings;
  `normalization` is a nullable attributed description of adapter/default changes.
  These support arithmetic/attribution, not complex-order capacity or execution.
  Negative signed composites and mark/midpoint differences survive unchanged;
  no flooring, substitution or P&L-based exclusion. Chain flags cannot label a leg.
- `legs.event` is the original per-contract event stamp, never derived from age.
  `age_seconds` is the provider/SDK nullable decimal-string duration in seconds;
  `age_reference` is the separately observed reference stamp. `age_semantics`
  describes the pinned implementation/formula, reference clock, event clock,
  precision, rounding/tie handling, missing-field behavior and every default.
  If any element is unknown, use null/unavailable evidence rather than claiming
  verified age. No timestamp is calculated by subtracting reported age. Nonnegative
  age is not evidence of synchronization or freshness. No age equality tolerance,
  freshness or dispersion bound is registered here.
- `chain_source` and `chain_flags` are separately nullable source/string flags for
  the response as a whole. They cannot supply missing selected-leg metadata.
- `payload.response_id` identifies the actual upstream response at the preserved
  boundary; nullable relative `path` and SHA-256 `sha256` bind its exact preserved
  market-only body bytes. `scope=market-only-body-v1` excludes headers, credentials,
  account IDs and unrelated sensitive endpoints. `redaction` records allowlist and
  transformation version, original boundary and which original-byte claims were
  lost. Prefer intercepting an exclusively market-data response body before JSON
  conversion; retain exact market number tokens. If a body cannot be preserved
  safely, retain an explicit failure and null path/hash. Never reconstruct an
  original body from database rows or call reserialized JSON original bytes.
  Hashes describe only that boundary; they do not prove provider truth or upstream
  wire bytes. A redacted derivative and original must have separate identities.
- `clocks` maps domain IDs to nonempty `owner`, `process`, `boot`, `source`, nullable
  `sync_evidence` and decimal-string `uncertainty_seconds`, and `discontinuity`
  boolean. Collector/consumer owns its own clock observations; provider/gateway
  clocks require upstream attestation. Synchronization evidence must identify
  measurement interval, offset/error bound and source artifact. Synthetic fixtures
  explicitly stipulate one clock with zero uncertainty; this is no physical claim.
- Every stamp is nullable, otherwise has timezone-aware UTC ISO `wall_utc`, nullable
  nonnegative integer `monotonic_ns` in nanoseconds and `clock` referencing that
  domain. Pair clocks at the observation point. Monotonic scope is the exact
  host/boot/process domain; cross-domain values are incomparable. A restart creates
  a new domain; wall-clock reversal or monotonic reversal is rejected, a declared
  discontinuity or unproved cross-domain ordering is insufficient. Clock uncertainty
  is recorded, not silently used as a widened tolerance. Cross-domain causal proof
  needs a later reviewed protocol; this v1 conservatively refuses to infer order.
- `stamps` has exactly the keys listed in `STAGES` in the checker: deadline,
  pass_start, request_start, gateway_receipt, response_receipt, fetch_completion,
  normalization_completion, insert_start, transaction_start, commit_ack,
  publication_ack, read_start, read_end, consumer_receipt. Deadline is scheduling
  intent; pass start is collector observation; gateway receipt belongs to gateway;
  fetch/normalization are local completion observations. Insert/transaction start
  is the caller's pre-write observation, never commit time. `commit_ack` is a local
  post-commit return bound, not an exact DB server event. `publication_ack` is the
  publisher's acknowledged complete manifest. Read interval and receipt belong to
  the named consumer, after complete decoding. Nulls are allowed for storage and
  missing historical facts, but required channel evidence produces insufficiency.
  Deadline, gateway receipt and transaction start are optional for receipt-chain
  sufficiency; missing upstream evidence cannot establish upstream timing.
- `publication` carries nullable `publication_id`, `transaction_id`, `snapshot_id`,
  `complete_manifest_path` and SHA-256 `complete_manifest_sha256`, plus nullable
  `visibility_evidence` and `failure`. `quote_write` and `metadata_write` independently
  say success/failed/unknown. A DB complete manifest must bind snapshot, exact symbols,
  response hash and successful quote/metadata state. Its bytes/hash/identity are
  checked. Publication requires immutable rows and a complete manifest exposed in
  one consistent transaction/read protocol; a string describing visibility does
  not independently attest a real DB. Real protocol integration remains Stage B.
  Metadata failure after quote success is preserved, not relabelled atomic success.
- `consumer.identity`, nullable `build_sha256`, nullable `returned_snapshot_id`,
  `returned_symbols` and `read_status` attribute the actual response to a reader.
  These come from its receipt record, not the collector. `receipt_observed_at`
  in results is that observation only; earliest possible availability stays null.
  A complete response received after close is a provenance observation and cannot
  create an intraday decision or fill. Failed reads are not missing market prices.
- `builds` maps collector, adapter, gateway, schema, config and dependencies to
  nullable SHA-256 artifact identities; pinned source/build/dependency manifests
  must describe each component and effective non-secret normalization/clock settings.
  `effective_settings` requires provider_channel, age_normalization, clock_policy,
  selected_universe, each a nullable non-secret string. Consumer build is separate.
  No credentials or account settings are retained. `dropped_records` is nullable
  nonnegative integer provenance-drop count; unknown/positive counts cannot claim
  complete coverage. `gap_before_seconds` is nullable decimal-string observed gap,
  never a selected maximum wait or a fabricated market value.

## Storage and failure semantics

Proposed storage is append-only by record ID and snapshot/version/channel.
Retries retain delivery identity; the checker rejects duplicate delivery/identity
rather than counting more evidence. Different IDs for the same version/channel
also conflict. Corrected versions link previous bytes by hash, retain old versions
and never fill missing historical facts without separately acquired evidence.
Consumers correlate request/response/pass IDs and returned snapshot, never nearest
wall time. Out-of-order arrival may be stored in arrival order; validate the
causal sequence before use, do not sort away contradictions.

A proposed DB publisher writes immutable rows, quote/provenance content hashes
and a complete-snapshot manifest with expected membership under one transaction.
It acknowledges locally after commit; a consumer retrieves manifest plus rows
under one consistent snapshot and records returned identity/membership and receipt.
This is intentionally different from the existing two writes. A transaction
start, INSERT success, or local post-commit acknowledgement alone cannot establish
that a different reader saw those rows. Earliest server visibility remains unknown.

Partial-write recovery appends a failure record with known quote/metadata state,
correlation IDs and dropped-count evidence. Retry uses a new version and parent
hash; no incomplete manifest is advertised complete. Missing payload or metadata,
read failure and drop records describe provenance failure separately from quote
presence. No local checker decision alters trading or risk behavior. Runtime
fail-open/fail-closed coupling, budgets, retention capacity and any migrations
must be reviewed in Stage B. No live migration or recording hook is implemented.

## Feasibility and gap ledger

- **Already recorded and verified:** exact historical raw DB legs, bid/ask/mark,
  sizes on complete groups, pass stamps, limited fetch/gateway/constituent fields,
  signed arithmetic and cohort exclusions. The five snapshot manifests, four
  parents and their source pins are checked by this command. See frozen fidelity
  report for coverage; none has consumer receipt or original body bytes.
- **Proposed local implementation:** stable acquisition/request/version IDs,
  market-body preservation at accessible boundary, paired local clocks, normalization
  trace, non-secret build/settings manifests, acknowledged complete DB publication,
  consistent read interval/receipt and drop/failure recovery journal. Source exists
  for these attachment points, but no hook or publisher is activated by this task.
- **Upstream/external dependency:** SchwabGateway SDK/service response identity,
  build and precise age/reference/cache policy; provider event clock and original
  mark/precision semantics; actual clock synchronization evidence across hosts.
  Needed evidence is pinned upstream source, delivered raw market body and clock
  observation artifacts. Local source cannot attest these. Actual complex-order
  order states/fills/costs and official XQC are separate requirements, not generated
  by quotes or this contract. No live orders for calibration.
- **Historically unavailable:** uncaptured original bodies, consumer receipts,
  historical clock synchronization/age references and complete producer deployments.
  Missing data on the 14 untimed trades remains missing. A planned field or synthetic
  receipt does not repair it. Private storage uses the previously accepted Eros
  filesystem; independent backup remains unestablished.

## Offline checker and interpretation

The checker requires explicit input/config/source-lock/output paths, pins inputs,
manifest membership, schema, source and parents, refuses output inside inputs or
existing output directories, and saves source copies and a run manifest. It opens
no broker, network or database connection. Input JSONL is a record sequence;
`results.jsonl` separates `rejected` contradictions from `unknown` evidence and
`diagnostics`. `sufficient` means the asserted receipt-chain record is complete
under this proposed protocol. It does not authenticate arbitrary asserted evidence,
prove synchronization, validate normalization against provider implementation, or
establish an economically usable observation. Synthetic data is always synthetic.

The frozen prior 0.00011-point and one-microsecond tolerances remain confined to
reproducing prior attribution. This checker uses exact decimal arithmetic and
recorded same-domain order, with no new physical tolerance or price threshold.
Freshness, dispersion, gap, fill and terminal policies remain unresolved; every
result has freshness_verified=false, replay_eligible=false and decision/fill=null.
No replay engine is included. See the [reproduction/handoff](NDX-02-provenance-reproduction.md)
and [remaining gates](NDX-remaining-roadmap.md).
