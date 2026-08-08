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

Run this exact block. It was executed read-only on 2026-08-06 and is known to produce
bounded output. **Do not improvise a variant under time pressure** — this project has
already lost a window to an ad-hoc wrapper that emitted a raw traceback and tripped the
information-exposure stop condition.

```sh
set -u
for c in butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  echo "$c status=$(docker inspect -f '{{.State.Status}}' "$c" 2>/dev/null || echo missing)" \
       "image=$(docker inspect -f '{{.Image}}' "$c" 2>/dev/null | cut -c8-19)" \
       "restarts=$(docker inspect -f '{{.RestartCount}}' "$c" 2>/dev/null)"
done
stat -c 'host_inode=%i mode=%a uid=%u gid=%g' /opt/butterflyguy/tokens.json
for c in butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  echo "$c inode=$(docker exec "$c" stat -c '%i' /app/tokens.json 2>/dev/null || echo NA)"
done
echo "keepalive_cron_entries=$(crontab -l 2>/dev/null | grep -c schwab_token_keepalive)"
```

Expected at last check: images `faa85d748358` / `ca2ca79ca2c6` / `cc58c70ea998`; host inode
`1067464` at mode `600`, uid/gid `1001`; SPX inode `1112240` with NDX/XSP on `1067464`;
2 cron entries. **If SPX already reports `1067464`, it has restarted on its own and the
divergence is already retired** — this changes nothing else in the window.

### Token field digests (read-only)

Used in A0 and again in A7. Compares SHA-256 prefixes only; no value is printed, copied,
or stored, and a digest cannot be reversed to the token.

```sh
probe='
import json,hashlib,sys
try:
    d=json.load(open(sys.argv[1]))
    t=d.get("token",{})
    for f in ("refresh_token","access_token"):
        v=t.get(f)
        print(f"{f}_sha12=" + (hashlib.sha256(v.encode()).hexdigest()[:12]
              if isinstance(v,str) and v else "absent"))
    ct=int(d.get("creation_timestamp",0))
    import time
    print(f"age_days={(time.time()-ct)/86400:.2f}" if ct>0 else "age_days=invalid")
except Exception:
    print("unreadable")
'
echo "== host =="; python3 -c "$probe" /opt/butterflyguy/tokens.json
for c in butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  echo "== $c =="; docker exec -i "$c" python3 -c "$probe" /app/tokens.json 2>/dev/null || echo unavailable
done
```

Expected before re-authorization: `refresh_token_sha12=c5f05cc3fe64` on all four, SPX's
`access_token_sha12` differing, `age_days` near 4.3 on all four.

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

**Helios is headless.** The Schwab OAuth flow is browser-based and cannot complete there.
Mint the token on `zeus`, which has a browser, then `scp` it across. `tools/auth_init.py`
is byte-identical on both hosts — same API key and app secret by digest — so a token minted
on zeus is valid on Helios.

**`easy_client` silently no-ops if a live token is already present.** It calls
`easy_client(..., max_token_age=561600.0)` — 6.5 days. If `tokens.json` in the working
directory is younger than that, it loads the existing document and skips the login flow
entirely, while `auth_init.py` still prints `tokens.json created successfully`. A token
younger than 6.5 days will therefore not actually be replaced by re-running this step.
**Park the existing document first, on whichever host is minting the token, so
`easy_client` finds nothing:**

```
cd /mnt/Repos/Trading/Butterflyguy      # on zeus
mv tokens.json tokens.json.pre-reauth   # forces easy_client to authorize
.venv/bin/python tools/auth_init.py
```

`tools/auth_init.py` calls `easy_client` with callback `https://127.0.0.1:8182` and writes
`tokens.json` **relative to the current directory**, so running it from anywhere else puts
the document in the wrong place. Complete the Schwab login and MFA in the browser. Then
ship it:

```
scp /mnt/Repos/Trading/Butterflyguy/tokens.json helios:/opt/butterflyguy/tokens.json
```

Do the same parking on Helios (`mv tokens.json tokens.json.pre-reauth`) before the `scp`
lands, so the old document doesn't collide with the incoming one.

**`tokens.json.pre-reauth` is not covered by `.gitignore`** (only `tokens.json` is) on
either host, and on Helios the repo root is also the token directory — move the parked
file outside the working tree rather than leaving it in place. It supplies Window A's only
rollback: the old refresh token stays valid until its own expiry, so if the flow fails or
is aborted, `mv tokens.json.pre-reauth tokens.json` restores it at no cost. Once A7 verifies
the new document, delete both parked copies — the old refresh token is retired the moment
the new authorization succeeds, so it has no further value.

**Never treat "the script said success" as evidence of re-authorization.** Only A4's digest
check does — the printed message is identical whether or not the login flow actually ran.

## A4 — Verify the new document

```
stat -c 'mode=%a uid=%u gid=%g' /opt/butterflyguy/tokens.json
```

**`scp` does not preserve mode 0600** (typically lands at `644`), and **`easy_client` does
not guarantee it either**. Fix it before starting any service:

```
chmod 600 /opt/butterflyguy/tokens.json
```

Then confirm: regular file, not a symlink, mode `600`, uid/gid `1001`, and a
`creation_timestamp` age near zero. The advisory lock `/opt/butterflyguy/.tokens.json.lock`
is expected to persist and is not a stale-lock signal. **`age_days` near zero and a changed
`refresh_token_sha12` are the only proof the re-authorization took effect** — cross-check
against the A0 digest, since a value still equal to the pre-A3 `refresh_token_sha12` means
`easy_client` loaded the old document instead of re-authorizing.

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

Re-run the **A0 snapshot block** and the **token field digests block** verbatim, then check:

1. All three containers `running` on the **same image IDs** recorded in A0, with
   `restarts` unchanged — `docker start` must not have recreated anything.
2. All three now resolve `/app/tokens.json` to the **same inode** as the host document.
   This is the SPX divergence fix, and it is the check that proves it.
3. All four `refresh_token_sha12` values identical **and different from `c5f05cc3fe64`** —
   a value still equal to the old one means the authorization did not take effect.
4. All four `access_token_sha12` values now identical too.
5. `age_days` near `0.00` on all four.

Then the settle window:

```sh
sleep 30
for c in butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  echo "$c errors_30s=$(docker logs --since 30s "$c" 2>&1 | grep -ci 'error\|traceback\|exception')"
done
```

Expect `0` for each. Verify by inode and digest, never by "the container started".

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

The evidence patterns are now in `.gitignore` on the branch, so once B2 lands the hazard is
structural rather than procedural and a stray `git add -A` can no longer capture them. Until
B2 lands, the rule above is the only protection.

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
