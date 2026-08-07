# Runbook — token re-authorization, then gateway enablement

Two windows, deliberately separate. Window A is mandatory and deadline-driven. Window B is
optional and unhurried. **Do not merge them.**

This revises the earlier advice to bundle everything into one window. Bundling looked
attractive because both need the containers recreated, but the token relocation turns out
to require source changes to `tools/schwab_token_keepalive.py` and `tools/auth_init.py`,
which in turn requires the 64-commit checkout update. Putting a code delivery inside a
deadline window means debugging new code and a fresh credential at the same time. Window A
is now the minimum that satisfies the deadline: no code change, no Compose change, no
rebuild.

All host facts below were verified read-only on 2026-08-06. Re-verify before acting.

---

# Window A — Token re-authorization (mandatory)

**Deadline.** The refresh token expires 7 days after its `creation_timestamp`, which was
4.32 days old at `2026-08-07T04:25Z` — so expiry falls around **2026-08-09T21:00Z**. The
keepalive begins alerting 8 hours before (`WARN_BEFORE`, `tools/schwab_token_keepalive.py`).

**Precondition.** Market closed. This is interactive and requires a browser and MFA.

**Scope.** Stop three services, re-authorize in place, start three services. Nothing else.
No code change, no Compose change, no image rebuild, no checkout update.

**Free side effect.** SPX is currently pinned to an orphaned token inode (1112240) because
it has not restarted since `2026-08-04T21:14:26Z`. Stopping and starting it re-resolves its
bind mount, which retires the divergence at no extra cost. This is the only reason it needs
fixing at all — the divergence is otherwise benign, since all four documents share refresh
token `c5f05cc3fe64`.

## A0 — Snapshot (read-only)

Record, so the verification step has a baseline:

- container and image IDs for `butterfly_spx_app`, `butterfly_ndx_app`, `butterfly_xsp_app`
  (last seen `faa85d748358`, `ca2ca79ca2c6`, `cc58c70ea998`);
- the token document's inode, mode, uid/gid, and SHA-256 prefix;
- `crontab -l | grep -c schwab_token_keepalive` (expected: 2).

## A1 — Disable the keepalive

The keepalive runs hourly and would race the authorization flow.

```
crontab -l > /tmp/crontab.snapshot.$(date +%s)
crontab -l | grep -v schwab_token_keepalive | crontab -
crontab -l | grep -c schwab_token_keepalive    # expect 0
```

Keep the snapshot path. Restoring the cron is step A6 and must not be skipped.

## A2 — Stop the three trading services

```
docker stop --timeout 30 butterfly_spx_app butterfly_ndx_app butterfly_xsp_app
```

Use `--timeout`, **not** `--time`. Docker CLI 29.6.2 writes
`Flag --time has been deprecated, use --timeout instead` to stdout, which broke a previous
window's output gate.

Confirm all three report `exited`.

## A3 — Re-authorize

```
cd /opt/butterflyguy
.venv/bin/python tools/auth_init.py
```

`tools/auth_init.py` calls `easy_client` with callback `https://127.0.0.1:8182` and writes
`tokens.json` **relative to the current directory**, so running it from anywhere else puts
the document in the wrong place. Complete the Schwab login and MFA in the browser.

## A4 — Verify the new document

```
stat -c 'mode=%a uid=%u gid=%g' /opt/butterflyguy/tokens.json
```

**`easy_client` does not guarantee mode 0600.** If it is anything else, fix it before
starting any service:

```
chmod 600 /opt/butterflyguy/tokens.json
```

Then confirm: regular file, not a symlink, mode `600`, uid/gid `1001`, and a
`creation_timestamp` age near zero. The advisory lock `/opt/butterflyguy/.tokens.json.lock`
is expected to persist and is not a stale-lock signal.

## A5 — Start the three services

```
docker start butterfly_spx_app butterfly_ndx_app butterfly_xsp_app
```

`start` rather than `up`, so no Compose recreation occurs and the recorded images are
retained.

## A6 — Restore the keepalive

```
crontab /tmp/crontab.snapshot.<timestamp>
crontab -l | grep -c schwab_token_keepalive    # expect 2
```

## A7 — Verify

1. All three containers `running` on the **same image IDs** recorded in A0.
2. All three resolve `/app/tokens.json` to the **same inode** as the host document — this
   is the SPX divergence fix; compare `docker exec … stat -c %i` against the host.
3. All four `refresh_token` SHA-256 prefixes are identical, and all four `access_token`
   prefixes now match too.
4. No fresh filtered errors per service over a 30-second settle window.
5. `/metrics` on each service still scrapes.

## Window A rollback

**There is none for the token document.** The standing rule forbids copying it, so no prior
copy exists, and the old refresh token is retired by the new authorization the moment it
succeeds. If the document ends up invalid, the remedy is to run A3 again.

Every other step is reversible: restore the cron from the snapshot, and `docker start` any
service left stopped. The container images are never touched.

---

# Window B — Gateway enablement (optional, unhurried)

**Precondition.** Window A complete, all three services healthy, all four token digests in
agreement.

Nothing here is deadline-driven. If any step looks wrong, stop; the gateway staying
undeployed costs nothing.

## B1 — Decide how the code reaches Helios

Helios is on branch `main` at `de84d91`, **64 commits behind local `main`** and 15 behind
`origin/main`, with nothing local `main` lacks. Two options:

- **Push and pull.** Simple, but puts 64 commits onto the live host's `main` and requires a
  remote push, which this project has never done.
- **Reviewed archive.** The credential proof's precedent: build a tarball of exactly the
  reviewed paths, verify its SHA-256 on both ends, extract. Slower, but it is the mechanism
  this project already trusts, and it does not alter the host's git state.

This is an operator decision and is not made here.

## B2 — Update the checkout, preserving evidence

**Never use `git clean`, and never `git add -A`.** The host carries 33 untracked
credential-proof and runtime-baseline evidence artifacts plus `.tokens.json.lock`, none of
which is gitignored. They must survive, and they must not be committed.

The two tracked modifications, `configs/universes/liquid.txt` and
`configs/universes/liquid_meta.json`, are weekly `refresh_equity_universes.py` output. None
of the 64 incoming commits touches either, so they will not conflict and can be left
modified.

Consider adding the evidence patterns to `.gitignore` as part of this window.

## B3 — Relocate the token document

This is what unblocks the gateway mount. `/opt/butterflyguy` is simultaneously the git
checkout root, the evidence directory, and the token directory, so mounting it into the
gateway container would expose the entire source tree read-write.

Required changes, all of which arrive with B2:

- `tools/schwab_token_keepalive.py` — `TOKEN_PATH = ROOT / "tokens.json"` must become
  configurable, honouring `SCHWAB_TOKEN_PATH`;
- `tools/auth_init.py` — writes `"tokens.json"` relative to the working directory; same;
- `infra/docker-compose.yml` — the bind source for all three trading services, currently
  `/opt/butterflyguy/tokens.json:/app/tokens.json`.

Then move the document into the dedicated directory (mode `0700`, uid/gid `1001`), recreate
the three services so their binds re-resolve, and verify as in A7. A bind mount whose source
path no longer exists **does not fail loudly** — Docker creates an empty directory — so
verify by inode and digest, never by "the container started".

Set `SCHWAB_GATEWAY_TOKEN_DIR` to the new directory.

## B4 — Issue the internal consumer keys

```
.venv/bin/python -m butterfly_guy.scripts.issue_gateway_keys \
  --output secrets/schwab-gateway-keys.json \
  --client butterfly-guy
```

Add `--client equity-scanner` / `--client afterhours-lab` only if those consumers will
actually use the gateway. The command prints each plaintext key exactly once — distribute
them then, because they cannot be recovered. It refuses to overwrite an existing path, and
it validates the result through the real loader before reporting success.

## B5 — Re-run the read-only preflight

Everything in the Option A runbook's preflight section. Note that **port 8010 is bound by
the unrelated `halt_scanner` container**, so the demo service cannot bind on this host; the
live service's 8011 was free.

## B6 — Bring the gateway up, then take it down

```
docker compose -f infra/docker-compose.gateway.yml --profile gateway-live up -d
```

The goal of the first window is "it started, answered `/ready` 200, served one authenticated
quote, and rolled back clean" — not "it stays up". Tear it down in the same window:

```
docker compose -f infra/docker-compose.gateway.yml --profile gateway-live down
```

The gateway is a separate Compose project with its own container name and port, and no
consumer points at it, so stopping it cannot affect the trading services. `SCHWAB_ACCESS_MODE`
and `SCHWAB_GATEWAY_SHADOW_READS` both still default to values that ignore it entirely.

## B7 — Not in this window

Wiring any consumer to the gateway, enabling `SCHWAB_GATEWAY_SHADOW_READS`, `GET /v1/history`,
and any account or order operation. Each is a separate decision.
