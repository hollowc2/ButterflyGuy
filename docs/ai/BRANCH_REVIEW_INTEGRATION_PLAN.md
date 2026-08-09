# Branch Review and Integration Plan

## Purpose

Provide one durable, updateable source of truth for reviewing work produced across
multiple models, resolving findings, and integrating the resulting branches into
`main` without disturbing unfinished work.

This plan is an orchestration document. It does not authorize live trading,
Schwab write calls, service deployment, branch deletion, force-pushing, or merging.

## Safety Boundaries

- Treat strategy, execution, risk, credentials, token handling, Docker runtime,
  and monitoring changes as high impact.
- Perform review and local verification without contacting Schwab, placing orders,
  changing live services, or exposing secret values.
- Do not print, summarize, rewrite, or commit `.env`, `tokens.json`, account IDs,
  API credentials, internal keys, or captured secret material.
- Preserve the current worktree and all unrelated user work. In particular,
  `Fable_refactor/fly_Spec.html` was already untracked when this review began and
  remains outside this review unless the owner explicitly adds it.
- A new uncommitted change to `src/butterfly_guy/data/schwab_client.py` appeared
  after the frozen snapshot and was excluded from every delegated review. It was
  subsequently committed in the post-boundary delta; it must not be used to close
  a frozen-SHA finding until that delta is separately reviewed.
- Do not merge, rebase, force-push, delete branches, open/close pull requests, or
  enable GitHub rules without the owner's explicit approval of that action.
- Subagents default to read-only review. The primary agent validates their findings
  before accepting them or proposing a change.

## Frozen Starting Snapshot

Snapshot recorded on 2026-08-08:

```text
origin/main  6179f2e
    |
    +-- 49 commits -- local main  ba2e6bc
                          |
                          +-- 43 commits -- codex/schwab-gateway-phase3-shadow-surfaces  7110158
```

- Current worktree: `/mnt/Repos/Trading/Butterflyguy`
- Current branch: `codex/schwab-gateway-phase3-shadow-surfaces`
- Current branch is also pushed to `origin` at `7110158`.
- Local `main` is 49 commits ahead of `origin/main`.
- Phase 3 is 43 commits ahead of local `main` and 92 commits ahead of
  `origin/main`.
- There is currently one Git worktree and no open GitHub pull request.
- GitHub currently reports `main` as unprotected.

These SHAs define the initial review boundaries even if development continues.
New commits will be reviewed as a separate delta from the last accepted SHA.

Handoff update: while the frozen review was running, the active branch advanced
from `7110158` to `0ad454b` with three commits:

```text
e05f837  Persist the Schwab token through the shared C1 lock
3da0cc1  Record the C1 deployment and correct the exit-137 diagnosis
0ad454b  Correct the Window F framing: the deadline recurs weekly
```

Those commits were not inspected by the frozen review. The next review boundary is
`7110158..0ad454b`. A commit title alone does not close B-H3 or any other finding.

## Initial Verification Baseline

- `uv run ruff check .`: passed using an isolated review environment.
- Full test suite: `970 passed, 1 skipped, 2 warnings`.
- The skip is `tests/integration/test_database_smoke.py` because
  `CI_DATABASE_URL` is only provided by the real-database workflow.
- `git diff --check` passed for both `origin/main..main` and `main..HEAD`.
- The repository `.venv` is stale and points to an old filesystem location;
  verification uses `/tmp/butterfly-review-env` until the owner chooses to rebuild
  the project environment.
- `graphify-out/GRAPH_REPORT.md` reports build commit `b825f5f2`, so the graph is
  stale relative to `7110158` and must be refreshed after accepted code changes
  and before final integration verification.

## Review Units

### Unit A: Local-main integration layer

- Range: `origin/main..main` (`6179f2e..ba2e6bc`)
- Size: 49 commits
- Primary concerns: credential-proof tooling, bounded operator behavior, token and
  config safety, Compose/runtime baselines, failure restoration, redaction,
  deployment assumptions, and test coverage.

### Unit B: Phase 3 layer

- Range: `main..codex/schwab-gateway-phase3-shadow-surfaces`
  (`ba2e6bc..7110158`)
- Size: 43 commits
- Primary concerns: collector-facing gateway surfaces, live provider boundaries,
  internal authentication, shadow-read behavior, readiness recovery, token locking
  and mounts, Prometheus surfaces, container restart behavior, and runbook accuracy.

### Unit C: Cross-cutting integration

- Range: `origin/main..codex/schwab-gateway-phase3-shadow-surfaces`
- Primary concerns: assumptions crossing Unit A/Unit B, configuration parity,
  security boundaries, failure modes, CI and branch hygiene, documentation drift,
  migration/rollback behavior, and whether the proposed PR stack represents the
  actual dependency graph.

## Delegated Workstreams

Each subagent must return findings rather than edit code. Every finding must include:

1. Severity: critical, high, medium, or low.
2. Exact file and line or commit reference.
3. Concrete failure scenario and affected runtime.
4. Evidence or a reproducible local check.
5. Smallest safe remediation and tests needed.
6. Confidence and any unresolved assumptions.

Planned workstreams:

- **A — Unit A safety review:** credential-proof/operator logic, restoration,
  redaction, token/config handling, and high-impact infrastructure changes.
- **B — Unit B runtime review:** gateway API/provider/client/shadow behavior,
  concurrency, authentication, readiness, and error classification.
- **C — Integration and operations review:** Compose mounts, Prometheus, runbooks,
  branch ancestry, PR stacking, CI/branch protection, and documentation consistency.
- **Primary agent — validation:** reproduce candidate findings, reject false
  positives, inspect cross-workstream interactions, run focused verification, rank
  accepted findings, and update this plan.

## Review and Remediation Workflow

1. Freeze the review boundary by SHA; ongoing development may continue beyond it.
2. Run delegated reviews in parallel with no repository edits.
3. Primary agent validates every critical/high finding and samples lower-severity
   findings against code and tests.
4. Record accepted, rejected, and deferred findings in the decision log below.
5. If fixes are requested, add failing focused tests first when practical, make
   surgical changes, and rerun the narrowest meaningful verification.
6. Review the combined final diff, not only individual fixes.
7. Run Ruff, the full test suite, `git diff --check`, and `graphify update .` after
   accepted code changes.
8. Obtain owner approval before any GitHub mutation or integration operation.

## Proposed Integration Shape

Do not open one 92-commit Phase 3 pull request directly against `main`.

Preferred stacked review:

1. Create a dedicated remote review branch at `ba2e6bc` and open a draft PR to
   `main` for Unit A.
2. Open or retarget a draft Phase 3 PR to use that Unit A review branch as its base;
   this isolates Unit B's 43-commit diff.
3. Merge Unit A with a merge commit after accepted findings are resolved and all
   gates pass. Avoid squash merging because Unit B already contains Unit A's exact
   ancestry.
4. Retarget Unit B to `main`, confirm GitHub displays only the intended Unit B
   delta, rerun verification, and merge only after a second approval gate.
5. Delete merged branches only in a separate cleanup step after the resulting
   `main` SHA is verified and recoverable.

## Final Integration Gates

- No unresolved critical or high finding.
- Medium findings are fixed or explicitly accepted/deferred with rationale.
- No unexpected change to paper/live mode, account guards, risk limits, order
  routing, broker writes, or secret handling.
- Full tests, focused changed-area tests, Ruff, and `git diff --check` pass.
- Real-database verification is either run in its controlled workflow or explicitly
  recorded as unavailable.
- Graphify is current at the final reviewed code SHA.
- Compose configuration renders for affected profiles without exposing secrets.
- Runbooks match final commands, paths, service names, and failure behavior.
- GitHub `main` protection/rules are agreed before integration.
- The owner approves each push, PR mutation, merge, and branch deletion step.

## Progress

- [x] Inventory local worktree, branches, remote branches, and PR history.
- [x] Establish frozen Unit A and Unit B commit boundaries.
- [x] Establish initial lint, test, and diff-check baseline.
- [x] Save this durable orchestration plan.
- [x] Complete delegated Unit A safety review.
- [x] Complete delegated Unit B runtime review.
- [x] Complete delegated integration/operations review.
- [x] Validate and consolidate all subagent findings.
- [ ] Review the post-freeze delta `7110158..0ad454b` and update affected findings.
- [ ] Resolve or disposition accepted findings.
- [ ] Refresh Graphify and complete final local verification.
- [ ] Obtain approval and create the stacked draft PRs.
- [ ] Merge Unit A after its gate.
- [ ] Retarget, verify, and merge Unit B after its gate.
- [ ] Verify integrated `main` and clean up merged branches with approval.

## Decision and Findings Log

Use this table for concise state; detailed evidence may be added below it.

| Date | Unit | Item | Status | Decision / Evidence |
|---|---|---|---|---|
| 2026-08-08 | Baseline | Branch ancestry | Accepted | Unit A is 49 commits; Unit B is a dependent 43-commit stack. |
| 2026-08-08 | Baseline | Local verification | Accepted | Ruff passed; 970 tests passed; DB smoke skipped without `CI_DATABASE_URL`; diff checks passed. |
| 2026-08-08 | Baseline | Existing WIP | Protected | Untracked `Fable_refactor/fly_Spec.html` is outside scope and untouched. |
| 2026-08-08 | Baseline | Graph freshness | Open | Graph reports `b825f5f2` and needs a final refresh. |
| 2026-08-08 | Baseline | Branch protection | Open | GitHub reports `main` as unprotected; agree rules before merge. |
| 2026-08-08 | Review | Delegated reviews | Complete | Unit A, Unit B, and integration/operations reviews completed read-only against frozen Git objects. |
| 2026-08-08 | Review | Primary validation | Complete | No critical finding; consolidated high/medium/low findings below were checked against committed code and reproductions. |
| 2026-08-08 | Review | Unit A gate | Blocked | Four validated high findings remain open; Unit A must not merge yet. |
| 2026-08-08 | Review | Unit B gate | Blocked | Runtime, token-writer, reauthorization, CI, and operational high findings remain open; Unit B must not merge or be activated yet. |
| 2026-08-08 | Handoff | Active branch advanced | Open | Current tip is `0ad454b`; review through `7110158` remains frozen and the three-commit delta is pending. |

## Consolidated Validated Findings

No critical finding was identified. The high findings below are integration
blockers. Similar findings from multiple workstreams were deduplicated.

### High — open blockers

| ID | Unit | Location | Validated problem | Required direction |
|---|---|---|---|---|
| A-H1 | A | `credential_proof_fingerprint.py:3775-3796,4426-4518` | Approval 2 can bind to a replacement archive and matching mutable source instead of the previously approved digest/commit. | Revalidate the stored digest and commit immediately before execution; preferably execute a private extracted tree. |
| A-H2 | A | `credential_proof_fingerprint.py:4228-4270,4442-4518` | Restoration can resume trading services while the host credential proof still runs, and the proof can later write success into a restored state. | Own/drain the exact proof process before restoration and recheck phase before recording proof results. |
| A-H3 | A | `credential_proof_fingerprint.py:4172-4184,4340-4369` | Fail-closed pause ignores command results and never proves the services are paused before cancelling watchdogs. | Require successful pause output and post-inspect every service; retain containment recovery on failure. |
| A-H4 | A | `credential_proof_fingerprint.py:4228-4250,4330-4369` | Public restore accepts pre-mutation failed states and can pause otherwise healthy services when no baseline exists. | Persist an explicit mutation/quiescence flag and make pre-mutation restore a verified no-op. |
| B-H1 | B | `token_manager.py:433-456`; `token_adapter.py:74-105`; `api.py:242-253` | OAuth/client authentication failures are collapsed without moving token health out of `READY`, leaving `/ready` falsely green and preventing recovery. | Classify bounded authentication failures and transition token health while preserving `READY` for ordinary transport/5xx failures. |
| B-H2 | B | `live_provider.py:128-130`; `api.py:321-338`; `admission.py:45-57` | Timing out `asyncio.to_thread()` releases admission while the real synchronous Schwab work continues, allowing unbounded residual work and priority inversion. | Use a bounded priority-aware worker queue and hold capacity until the underlying operation ends. |
| B-H3 | B/C | `data/schwab_client.py:35-45`; `gateway_client/shadow.py:202-254` | Direct SDK clients do not share the gateway/keepalive token lock; concurrent shadow/direct refresh can corrupt or overwrite shared token state. | Do not activate shadow mode until every persistent writer shares one lock/atomic path or the gateway is the sole writer. |
| B-H4 | B/C | `tools/auth_init.py:7-16`; token reauthorization runbook | Reauthorization targets the shared production document without the shared lock, can race live consumers, and can report an existing-token no-op as success. | Mint to staging, validate, then atomically install under the shared lock; point reminders only to the safe runbook. |
| C-H1 | B/C | `config_spx_candidate.yaml:1-3`; `core/config.py:230-237`; default Compose candidate service | The documented legacy rollback service pins relative `tokens.json`, overriding its absolute mounted token path and making rollback authentication fail. | Remove the YAML pin, cover every Compose `run_live` config, and decide/test read-only token persistence semantics. |
| C-H2 | B/C | `.github/workflows/deploy.yml:17-23`; required variables in `infra/docker-compose.yml` | Clean-runner validation now fails because Compose requires `SCHWAB_GATEWAY_TOKEN_DIR`, but CI creates an empty environment and supplies none. | Supply a safe dummy absolute validation path and render both affected Compose projects/profiles. |
| C-H3 | All | `.github/workflows/database-smoke.yml`; `.github/workflows/deploy.yml`; GitHub settings | PRs run only one DB smoke test; full tests/Ruff/Compose run only after a main push, and `main` is unprotected. | Add a PR quality workflow, then require it and DB smoke with branch protection before integration. |
| C-H4 | B/C | token reauthorization, Option A, and C3 runbooks | Current documents contain expired windows, contradictory rollback claims, old paths/topology, and unsafe procedures that omit always-on consumers. | Mark obsolete documents historical and publish one current locked, staged, all-consumer procedure. |
| C-H5 | B/C | `infra/docker-compose.gateway.yml:64-83` | The live gateway imports the full application `.env`, widening compromise exposure to unrelated account/database/notification secrets. | Remove the broad `env_file`; explicitly map and test the exact required environment allowlist. |

### Medium — fix or explicitly defer

| ID | Unit | Location | Validated problem |
|---|---|---|---|
| A-M1 | A | `tests/test_gateway_compose.py:37-43`; commit `5055991` | Unit A alone is test-red because a whole-file Compose hash is stale; Unit B later masks this with a repin. Replace the brittle pin with semantic assertions in Unit A. |
| A-M2 | A | proof operator `_run()` and `_proof_process_environment()` | Credentials and unrelated parent secrets are inherited by pre-approval subprocesses and the proof receives a broader environment than required. |
| A-M3 | A | `credential_probe.py:69-87`; probe result-code table | Lock/store failures before a token read are reported as `probe_token_invalid`, whose evidence contract claims a token read occurred. |
| B-M1 | B | `gateway_client/client.py:81-130`; shadow classification table | The client discards bounded server error codes, collapsing parsing/readiness defects into generic upstream-unavailable observations. |
| B-M2 | B | `chain_metadata.py:102-145`; `live_provider.py:148-164` | Explicit `status=FAILED` chain shapes can become HTTP 200 empty success, while non-object payloads are misclassified as availability failures. |
| B-M3 | B | `gateway_client/models.py`; `upstream.py:41-69`; API JSON helper | Non-finite numbers and extreme epochs can produce non-standard `NaN` JSON or unbounded timestamp exceptions. |
| C-M1 | B/C | `schwab-gateway-alerts.yml`; gateway `/metrics` and `/ready` | Monitoring alerts on process loss but not sustained non-ready/token degradation. |
| C-M2 | B/C | `infra/prometheus.yml`; gateway alert/runbook assets | Gateway monitoring deployment depends on untracked/manual live edits and is not reproducible from the repository. |
| C-M3 | B/C | `.env.example`, `README.md`, `docs/live-runbook.md` | Required `SCHWAB_GATEWAY_TOKEN_DIR` setup is missing from normal developer/operator instructions. |

### Low — cleanup

| ID | Unit | Location | Validated problem |
|---|---|---|---|
| B-L1 | B | `schwab_gateway/api.py:189-215` | Unexpected authenticated handler failures are audited as `anonymous`. |
| C-L1 | All | `graphify-out/` and `.gitattributes` | Generated Graphify churn dominates Unit A, is not marked generated, and is currently stale. |

## Remediation Order

1. **Guardrails first:** add a PR quality workflow from `origin/main`, then enable
   agreed branch protection once its checks exist.
2. **Unit A safety:** fix A-H1 through A-H4 with deterministic failing tests; then
   address A-M1 through A-M3 and verify Unit A independently at its own head.
3. **Rebase the review boundary by ancestry, not history rewriting:** make Unit B
   contain the accepted Unit A remediation tip by merging Unit A into Unit B.
4. **Unit B token/runtime:** fix B-H1, B-H2, B-H3, and B-H4 before any shadow or
   gateway-consumer activation.
5. **Unit B integration/operations:** fix C-H1 through C-H5, then resolve or
   explicitly defer the medium findings.
6. **Final evidence:** run focused tests, full tests, Ruff, safe Compose renders,
   `git diff --check`, monitoring-rule validation, and a final Graphify refresh.
7. **Integration approvals:** open/retarget and merge the stacked PRs only after the
   applicable gates pass and the owner approves each GitHub mutation.

## Update Protocol

- Update the frozen SHA and progress checklist whenever a review checkpoint is
  accepted.
- Append decisions; do not erase prior conclusions. Mark superseded entries and
  link the replacement.
- Record exact verification commands and outcomes after any code change.
- Keep operational evidence redacted and outside Git unless the repository already
  defines a safe tracked evidence format.
- At session handoff, state the last reviewed SHA, current branch/worktree, open
  findings, and the next unchecked progress item.
