# Schwab gateway current status

Status date: 2026-09-11

This is the current Butterfly Guy status record for Schwab gateway ownership and deployment. It
supersedes the former extraction plan, phase prompts, cutover handoffs, and dated transition
runbooks. Those files remain available under `docs/archive/schwab-gateway/` as historical evidence;
they are not operating instructions.

## Current state

- The gateway server is maintained and deployed from
  [`hollowc2/SchwabGateway`](https://github.com/hollowc2/SchwabGateway).
- Butterfly Guy consumes `schwab-gateway-sdk` v0.4.4 from commit
  `e04afbdf40f4dcf7d7241dac41c8dd90ce96362a`, as pinned in `pyproject.toml` and `uv.lock`.
  `schwab-token-store` remains pinned to `v0.1.0`.
- The deployed PAPER SPX, NDX, and XSP strategies use gateway market data as the authoritative
  read path. The deployment overlay sets `SCHWAB_ACCESS_MODE=gateway` and
  `SCHWAB_GATEWAY_SHADOW_READS=false`.
- Gateway market-data coverage includes quotes, spot, movers, history/session history, full option
  chains, and order books. The gateway does not own accounts, positions, transactions, or order
  writes.
- Butterfly Guy's direct Schwab client remains the owner of account, order, transaction,
  reconciliation, and token operations. This separation is intentional and unchanged by the
  market-data cutover.
- The base Compose file retains opt-in gateway settings for local development and rollback. It is
  not a statement of the deployed PAPER mode.

## Runtime boundaries

`src/butterfly_guy/scripts/run_live.py` constructs the direct broker client for broker operations,
then selects `GatewayAuthoritativeMarketDataProvider` when `SCHWAB_ACCESS_MODE=gateway`. The
collector, entry logic, position monitoring, settlement reads, and strategy history reads use that
provider. Gateway failures fail closed according to the provider freshness and quality checks.

The old standalone `src/butterfly_guy/scripts/run_collector.py` was removed because it had no active
deployment reference and constructed a direct-only market-data path. Collection is part of the
gateway-aware `run_live.py` orchestration.

## Deferred Helios cleanup

The experimental candidate fleet's source and local deployment definitions have been retired from
this repository. The items below are stopped Helios artifacts retained only for rollback/evidence;
they are not current Butterfly Guy runtime dependencies.

The following stopped artifacts are retained pending an explicit decision on rollback and evidence
retention:

- the stopped legacy embedded gateway container;
- the stopped candidate feed and six candidate evaluators;
- the older stopped legacy candidate.

Do not remove these containers or their images until rollback identifiers, required evidence, and
the retention period have been agreed and the cleanup has been explicitly approved. This document
does not authorize any Helios mutation.

## Historical record

Use the archive index for the former extraction ledger, execution prompts, handoff, dated soak
launchers, and deployment/reauthorization runbooks. New operational facts belong in this document
or in the standalone SchwabGateway repository; do not revive archived phase checklists.
