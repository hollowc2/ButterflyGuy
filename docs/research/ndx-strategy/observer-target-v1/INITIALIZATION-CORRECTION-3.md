# Confirmed entrypoint socket contract — revision 3

Revision-2 exact compatibility run-05 correctly refused the bootstrap server and
timed out before testing. Its container was stopped and source/logs retained.
Read-only inspection of the exact image's entrypoint shows `docker_process_sql`
explicitly clears PGHOST/PGHOSTADDR at line 212. Therefore PGHOST alone cannot
redirect initialization psql. The preserved source is
`reports/research/ndx-02-observer-20261015/target-entrypoint-source-review/run-01/`.

Revision 3 retains the image's default **container-only** Unix socket at
`/var/run/postgresql` alongside the private host-visible `/socket`. TCP remains
disabled and network mode none. Both final-postmaster startup proofs from
revision 2 remain mandatory. No upstream image/source or live service is changed.
Preserve both failed attempts and the original bootstrap-only test evidence.

Use `contract-v3.json` and `source-lock-v3.json`, with new outputs:

```bash
uv run --offline --frozen python tools/check_ndx_timescale.py \
  --config docs/research/ndx-strategy/observer-target-v1/contract-v3.json \
  --source-lock docs/research/ndx-strategy/observer-target-v1/source-lock-v3.json \
  --output /tmp/ndx-timescale-observer-target/run-06

uv run --offline --frozen python tools/check_ndx_target_restore.py \
  --config docs/research/ndx-strategy/observer-target-v1/contract-v3.json \
  --source-lock docs/research/ndx-strategy/observer-target-v1/source-lock-v3.json \
  --output /tmp/ndx-target-resources-restore/run-02
```

Resource cases, restore assertions and budgets are unchanged; no performance
observations have informed this infrastructure correction. Nothing is activated.
