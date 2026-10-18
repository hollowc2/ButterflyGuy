# Bounded causal use of independent NDX minute evidence

**Status: reviewable requirements; current evidence insufficient.** This is not
a registered replay, a trading policy or authorization to collect/deploy. The
[fidelity audit](NDX-02-quote-fidelity.md) and immutable parents retain zero
R0/minute eligible trades. A future eligibility policy must have its own contract,
source pins, evidence and run identity, without rewriting these decisions.

## What the distinct times establish

- **Scheduled time:** intended collector deadline, not acquisition or decision
  time. All complete groups lack this field. Do not substitute minute boundaries.
- **Pass start / `snapshot_time`:** collector stamp before requests; keys a batch.
  It cannot establish constituent event time, fetch completion or availability.
- **Constituent event:** recorded provider/gateway contract quote-event stamp;
  available on 444 complete-group legs, absent on 2,898. It indicates the
  recorded event clock, not receipt or guaranteed simultaneous quote liquidity.
  Provider semantics and synchronization need attestation.
- **Gateway receive:** reported gateway receipt of the chain on 148 groups.
  It is neither local consumer receipt nor DB publication. Cross-clock comparisons
  require reference-clock and skew evidence. Chain event/age is distinct from
  each selected contract's event/age.
- **Local fetch start/completion:** collector request interval on 148 groups.
  Completion attests a collector-side stamp after its call returned. It does not
  prove a separate research/live consumer could then read a stored snapshot.
- **Persistence/commit:** quote and metadata writes are distinct in current
  source; no historical commit stamp or atomic publication marker was captured.
  Source ordering cannot manufacture a per-row historical commit time.
- **Consumer availability/receipt:** no recorded consumer read, delivery or
  publication time. This is the critical missing decision boundary. Even an
  observed DB commit needs visibility, query and consumer receipt semantics.
- **Decision and fill:** no independent post-exit minute decisions, orders or
  fills are observed. Neither an exit-event log write nor a later collection
  stamp supplies them. The minute rows are quotes, not a fill journal.

Reported ages remain reported numbers. Do not derive a missing timestamp by
subtracting an age or assume gateway/collector/exchange clocks agree. Retain
known clock differences as diagnostics with the one-microsecond stored equality
allowance; this is not an allowance for physical clock error.

## Supported observations

Exact symbols, expiration/direction/strikes and raw prices/sizes are available
for complete groups. The source has irregular roughly-minute collection, eleven
incomplete groups, measurable gaps, partial clock coverage, negative composite
marks and no availability timestamps. Signed leg-market quotes are diagnostic
execution stress; no simultaneous complex fill is established. These observations
can support descriptive fidelity research now. They cannot supply a causal
post-exit signal/fill path under the requirements below.

## Provisional requirements for a future contract

These are reviewable modeling choices and evidence requirements, **not active
eligibility rules or an implementation**. Fix them before economic evaluation;
never choose thresholds using these sessions' returns.

1. **Availability:** identify the actual consumer and channel. Require an
   immutable snapshot version plus observed delivery/read time after all used
   legs and required metadata are visible. For DB consumers, preserve commit/
   publication identity and consumer query/receipt times; for direct consumers,
   preserve receipt of the exact response. Record wall/monotonic clock mapping,
   clock source, synchronization uncertainty and build/config identity.
   Collector completion can only be a collector-local availability assumption
   for that collector, explicitly provisional; it cannot backdate a DB consumer.
2. **Decision cadence:** prefer event-driven decisions at actual eligible
   snapshot receipt times. Process snapshots in known availability order, with
   deterministic duplicate/out-of-order handling. A fixed-minute decision model
   instead needs separately attested scheduling and receipt by each deadline;
   the current source is not a minute-close bar series. Never resample,
   interpolate or backdate to pass start. Boundary snapshots completing/arriving
   after close require their own session-end treatment; start time alone is
   insufficient.
3. **Next-observation fills:** a candidate quote-fill proxy must use a distinct
   later snapshot whose availability is strictly after the recorded decision
   and any declared order-acceptance delay. Define price basis, costs, quantity,
   price precision and bounded wait before replay. Validate that observation
   and constituent evidence independently. If no next eligible observation
   exists, mark the fill censored/unknown. Never reuse the signal quote for a
   retroactive fill. Quote proxies remain hypothetical; actual complex-order
   feasibility requires broker execution, queue/size and order-state evidence.
4. **Incomplete/invalid groups:** preserve original rows and reasons. Do not
   produce a butterfly observation with missing, duplicate or invalid legs.
   Never fill a missing wing from an earlier timestamp or repair its market.
   A later complete snapshot cannot retrospectively complete the missing one.
5. **Gaps and temporal state:** retain actual adjacent intervals and missing
   buckets. Specify an ex-ante maximum decision/fill wait from the intended
   mechanism, or retain insufficient evidence. Across a disallowed gap,
   confirmation/persistence state and pending fills become unknown/censored;
   do not infer that stops or triggers were not crossed. Specify terminal
   handling without synthetic exits or inventing marks. Parent 30/60/90/120
   diagnostics are descriptive, not automatic acceptance limits.
6. **Constituent freshness:** require event clock, age-reference semantics,
   receive time and synchronization uncertainty for each selected leg. If the
   chosen mechanism needs freshness and any leg is unknown, the observation
   cannot satisfy that contract. A future intentionally timing-agnostic model
   is a distinct assumption with qualified conclusions, not verified freshness.
   Define and justify any age/dispersion limits ex ante; do not tune them from
   P&L or infer a per-leg stale label from chain-wide flags.
7. **Negative composites:** retain signed marks, leg-market bids and anomaly
   categories. They must not silently supply an economic portfolio value or
   fill. The conservative proposed policy is to mark the valuation unusable
   for signals/fills that require admissible butterfly value, with an explicit
   missing-observation state; preserve counts and the resulting censoring.
   Review and freeze this separately before use. No flooring, midpoint
   replacement or retrospectively selected exclusion is permitted. A negative
   leg-market bid remains a diagnostic cost to close and is not a zero fill.
8. **Auditability:** retain original payload/response hash, raw values and
   precision, normalization decisions, source flags, snapshot/version identity,
   exact universe, source/config/dependency pins, all exclusions and output
   hashes. Preserve failed and corrected runs under new identities. Keep these
   development sessions labelled inspected; plan fresh evaluation separately.

## Evidence needed and present feasibility

Consumer availability is missing for every observation, so **none of the 17
trades can currently satisfy the proposed availability contract**. Constituent
timing is additionally absent on 14 trades; historical age-reference semantics
and clock synchronization are unproven even on the three timed trades. Gaps and
negative prices further require a predeclared missing/state policy. There is no
usable cohort under this specification; the audit does not implement or evaluate
one. Official XQC and actual execution evidence remain separate open matters.

The next action is a bounded **prospective provenance specification**: enumerate
minimal fields and storage/channel semantics for original responses, historical
adapter/collector/gateway identities, age clocks, synchronized timing, DB commit/
publication and consumer receipt. Review its feasibility and independent fixtures
before requesting any acquisition or runtime activation. Specification alone
will not recover missing historical facts or authorize strategy experiments.
