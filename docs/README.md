# Documentation map

Use this page to distinguish current operating guidance from research records and
historical evidence. The checked-in configuration and source code remain the
authority for active strategy parameters and runtime behavior.

## Start here

- [`../AGENTS.md`](../AGENTS.md): safety boundaries and repository workflow.
- [`../README.md`](../README.md): project overview, setup, and primary commands.
- [`live-runbook.md`](live-runbook.md): startup, supervision, recovery, and rollback.
- [`architecture/target-trading-platform.md`](architecture/target-trading-platform.md):
  target system boundaries.
- [`architecture/schwab-gateway-current-status.md`](architecture/schwab-gateway-current-status.md):
  current SchwabGateway state and ownership.
- [`reviews/2026-09-25-code-review.md`](reviews/2026-09-25-code-review.md): latest
  repository-wide safety review and ranked follow-ups.

## Operations and data

- [`data-management.md`](data-management.md): historical storage ownership,
  canonical datasets, inventory evidence, and verification commands.
- [`live-runbook.md`](live-runbook.md): paper/live guards and operational recovery.
- [`gateway-order-books.md`](gateway-order-books.md): Level II order-book capture.
- [`equity-market-data.md`](equity-market-data.md): equity candle and depth recording.
- [`data-sources-inventory.md`](data-sources-inventory.md): data-source and schema
  inventory. Treat its dated samples as descriptive evidence, not current runtime
  configuration.
- [`../infra/systemd/README.md`](../infra/systemd/README.md): host timers and services.

## Architecture

The current graph-derived architecture index is
[`../graphify-out/GRAPH_REPORT.md`](../graphify-out/GRAPH_REPORT.md). Check its
recorded commit against `git rev-parse HEAD` before relying on inferred relationships.

Focused current documents:

- [`architecture/target-trading-platform.md`](architecture/target-trading-platform.md)
- [`architecture/schwab-capability-matrix.md`](architecture/schwab-capability-matrix.md)
- [`architecture/schwab-gateway-current-status.md`](architecture/schwab-gateway-current-status.md)

The prior generated application-architecture handoff is preserved as a dated
snapshot under [`archive/application-architecture-2026-07-22.html`](archive/application-architecture-2026-07-22.html).
It is historical evidence, not a current architecture map.

## Research

Research narratives, preregistration, reproducibility records, and dated experiment
packages live under [`research/`](research/). The primary long-running narrative is
[`research/strategy-discovery-journal.md`](research/strategy-discovery-journal.md).

Research Python files under `docs/research/` are experiment artifacts. They are not
installed package entry points, and `test_*.py` files there are not collected by the
default `pytest` command because project test discovery is limited to `tests/`.
Each experiment README or verification record owns its reproduction command.

## Reviews and agent handoffs

- [`reviews/`](reviews/): dated code and architecture reviews.
- [`ai/REVIEW_STATE.md`](ai/REVIEW_STATE.md): retained AI-review state and safety
  constraints.
- [`ai/BRANCH_REVIEW_INTEGRATION_PLAN.md`](ai/BRANCH_REVIEW_INTEGRATION_PLAN.md):
  historical multi-branch integration evidence; its header marks it non-current.

## Archive

[`archive/`](archive/) contains superseded plans, runbooks, architecture snapshots,
and migration evidence. Archive documents may contain old paths, container names,
and runtime assumptions. Do not use them as operating instructions unless a current
document explicitly links to a specific historical procedure.

## Artifact retention

Keep the smallest durable evidence needed to reproduce or audit a decision:

- Version manifests, checksums, configs, verification summaries, final reports, and
  small decision tables.
- Keep raw captures, frozen source copies, caches, and large reproducible intermediate
  output out of Git; store them in the designated evidence or data location.
- Do not remove existing research evidence merely because it is large. Migrate it
  only as a separately reviewed change that preserves checksums and report links.
- Refresh generated graph files at integration boundaries after code changes, rather
  than on documentation-only edits.

## Command ownership

- `src/butterfly_guy/scripts/`: package-aware application, report, collection, and
  backtest entry points, normally run with `uv run python ...`.
- `tools/`: repository and host operational utilities, including authentication,
  health, scheduled reports, and gateway acceptance checks.
- `tools/archive/`: retired operational utilities retained as evidence; not current
  commands.
- `docs/research/**.py`: self-contained experiment code governed by the containing
  research README, not by the main runtime command surface.
