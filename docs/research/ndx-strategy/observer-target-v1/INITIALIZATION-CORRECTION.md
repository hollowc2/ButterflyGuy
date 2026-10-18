# Fixture initialization correction — revision 2

Resource/restore run-01 failed before resource acquisition. The task-owned server
was stopped and all source/commands/logs preserved. Its entrypoint started a
temporary bootstrap postmaster on `/socket`, then its psql initialization tried
the default `/var/run/postgresql` socket and failed. This is a test-infrastructure
startup failure, not an application permission, response or restore result.

Revision 2 sets `PGHOST=/socket` in both exact-image fixture runners and requires
proof that initialization reached the final server before any database check.
The resource/restore fixture uses PostgreSQL PID 1. The restart-test fixture uses
a shell PID 1 so its tmpfs survives PostgreSQL restarts; its final postmaster PID
must match the original entrypoint child's explicitly recorded PID, rather than
the temporary bootstrap server's PID. Commands and logs retain this evidence.

The earlier run-04 executed 50 checks against the actual registered engine and
extension, but its shell wrapper could leave the temporary bootstrap server alive
after the entrypoint failed. Preserve those actual checks without claiming clean
image initialization from them. A new exact-image compatibility run with the
corrected startup gate is required. Do not edit the old contract, lock, test result
or source copies. Record both the infrastructure failure and its correction.

Use the new `contract-v2.json` and `source-lock-v2.json`, registered before reruns:

```bash
uv run --offline --frozen python tools/check_ndx_timescale.py \
  --config docs/research/ndx-strategy/observer-target-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/observer-target-v1/source-lock-v2.json \
  --output /tmp/ndx-timescale-observer-target/run-05

uv run --offline --frozen python tools/check_ndx_target_restore.py \
  --config docs/research/ndx-strategy/observer-target-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/observer-target-v1/source-lock-v2.json \
  --output /tmp/ndx-target-resources-restore/run-02
```

No resource recipe, limit, runtime trading behavior, secret or live service is
changed. Both commands use separate new, privately owned synthetic local fixtures.
Resource/restore and current operational readiness remain unproven until their
own checks pass. A successful same-container restore does not prove independent
backup or production disk/WAL capacity.
