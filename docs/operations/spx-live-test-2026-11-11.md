# Supervised SPX live pilot — November 11, 2026

Corey authorized preparation for November 11 and a $400 debit ceiling plus fees.
Morning activation follows fresh checks and confirmation Corey is supervising in Schwab.

## Session

Preflight at 06:45 Pacific. Configured entry window is 07:00–07:45 Pacific
(10:00–10:45 Eastern). One SPX fly, one trade, maximum opening limit 4.00
points ($400) plus actual fees. Existing strategy and width-specific cost caps
determine eligibility. An entry may be skipped or remain unfilled. Normal
management can hold through the 13:00 Pacific close, requiring continued supervision.

The overlay retains the existing $20,000 allocation and $500 daily-loss
confirmations. The dated guard allows new entries only on November 11 while
continuing to monitor held positions afterward. Automatic restart is disabled.

## Prepared release

Clean source commit `247261764e22a5e98940ccc4d20c28e04e49aa94`, matching Helios
repository HEAD, contains the pilot controls and manual-exit takeover handling.
Release directory on Helios is `/opt/butterflyguy-releases/spx-live-test-20261111-24726176`.

Candidate image is `sha256:37b2213888c3968d9d377d503dcea2e68ce5a24d95e787a621800548884379c7`.
Baseline paper image is `sha256:172359a607bc9d6c569d07305169d5d6ac754970bee63b7061009d365486e60d`.
The original Compose files are `/opt/butterflyguy/infra/docker-compose.yml` and
`/opt/butterflyguy/.releases/spx-charts-20261103/release-image.yml`, project `infra`.

The exact activation and rollback arguments, environment, baseline container
identity, image hashes and validation results are in
`reports/execution_audits/spx-live-test-2026-11-11/prepared-deployment.json`.
A copy is staged in the Helios release directory with `rollback-image.yml`.

Verification completed with 1,443 local tests passed and 37 skipped, full Ruff
passed, and GitHub validate and real TimescaleDB smoke passed for this commit.
Local tests used Python 3.13. The Python 3.12 candidate image passed an isolated,
network-disabled pilot configuration smoke. Live and rollback Compose rendering
passed, with all other rendered services equivalent to the original configuration.

Preparation broker flatness/authentication check passed. Database checks showed
zero open SPX trades and zero nonterminal SPX intents. Repeat before activation.

## Morning activation

Activation replaces the running SPX service and enables real Schwab orders for
the dated session. Confirm Corey is supervising, broker and DB are flat, orders
and intents are terminal, buying power is sufficient, token access works, and
one intended SPX instance exists. Recheck baseline image/container/Compose files.

From the staged release directory, run the read-only gates in the current container.

```bash
docker exec -i butterfly_spx_app python - < tools/deploy_broker_flat_check.py
docker exec -i butterfly_spx_app python - < deployment-check-database.py
```

Execute the preparation manifest's activation argument array with its
`activation_env` after fresh checks and supervised activation confirmation.
It uses `up -d --no-deps --no-build --pull never app_spx` with the staged pilot
overlay last. Verify image, readiness, live/date/size settings and reconciliation
before 07:00 Pacific. Never reset risk counters to force an entry.

The pilot records pre-submit/reprice leg quotes, local acknowledgements, fill
detection and broker fills. Post-fill quote observations follow execution.
The ten-second quote-age guard may require operator help at exit when quotes
are stale. For partial fills, unknown orders or manual intervention, follow
`docs/live-runbook.md`. Reconcile broker state before restarting.

## Completion

After closure, export evidence from the authenticated SPX container.

```bash
docker exec -i butterfly_spx_app python - --date 2026-11-11 \
  --out-dir /tmp/spx-live-test-20261111-evidence < tools/report_spx_live_test.py
```

Copy the evidence to a new durable host directory before recreating the
container. Reconcile every leg, actual fees, limits, timestamps and prior quotes.
Re-export into a new directory after settlement cash flows post when needed.

Once broker positions are flat and orders terminal, execute the manifest's
rollback argument array. It pins the baseline paper image using
`rollback-image.yml` without the live overlay. Verify paper mode, readiness,
reconciliation and a single SPX container.

No activation was scheduled or executed during preparation.
