# Read-only broker flatness audit — 2026-10-16 UTC

**Passed for the existing helper's declared scope. Capture remains disabled.**
Corey explicitly authorized proceeding after being told that this account/order
audit may perform a normal token refresh. This supplements the frozen operational
review; its earlier no-token-operation constraint and missing broker evidence
describe the prior stage, not the newly authorized audit.

Observed 05:50:41–05:50:56 UTC on October 16, through the existing
`butterfly_ndx_app` process environment on Helios. The runtime session date was
October 16. The local existing `gateway_cutover_flatness_audit.py` was streamed
into a new one-shot Python process; no remote source file or service was changed.
Deployed pool/account/order method source was inspected first: pool startup makes
connections without migrations, and the called broker methods are account/order
reads. Normal authentication/token handling used the existing client and shared
token-store guards. No credentials or token values were printed or archived.

Results:

- SPX, NDX and XSP option position counts: zero each.
- Orders returned for the audited entry-date window: zero for each tracked asset;
  no active, missing-status, unmapped-status or duplicate-ID nodes.
- OPEN DB trades: zero; nonterminal broker order intents: zero.
- Existing helper `flat=true`, exit code zero.
- One normal token-write callback invocation observed. This counter is not an
  independent attestation of a token-file write; no token value was inspected.

Order scope is the helper's current-session entry-date query, with its original
naive datetime arguments 2026-10-16T00:00:00 through 23:59:59.999999. Those arguments
are preserved as supplied, not relabeled as attested exchange/UTC instants. This
is **not** an all-history/all-GTC-order inventory and does not establish absence
of older orders outside that query. Positions are the current snapshot for the
three tracked option roots, not a claim about unrelated holdings. Repeat the
appropriate preflight at activation; this observation is not an ongoing guarantee.

The audit's one-connection DB pool was forced read-only with 5 s statement and
1 s lock timeouts. Transient audit-process guards refused malformed account/order
response shapes rather than turning them into empty successful results. Logs and
exception/HTTP context were suppressed in-process; only the known redacted result
keys and categorical failure paths could be returned. No account identifiers,
balances, raw broker payloads, auth headers, token contents or raw logs persisted.
No order was placed/cancelled/replaced, no market-data capture ran, and no live
DDL, research grants, deployment, service restart or strategy change occurred.

The [versioned audit](evidence/2026-10-15/ndx02-observer-broker-flatness-20261016T0550Z.json)
binds exact invocation, source review/helper hash and archive member verification.
Closed source/wrapper/redacted evidence is
`reports/research/ndx-02-observer-20261015/broker-flatness-run-01/`.
Earlier verification and source locks remain unchanged; this operational/docs
step required no code-test rerun or graph refresh.

Next is the concrete one-shot capture plan: exact real NDXP session/three symbols,
calendar/close and acquisition/build/config identity; dedicated research role/key
references and connectivity; immutable image transfer/release identity; storage
reserve/WAL/retention review. Those choices must be concrete before separately
named live schema/grant and one-shot capture approval. No such approval or capture
is implied by the broker audit. The tested image and original trading services
remain unchanged. All historical replay and later NDX research gates still apply.
