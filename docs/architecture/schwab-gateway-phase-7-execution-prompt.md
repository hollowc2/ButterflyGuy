# Phase 7 Execution Prompt — Remove the Embedded Schwab Gateway

Use the prompt below for the Phase 7 implementation run. It is intentionally self-contained,
but the repository and its append-only extraction ledger remain authoritative if details drift.

```text
/goal

Complete Phase 7 of the standalone SchwabGateway extraction in ButterflyGuy. Work persistently
through implementation and local verification, then stop at any approval boundary that has not
been explicitly granted. Do not start Phase 8 or migrate trading reads, accounts, positions,
transactions, or orders to the gateway.

Objective

Remove ButterflyGuy's embedded Schwab gateway implementation now that standalone v0.1.0 is the
healthy production service on Helios. Keep ButterflyGuy's direct Schwab integration authoritative
and behaviorally unchanged. Retain only the consumer-side, default-off shadow-read integration
that imports the pinned standalone SDK. Change XSP's default shadow URL to
http://schwab-gateway:8011 while leaving shadow reads disabled.

Authoritative context and first reads

1. Read AGENTS.md, README.md, graphify-out/GRAPH_REPORT.md, and, if present,
   graphify-out/wiki/index.md.
2. Read docs/architecture/schwab-gateway-standalone-extraction-plan.md, especially the progress
   rules, Phase 7, fixed defaults, required test matrix, and the latest append-only evidence rows.
3. Read the standalone repository's v0.1.0 migration provenance and current SDK/token-store
   public surface from /mnt/Repos/Trading/SchwabGateway. Treat the tag and uv.lock-resolved commit
   as immutable; do not publish or consume an untagged standalone revision.
4. Inventory all remaining embedded implementation and consumers before editing. Use graphify for
   cross-module relationships and rg for exact references. Classify each reference as embedded
   server/operator code to remove, consumer shadow/direct code to retain, historical evidence to
   preserve, or current documentation/configuration to update.

Required implementation

- Delete src/butterfly_guy/schwab_gateway/ and its server, admission, authentication,
  configuration, live provider, token adapter/manager, upstream normalization, readiness,
  redaction, and credential-probe implementation.
- Delete embedded gateway runners and operator CLIs, including run_schwab_gateway,
  probe_schwab_gateway_credentials, embedded key issuance, and code used only by those commands.
  Prove a file has no retained consumer or token-operation responsibility before deleting it.
- Delete infra/docker-compose.gateway.yml and the obsolete ButterflyGuy-owned gateway alert rules.
  Do not modify the standalone production Compose or Prometheus configuration in this code-removal
  change.
- Remove temporary gateway_client compatibility re-export modules for client, models, config, and
  chain metadata. Update retained callers and tests to import directly from schwab_gateway_sdk.
- Keep src/butterfly_guy/gateway_client/shadow.py, its focused tests and metrics, and only the
  minimal package exports/configuration needed by ButterflyGuy. No-shadow must construct no
  gateway client; every shadow failure must remain swallowed and observed; direct results must
  always be returned.
- Keep schwab-gateway-sdk and schwab-token-store pinned to standalone v0.1.0 and their immutable
  uv.lock SHAs. Keep the shared token-store migration used by direct trading, candidate feed,
  keepalive, and token utilities. Do not reintroduce local copies.
- In infra/docker-compose.yml, change only XSP's default SCHWAB_GATEWAY_URL to
  http://schwab-gateway:8011. Keep SCHWAB_GATEWAY_SHADOW_READS_XSP default false. SPX and NDX must
  remain without gateway-client configuration.
- Remove or rewrite tests that exist solely for deleted embedded code. Retain or strengthen tests
  for SDK import boundaries, shared token-store use, default-off shadow behavior, direct-result
  authority, XSP's standalone alias, absence of account/order gateway routes in ButterflyGuy, and
  zero imports of butterfly_guy.schwab_gateway.
- Update current README/runbooks/architecture navigation to point operators to the standalone
  repository. Preserve historical proof documents as historical records: archive or label them
  where helpful, but do not rewrite old evidence or delete the append-only ledger.
- Append dated Phase 7 evidence rows after material checkpoints. Update Phase 7 status and
  checkboxes only when their actual gates pass. Run graphify update . after code changes.

Non-negotiable safety boundaries

- Do not change strategy parameters, risk limits, schedules, asset selection, paper/live mode,
  account guards, buying-power checks, order construction/routing, reconciliation semantics,
  fill pricing, token paths, token contents, credential values, or token lineage behavior.
- Never print, summarize, copy into Git, or rewrite .env, tokens.json, API keys, account IDs, or
  internal gateway key values. Secret checks may report only presence, ownership/mode, validity,
  and non-secret digests when already established by the runbook.
- Do not enable shadow reads and do not enable any gateway access mode. The gateway remains
  read-only market data; direct Schwab access remains authoritative.
- Preserve unrelated worktree changes. Do not use destructive Git commands. Do not push main,
  deploy, restart a trading service, rotate credentials, or remove the stopped legacy container
  without explicit approval for that exact action.
- Phase 8 owns the seven-day stability window and legacy retirement. Leave the stopped legacy
  container/image and rollback evidence intact.

Execution and verification sequence

1. Establish a clean baseline. Record branch/SHA and status for both repositories. Run the focused
   gateway/shadow/token tests before editing so any pre-existing failure is distinguishable.
2. Add or adjust boundary tests first. They must fail against the embedded tree for the intended
   reason and pass only after removal. Avoid tests that merely grep one known path; cover imports,
   CLI/module entry points, Compose services, alerts, and retained SDK/shadow behavior.
3. Make the smallest surgical removal. Do not refactor unrelated trading code. Remove dependencies,
   imports, variables, fixtures, and documentation made unused by this phase.
4. Run focused tests for shadow reads, configuration, token store/keepalive, direct client, candidate
   feed, reconciliation, and deployment boundaries. Then run uv run pytest, uv run ruff check .,
   package/build validation, and Docker Compose rendering for SPX, NDX, and XSP. Confirm uv.lock
   still resolves the approved standalone tag/commits and that no secret path enters the build
   context or Git index.
5. Run graphify update . and repeat the boundary scan. Required final static proofs: no
   butterfly_guy.schwab_gateway imports or package; no embedded gateway runner/CLI/Compose/alerts;
   no temporary SDK compatibility modules; retained shadow code imports the standalone SDK;
   XSP defaults to schwab-gateway:8011 with shadow false; SPX/NDX remain direct-only.
6. Review the complete diff for trading behavior and secrets. Commit cohesive changes locally.
   Report exact tests, any skipped verification, residual risks, and the proposed live rollout.

Live rollout gate (requires separate explicit approval)

Before any ButterflyGuy rebuild/restart, record the deployed Git SHA and container/image IDs and
prepare exact per-service rollback commands. Require both safety gates to pass immediately before
the window:

- Database count is zero for OPEN butterfly_trades plus broker_order_intents whose status is null
  or not one of FILLED, CANCELED, REJECTED, or EXPIRED.
- A read-only authenticated broker audit over the established lookback finds no SPX/NDX/XSP option
  positions, no active orders, no missing order statuses, and no unmapped statuses. It must make no
  broker write calls and emit no account IDs, symbols, order details, or credentials.

After approval, deploy only the three active trading services, one at a time: SPX, then NDX, then
XSP. Build before the first recreation. For each service, preserve its old image, recreate only
that service, and require healthy/readiness state, expected token metadata/reload, clean bounded
logs, successful reconciliation, exactly one active owner for its asset, direct Schwab access,
and no unknown/duplicate orders before proceeding. XSP additionally must prove shadow is disabled
and its configured default resolves the standalone network alias. Keep database, monitoring,
standalone gateway, candidates, and already stopped services unchanged unless separately approved.

On any failed or ambiguous check, stop the rollout automatically, restore the affected service's
recorded image/configuration, re-run health/reconciliation/uniqueness/direct-access gates, append a
redacted rollback evidence row, and do not continue to the next service. If broker state is not
provably flat or any order status is unknown, make no service change.

Definition of done

Phase 7 is complete only when the implementation and full local matrix pass; the approved staged
Helios rollout passes every per-service gate; ButterflyGuy contains no embedded gateway
implementation; direct trading, reconciliation, and token handling are unchanged; XSP points by
default to the standalone alias with shadow disabled; the append-only ledger and graph are current;
both repository and deployed main are clean and at the recorded commit; and no required work,
temporary artifact, uncommitted change, or unreported skipped check remains. Otherwise keep the
phase IN PROGRESS or BLOCKED with precise evidence and the next safe action.
```
