# First observer capture — Monday 2026-10-19

**Result: `accepted`** — see [Outcome](#outcome-2026-10-19).

Prepared 2026-10-18. Both scripts run on Helios as `billy`, launched by Corey from
the workstation (Claude's auto mode cannot read Helios secrets). Neither prints
secrets; each writes a result JSON under
`/opt/ndx-observer-review/v1/sessions/2026-10-19/`.

| Script | SHA-256 | Effect |
| --- | --- | --- |
| [ndx_capture_prepare.py.txt](ndx_capture_prepare.py.txt) | `6221572f…e91a6` | Read-only checks + builds the session package. No market-data request. |
| [ndx_capture_run.py.txt](ndx_capture_run.py.txt) | `eb6055c8…0c04` | **The one capture.** Needs separate approval. One background option-chain request. |

## Timeline (UTC, PDT in effect)

| When | What |
| --- | --- |
| 13:30 | Cash open. Apps' `/ready` should turn 200 once fresh spot/chain/bars arrive. |
| 14:00–14:45 | NDX paper entry window (07:00–07:45 PT). Don't run anything here. |
| ≥ 14:50 | **Prepare.** Needs exactly one OPEN NDX trade today. |
| after approval, ≤ 19:45 | **Capture**, ideally soon after prepare (deadline = close − 15 min). |
| 20:00 | Close. The context expires and is never reused. |

```
cd /mnt/Repos/Trading/Butterflyguy/docs/research/ndx-strategy/observer-capture-20261019
ssh billy@helios python3 - < ndx_capture_prepare.py.txt   # expect "status": "prepared"
ssh billy@helios python3 - < ndx_capture_run.py.txt       # only after approval
```

## Prepare checks (any failure → `not_prepared`, nothing built)

App/gateway images match the pinned identities; gateway healthy; registry
`32ac923c…` on host and in container; all `/health` 200 and NDX `/ready` 200; no
observer container running; no stale root `context.json`. The NDX app's own
calendar says paper NDX, trading day, market open, session = today, ≥ 45 min to
close; exactly one OPEN NDX trade (none → skip the day; never pick contracts by
hand). DB filesystem free ≥ 10 GiB (WAL size recorded); research relations
< 512 MiB via the observer login. It then writes `package/` (exclusive create)
with `capture-policy.json`, `context.json` (fresh random ids) and
`compose.capture.yaml` (flag literally `false`; context bound read-only).
Validation runs the context through `Acquisition` with `--network none`, plus
`compose config --no-env-resolution`. A failed prepare leaves no package and can
be rerun.

## Capture checks and acceptance

Before: exactly one `prepared` result whose package hashes still match; before
the deadline; no prior claim/capture container; images unchanged since prepare;
registry unchanged; NDX ready; the selected trade is still OPEN with the same
three symbols; zero research rows for this snapshot. Then it creates
`capture-claim.json` (exclusive, never removed) and makes **one**
`docker compose run -e NDX_OBSERVER_ENABLED=true` with a 90 s timeout. The
container is retained.

`accepted` requires all of: exit 0; output exactly
`{"quote_status":"success","recording_status":"published","receipt_journaled":true}`;
exactly one quote/provenance/publication row and one `attempt` + one `commit_ack`
journal row for the snapshot; total publications +1; app/gateway images and
start times unchanged; apps `/health` 200 and NDX `/ready` 200.

Anything else after the attempt → `needs_reconciliation_do_not_retry`. Do not
rerun. Reconcile the evidence first; any corrective acquisition needs new ids,
explicit lineage and its own approval. Rollback is only stopping the named
observer container. Never drop or truncate research tables, or restart trading
apps.

## Not covered

No broker position/order query (paper DB state only). No independent full-DB
backup. No WAL growth cap beyond the 10 GiB admission floor. Acceptance is
mechanics only: the capture feeds NDX-02 Stage C and makes no economic claim.

## Outcome 2026-10-19

- Prepare attempt 1 (16:06 UTC) failed `not_prepared` (IndexError) before building
  anything: the DB image's busybox `df` has no `--output`. Fixed to `df -Pk`/`du -sk`
  (prepare script hash above is the fixed one; original `ff3454ab…`).
- Prepare attempt 2 (16:07:54 UTC) `prepared`: trade **358** OPEN (entered 14:12:51),
  `NDXP  261019C29510000/29610000/29710000`; free 23.2 GB, WAL 512 MiB; research
  tables empty (128 KiB). Package hashes: policy `2397a8f2…`, context `82f45a5d…`,
  compose `bde48b9c…`.
- Capture (16:08:55 UTC) **accepted**: acquisition
  `ndx-20261019-t358-6d20ec88b383-acquisition`; exit 0; quote success, published,
  receipt journaled; exactly one quote/provenance/publication row; journal
  `acquisition_started`, `attempt`, `commit_ack`, `consumer_receipt` × 1 each.
  Quote `3e364527…`, response `a919dbb4…`, publication `1ef8c863…`. All app/gateway
  identities unchanged, all `/health` and `/ready` 200 before and after.
- Gateway log: one `option_chain_v1` from `ndx-timescale-observer-v1`, HTTP 200,
  **12 ms**, no errors or warnings. That latency implies the body was served from the
  gateway's short option-chain cache (likely the NDX app's own recent fetch), not a
  fresh upstream call. Stage C must treat freshness and cache provenance as an explicit
  question, not assume a fresh upstream quote.

Evidence: `reports/research/ndx-02-observer-capture-20261019/` (summary) and
`/opt/ndx-observer-review/v1/sessions/2026-10-19/` on Helios (full results, package,
claim, retained container `ndx_observer_capture_20261019`). Not done: research-schema
export to the Eros archive.
