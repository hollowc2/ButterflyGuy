# Standalone SchwabGateway Extraction Plan

This file is the single append-only evidence ledger for extracting the deployed read-only
Schwab gateway into `hollowc2/SchwabGateway`. The local checkout is
`/mnt/Repos/Trading/SchwabGateway`; the Helios checkout will be `/opt/schwab-gateway`.

The initial release is parity-only. It preserves `/health`, `/ready`, `/metrics`,
`/v1/quotes`, `/v1/spot`, and `/v1/chain`. It does not add history, full option-chain
rows, streaming, account, position, transaction, or order routes. ButterflyGuy direct
Schwab access remains authoritative throughout the extraction.

## Progress rules

Phase states are `NOT STARTED`, `IN PROGRESS`, `BLOCKED`, and `COMPLETE`.

- Complete a checkbox only after its acceptance gate passes.
- Append a dated progress-log row after every material checkpoint; do not rewrite prior rows.
- Evidence must be a commit, tag, test result, image ID, or deployment observation.
- Never record tokens, keys, account identifiers, or secret values.
- Record rollback identifiers before every Helios deployment or ButterflyGuy restart.
- Obtain explicit approval before creating/copying secrets, deploying or restarting live
  services, rotating keys, or pushing to `main`.
- Preserve the legacy gateway container and image until the full stability gate passes.

## Phase 0 — Baseline and safety record

Status: `COMPLETE`

- [x] Record the 2026-08-10 Helios baseline: checkout `/opt/butterflyguy`; branch `main`;
  commit `e851c22152878b44ea748bbf8ad86b5d7871f517`; container
  `butterfly_schwab_gateway_live`; image
  `sha256:6eb9f560effae529a2f578b5a4e5a1b0da2fd124cb4566fe9b097f01ec8b0ec8`;
  healthy on `monitoring_net`; restart policy `unless-stopped`; `/opt/schwab-gateway`
  absent.
- [x] Save this plan to the target tracking file.
- [x] Record the exact ButterflyGuy source commit used for extraction.
- [x] Run and record the focused gateway, token-store, shadow, and `run_live` baseline.
- [x] Capture redacted golden HTTP fixtures for all current success and error contracts.
- [x] Confirm XSP shadow mode is disabled and SPX/NDX have no gateway client configuration.
- [x] Confirm no open/working broker state before any later trading-service restart.
- [x] Record the legacy gateway restore command and verify the existing container can be
  restarted without rebuilding it.

Acceptance: reproducible local tests, API fixtures, current deployment identifiers, and a
rollback procedure are recorded before source extraction begins.

## Phase 1 — Create the standalone repository

Status: `COMPLETE`

- [x] Create public repository `hollowc2/SchwabGateway` and local checkout.
- [x] Import from the recorded source commit and add `MIGRATION_PROVENANCE.md`.
- [x] Configure a `uv` workspace containing `schwab_gateway`, `packages/sdk` producing
  `schwab_gateway_sdk`, and `packages/token-store` producing `schwab_token_store`.
- [x] Move the server, live adapter, token manager, authentication, admission, redaction,
  handlers, operator CLIs, deployment, alerts, and focused tests.
- [x] Add a minimal Dockerfile/dependency set excluding ButterflyGuy trading dependencies.
- [x] Add secret-safe ignores, examples, README, demo instructions, Helios and rollback
  runbooks, and CI covering tests, Ruff, builds, wheel installation, Compose rendering,
  and secret-path exclusion.
- [x] Confirm the repository contains no secrets, account identifiers, or evidence artifacts.

Acceptance: the standalone repository builds and tests without ButterflyGuy installed or
present.

## Phase 2 — Remove program-specific coupling

Status: `COMPLETE`

- [x] Remove every `butterfly_guy.*` import.
- [x] Add standalone logging and Prometheus setup while preserving gateway metric names and
  bounded labels.
- [x] Define server-owned upstream protocols.
- [x] Move version-1 wire models and `GatewayMarketDataClient` into `schwab_gateway_sdk`.
- [x] Preserve names, fields, timestamps, validation, statuses, timeouts, and error mappings.
- [x] Check in a matching OpenAPI 3.1 contract.
- [x] Make validated unique caller IDs configuration-driven while preserving the version-1
  keys document, capabilities, priority classes, duplicate checks, and permission checks.
- [x] Limit capabilities to `market_data:read`; update key issuance to accept application ID,
  capability, and `protected`/`background` explicitly.
- [x] Preserve the `butterfly-guy`, `equity-scanner`, and `afterhours-lab` identities and keys;
  do not rotate keys.
- [x] Assert no account/order route exists and order writes cannot be enabled.

Acceptance: zero ButterflyGuy imports, existing key configuration loads unchanged, and golden
contracts match the original gateway.

## Phase 3 — Package and contract parity

Status: `COMPLETE`

- [x] Test SDK and token-store wheels independently in empty environments.
- [x] Prove old/new token stores contend on the same lock and reject torn/stale-lineage writes.
- [x] Exercise demo mode over real HTTP from the standalone repository.
- [x] Compare health/readiness, authentication/capabilities, quote/spot/chain normalization,
  missing/stale/malformed data, bounded failures, metrics/log redaction, and shutdown recovery.
- [x] Build an unprivileged, read-only-root-filesystem Docker image.
- [x] Tag immutable release `v0.1.0` and confirm public Git-tag dependency resolution without
  credentials.

Acceptance: `v0.1.0` is reproducible, contract-compatible, and independently runnable.

## Phase 4 — Prepare ButterflyGuy to consume shared packages

Status: `COMPLETE`

- [x] Pin SDK and token-store Git-tag dependencies to `v0.1.0`; lock immutable SHAs.
- [x] Migrate direct wrapper, candidate feed, keepalive, and token utilities to
  `schwab_token_store`.
- [x] Keep the consumer-specific shadow comparator in ButterflyGuy; import contracts/client
  from `schwab_gateway_sdk`.
- [x] Remove duplicate token-store code; use only temporary compatibility re-exports needed
  for reviewability.
- [x] Prove no-shadow constructs no gateway client and direct results remain authoritative.
- [x] Run focused/full tests, Ruff, package build, Compose render, and `graphify update .`.
- [x] Record the ButterflyGuy commit and candidate image IDs without deploying.

Acceptance: the complete ButterflyGuy suite passes with no strategy, risk, execution, account,
order, paper/live, or default-access change.

## Phase 5 — Parallel Helios candidate

Status: `COMPLETE`

- [x] Obtain explicit approval to provision `/opt/schwab-gateway`, copy secrets, and start a
  candidate.
- [x] Check out `v0.1.0`; use only Schwab app credentials and gateway settings.
- [x] Reuse `/opt/butterflyguy-tokens` unchanged; copy digest-only keys at mode `0600` without
  rotation.
- [x] Start `schwab_gateway_candidate` on `8012`, only on `monitoring_net`; leave legacy and
  ButterflyGuy services unchanged.
- [x] Validate health/readiness/metrics/logs/recovery/authenticated routes and concurrent
  old/new reads with token-lock safety.
- [x] Compare bounded structures/quality flags and observe one complete market session without
  readiness, authentication, persistence, or lock anomalies.

Acceptance: candidate completes a market session while legacy gateway and ButterflyGuy remain
healthy and unchanged.

## Phase 6 — Standalone production cutover

Status: `COMPLETE`

- [x] Obtain explicit deployment approval and record IDs, token metadata, monitoring state,
  and rollback commands.
- [x] Configure project `schwab_gateway`, container `schwab_gateway_live`, network alias
  `schwab-gateway`, port `8011`, and loopback-only publication.
- [x] Stop but preserve the legacy container; start standalone `v0.1.0`.
- [x] Change the Prometheus scrape target, validate, and hot-reload monitoring.
- [x] Validate routes, authenticated reads, metrics, alerts, logs, network, restart policy,
  recovery, and unchanged ButterflyGuy direct access.
- [x] On failure, stop standalone, restart legacy, restore monitoring, and log rollback.

Acceptance: standalone production is healthy and monitored; ButterflyGuy is unchanged.

## Phase 7 — ButterflyGuy deployment and embedded-code removal

Status: `IN PROGRESS`

- [ ] Obtain explicit approval before any trading-service rebuild/restart and pass broker/DB
  flatness and unknown-order gates.
- [ ] Deploy one service at a time, preserving image IDs and validating health, token reload,
  logs, reconciliation, uniqueness, and direct access.
- [x] Change XSP's default shadow URL to `http://schwab-gateway:8011`; keep shadow disabled.
- [x] Remove embedded gateway server/SDK/runner/CLIs/Compose/alerts and compatibility exports
  after standalone proof; retain only Butterfly-specific shadow/configuration.
- [x] Update docs/runbooks/graph and archive historical proof documents without rewriting
  historical evidence.

Acceptance: ButterflyGuy runs without embedded gateway implementation; direct trading,
reconciliation, and token handling are unchanged.

## Phase 8 — Stability window and legacy retirement

Status: `NOT STARTED`

- [ ] Run standalone for seven consecutive days including one full market session and one
  scheduled token reauthorization/reload lineage cycle.
- [ ] Confirm monitoring has no unexplained downtime, persistence/lock/auth degradation and
  ButterflyGuy has no decision or broker-safety regression.
- [ ] Obtain explicit approval before removing the stopped legacy container or obsolete
  Helios artifacts; preserve release/image/migration/rollback evidence.

Acceptance: legacy is not needed for the full stability window.

## Phase 9 — Consumer onboarding

Status: `NOT STARTED`

- [ ] Document base URL, API-key header, timeouts, errors, readiness, and data quality.
- [ ] Add a minimal Python example pinned to `v0.1.0`, history-safe curl examples, SSH-tunnel
  access, and fake-client fixtures.
- [ ] Preserve or issue separate background identities for `equity-scanner` and
  `afterhours-lab`.
- [ ] Verify two independent consumers without ButterflyGuy or Schwab credentials.
- [ ] Track history, full chains, instruments, market hours, and streaming separately; do not
  build Equity Scanner or AfterHoursLab here.

Acceptance: either future application can install the SDK and consume the versioned interface
with an independent key and no ButterflyGuy dependency.

## Required test matrix

- Unit: models, auth, admission, redaction, token store, normalization, configuration.
- Contract: exact original fixtures and OpenAPI schemas/statuses.
- Packaging: independent wheels with no unintended ButterflyGuy dependencies.
- Boundary: zero standalone ButterflyGuy imports; zero Butterfly strategy/risk/execution
  gateway-server imports.
- Concurrency: old/new token-store lock and stale-lineage behavior.
- Docker: demo/live Compose, unprivileged/read-only restrictions.
- Butterfly regression: complete tests, Ruff, build, Compose render, graph update.
- Live candidate/production: health, readiness, auth reads, metrics, recovery, monitoring,
  token lifecycle, direct continuity, and rollback drill.

## Fixed defaults

- Canonical application is `AfterHoursLab`, principal `afterhours-lab`.
- The repository is public; runtime secrets remain external and ignored.
- Consumers use immutable public Git tags recorded by SHA in `uv.lock`.
- Access remains on Helios's Docker network; remote development uses SSH tunneling.
- API schema remains `1.0`, market-data-only, and read-only.
- Direct Schwab access remains ButterflyGuy's authoritative path.
- Account/order migration requires a separate explicitly approved plan.

## Progress log

| Date | Phase | Status | Evidence | Notes / rollback |
|---|---|---|---|---|
| 2026-08-10 | Baseline | COMPLETE | Helios commit `e851c221`; legacy image `sha256:6eb9f...0ec8` | Gateway healthy; standalone checkout absent |
| 2026-08-10 | Phase 0 | IN PROGRESS | extraction source `122c4ba9451a5349d4edd99024342ba9673637a9` | Existing unrelated documentation edits preserved |
| 2026-08-10 | Phase 0 | IN PROGRESS | focused baseline: `332 passed, 1 warning in 9.92s` | `.venv/bin/python -m pytest`; no broker writes or live changes |
| 2026-08-10 | Phase 0 | IN PROGRESS | `tests/fixtures/schwab_gateway_http_v1.json` | Synthetic/redacted v1 success, readiness, auth, validation, capacity, timeout, unavailable, and malformed contracts |
| 2026-08-10 | Phase 0 | IN PROGRESS | `infra/docker-compose.yml` source inspection | Only XSP declares gateway variables; access is `direct` and shadow defaults `false`; SPX/NDX declare none |
| 2026-08-10 | Phase 0 | BLOCKED | Helios SSH authentication refused by local agent | Current remote revalidation deferred; no remote state changed |
| 2026-08-10 | Phase 1 | COMPLETE | public `hollowc2/SchwabGateway`; local commit `2d1da47` | Local `main` only; GitHub repository intentionally remains unpushed pending explicit approval |
| 2026-08-10 | Phase 2 | COMPLETE | standalone `230 passed`; Ruff clean; zero-import AST test | Golden v1 models/errors and exact six-route OpenAPI boundary pass |
| 2026-08-10 | Phase 3 | IN PROGRESS | three distributions built; SDK/token-store empty-environment imports pass; Compose renders | Docker image build blocked: local Docker service is inactive and could not start; no image/tag created |
| 2026-08-10 | Phase 3 | IN PROGRESS | `cross-token-store-lock-and-lineage-ok` | Old/new processes shared `.tokens.json.lock`; new timed out behind old, stale old callback was rejected, generation 2 remained intact |
| 2026-08-10 | Phase 1 | COMPLETE | public `main` at `2d1da47b37ba48e3603f8d52a2fe73a55924aaf0` | Approved push completed; no secret, deploy, or runtime action |
| 2026-08-10 | Phase 3 | COMPLETE | GitHub Actions run `31460632109`; annotated tag `v0.1.0` → `2d1da47b` | CI tests/Ruff/builds/wheel installs/Compose/Docker/boundaries passed; public tag installs resolved without credentials |
| 2026-08-11 | Phase 4 | IN PROGRESS | lock resolves both packages to `2d1da47b`; focused `332 passed`; full `1009 passed, 1 skipped`; Ruff/build/Compose/graph pass | Direct remains authoritative; no runtime default changed; candidate image unavailable because local Docker is inactive |
| 2026-08-11 | Phase 4 | IN PROGRESS | ButterflyGuy commit `6884cc2` | Local commit only; existing unrelated documentation edits remain unstaged; no image built or service changed |
| 2026-08-11 | Phase 0 | COMPLETE | Helios `e851c221`; legacy image `sha256:6eb9f...0ec8`; broker gate `flat` | Legacy container healthy and image present; restore is `docker start butterfly_schwab_gateway_live`; no restart performed; DB has 2 OPEN rows and 0 nonterminal intents, so a later trading-service restart is not authorized |
| 2026-08-11 | Phase 4 | IN PROGRESS | candidate build of `6884cc2` failed before image export | Slim image lacked Git for immutable public dependencies; no container or service changed |
| 2026-08-11 | Phase 4 | COMPLETE | ButterflyGuy `03be00c`; candidate image `sha256:3c2e944c25cdc3a0d1dba05258a1a10fcb07b6f0e3063a524869e5950ea4c91a` | Image imports SDK/token-store `0.1.0` as unprivileged user under read-only/no-network smoke; zero candidate containers running; no deployment |
| 2026-08-11 | Phase 5 | IN PROGRESS | explicit owner approval; standalone `v0.1.0`; legacy `e851c221` / `sha256:6eb9f...0ec8` | Approved provision/secret copy/candidate start only. Rollback: `docker stop schwab_gateway_candidate`; legacy remains running and monitoring/trading services remain unchanged |
| 2026-08-11 | Phase 5 | IN PROGRESS | checkout `2d1da47b`; candidate image `sha256:d31e679d...5ef04`; container `edfff43e658e` | Candidate is healthy on loopback `8012` and `monitoring_net`, unprivileged/read-only; protected environment and digest-only keys are mode `0600`; rollback remains `docker stop schwab_gateway_candidate` |
| 2026-08-11 | Phase 5 | IN PROGRESS | health/ready/metrics `200`; quote/spot/chain parity `200`; restart count `1` | Concurrent legacy/candidate structures, quality flags, and prices matched within tolerance; token inode/size/mtime stayed unchanged; genuine process crash recovered; legacy and SPX/NDX/XSP stayed unchanged. Full-market-session observation remains pending |
| 2026-08-15 | Phase 5 | COMPLETE | candidate `edfff43e658e` / `sha256:d31e679d...5ef04`; Aug 14 session `4,364` readiness checks at `200`; fresh quote/spot/chain parity `200` | Candidate ran continuously across Aug 12–14 with no restart after the deliberate recovery drill; retained full-session logs contained no readiness, lock, persistence, refresh, or recovery anomaly; an atomic shared-token refresh completed during concurrent parity reads and both gateways remained ready; legacy and SPX/NDX/XSP stayed unchanged. Rollback remains `docker stop schwab_gateway_candidate` |
| 2026-08-15 | Phase 6 | IN PROGRESS | predeployment: legacy `675a04e26b1c` / `sha256:6eb9f...0ec8`; standalone candidate image `sha256:d31e679d...5ef04`; candidate `edfff43e658e` healthy | Approved cutover. Rollback backups: `/opt/monitoring/prometheus.yml.phase6-precutover-20260815T165054Z`, `/opt/monitoring/prometheus-alerts/schwab-gateway.yml.phase6-precutover-20260815T165054Z`; restore: stop `schwab_gateway_live`, `docker start butterfly_schwab_gateway_live`, restore both files, validate with promtool, hot-reload Prometheus, then recheck legacy health/readiness/metrics/scrape. |
| 2026-08-15 | Phase 6 | ROLLED BACK | standalone `11f588627c88` / `sha256:d31e679d...5ef04`; legacy `675a04e26b1c` / `sha256:6eb9f...0ec8` | Prometheus standalone-target acceptance did not complete in the validation window. Automatic rollback stopped standalone, restored the legacy container and backed-up Prometheus target/alert file, hot-reloaded Prometheus, and confirmed the legacy target up with no gateway alerts firing. Further deployment debugging stopped pending explicit direction. |
| 2026-08-15 | Phase 6 | BLOCKED | Prometheus host config inode `3182329`; running bind-mount inode `3146871`; standalone runbook fix `5fdb728` | Root cause confirmed: `sed -i` replaced the host file while the running Prometheus container remained bound to the old inode, so both successful reloads read the legacy target. Corrected deployment and rollback write the rendered configuration in place to both host and container views, validate both views, then reload and require the exact target up. Focused runbook regression: `5 passed`; Ruff clean. Live retry requires renewed approval. |
| 2026-08-15 | Phase 6 | IN PROGRESS | corrected retry approved; legacy `675a04e26b1c` / `sha256:6eb9f...0ec8`; standalone `11f588627c88` / `sha256:d31e679d...5ef04`; candidate `edfff43e658e` healthy | Fresh rollback backups: `/opt/monitoring/prometheus.yml.phase6-retry-precutover-20260815T205609Z`, `/opt/monitoring/prometheus-alerts/schwab-gateway.yml.phase6-retry-precutover-20260815T205609Z`. Corrected rollback writes the saved config in place to both host and container views, starts the preserved legacy container, validates rules/config, hot-reloads Prometheus, and requires the legacy target up. |
| 2026-08-15 | Phase 6 | ROLLED BACK | standalone retry `11f588627c88` / `sha256:d31e679d...5ef04`; legacy restored `675a04e26b1c` / `sha256:6eb9f...0ec8` | Bind-safe synchronization reached the running container but its Prometheus user is `65534:65534`; the config is `0664`, owner `1001:1001`, so the write was denied before reload. Automatic rollback restored legacy health/readiness/metrics and the legacy Prometheus target; candidate and SPX/NDX/XSP remained unchanged. Least-privilege correction: perform only the one-shot config write as `1001:1001`; live retry requires renewed approval. |
| 2026-08-15 | Phase 6 | IN PROGRESS | config-owner retry approved; legacy `675a04e26b1c` / `sha256:6eb9f...0ec8`; standalone `11f588627c88` / `sha256:d31e679d...5ef04`; candidate authenticated quote/spot/`$SPX` chain/401 contracts passed | Fresh rollback backups: `/opt/monitoring/prometheus.yml.phase6-retry2-precutover-20260815T210203Z`, `/opt/monitoring/prometheus-alerts/schwab-gateway.yml.phase6-retry2-precutover-20260815T210203Z`. Only the one-shot container config write uses owner `1001:1001`; Prometheus remains `65534:65534`. Automatic rollback restores both inode views, legacy, monitoring, and validates the legacy target. |
| 2026-08-15 | Phase 6 | ROLLED BACK | standalone `11f588627c88` / `sha256:d31e679d...5ef04` reached healthy monitored production; legacy restored `675a04e26b1c` / `sha256:6eb9f...0ec8` | Config-owner synchronization, promtool validation, hot reload, exact `schwab-gateway:8011` target-up, rules-loaded, and no-alert gates passed. A later production validation assertion failed without emitting its step identifier, so automatic rollback restored legacy health/readiness/metrics, both Prometheus views, and the legacy target. Candidate and SPX/NDX/XSP remained unchanged; crash recovery was not attempted. Further diagnosis requires explicit direction. |
| 2026-08-15 | Phase 6 | BLOCKED | candidate replay: quote/spot/`$SPX` chain/401 schemas pass; token-ready metric passes; stopped-production anomaly count `0` | Root cause was the inline validator: the `ports=...` and `aliases=...` assignments lacked a newline, concatenating the alias assignment into `ports`; the port assertion—not production—triggered rollback before authenticated smoke. The runbook now requires distinct assignments and `CHECK`/`PASS` markers for every gate. Live retry requires renewed approval. |
| 2026-08-15 | Phase 6 | IN PROGRESS | final step-labelled retry approved; legacy `675a04e26b1c` / `sha256:6eb9f...0ec8`; standalone `11f588627c88` / `sha256:d31e679d...5ef04`; candidate `edfff43e658e` healthy | Fresh rollback backups: `/opt/monitoring/prometheus.yml.phase6-final-precutover-20260815T213848Z`, `/opt/monitoring/prometheus-alerts/schwab-gateway.yml.phase6-final-precutover-20260815T213848Z`. Every gate emits `CHECK`/`PASS`; automatic rollback restores both Prometheus inode views, legacy, monitoring, and requires the legacy target up. |
| 2026-08-15 | Phase 6 | COMPLETE | production `11f588627c88` / `sha256:d31e679d...5ef04`; healthy after controlled crash at `2026-08-15T21:42:49Z`; restart count `1`; Prometheus target `schwab-gateway:8011` up | Project `schwab_gateway`; loopback `8011`; monitoring-only alias; `1001:1001`; read-only root; no-new-privileges; all capabilities dropped. Quote/spot/`$SPX` 2026-08-17 chain returned `200`; bounded unauthenticated contract returned `401`; token-ready metric and both alert rules valid with no firing alerts; bounded anomaly count `0`. Legacy `675a04e26b1c` / `sha256:6eb9f...0ec8` is preserved stopped; candidate remains healthy; SPX/NDX/XSP IDs, images, starts, and restart counts are unchanged; direct access remains authoritative and shadow disabled. Rollback uses the final pre-cutover backups recorded above. |
| 2026-08-15 | Phase 7 prep | BLOCKED | Helios token `creation_timestamp` remained `2026-08-10T20:23:30Z`; DB gate passed; authenticated broker initialization returned Schwab `invalid_grant` | The copied document was the revoked Aug 10 lineage, so the approved rebuild stopped before any image build, container restart, or runtime mutation. A newer local Aug 15 lineage was verified with the read-only broker audit before replacement; no secret value was emitted. |
| 2026-08-15 | Phase 7 prep | IN PROGRESS | ButterflyGuy `16d9c86`; token created `2026-08-15T21:36:48Z`, mode `0600`, `1001:1001`; DB unsafe count `0`; broker SPX/NDX/XSP positions, active orders, and unknown statuses all `0` | Corrected token installed under the shared lock. Approved full application/candidate rebuild baseline images: SPX `sha256:377ae0b...55aa6`, NDX `sha256:8f90a18...bc77`, XSP `sha256:801ff60...3d24`, feed `sha256:f9df84d...97274`, six candidates `sha256:24a14da...c7e4`, `ba3343a...2735`, `2b2bdf0...a7574`, `3074ab5...b1f0`, `ba968cc...d0df9`, and `6208657...e957`. Exact recovery tags use `butterfly-phase7-rollback-<service>:20260815T2225Z`; database, monitoring, standalone gateway, stopped legacy gateway, and stopped legacy candidate remain out of scope. |
| 2026-08-15 | Phase 7 prep | COMPLETE | deployed source `5be6630`; SPX `sha256:e2b7c0c...d17e9`, NDX `sha256:da381f8...7e44`, XSP `sha256:26951e7...1634`, feed `sha256:74b0c0e...5a1e`; candidates `sha256:43e73b9...79b8`, `4820dc1...09fd`, `d93a3a0...1173`, `90b91e6...2600`, `4da3cd4...e666`, `15355db...bbbe` | No-cache builds and unprivileged/read-only image smokes passed after adding Git to the candidate image. SPX, NDX, XSP, feed, and six paper evaluators were recreated one at a time; each passed image, readiness/health, token where applicable, clean-log, zero-restart, uniqueness, reconciliation/direct-access, and rollback-armed gates. Fleet settle: `10` running, `9` ready endpoints, feed health up, `6` token views equal, DB unsafe count `0`, final broker SPX/NDX/XSP positions/active orders/unknown statuses all `0`, standalone Prometheus target up, gateway alerts `0`. XSP remains direct with shadow disabled; database/monitoring/standalone and both stopped rollback services were unchanged. Recovery tags from the predeployment row are retained. Phase 7 embedded-code removal remains `NOT STARTED`. |
| 2026-08-15 | Phase 7 removal | IN PROGRESS | ButterflyGuy baseline `44e6184`; focused pre-change matrix `139 passed`; standalone tag `v0.1.0` → `2d1da47b`; both lock entries resolve `2d1da47b` | Worktrees were clean before editing. Standalone `main` is newer, but its SDK/token-store trees match `v0.1.0`; no untagged revision was consumed and no live or broker action occurred. |
| 2026-08-15 | Phase 7 removal | IN PROGRESS | focused retained matrix `187 passed`; full suite `630 passed, 1 skipped`; Ruff, wheel/sdist build, SPX/NDX/XSP Compose renders, immutable-pin/package/static boundaries, and `graphify update .` passed | Embedded server/operator/credential-proof code, compatibility exports, Compose, alerts, and key templates are removed; XSP defaults to `schwab-gateway:8011` with shadow false; direct trading/token consumers are unchanged. Deploying this removal build requires fresh explicit approval and broker/DB gates; no service was rebuilt or restarted. |
| 2026-08-15 | Phase 7 removal | IN PROGRESS | local implementation commit `d643b08` | Cohesive removal and local evidence were committed on `main` without pushing. The local repository is ready for a separately approved staged rollout; deployed source remains the earlier recorded Phase 7 prep build, so Phase 7 is not complete. |
