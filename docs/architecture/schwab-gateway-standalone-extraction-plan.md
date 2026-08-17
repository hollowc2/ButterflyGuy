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

Status: `COMPLETE`

- [x] Obtain explicit approval before any trading-service rebuild/restart and pass broker/DB
  flatness and unknown-order gates.
- [x] Deploy one service at a time, preserving image IDs and validating health, token reload,
  logs, reconciliation, uniqueness, and direct access.
- [x] Change XSP's default shadow URL to `http://schwab-gateway:8011`; keep shadow disabled.
- [x] Remove embedded gateway server/SDK/runner/CLIs/Compose/alerts and compatibility exports
  after standalone proof; retain only Butterfly-specific shadow/configuration.
- [x] Update docs/runbooks/graph and archive historical proof documents without rewriting
  historical evidence.

Acceptance: ButterflyGuy runs without embedded gateway implementation; direct trading,
reconciliation, and token handling are unchanged.

## Phase 8 — Stability window and legacy retirement

Status: `IN PROGRESS`

- [ ] Run standalone for seven consecutive days including one full market session and one
  scheduled token reauthorization/reload lineage cycle.
- [ ] Confirm monitoring has no unexplained downtime, persistence/lock/auth degradation and
  ButterflyGuy has no decision or broker-safety regression.
- [ ] Obtain explicit approval before removing the stopped legacy container or obsolete
  Helios artifacts; preserve release/image/migration/rollback evidence.

Acceptance: legacy is not needed for the full stability window.

### Phase 8 stability ledger

- Qualifying start: `2026-08-17T00:39:37.451595824Z`, the latest successfully
  validated Phase 7 application start (`butterfly_xsp_app`) after SPX at
  `2026-08-17T00:35:43.575860619Z` and NDX at `2026-08-17T00:37:12.747255083Z`.
  Seven consecutive 24-hour periods therefore cannot complete before
  `2026-08-24T00:39:37.451595824Z`.
- Continuity: no clock reset is recorded. Fixed-output log, lifecycle, monitoring, runtime,
  database, and resource evidence is complete through `2026-08-17T18:35:11.363397Z`; the
  serialized broker-flatness and post-audit shared-lineage checks are complete through
  `2026-08-17T18:35:29.242914Z`. The candidate feed's Docker log API gap was resolved through
  the existing node-exporter's read-only host mount; every bounded nonempty envelope remains
  well formed and every required anomaly category remains zero.
- Full regular market session: `IN PROGRESS`. Continuous retrospective evidence begins before
  pre-open and is clean through `2026-08-17T18:35:29.242914Z`; market close, settlement, EOD
  charts, and the scheduled report are not yet credited.
- Scheduled token reauthorization/reload-lineage cycle: `PENDING`. The lineage installed
  immediately before this window is baseline evidence only and does not satisfy this item.
- Interruptions / clock resets: none observed. The initial log-retrieval evidence gap was
  resolved read-only without changing the feed, Docker configuration, or any live resource.
- Retained rollback: stopped legacy container/image; standalone `v0.1.0` image; Phase 6
  final monitoring backups; the three `butterfly-token-rebuild-rollback-*` tags stamped
  `20260816T234322Z`; and the XSP Phase 7 removal rollback tag stamped
  `20260816T160420Z`. No rollback artifact was invoked or changed.

#### Scheduled token-cycle approval packet — prepared, not approved

- Proposed window: Saturday `2026-08-22T16:15:00Z` (`09:15 PDT`), while the market is closed,
  after the required Monday full-session proof and before the baseline lineage's seven-day
  deadline. The non-hour boundary avoids the normal hourly keepalive slot and restores a
  Saturday-morning cadence with recovery time.
- Current packet baseline: lineage `2026-08-16T23:34:35Z`; protected regular document mode
  `0600`, owner `1001:1001`; six identical mounted views; lock available; all exact Phase 8
  container identities unchanged; DB open trades/nonterminal intents `0/0`; serialized broker
  SPX/NDX/XSP positions `0/0/0`, active orders `0`, missing/unmapped statuses `0/0`, and
  duplicate IDs `0`. These facts must be re-proved immediately before the window; this packet
  does not authorize proceeding on stale evidence.
- Approval boundary: one interactive reauthorization minted by Corey on Zeus in a real terminal,
  one protected stage to Helios, one protected pre-install backup, and one lock-aware atomic
  install. It authorizes no strategy/config/schedule/network/database change, image build,
  container recreate/restart, legacy action, push, or deletion. The browser/MFA flow is not run
  through an agent because the underlying client can print credential material on an interrupted
  terminal flow.
- Affected readers/writers: `butterfly_spx_app`, `butterfly_ndx_app`, `butterfly_xsp_app`,
  `butterfly_spx_candidate_feed`, `schwab_gateway_live`, and `schwab_gateway_candidate`, plus
  lock-aware host utilities when they next run. Candidate evaluators do not hold the credential;
  the stopped legacy gateway and stopped legacy candidate remain untouched.
- Exact backup: under the shared exclusive lock, retain one mode-`0600`, owner-`1001:1001`
  pre-install copy outside the worktree with redacted identifier
  `phase8-pre-cycle-20260822T161500Z`. Its secret-bearing path and bytes must never enter output or
  Git. Because successful OAuth reauthorization can invalidate the prior refresh lineage, this
  backup is authoritative pre-install evidence but is not assumed usable after the issuer accepts
  the new authorization.
- Stage/install gates: prove the incoming file is regular, nonsymlink, protected, correctly owned,
  schema-valid, newly created, and byte-identical to Corey's staged source using boolean comparison
  only. Refuse an unchanged or older lineage. Acquire the existing exclusive lock with a bounded
  timeout, capture the protected backup, atomically replace the shared document, then prove the
  intended lineage, inode advancement, mode/owner, lock release, and all six identical views.
- Required validation: zero container lifecycle changes; exact IDs/images/start/restarts remain;
  all health/readiness and Prometheus target/token-ready/rule/alert gates pass; SPX/NDX/XSP and the
  feed each emit one successful hot-reload and zero reload failures within the bounded window;
  both gateways authenticate on fresh per-request clients; bounded logs have zero OAuth, lock,
  persistence, readiness, reconciliation, unknown-order, duplicate-order, traceback, or
  error/critical anomalies. Run the runtime image's isolated synthetic stale-callback probe, then
  prove the new live lineage stays monotonic through repeated serialized account/order/position
  audits with every broker count flat and every consumer view still identical.
- Failure/rollback: before atomic install, leave the active document untouched and stop. After
  install, never restore the older backup merely because it exists. If validation fails and the
  prior lineage is still independently proven valid, restoration uses the same exclusive-lock and
  atomic-install gates; otherwise the only safe rollback is one fresh Corey-minted authorization
  followed by the same validation. No fallback restart is included: preserve evidence and pause
  for separate approval if a cached consumer does not reload. Retain staging and backup artifacts
  until cleanup is separately approved.

Explicit Corey approval is required before staging, backing up, replacing, or otherwise touching
credential material in this packet.

Initial fixed-output resource baseline (all timestamps UTC):

| Resource | Full container ID | Full image ID | Started at | Restarts | State / health / readiness |
|---|---|---|---|---:|---|
| `schwab_gateway_live` | `11f588627c88c00312b360451eadb9b56c86542aacfa6a4468e20826f61a02fb` | `sha256:d31e679d15e60e3ca8b794a4ff22ed4c742836cabd102656121a90630ab5ef04` | `2026-08-15T21:42:49.554138686Z` | 1 | running / healthy / `200` |
| `butterfly_schwab_gateway_live` | `675a04e26b1c9b4c2726bfc0cc082b0ccebbb369d0f38fc05e7463eef29d3114` | `sha256:6eb9f560effae529a2f578b5a4e5a1b0da2fd124cb4566fe9b097f01ec8b0ec8` | `2026-08-15T21:06:54.410187984Z` | 0 | preserved stopped; finished `2026-08-15T21:40:04.646047491Z` |
| `butterfly_spx_app` | `ef8c1dbc060f53b51f0cfa31fa3d524cfa9ca6307e6c6f41920d685c6007d162` | `sha256:1ca3485062f8e352e23efce48447b5b3463ee46f6c27ea39bc5da3a2dd9c726d` | `2026-08-17T00:35:43.575860619Z` | 0 | running / `200` / `200` |
| `butterfly_ndx_app` | `0331224f4d131a4bf17603241140717c66cf2da1cc1a92fae81be307c0751ee8` | `sha256:a5d0cb60883b58ddc33e820944423ae83d85c75b412afe6cbf28ba31571e1203` | `2026-08-17T00:37:12.747255083Z` | 0 | running / `200` / `200` |
| `butterfly_xsp_app` | `8979c8c645d87eeb0cbad0acf9c44887b355733d7cb33c98714cb6f0544f3950` | `sha256:e14544ec2b85e42f967038e322c3f991215f968220df16f669a69d0e895c44ac` | `2026-08-17T00:39:37.451595824Z` | 0 | running / `200` / `200` |
| `butterfly_spx_candidate_feed` | `7c58e73b0178b8c7574e01a183f454747c47f3df4e9bc4fab72b624407ae8dc5` | `sha256:74b0c0eed742e4c1f4952bdd1c0ea6af77565e5c3decbf5f987eef3508035a1e` | `2026-08-15T22:56:16.342959487Z` | 0 | running / internal health `200`; log evidence pending |
| `butterfly_spx_candidate_best-rr` | `e812e00e1aa28e180c5ca604793654166fcfa626d16ed89f2f5d606902fc9acd` | `sha256:43e73b9054fbe80fb332e6bf014fdee8329906bb8a911e73f578533bc8e579b8` | `2026-08-15T22:56:46.280166573Z` | 0 | running / `200` / `200` |
| `butterfly_spx_candidate_vix-center` | `07433d2bf03f32eb155a1e59f639967be9971a9b10fd94d428fe046bc36616b4` | `sha256:4820dc10dc83d4fc72fe2de7419dacb2fbaa83abd14d9909609e6f76e62609fd` | `2026-08-15T22:57:10.301630582Z` | 0 | running / `200` / `200` |
| `butterfly_spx_candidate_target-cost` | `e55cd8bed0674723b137686ad3aab14d40a47f1fb72802d880a98f148dc984ad` | `sha256:d93a3a0d7be86763a3cb138bc1abc8d8691e750d33c0cbb916db5861223d1173` | `2026-08-15T22:57:37.639036526Z` | 0 | running / `200` / `200` |
| `butterfly_spx_candidate_gap-conviction` | `a07aaa102caee1849dcf92efb3fcc6efa3fa47ece70a8777515937d782a6bebd` | `sha256:90b91e665899b35374f04c3e1c4dc61906ae90630896ce55c34effe8d6042600` | `2026-08-15T22:58:06.845379052Z` | 0 | running / `200` / `200` |
| `butterfly_spx_candidate_peak-trailer` | `8cb595ccefe75cc1660285066d4f30c13ace026a0113f5e87dc9e93ad0248ac4` | `sha256:4da3cd4ef0386c921b8922c2a2d11b9cc27a71562d375a93709ea7812b08e666` | `2026-08-15T22:58:35.229563554Z` | 0 | running / `200` / `200` |
| `butterfly_spx_candidate_absolute-stop` | `0777f138db85202a6a6e4198d80af404d72f0d208b65f0b3251899d6abb18ede` | `sha256:15355dbb5aeb84c589ae1c477f56ac9bd2ea9c40700893d7df376a13a32fbbbe` | `2026-08-15T22:59:03.193518036Z` | 0 | running / `200` / `200` |
| `schwab_gateway_candidate` | `edfff43e658ec5d92ea700f889647902bb9400a11e71c7b8abe7684e7cafe062` | `sha256:d31e679d15e60e3ca8b794a4ff22ed4c742836cabd102656121a90630ab5ef04` | `2026-08-11T17:15:06.528342560Z` | 1 | running / healthy / `200` |
| `butterfly_spx_candidate` | `fb82c5e4302b10439da5c0067bbb5f01d4170ad0bfc491443aa4a2e3f1b6a9d5` | `sha256:f21f7b928b40f451831a5c1f974d66dfcf74d8f01f5e5ab602c1d537ba54a760` | `2026-07-23T16:30:58.483778998Z` | 0 | preserved stopped; finished `2026-07-28T16:50:15.545501365Z` |
| `butterfly_timescaledb` | `668bde36dda806638f54a25b7b75d6397a76340966373a9cd4ed13f86dcb855c` | `sha256:0af03ecf697825f6ddae76fd275d16bf46007bed6d00eb3d754779cb7db96fa6` | `2026-07-28T22:17:25.583848895Z` | 0 | running / healthy |
| `butterfly_prometheus` | `28f88d40ea4d555f1e2f826eb6f9d853b8bdb969ae383daeb8c9afc68d8cf265` | `sha256:4a61322ac1103a0e3aea2a61ef1718422a48fa046441f299d71e660a3bc71ae9` | `2026-07-28T22:19:51.125151930Z` | 0 | running |
| `butterfly_grafana` | `78d8a5b50d27ba2d0cdc368626d6394ec63c6e4857eb0942db50aa6b89af3b3f` | `sha256:e932bd6ed0e026595b08483cd0141e5103e1ab7ff8604839ff899b8dc54cabcb` | `2026-07-23T16:51:33.806423578Z` | 0 | running |
| `butterfly_alertmanager` | `f47c29b624e9e8a4bc727674e92438a6826ce95d9c47caf749eb04575c7f0c09` | `sha256:51a825c2a40acc3e338fdd00d622e01ec090f72be2b3ea46be0839cd47a4d286` | `2026-07-22T16:21:12.601362566Z` | 0 | running |

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
| 2026-08-15 | Phase 7 removal rollout | BLOCKED | approved preflight at deployed source `44e6184`; DB OPEN trades `0`; nonterminal intents `0`; authenticated broker account-position read returned HTTP `500` after three bounded attempts | Rollout stopped before source transfer, image build, tag, rebuild, restart, or other runtime mutation because broker flatness could not be proven. SPX/NDX/XSP retained their baseline container IDs/images, remained running with restart count `0`, and the Helios checkout remained clean. Retry requires a fresh broker/DB audit and renewed rollout approval after the upstream account read is healthy. |
| 2026-08-15 | Phase 7 removal rollout retry | BLOCKED | local target `43a0102`; Helios source `44e6184`; DB OPEN trades `0`; nonterminal intents `0`; fixed-output seven-day audit returned `broker_initialization_failed` | Fresh local full suite `630 passed, 1 skipped`; Phase 7 boundary `7 passed`; Ruff, wheel/sdist build, and quiet SPX/NDX/XSP Compose renders passed. The authenticated broker client could not initialize, so neither order history nor account positions were provably read. A post-failure audit confirmed the clean Helios source, all three original container IDs/images/start times, zero restarts, `200` health/readiness, unique service ownership, zero bounded log anomalies, all out-of-scope container IDs, and both DB counts unchanged. No source transfer, rollback tag, image build, recreation, restart, or other runtime mutation occurred. Retry only after broker initialization and the aggregate read-only audit pass, followed by fresh explicit rollout approval. |
| 2026-08-15 | Phase 7 removal rollout retry 2 | BLOCKED | host audit context has all required credential fields, absolute protected token file mode `0600`, owner `1001`, valid document, and creation marker; DB OPEN trades `0`; nonterminal intents `0`; seven-day audit returned `broker_initialization_failed` | The non-secret audit context ruled out a missing host credential or token-file path, but authenticated account-number resolution still did not complete and no order or position response was available. Post-failure checks again matched Helios source `44e6184`, all three original container IDs/images/start times, zero restarts, `200` health/readiness, unique service ownership, zero bounded log anomalies, all out-of-scope container IDs, and both DB counts. No source transfer, rollback tag, image build, recreation, restart, token change, or other runtime mutation occurred. Retry only after the authenticated broker client can initialize and the aggregate audit passes, followed by fresh explicit rollout approval. |
| 2026-08-15 | Phase 7 removal rollout retry 3 | BLOCKED | local full suite `630 passed, 1 skipped`; boundary `7 passed`; Ruff, wheel/sdist build, and quiet SPX/NDX/XSP Compose renders passed; DB OPEN trades `0`; nonterminal intents `0`; seven-day audit returned `broker_initialization_failed` | The same external broker-initialization gate failed for a third consecutive goal turn before any order or position response was available. Post-failure checks matched clean Helios source `44e6184`, all three original container IDs/images/start times, zero restarts, `200` health/readiness, unique service ownership, zero bounded log anomalies, all out-of-scope container IDs, and both DB counts. No source transfer, rollback tag, image build, recreation, restart, token change, or other runtime mutation occurred. Phase 7 remains blocked until authenticated broker initialization and the aggregate audit pass; a later successful retry still requires fresh explicit rollout approval. |
| 2026-08-15 | Phase 7 removal rollout retry 4 | IN PROGRESS | precise host diagnostic `import_token_store_failed`; the identical fixed-output seven-day audit from the deployed SPX image returned SPX/NDX/XSP positions `0`, active orders `0`, missing statuses `0`, and unmapped statuses `0`; DB OPEN trades `0`; nonterminal intents `0` | Root cause was the stale Helios host virtualenv, which lacks the shared token-store package; the copied token was not the failing component. The deployed runtime image has the required dependency and completed the authenticated read-only gate. Fresh local full suite `630 passed, 1 skipped`, boundary `7 passed`, Ruff, wheel/sdist build, quiet Compose renders, clean Helios source `44e6184`, original target container IDs/images/start times, zero restarts, `200` health/readiness, unique ownership, zero bounded log anomalies, and unchanged out-of-scope IDs all pass. No dependency install, source transfer, rollback tag, image build, recreation, restart, token change, or other runtime mutation occurred. Rollout to exact `43a0102` now awaits fresh explicit approval. |
| 2026-08-15 | Phase 7 removal rollout retry 4 | ROLLED BACK | approved rollout activated clean source `43a0102`; rollback tags retained for SPX/NDX/XSP; all three target images built before recreation; SPX candidate image `sha256:b1dfbe1...7e549` failed the bounded log-validation stage | Automatic rollback restored only SPX to `sha256:e2b7c0c...d17e9`; the restored service is running with restart count `0`, health/readiness `200`, unique ownership, clean bounded logs, paper mode, live trading disabled, direct access, shadow disabled, and valid protected token/runtime dependencies. Post-rollback DB OPEN trades and nonterminal intents are `0`; the authenticated seven-day audit reports SPX/NDX/XSP positions, active orders, missing/unmapped statuses, and duplicate order IDs all `0`. NDX/XSP and all out-of-scope container IDs remained unchanged. Rollout stopped without recreating NDX or XSP; retry requires review of the ambiguous SPX log gate and renewed explicit approval. |
| 2026-08-16 | Phase 7 removal rollout retry 5 | ROLLED BACK | renewed approval and fresh gates passed; SPX `c0f176cee845` / `sha256:b1dfbe1...7e549` and NDX `ef0ed41f6b0e` / `sha256:b4cea80...321f6` passed intended-image, zero-restart, health/readiness, structured-log, token initialization, uniqueness, removal-boundary, direct-access, and reconciliation gates; XSP target `sha256:804a757...06f6` passed service validation but failed its required gateway-URL runtime gate | Only XSP was automatically restored to `6d695db208c4` / `sha256:26951e7...1634`; SPX and NDX remain on the accepted removal images. XSP restoration passed zero-restart, health/readiness, clean-log, token initialization, uniqueness, and unchanged-container checks. Root cause is a Helios `infra/.env` `SCHWAB_GATEWAY_URL` override whose hostname is not `schwab-gateway`; the required alias resolves, port `8011` is correct, and shadow reads are disabled. Post-rollback DB OPEN trades and nonterminal intents are `0`; the seven-day broker audit reports SPX/NDX/XSP positions, active orders, missing/unmapped statuses, and duplicate order IDs all `0`. Rollout stopped; completing XSP requires approved correction/removal of the stale non-secret URL override and an XSP-only recreate. |
| 2026-08-16 | Phase 7 removal rollout retry 6 | COMPLETE | approved XSP-only correction preserved image rollback tag `butterfly-phase7-removal-retry2-rollback-xsp:20260816T160420Z` and permission-identical environment backup `/opt/butterflyguy/infra/.env.phase7-xsp-pre-20260816T160420Z`; exactly one `SCHWAB_GATEWAY_URL` line changed, with all other lines and file metadata preserved; rendered Compose requires `schwab-gateway:8011` and shadow false | XSP `d397feeda674` / `sha256:804a757...06f6` passed intended-image, zero-restart, health/readiness, structured-log, token initialization, uniqueness, paper/live guards, direct access, absent embedded gateway, resolved gateway alias, and unchanged-container gates. Settled fleet at clean source `43a0102`: SPX `c0f176cee845` / `sha256:b1dfbe1...7e549`, NDX `ef0ed41f6b0e` / `sha256:b4cea80...321f6`, and XSP all run uniquely with health/readiness `200`, zero restarts, and zero bounded log anomalies; all out-of-scope IDs are unchanged. Final DB OPEN trades and nonterminal intents are `0`; seven-day broker SPX/NDX/XSP positions, active orders, missing/unmapped statuses, and duplicate order IDs are all `0`. Rollback artifacts are retained; no database, monitoring, gateway, candidate, or legacy service was changed. |
| 2026-08-16 | Token refresh rebuild | BLOCKED | pushed and activated clean source `a8376f6`; refreshed token file is newer than the Phase 7 rollout, protected as mode `0600`/owner `1001`, and byte-identical through the shared SPX/NDX/XSP mount; one authenticated seven-day audit passed with every position/order/status count `0`, then the immediate pre-restart audit and one bounded retry both returned `oauth_error` | DB OPEN trades and nonterminal intents remained `0`. Fresh no-cache images were built but not deployed: SPX `sha256:1ca3485...c726d`, NDX `sha256:a5d0cb6...e1203`, XSP `sha256:e14544e...c44ac`. Verified rollback tags `butterfly-token-rebuild-rollback-{spx,ndx,xsp}:20260816T234322Z` preserve the running images; `infra-app_*:latest` was restored to those images after the failed gate. SPX `c0f176cee845`, NDX `ef0ed41f6b0e`, and XSP `d397feeda674` were not recreated or restarted and remain unique, zero-restart, health/readiness `200`, and log-clean. Rebuild/restart remains blocked until authenticated broker initialization and the aggregate audit pass reliably with the refreshed token. |
| 2026-08-16 | Token refresh rebuild retry | COMPLETE | explicit secret-replacement approval; secret-safe comparison proved the local configured token had a newer authorization lineage while Helios still mounted the prior lineage; lock-aware atomic replacement advanced the shared lineage, preserved mode `0600`/owner `1001`, and created a protected pre-replacement backup stamped `20260817T003229Z`; authenticated refresh and the aggregate broker audit passed before restart | At clean source `4098339`, previously built images were activated and services recreated one at a time: SPX `ef8c1dbc060f` / `sha256:1ca3485...c726d`, NDX `0331224f4d13` / `sha256:a5d0cb6...e1203`, XSP `8979c8c645d8` / `sha256:e14544e...c44ac`. Each passed intended-image, zero-restart, health/readiness, structured-log, token initialization, uniqueness, paper/live guards, direct access, absent embedded gateway, and between-service DB/broker gates; XSP also passed resolved `schwab-gateway:8011` and shadow false. Settled final fleet is unique, health/readiness `200`, zero-restart, log-clean, and sees byte-identical protected token contents. DB OPEN trades/nonterminal intents and seven-day broker SPX/NDX/XSP positions, active orders, missing/unmapped statuses, and duplicate order IDs are all `0`; all out-of-scope container IDs are unchanged and rollback tags remain retained. |
| 2026-08-16 | Phase 8 baseline | IN PROGRESS | clean Helios `main` at `7ca86fb52fe05bb60f70afe2480db92361d45dda`; exact full resource baseline above; qualifying start `2026-08-17T00:39:37.451595824Z` | SPX/NDX/XSP match the expected full images, are uniquely running with zero restarts, and return health/readiness `200`. The seven-day gate ends no earlier than `2026-08-24T00:39:37.451595824Z`; earlier candidate and Phase 7 evidence is not credited. |
| 2026-08-16 | Phase 8 baseline | IN PROGRESS | standalone `11f588627c88c00312b360451eadb9b56c86542aacfa6a4468e20826f61a02fb` / `sha256:d31e679d15e60e3ca8b794a4ff22ed4c742836cabd102656121a90630ab5ef04`; legacy `675a04e26b1c9b4c2726bfc0cc082b0ccebbb369d0f38fc05e7463eef29d3114` / `sha256:6eb9f560effae529a2f578b5a4e5a1b0da2fd124cb4566fe9b097f01ec8b0ec8` | Standalone is unique, healthy/ready `200`, loopback-only on `8011`, monitoring-only with alias `schwab-gateway`, unprivileged/read-only, all capabilities dropped, `no-new-privileges`, and `unless-stopped`; legacy remains preserved stopped. Exact Prometheus target is up, token-ready is `1`, both gateway rules are loaded, and zero gateway alerts fire. |
| 2026-08-16 | Phase 8 baseline | IN PROGRESS | shared protected document: lineage `2026-08-16T23:34:35Z`, mode `0600`, owner `1001:1001`, six identical consumer views, lock available | One serialized authenticated broker audit caused an ordinary atomic access-token persistence: inode advanced from `876` to `3842` and mtime to `2026-08-17T02:11:27.607379Z` while reauthorization lineage remained unchanged. All six views stayed identical; this ordinary refresh is not the scheduled Phase 8 reauthorization cycle. |
| 2026-08-16 | Phase 8 baseline | IN PROGRESS | DB OPEN trades `0`; nonterminal intents `0`; window trades/mark-v1 trades/broker intents `0/0/0`; broker SPX/NDX/XSP positions `0/0/0`, active orders `0`, missing/unmapped statuses `0/0`, duplicate order IDs `0`; Docker lifecycle events through `2026-08-17T03:12:02Z` all `0` | SPX/NDX/XSP and standalone logs from the window start have zero error/critical, traceback, auth, lock, persistence, reload-failure, unknown/duplicate-order, reconciliation, and readiness anomalies. Candidate-feed internal health/metrics are `200` with zero collection/archive failure counters, but its Docker history timed out after five minutes and again with an explicit end bound. Preserve this as an unresolved evidence gap; do not count the initial checkpoint complete or infer an outage/clock reset from it alone. |
| 2026-08-16 | Phase 8 rollback baseline | IN PROGRESS | `butterfly-token-rebuild-rollback-spx:20260816T234322Z` → `sha256:b1dfbe1e90c70cf128be86c04ccc4c34ee87b6b27e5a3d04513f9a13ca17e549`; NDX → `sha256:b4cea80e9292e463f296b432cf473e7b812ca23a3052e87e8d4d9ab83bf321f6`; XSP → `sha256:804a757434dffdefbf96ae2a26781bdfa55cdb6e769ec90d4fffb7343a3406f6`; Phase 7 XSP rollback → `sha256:26951e728019d8fda94c9ea2b5b1bf69766bb0ef14c028cb3ccc58b04e351634` | All four verified tags remain present; stopped legacy and standalone release images remain present. No rollback, rebuild, restart, secret replacement, or runtime mutation occurred. |
| 2026-08-16 | Phase 8 checkpoint 0 | COMPLETE | direct read-only candidate-feed log aggregate through `2026-08-17T03:30:00Z`: file bytes `170225`, envelopes `848`, malformed `0`, qualifying records `684`; SPX control records `341`, malformed `0` | Docker's log API returned immediately for `tail=0` but timed out before one record for `tail=1`. The existing node-exporter host-root mount is read-only, so its UID-0 exec parsed the protected log in place without emitting records or changing state. Candidate feed and SPX both had zero error/critical, traceback, authentication, lock, persistence, reload-failure, unknown-order, duplicate-order, reconciliation, and readiness anomalies. The initial evidence gap is resolved and the qualifying clock remains `2026-08-17T00:39:37.451595824Z`. |
| 2026-08-16 | Phase 8 checkpoint 0 follow-up | COMPLETE | fixed-output interval `2026-08-17T03:30:00Z`–`04:41:50.162180Z` (`4,310` seconds): exact source and all `18` container baselines unchanged; `12` direct log sources / `4,454` bounded records; lifecycle events `0`; Prometheus target/token-ready interval minima `1/1`; gateway alerts `0`; DB open trades/nonterminal intents/non-mark-v1 trades/broker intents `0/0/0/0` | All nonempty log envelopes were well formed and every required anomaly count was `0`; gateway historical blank physical records were classified separately and are not malformed events. Paper/live/direct/shadow/XSP-alias guards passed. A serialized authenticated audit returned SPX/NDX/XSP positions `0/0/0`, active orders `0`, missing/unmapped statuses `0/0`, and duplicate IDs `0`. The ordinary refresh persisted atomically at `2026-08-17T04:42:19.598246Z`, changed inode `3842` → `876`, preserved the `2026-08-16T23:34:35Z` lineage, mode/owner, six identical views, and lock availability; it is not the scheduled reauthorization cycle. Observed continuity remains clean; inference: Phase 8 is on track, with the full session and scheduled cycle still pending. |
| 2026-08-16 | Phase 8 checkpoint 1 | COMPLETE | fixed-output interval `2026-08-17T04:41:50.162180Z`–`05:07:30.206354Z` (`1,540` seconds): clean source and all `18` exact container ID/image/start/restart/state baselines unchanged; `12` direct log sources / `1,596` bounded records; lifecycle events and all required anomaly categories `0`; Prometheus target/token-ready interval minima `1/1`; gateway alerts `0`; DB open trades/nonterminal intents/non-mark-v1 trades/broker intents `0/0/0/0` | Health/readiness, gateway exposure/security, paper/live/direct/shadow/XSP-alias, protected-token, and unchanged out-of-scope gates passed. The first host-virtualenv helper stopped before Schwab access because that stale host environment does not contain the extracted token-store package; the unchanged SPX runtime image does, and the identical serialized in-container audit returned SPX/NDX/XSP positions `0/0/0`, active orders `0`, missing/unmapped statuses `0/0`, and duplicate IDs `0`. Its ordinary atomic access-token persistence changed inode `876` → `3413` and mtime to `2026-08-17T05:10:11.775511Z` while preserving the `2026-08-16T23:34:35Z` reauthorization lineage, mode `0600`, owner `1001:1001`, six identical views, and lock availability. This is not the scheduled Phase 8 cycle. Observed continuity is clean through the fixed interval; inference: the qualifying clock remains `2026-08-17T00:39:37.451595824Z`, with the full session and scheduled cycle pending. |
| 2026-08-17 | Phase 8 checkpoint 2 / market session | IN PROGRESS | fixed-output interval `2026-08-17T05:07:30.206354Z`–`18:35:11.363397Z` (`48,461` seconds), beginning well before the `13:30Z` regular open: clean source; all `18` exact resource baselines unchanged; `12` direct log sources / `72,255` bounded records; lifecycle events and every required anomaly category `0`; Prometheus target/token-ready interval minima `1/1`; gateway alerts `0` | Observed: all health/readiness, exposure/security, paper/live/direct/shadow/XSP-alias, protected-token, and out-of-scope gates passed continuously across reconstructed pre-open and the session so far. Production DB activity is expected paper trading: `3` entries, all `mark_v1`; `2` open rows, both current-date single-quantity positions on distinct supported assets; unsafe/duplicate/wrong-date opens, nonterminal intents, non-mark fills, and broker intents are all `0`. The serialized real-broker audit returned SPX/NDX/XSP positions `0/0/0`, active orders `0`, missing/unmapped statuses `0/0`, and duplicate IDs `0`. Its ordinary atomic persistence changed inode `3779` → `876` and mtime to `2026-08-17T18:35:29.242914Z` while preserving lineage `2026-08-16T23:34:35Z`, mode/owner, six identical views, and lock availability. Inference: session behavior is on track; this row does not credit market close, settlement, EOD charts, or reporting. |
