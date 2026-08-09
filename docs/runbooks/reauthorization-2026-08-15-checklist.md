# Re-authorization checklist — Saturday 2026-08-15

Operator-executed. Derived from the Window F execution (2026-08-08 21:56–22:15 UTC), which ran
cleanly; this is that sequence with the Window G and Window H findings folded in.

## The deadline, and why the time of day matters

| | |
|---|---|
| Current refresh token created | `2026-08-08T22:05:28Z` (Sat) |
| **Hard expiry** | **`2026-08-15T22:05:28Z` (Sat) = 15:05 PDT** |
| Keepalive starts alerting | `2026-08-15T14:05Z` = **07:05 PDT**, only 8 h of margin |

**Finish before 15:05 PDT / 22:05 UTC.** This is a Saturday *morning-to-midday* task in local time,
not an evening one. 2026-08-15 is the only Saturday before expiry.

**Go earlier in the day than 15:05 PDT, not later.** Each new expiry is exactly seven days after the
moment you re-authorize. Re-authorizing at 09:00 PDT banks permanent slack in the weekly cadence;
re-authorizing at 14:30 PDT spends it and leaves 30 minutes of margin next week. The slack only ever
accumulates in one direction, so buy it early.

**Do not slip to Sunday.** The cadence is self-perpetuating: a Sunday re-auth makes every future
expiry a Sunday, and it stays there. Losing the Saturday property means every future re-auth
restarts five containers on a trading day.

## Before you start

- [ ] No open position — `butterfly_trades` must have zero rows with a null `exit_time`.
      (At Window H close: 224 rows, all `CLOSED`.)
- [ ] Market closed (Saturday — automatic).
- [ ] All five token consumers `running`, `RestartCount=0`.
- [ ] Baseline green: `uv run python -m pytest` → 975 passed, 1 skipped; `uv run ruff check .` clean.
      Use `python -m pytest`; `uv run pytest` cannot spawn on this machine.

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

## Step 4 — restart all five consumers, **gateway first**

A directory bind lets a container *see* a new inode; it does not make it *re-read* one.
`SchwabClientWrapper.initialize()` calls `client_from_token_file` exactly once at startup, and
schwab-py then holds the token in memory and only ever writes back. **All five consumers need
restarting, not just the feed.**

**The gateway must go first.** It holds the old refresh token in memory and will write it back over
your new document on its next refresh if it is still running.

```bash
ssh helios 'docker restart butterfly_schwab_gateway_live'
# wait for healthy before continuing
ssh helios 'docker inspect -f "{{.State.Health.Status}}" butterfly_schwab_gateway_live'
ssh helios 'docker restart butterfly_spx_app butterfly_ndx_app butterfly_xsp_app'
ssh helios 'docker restart butterfly_spx_candidate_feed'
```

- [ ] Gateway restarted first and reached `healthy`.
- [ ] Three trading apps restarted.
- [ ] Candidate feed restarted.

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

## Known defect to work around

The `--sunday-reminder` cron (`50 1 * * 1`) fires **Monday 01:50 UTC, 27.7 hours after the Saturday
expiry**. It cannot prompt a re-auth in time and must not be relied on. Your only automated warning
is the hourly keepalive's 8-hour window opening at 07:05 PDT that morning. Set your own calendar
reminder. Changing the cron requires an explicit operator decision and was not made in Window H.
