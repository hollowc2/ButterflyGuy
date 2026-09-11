# Re-authorization checklist — Saturday 2026-08-22

Operator-executed. Derived from `reauthorization-2026-08-15-checklist.md`, with the consumer list,
container names, and Phase 8 constraint corrected to host state verified read-only at
`2026-08-22T15:45:36Z`.

## What is different this time: the Phase 8 clock

| | |
|---|---|
| Current refresh token expiry | `2026-08-23T23:34Z` (Sun) — 32.6 h out at 15:45Z |
| Phase 8 qualifying start | `2026-08-18T04:00:06.893767848Z` |
| **Phase 8 seven-day gate ends** | **`2026-08-25T04:00:06.893767848Z`** |

> The `2026-08-17T00:39:37.451595824Z` start that appears in ledger row `2026-08-16 | Phase 8
> baseline` is **invalidated** and no part of it is credited. Read the qualifying start from the
> "Phase 8 stability ledger" section header, not from that row.

The token dies **1 d 4 h before the soak window closes**, and Monday's open falls 14.5 h before it.
That ordering is the whole reason this checklist matters more than usual:

- The reload path changes no container identity, so the window survives it.
- **Deferring the re-authorization is not an option.** A dead refresh token would be carried through
  a full live trading session before the gate closes.
- **The step-4 restart fallback would zero a seven-day clock with ~2.5 days left.** If a reload does
  not appear to fire, stop and diagnose — do not restart reflexively. See step 4.

One deviation is already on the record: a docker daemon restart at `2026-08-20T02:39:5xZ` advanced
`StartedAt` on every baselined container (IDs, `Created`, images, and `RestartCount=0` all survived).
A second, deliberate restart would not be ambiguous.

## Preconditions — verified 2026-08-22T15:45:36Z

- [x] No open position — `butterfly_trades` rows with null `exit_time`: **0**. Friday's 252/253/254
      are all `CLOSED`.
- [x] Market closed (Saturday).
- [x] All **six** token consumers `running`, `RestartCount=0`.
- [ ] Baseline green: `uv run python -m pytest` and `uv run ruff check .`.
      Use `python -m pytest`; `uv run pytest` cannot spawn on this machine.

Host document at baseline: inode `1766`, `787` bytes, mode `600`, owner `1001:1001`.

## The six consumers

The 2026-08-15 checklist listed five and used the pre-extraction name
`butterfly_schwab_gateway_live`. Current state:

| Consumer | Mount | How it holds the token | Restart? |
|---|---|---|---|
| `schwab_gateway_live` | rw | fresh client per request, built inside the token lock and discarded | **No** |
| `schwab_gateway_candidate` | rw | same adapter, same per-request construction | **No** |
| `butterfly_spx_app` / `_ndx_` / `_xsp_` | rw | cached at startup; `reload_if_reauthorized` picks up a new one by itself | **No, if the reload fires** |
| `butterfly_spx_candidate_feed` | ro | cached, with a marker watcher and a read-only `$SPX` validation quote before swap | **No, if the reload fires** |

`TOKEN_RELOAD_INTERVAL` is `300.0 s`, hardcoded in `run_live.py:101` and `run_candidate_feed.py:24`;
it is not set in any container environment, so the default is what runs.

**Expected restarts: zero.**

## Step 1 — mint on zeus, in a real terminal

> **Run this in a real terminal window.** Not through a Claude session's `!` prefix, and not through
> any agent-run shell. That path has no stdin, the flow prompts for ENTER, and **schwab-py prints the
> app key in its own banner before failing** — that is how Window F leaked the `client_id` into a
> transcript.

```bash
cd /mnt/Repos/Trading/Butterflyguy
SCHWAB_TOKEN_PATH=/tmp/tokens.new.json .venv/bin/python tools/auth_init.py
```

- [ ] Flow completed; `/tmp/tokens.new.json` written.
- [ ] Sanity-check the envelope **without printing values**:

```bash
python3 -c "
import json,datetime
d=json.load(open('/tmp/tokens.new.json'))
c=datetime.datetime.fromtimestamp(d['creation_timestamp'],datetime.timezone.utc)
print('created', c.isoformat(), c.strftime('%A'))
print('expires', (c+datetime.timedelta(days=7)).isoformat())
print('keys   ', sorted(d.keys()), sorted(d['token'].keys()))
print('bytes  ', len(open('/tmp/tokens.new.json','rb').read()))"
```

Expect schema `{creation_timestamp, token:{access_token, expires_at, expires_in, id_token,
refresh_token, scope, token_type}}` and ~787 bytes. `creation_timestamp` must be **today**, and the
derived expiry must be **Saturday 2026-08-29**. If `creation_timestamp` did not move, the
re-authorization silently no-opped — stop and investigate (CODEX_STATE, "Correction 2 —
`easy_client` silently no-ops the re-authorization").

- [ ] Record the digest prefix on zeus: `sha256sum /tmp/tokens.new.json | cut -c1-12`

## Step 2 — stage on Helios, verify byte-identical

```bash
scp /tmp/tokens.new.json helios:/opt/butterflyguy-tokens/.tokens.json.incoming
ssh helios 'chmod 600 /opt/butterflyguy-tokens/.tokens.json.incoming
            sha256sum /opt/butterflyguy-tokens/.tokens.json.incoming | cut -c1-12'
```

- [ ] Digest matches step 1. `scp` does not preserve mode — the `chmod 600` is required.

## Step 3 — move into place under the C1 lock

```bash
ssh helios 'cd /opt/butterflyguy-tokens && flock -w 30 .tokens.json.lock \
  mv .tokens.json.incoming tokens.json && \
  stat -c "%i %s %a %u:%g" tokens.json && sha256sum tokens.json | cut -c1-12'
```

- [ ] Moved. Inode is **new** (baseline was `1766`); digest still matches step 1.
- [ ] Mode `600`, `1001:1001`, ~787 bytes.

## Step 4 — watch the reloads; restart only on a *confirmed* failure

> **Use `--tail`, not `--since`.** On `2026-08-22`, `docker logs --since` returned **zero lines** for
> `butterfly_spx_candidate_feed` while `--tail` showed live traffic through the same instant. The
> feed had reloaded at `15:56:12.683Z` — first of the four — and `--since` reported `reloaded=0` for
> eight consecutive minutes. Trusting it would have triggered the fallback restart on a reload that
> had already succeeded. This is the same class of defect already recorded for `docker events`, and
> it is why Phase 8 checkpoint 0 read log files directly rather than using the Docker log API.

Within 5 minutes of the move, all three apps should log `schwab_token_reloaded`:

```bash
ssh helios 'for c in butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  printf "%-22s reloaded=%s failed=%s\n" $c \
    $(docker logs --tail 3000 $c 2>&1 | grep -c schwab_token_reloaded) \
    $(docker logs --tail 3000 $c 2>&1 | grep -c schwab_token_reload_failed); done'
```

- [ ] `reloaded=1` on all three, `failed=0`.

The feed logs **two** events on success, from two different loggers — grep for either:

```bash
ssh helios 'docker logs --tail 3000 butterfly_spx_candidate_feed 2>&1 \
  | grep -E "candidate_market_data_token_reloaded|candidate_token_reload_applied|candidate_token_reload_failed" | tail -3'
```

- [ ] `candidate_market_data_token_reloaded` (from `schwab_market_data.py:104`) **and**
      `candidate_token_reload_applied` (from `run_candidate_feed.py:37`), no `_failed`. The feed
      validates against Schwab before installing the replacement, so this also proves the credential
      reached Schwab.

The Docker log API on Helios is slow; a `--tail` query can take minutes or exceed a 120 s timeout.
Let it finish. A timeout is not a negative result.

**If a reload has not appeared after 6+ minutes, do not restart yet — diagnose.** The pre-existing
fallback is `docker restart <consumer>`, and it costs the whole soak window. Two hypotheses produce
an identical `reloaded=0`:

1. **The system failed** — the consumer did not pick up the new token.
2. **The measurement failed** — it reloaded and the query cannot see it.

They cost wildly different things to be wrong about and about two minutes to tell apart, so:

- [ ] Query a **second way** (`--tail` vs `--since`, different grep, wider window).
- [ ] **Sanity-check the instrument**: confirm the query returns *anything at all* for that
      container. An instrument that cannot report a positive cannot report a negative.
- [ ] Only on a confirmed negative, price the restart against the remaining gate time, then decide
      deliberately and record loudly.

Deferring past the gate is **not** a safe alternative here — see the clock table above.

Neither gateway needs anything. `LockedSchwabClientAdapter.execute` builds a client, runs one
operation, and discards it inside a single locked token transaction, so it holds no token between
requests and cannot write a stale one back. Restarting is harmless but is belt-and-braces, and
nothing needs sequencing around it.

Use `docker restart` (not `compose up`) and name services explicitly. `butterfly_spx_candidate` is a
legacy rollback service, `restart: "no"`, exited since 2026-07-23 — a broad `compose up` would start
it. Leave it alone.

## Step 5 — verify, host against containers

```bash
ssh helios 'echo "HOST $(stat -c %i /opt/butterflyguy-tokens/tokens.json) $(sha256sum /opt/butterflyguy-tokens/tokens.json | cut -c1-12)"
for c in schwab_gateway_live schwab_gateway_candidate butterfly_spx_app butterfly_ndx_app \
         butterfly_xsp_app butterfly_spx_candidate_feed; do
  printf "%-30s " $c
  docker exec $c sh -c "stat -c %i /opt/butterflyguy-tokens/tokens.json; sha256sum /opt/butterflyguy-tokens/tokens.json | cut -c1-12" 2>&1 | tr "\n" " "; echo
done'
```

- [ ] Host and **all six** consumers agree on one inode and one digest. Verify *agreement against the
      host* — never container-against-container, and never against a number copied from a previous
      window.
- [ ] All six `running`, `RestartCount=0`, `StartedAt` unchanged from `2026-08-20T02:39:5xZ`.
- [ ] Both gateways `healthy`; `up{job="schwab_gateway"} == 1`; `SchwabGatewayDown` inactive.
- [ ] SPX/NDX/XSP `/ready` 200 on `127.0.0.1:8000/8001/8003`.
- [ ] `schwab_token_persist_failed` and `task_group_error` absent from all three trading apps.

**Proof on the production path:** all three trading apps resolve account hashes on startup, and the
reload re-resolves one before installing its candidate client — a real authenticated Schwab call.
Zero errors there means the credential is proven for the trading path, not merely mounted.

## Step 6 — record

- [ ] Add a Phase 8 ledger row to `docs/architecture/schwab-gateway-standalone-extraction-plan.md`
      with the new lineage timestamp, the new inode/digest, the reload counts, and an explicit
      statement that no consumer restarted and no container identity changed.
- [ ] Next deadline: **Saturday 2026-08-29**, seven days after the moment of authorization. Go early
      in the day; the deadline inherits the time you authorize. Do not slip to Sunday — the cadence
      is self-perpetuating.
