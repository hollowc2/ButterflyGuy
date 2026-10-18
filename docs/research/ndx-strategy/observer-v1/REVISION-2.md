# Observer resource runner correction — revision 2

Use `contract-v2.json` and `source-lock-v2.json` for new runs. The original
contract/lock and target run-01 remain immutable. Resource run-01 failed at import
before any fixture, database or market request: direct script execution did not
put the checkout root on Python's module path. The corrected runner explicitly
adds its own checkout root when loading its source-locked test helpers. Runtime
observer behavior, resource recipes and limits are unchanged.

The frozen target and failed resource run-01 contain all original source copies.
To reproduce that original source lock, copy its source tree to a separate working
directory (retaining the package layout and locked environment); never restore
old files over current work. The original postgres-v1 test fixture is likewise
preserved in native-postgres run-01. No earlier source lock was rewritten.

New exact-target command:

```bash
uv run --offline --frozen python tools/check_ndx_timescale.py \
  --config docs/research/ndx-strategy/observer-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/observer-v1/source-lock-v2.json \
  --output /tmp/ndx-timescale-observer-target/run-02
```

New independent resource command (ordinary PG 16.2; not TimescaleDB proof):

```bash
uv run --offline --frozen python tools/check_ndx_observer_resources.py \
  --config docs/research/ndx-strategy/observer-v1/contract-v2.json \
  --source-lock docs/research/ndx-strategy/observer-v1/source-lock-v2.json \
  --postgres-bin /home/corey/.cache/uv/archive-v0/ZWZ0Mqbj4Iv7hOst/pgserver/pginstall/bin \
  --output /tmp/ndx-observer-resources/run-02
```

The exact harness deliberately restarts PostgreSQL **inside** its task-owned
container, using `pg_ctl` and a shell PID 1. It does not restart the container:
Docker would discard its tmpfs on container restart. Shutdown still stops only
that new fixture container; no existing container or daemon is managed.

Preparatory checks also exposed a test-only subprocess output-pipe timeout on
`pg_ctl restart`; sending the restarted server output to its owned fixture log
fixed it. The subsequent focused suite passed all 22 checks. This was before
registration; no market data or performance decision depended on the failed check.

Read with [the implementation/activation review](../NDX-02-timescale-observer-review.md).
Both documents retain an incomplete readiness decision until exact-target,
target capacity/restore and current operational preflight evidence exist.
