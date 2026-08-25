# Helios PAPER gateway cutover — 2026-08-25

## Scope

SchwabGateway `v0.2.4` was promoted to the production gateway, followed by a
staged authoritative market-data cutover of PAPER SPX, NDX, and XSP. Account,
token, position, transaction, reconciliation, and order operations remain on
the existing direct broker client. Gateway order writes remain disabled.

Real-money use was not enabled. A real-money XSP workflow must not rely on the
four-second PAPER cache and requires a separately reviewed force-fresh chain
policy.

## Immutable releases

- SchwabGateway tag/commit: `v0.2.4` / `25f9ae007d8dcfff38a51c8d74085f04f6368601`
- SchwabGateway image: `sha256:9c3a1da5e5b8bf259a8146fdea960790cb04a97f0184beef33390fe58b060ec5`
- ButterflyGuy commit: `8b1e8913cc45e5fcd0bc2b0a3cee5e01e20a8029`
- ButterflyGuy image: `sha256:9154ddf82cb1c4841c54c5269408c5c59b965680389be53c50981d393afc8e06`
- Deployed overlay SHA-256: `f232c4d89f64bfebbe401e9ed194f59ed78bf4f26f6f77939b329acb69453db5`
- Versioned overlay SHA-256: `285279280b7c379911f4793c425b05e820270268bd46df7aa745209e31465800`

The gateway was deployed from the clean detached
`/opt/schwab-gateway-v0.2.4` worktree. The strategies were built from the clean
detached `/opt/butterflyguy-gateway-paper-8b1e891` worktree. The dirty legacy
checkouts and their unrelated generated universe files were preserved.

The scoped `butterfly-guy` consumer key is stored separately at
`/opt/butterflyguy-gateway-consumer.env`, mode `0600`. Its value and digest are
not recorded here. Compose must receive the protected ButterflyGuy, gateway,
and consumer env files; rendered Compose output must never be printed.

## Validation evidence

Before the first restart and after every strategy stage:

- database OPEN trades: `0`;
- nonterminal broker intents: `0`;
- authenticated Schwab SPX/NDX/XSP option positions: `0/0/0`;
- active orders: `0`;
- missing or unmapped order statuses: `0`;
- duplicate order IDs: `0`.

Production gateway health/readiness/metrics returned HTTP 200. Authentication,
spot, complete option-chain, minute-history, and session-history contracts
passed. The final 60-second concurrent production test passed SPX, NDX, and XSP
chains `30/30` each, history `4/4`, and spot `6/6`, with no non-200 response.

Each PAPER app is unique, running on the intended image with restart count zero,
read-only root filesystem, all capabilities dropped, and
`no-new-privileges`. Runtime guards showed authoritative gateway mode,
`paper_trading=true`, `allow_live_trading=false`, shadow reads false, and XSP
canary false. Startup logs contained the authoritative-gateway event and no
error, critical, traceback, or exception records.

## After-hours readiness condition

The deployment occurred after market close. Each PAPER app therefore reports
HTTP 503 with the bounded reason `gateway_market_data_warming`: the collector
intentionally waits while the market is closed and cannot clear readiness until
fresh spot, option-chain, and minute-history reads all succeed.

At the next market open, verify all three apps clear that reason after the first
collector cycle. Restore the affected strategy to its retained direct-mode image
if warming persists, data is stale or missing, readiness flaps, latency threatens
the monitoring interval, or any decision divergence appears.

## Retained rollback images

- Gateway: `sha256:e45e70f227f60132751c6e6e2aa6f2035928a64171321a9da44aa851bb671528`
- SPX: `sha256:1ca3485062f8e352e23efce48447b5b3463ee46f6c27ea39bc5da3a2dd9c726d`
- NDX: `sha256:a5d0cb60883b58ddc33e820944423ae83d85c75b412afe6cbf28ba31571e1203`
- XSP: `sha256:e14544ec2b85e42f967038e322c3f991215f968220df16f669a69d0e895c44ac`

Before any rollback recreate, repeat the database and authenticated broker
flatness gates. Restore only the affected service, validate exact image,
uniqueness, PAPER/live guards, health, readiness, and logs, then preserve the
failed gateway evidence for diagnosis.
