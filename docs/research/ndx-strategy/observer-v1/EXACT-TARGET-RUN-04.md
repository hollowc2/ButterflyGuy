# Exact TimescaleDB compatibility verified — run-04

The exact-image gate now **passes**. This supplements the frozen implementation
review and revision-2 records; their earlier unavailable-runtime observations
remain preserved. The owner explicitly authorized starting local Docker after
the distinction from Helios was explained. `systemctl start docker` succeeded;
the local daemon remains running. No Helios connection or live service change
occurred.

The unchanged `contract-v2.json` and `source-lock-v2.json` verified all source and
parent output hashes before execution. Actual image identity matched the pinned
repository digest and linux/amd64 platform. The isolated server reported
PostgreSQL **16.11** and TimescaleDB **2.25.2**, also checked in each newly created
test database.

The native response, real adapter and observer suite passed **50 tests, zero
failures/errors/skips, in 12.41 s**. This includes actual restricted-role
publication and consumer receipts, immutability, correction/duplicate handling,
transaction failures/commit ambiguity, MVCC, backend termination, observer crash,
owned-DB restart/reconnect, timeouts/admission and default-off factory/CLI checks.
The synthetic COMMIT-reply-loss injection remains an injected transport failure
after an actual server commit; it does not establish a real network incident.

These are the affected 50 checks rerun on the exact engine. The earlier 186-test
private-enabled result remains separate; do not sum the runs as 236 unique tests.

Exact executed command:

```bash
UV_CACHE_DIR=/tmp/butterfly-uv-cache uv run --offline --frozen python tools/check_ndx_timescale.py \
  --config docs/research/ndx-strategy/observer-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/observer-v1/source-lock-v2.json \
  --output /tmp/ndx-timescale-observer-target/run-04
```

The new container `ndx-timescale-4054df420cbb45a48bb572630c1e14db` was confirmed
stopped (`exited`, running=false). Its network mode was none, with 1 GiB memory,
one CPU, 128 PIDs, private Unix socket and disposable bounded data tmpfs. No
existing container/volume was used or deleted. The stopped container and logs
are retained. A single post-suite Docker sample reported 529.6 MiB including
test-database tmpfs, 0.10% CPU and 15 PIDs; this is not peak profiling or a
production-capacity result.

Closed output is archived at
`reports/research/ndx-02-observer-20261015/target-run-04/`; every copied file and
the run's output hashes verified. It includes commands, image/server/extension
identities, JUnit XML, server/restart logs, source copies and shutdown proof. The
versioned [verification record](../evidence/2026-10-15/ndx02-observer-target-verification-04.json)
binds these artifacts and distinguishes prior ordinary-PG resource measurements.
Use a new output directory for any repeat.

Overall activation preparation remains incomplete: target resource/restore
validation, storage reserve/quota, current operational preflight and the named
release/permissions/uniqueness/rollback baseline still need review. Independent
backup and upstream age-reference/build/cache/clock/provider-body gaps remain.
No production-budget, freshness, execution or strategy claim follows from these
mechanics checks. All 17 historical paths remain ineligible. Capture, live DDL/
grants and economic experiments remain disabled and separately authorized.
