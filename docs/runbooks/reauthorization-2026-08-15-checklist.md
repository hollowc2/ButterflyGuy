# Re-authorization checklist — Saturday 2026-08-15

Operator-executed. Derived from the Window F execution (2026-08-08 21:56–22:15 UTC), which ran
cleanly; this is that sequence with the Window G and Window H findings folded in.

## The deadline, and why the time of day matters

| | |
|---|---|
| Current refresh token created | `2026-08-08T22:05:28Z` (Sat) |
| **Hard expiry** | **`2026-08-15T22:05:28Z` (Sat) = 15:05 PDT** |
| Keepalive starts alerting | `2026-08-14T22:05Z` = **Fri 15:05 PDT**, 24 h of margin |

**Finish before 15:05 PDT / 22:05 UTC.** This is a Saturday *morning-to-midday* task in local time,
not an evening one. 2026-08-15 is the only Saturday before expiry.

**Go earlier in the day than 15:05 PDT, not later.** Each new expiry is exactly seven days after the
moment you re-authorize. Re-authorizing at 09:00 PDT banks permanent slack in the weekly cadence;
re-authorizing at 14:30 PDT spends it and leaves 30 minutes of margin next week. The slack only ever
accumulates in one direction, so buy it early.

**Do not slip to Sunday.** The cadence is self-perpetuating: a Sunday re-auth makes every future
expiry a Sunday, and it stays there. Losing the Saturday property means every future re-auth
restarts the candidate feed on a trading day until its separate hot-reload path is deployed.

## Before you start

- [ ] No open position — `butterfly_trades` must have zero rows with a null `exit_time`.
      (At Window H close: 224 rows, all `CLOSED`.)
- [ ] Market closed (Saturday — automatic).
- [ ] All five token consumers `running`, `RestartCount=0`.
- [ ] Baseline green: `uv run python -m pytest` and `uv run ruff check .` both pass.
      Use `python -m pytest`; `uv run pytest` cannot spawn on this machine.

## Step 0 — already done, nothing to do

The token reload was **deployed 2026-08-09T21:59:16Z**, on images `9a7fcf6f0704` (spx) /
`4d3f578c8cfd` (ndx) / `efc7c0e0c590` (xsp). Do not rebuild.

This makes 2026-08-15 the reload's **first real test**: after step 3 the three trading apps should
pick up the new token on their own, within `TOKEN_RELOAD_INTERVAL` (300 s), with no restart. See
step 4.

The candidate-feed hot reload was built locally on 2026-08-10 but is **not deployed**. Unless a
separate approved deployment is completed and verified before this checklist runs, the feed still
requires the explicit restart in step 4. Do not infer live capability from repository code.

## Step 1 — mint the token on zeus, in a real terminal

Helios is headless; the browser flow runs on zeus. zeus and Helios carry identical app credentials
(API key sha `6888173cf7e1`, secret sha `872ed858a44d`), so a token minted on zeus is valid on Helios.

> **Run this in a real terminal window.** Not through a Claude session's `!` prefix, and not through
> any agent-run shell. That path has no stdin, the flow prompts for ENTER, and **schwab-py prints the
> app key in its own banner before failing** — that is exactly how Window F leaked the `client_id`
> into a transcript.

Point `SCHWAB_TOKEN_PATH` at a scratch file so your existing `./tokens.json` is untouched:

```bash
cd /mnt/Repos/Trading/Butterflyguy
SCHWAB_TOKEN_PATH=/tmp/tokens.new.json .venv/bin/python tools/auth_init.py
```

- [ ] Flow completed in the browser; `/tmp/tokens.new.json` written.
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

Expect the schema `{creation_timestamp, token:{access_token, expires_at, expires_in, id_token,
refresh_token, scope, token_type}}` and ~787 bytes. `creation_timestamp` must be **today**, and the
derived expiry must be **Saturday 2026-08-22**. If `creation_timestamp` did not move, the
re-authorization silently no-opped — stop and investigate (see CODEX_STATE "Correction 2 —
`easy_client` silently no-ops the re-authorization").

- [ ] Record the digest prefix on zeus: `sha256sum /tmp/tokens.new.json | cut -c1-12`

## Step 2 — stage on Helios and verify byte-identical

```bash
scp /tmp/tokens.new.json helios:/opt/butterflyguy-tokens/.tokens.json.incoming
ssh helios 'chmod 600 /opt/butterflyguy-tokens/.tokens.json.incoming
            sha256sum /opt/butterflyguy-tokens/.tokens.json.incoming | cut -c1-12'
```

- [ ] Digest on Helios **matches** the zeus digest from step 1. `scp` does not preserve mode — the
      `chmod 600` above is required, not optional.

## Step 3 — move into place under the C1 lock

Take `.tokens.json.lock` — the same `fcntl.flock` primitive the gateway, the trading apps
(`token_manager.py:295`) and the keepalive use. Moving without the lock bypasses C1.

```bash
ssh helios 'cd /opt/butterflyguy-tokens && flock -w 30 .tokens.json.lock \
  mv .tokens.json.incoming tokens.json && \
  stat -c "%i %s %a %u:%g" tokens.json && sha256sum tokens.json | cut -c1-12'
```

- [ ] Moved. Note the **new inode** and confirm the digest still matches step 1.
- [ ] Mode `600`, uid/gid `1001`, ~787 bytes.

## Step 4 — restart the consumers that actually cache the token

A directory bind lets a container *see* a new inode; it does not make it *re-read* one. But the three
token paths differ, and earlier versions of this runbook got the list wrong:

| Consumer | How it holds the token | Restart? |
|---|---|---|
| `butterfly_schwab_gateway_live` | **fresh client per request**, constructed inside the token lock and discarded | **No** |
| `butterfly_spx_app` / `_ndx_` / `_xsp_` | cached at startup — **but the reload now picks up a new one by itself** | **No, if the reload fires** |
| `butterfly_spx_candidate_feed` | read once at first use, cached in memory, never written back | **Yes** |

**Expected restarts this time: one — the feed.** Down from the four this work started with.

### First, watch the reload do its job

Within 5 minutes of the step-3 move, all three apps should log `schwab_token_reloaded`:

```bash
ssh helios 'for c in butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  printf "%-22s reloaded=%s failed=%s\n" $c \
    $(docker logs --since 10m $c 2>&1 | grep -c schwab_token_reloaded) \
    $(docker logs --since 10m $c 2>&1 | grep -c schwab_token_reload_failed); done'
```

- [ ] `reloaded=1` on all three, `failed=0`. **This is the first production test of the reload —
      record the result either way.**
- [ ] If `reloaded=0` after 6+ minutes, or `failed` is non-zero: **fall back** to
      `docker restart butterfly_spx_app butterfly_ndx_app butterfly_xsp_app`, which is the
      pre-existing procedure, and record loudly that the reload did not fire.

**The gateway does not need restarting, and the old "gateway must go first" rule rested on a false
premise.** `LockedSchwabClientAdapter.execute` constructs a client, runs one operation, and discards
it, all inside a single locked token transaction — its own module docstring calls this "deliberate
and load-bearing". The gateway therefore holds no token between requests and cannot write a stale
one back over your new document. Restarting it anyway is harmless, but it is belt-and-braces, not a
requirement, and nothing needs to be sequenced around it.

### Then restart the feed — the only one that still needs it

```bash
ssh helios 'docker restart butterfly_spx_candidate_feed'
```

- [ ] Candidate feed restarted.
- [ ] Three trading apps **not** restarted (unless the reload failed to fire, above).
- [ ] Gateway left alone (or restarted for reassurance — either is fine).

Thanks to the Window G SIGTERM fix these are now clean sub-2-second exit-0 shutdowns rather than
10-second SIGKILLs. **That is a convenience, not a licence to skip the verification below.**

Use `docker restart` (not `compose up`) and name services explicitly. `butterfly_spx_candidate` is a
legacy rollback service, `restart: "no"`, `Exited (137)` since 2026-07-23 — a broad `compose up`
would start it. Leave it alone.

## Step 5 — verify, host against containers

```bash
ssh helios 'echo "HOST $(stat -c %i /opt/butterflyguy-tokens/tokens.json) $(sha256sum /opt/butterflyguy-tokens/tokens.json | cut -c1-12)"
for c in butterfly_schwab_gateway_live butterfly_spx_app butterfly_ndx_app butterfly_xsp_app butterfly_spx_candidate_feed; do
  printf "%-34s " $c
  docker exec $c sh -c "stat -c %i /opt/butterflyguy-tokens/tokens.json; sha256sum /opt/butterflyguy-tokens/tokens.json | cut -c1-12" 2>&1 | tr "\n" " "; echo
done'
```

- [ ] Host and **all five** consumers agree on one inode and one digest. Verify *agreement against
      the host* — never container-against-container, and never against a specific number copied from
      a previous window.
- [ ] All five `running`, `RestartCount=0`.
- [ ] Gateway `healthy`, on `monitoring_net`, `up{job="schwab_gateway"} == 1`, `SchwabGatewayDown`
      inactive.
- [ ] `schwab_token_persist_failed` and `task_group_error` absent from all three trading apps.
- [ ] All three apps exited `0` on the restart, not `137`.

**Proof on the production path:** all three trading apps resolve account hashes on startup, which is
a real authenticated Schwab call. Zero errors there means the credential is proven for the trading
path, not merely mounted.

## Step 6 — what Saturday cannot prove

The candidate feed makes no Schwab call while the market is closed. `/ready` returning
`503 snapshot_unavailable` on a Saturday is **expected and is not a fault**. The feed's
authentication against the new document will be unobserved until the next market open.

- [ ] Note that the feed's auth is unproven, and carry the Monday check forward. Do not record it as
      passed.

## Step 7 — record

- [ ] New refresh-token sha prefix and `creation_timestamp`/expiry appended to CODEX_STATE.md.
- [ ] Next deadline: **seven days from the moment of re-authorization** — write down the exact UTC
      timestamp, and confirm it is a Saturday.

## Your automated warnings for this deadline

Fixed in Window H — the reminder used to fire **after** the deadline it protected. Current schedule
for the 2026-08-15 expiry:

| When | What | Lead |
|---|---|---|
| Fri 2026-08-14 07:00 PDT | weekly reminder (Telegram), `0 14 * * 5` | 32.1 h |
| Fri 2026-08-14 15:05 PDT | keepalive alert window opens, `WARN_BEFORE = 24h` | 24.0 h |
| **Sat 2026-08-15 15:05 PDT** | **expiry** | — |

The reminder fires **Friday**, not Saturday, deliberately: as you bank slack by re-authorizing
earlier each Saturday, the deadline drifts earlier in the day, and a Saturday-morning reminder would
eventually be too late again. A Friday reminder keeps 24 h+ of lead regardless.

Belt and braces: set your own calendar reminder too. This is the only deadline in the system where
missing it costs a weekday outage.
