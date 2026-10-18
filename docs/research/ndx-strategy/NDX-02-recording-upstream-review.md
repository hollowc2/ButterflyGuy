# Pinned upstream source supplement — 2026-10-15

This read-only source review followed the registered SQLite recording runs.
It supplements the [implementation record](NDX-02-recording-implementation.md)
without rewriting its source locks or run artifacts. Some static age semantics
are now known for a pinned source revision; historical reference instants,
synchronization and producer deployment attribution remain unavailable.

Local SchwabGateway checkout HEAD was
`806fff5286aeecbdeb19f5129308a45752991bc0`, with clean status. The inspected Git
objects were instead from ButterflyGuy's pinned SDK revision
`0d0125e51266740de0f43c72b540002a4dcfc25d`. Inspecting that source does not establish
that a historical gateway server ran it. No file in the other repository was
modified, no credential material was inspected and no remote connection was made.

The [source trace](evidence/2026-10-15/ndx02-recording-upstream-source-trace.json)
records paths, line references, exact hashes and retained copies under
`reports/research/ndx-02-recording-20261015/upstream-source-review/`.

Observed in `src/schwab_gateway/upstream.py` at that revision:

- `_event_time` chooses the latest positive integer among quoteTime, tradeTime,
  quoteTimeInLong and tradeTimeInLong, interpreting it as epoch milliseconds.
  Consequently this selected event is not necessarily a pure quote-update time.
- `_age_seconds` returns null for missing events; otherwise it clamps
  `(reference - event).total_seconds()` at zero. A recorded zero therefore need
  not mean an event exactly at the reference instant.
- Initial contract normalization uses the gateway UTC clock after the provider
  request returns as received_at. Default UTC source is datetime.now(UTC).
- Cache hits recompute chain and constituent ages at a new evaluation instant,
  while retaining gateway_received_at from the cached chain. Reported age must
  not be subtracted from gateway_received_at or local fetch completion to invent
  event/reference timestamps.
- Finite nonnegative crossed bid/ask endpoints may be reordered with flags;
  supplied mark is converted numerically and left separate. This is a prospective
  normalization-attribution requirement, not proof of any old anomaly's cause.
- The SDK public method returns a validated model from response.json(). The gateway
  API returns a typed option_chain envelope, not the selected-leg fixture envelope.
  Neither observed public interface supplies original provider body bytes.

Concrete upstream requirements are therefore more specific: expose response/body
identity at an explicitly reviewed boundary, the actual per-response freshness
reference instant, clock/process/build identity, cache-hit/coalescing provenance
and normalization flags/source values. Preserve the distinction between native
provider body, gateway-normalized body and selected-leg derivative. Clock offset/
uncertainty measurements and effective deployed cache/normalization settings are
still separate evidence needs. No physical bound or filter threshold is selected.

This source discovery changes no frozen historical result or eligibility. The
17 old paths remain ineligible; no clock is reconstructed and no new market
coverage, order, capture or economic experiment results from reading source.
