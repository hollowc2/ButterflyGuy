# Schwab Gateway Credential-Proof Evidence Template

> **Historical template:** Credential-proof operations and current evidence guidance moved to
> [`hollowc2/SchwabGateway`](https://github.com/hollowc2/SchwabGateway). This template is retained
> only with the historical proof record.

Use this redacted template only after the two approvals in the after-hours runbook. Store captured
evidence mode `0600`. Never add token or credential paths/values, environment values, payloads,
headers, cookies, account identifiers, URLs, or raw exception text.

## Classification

- Package status: `prepared_not_executed`
- Code/auth/admission status: `implemented_fake_tested`
- Prior filesystem observations: `observed_on_helios_previously`
- Executable staging mount: `proposed_unproven`
- Real credential proof: `still_unproven`

## Window and provenance

- Exact `origin/main` SHA:
- Exact reviewed feature/commit SHA:
- UTC start:
- UTC end:
- Approved operator:
- Approved window/reference:
- Rollback owner:
- Watchdog owner and hard deadline:

## Baseline and staging

- Baseline SPX container ID:
- Baseline SPX image ID:
- Baseline NDX container ID:
- Baseline NDX image ID:
- Baseline XSP container ID:
- Baseline XSP image ID:
- Baseline candidate-feed container/image ID:
- Baseline redacted configuration fingerprint:
- NDX image/health recorded: `yes|no`
- XSP image/health recorded: `yes|no`
- Service/process health before staging: `pass|fail`
- Keepalive absent/quiesced: `yes|no`
- CI worker/host writer absent: `yes|no`
- Candidate token mount read-only: `yes|no|unproven`
- Staged source SHA-256:
- Bounded synthetic smoke result: `pass|fail|not_run`
- Default Compose unchanged: `yes|no`
- Staging override was the only configuration delta: `yes|no`

## Single-writer and approvals

- SPX application process suspended: `yes|no`
- NDX/XSP writers stopped: `yes|no`
- Single-writer verification: `pass|fail`
- Approval 1 reference and UTC:
- Fresh explicit Approval 2 reference and UTC:
- Credential authorization scope: `one_read_one_AAPL_quote|not_authorized`

## Bounded command result

- Command started UTC:
- Command ended UTC:
- Exit status:
- Exact bounded stdout: `{"quote_count":1,"status":"ok","token_state":"ready"}` or
  `empty`
- Bounded token state:
- Bounded reason code:
- Retry count (must be `0`):
- Information-exposure check: `pass|fail`

Do not paste any additional stdout/stderr. Map failures to an approved bounded reason code.

## Restoration and review

- Proof process absent:
- Service restoration completed UTC:
- SPX restored image/config fingerprint matches baseline: `yes|no`
- SPX/NDX/XSP health: `pass|fail`
- Expected process uniqueness: `pass|fail`
- Keepalive ownership restored: `pass|fail`
- Candidate read-only ownership preserved: `pass|fail`
- Filtered startup-error counts by bounded service name/status:
- Executable staging mount absent after rollback: `yes|no`
- Reviewer disposition: `accepted|rejected|inconclusive`
- Follow-up authorization required:

Passing evidence must not be rewritten as deployment, cutover, order, account, streaming, or
rate-limit proof.
