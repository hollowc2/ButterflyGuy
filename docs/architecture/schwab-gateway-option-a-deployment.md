# Option A deployment runbook — Helios, containerized

Scope: bring up the read-only Schwab gateway as an isolated container on Helios, serving
real market data through the locked token manager. The operator selected Option A from
`docs/architecture/schwab-gateway-deployment-options.md`.

**Nothing in this runbook has been executed.** It was written offline, against a host with
no Docker daemon and no Helios access. Every step below is a step to perform in an
approved window, not a step already taken.

**Not authorized by this runbook**: wiring any consumer to the gateway, enabling
`SCHWAB_GATEWAY_SHADOW_READS`, order or account operations, or changing anything about
SPX/NDX/XSP. Those remain separate decisions.

## What this deploys

`infra/docker-compose.gateway.yml` service `schwab_gateway_live`, profile `gateway-live`,
container `butterfly_schwab_gateway_live`, bound to `127.0.0.1:8011`. It runs
`run_schwab_gateway.py --serve-live` with both required confirmations.

It serves exactly three routes plus three operational ones: `/v1/quotes`, `/v1/spot`,
`/v1/chain`, `/health`, `/ready`, `/metrics`. There is no account or order route, and
`LockedSchwabMarketDataProvider` exposes only `get_spot_price`, `get_option_chain`, and
`get_equity_quotes` — pinned by
`tests/test_gateway_live_provider.py::test_provider_exposes_only_the_three_read_surfaces`.

The demo service `schwab_gateway_foundation` is unchanged, keeps profile
`gateway-foundation` and port 8010, and cannot be started by the same command.

## Prerequisites

### 1. The internal keys file — Phase 3 dependency 4

Copy `infra/schwab-gateway-keys.example.json` to `secrets/schwab-gateway-keys.json` and
replace each `key_sha256` with the SHA-256 of the consumer key you issue. The template is
schema-checked against the real loader by
`tests/test_gateway_compose.py::test_gateway_keys_example_matches_the_authenticator_schema`.

Rules the loader enforces (`schwab_gateway/auth.py:75-112`):

- the file must not be group- or world-writable — create it mode `0600`;
- `version` must be `1` and the only other key is `clients`;
- each client needs exactly `id`, `key_sha256`, `capabilities`, `priority_class`;
- `id` must be one of `butterfly-guy`, `equity-scanner`, `afterhours-lab`;
- `priority_class` must match the identity's fixed class (`auth.py:31-34`);
- the only known capability is `market_data:read`.

Issue only the identities you actually need. A client absent from the file cannot
authenticate. **Never commit this file.**

### 2. The token directory

Set `SCHWAB_GATEWAY_TOKEN_DIR` to the host directory holding `tokens.json` — on Helios
that is `/opt/butterflyguy`, which the credential proof established is writable by the
same uid the containers run as (`CODEX_STATE.md:224-233`).

The **directory** is bind-mounted, not the document. `AtomicTokenManager` creates its
advisory lock and its atomic replacement as siblings of the token file, and `os.replace`
cannot cross filesystems, so a document-only bind under `read_only: true` cannot work.
That is precisely what stopped the in-container credential proof
(`CODEX_STATE.md:221-224`), and re-introducing it would reproduce that failure exactly.

### 3. Credentials

`SCHWAB_API_KEY` and `SCHWAB_SECRET_KEY` come from `../.env` via `env_file` and are never
named on a command line. `SCHWAB_TOKEN_PATH` is set in the service's `environment:` block,
which overrides any value `../.env` carries — deliberate, because `.env` points the
trading containers at their own in-container path.

## The single-writer problem — read before scheduling

The gateway becomes a **second writer** of the production token document. The existing
writers are the SPX/NDX/XSP containers (`CODEX_STATE.md:320`) and the hourly keepalive
cron. `AtomicTokenManager` takes an exclusive advisory lock, but the existing direct
services do **not** — `CODEX_STATE.md:186-188` records that no live service path acquires
`.tokens.json.lock`. The lock therefore protects gateway writers from each other, not from
the direct services.

Consequences to accept explicitly before starting:

- a gateway token refresh and a direct-path refresh can still interleave;
- the gateway's atomic replace is safe in itself, but it can land on top of a refresh a
  direct service just wrote, and vice versa.

The lowest-risk first window is therefore **outside market hours, with the keepalive cron
disabled**, which is the same posture the credential proof used.

## Recorded preflight — 2026-08-06, read-only

Run under an operator authorization limited to non-mutating commands. Nothing was
created, started, written, or changed. Bounded results:

| Check | Result |
|---|---|
| Docker daemon | reachable, 21 containers running |
| `butterfly_spx_app` / `ndx` / `xsp` | all `running`, images `faa85d748358` / `ca2ca79ca2c6` / `cc58c70ea998` |
| Port 8011 (live service) | free |
| Port 8010 (demo service) | **bound**, by the unrelated `halt_scanner` container |
| Gateway containers | neither `..._foundation` nor `..._live` exists |
| Helios checkout | branch `main` at `de84d91`, **64 commits behind local `main`** |
| `infra/docker-compose.gateway.yml` there | **absent** |
| `secrets/schwab-gateway-keys.json` there | absent, as expected |
| Helios working tree | **not clean** — uncommitted local changes present |
| Token document | regular file, not a symlink, mode `600`, uid/gid `1001` |
| Token directory | mode `755`, uid `1001`, writable by the operator account |
| Operator account | uid `1001`, gid `1001` — the same uid the containers run as |
| `.env` | present; defines `SCHWAB_API_KEY`, `SCHWAB_SECRET_KEY`, `SCHWAB_TOKEN_PATH` (names only — no value was read) |
| Keepalive cron | 2 entries |
| Disk available | 45 GB |

Three of these change the plan:

**1. The gateway code is not on Helios at all.** The checkout is 64 commits behind local
`main`, so neither `infra/docker-compose.gateway.yml` nor any `schwab_gateway` source
exists there, and the branch has never been pushed anywhere. Bringing Option A up is
therefore not "start a container" — it requires moving 64 commits onto the checkout of the
machine running live trading. That includes the entire gateway change set *and* `5055991`,
which changes the live `infra/docker-compose.yml`. This needs its own plan and its own
approval; it is a larger step than this runbook originally assumed.

**2. The Helios working tree is not clean.** Whatever is uncommitted there must be
identified and preserved before any checkout update. Do not update the checkout until this
is resolved.

**3. Port 8010 is taken by `halt_scanner`.** The demo service as configured would fail to
bind. The live service's 8011 is free, so Option A itself is unaffected, but the demo
service needs a different port before it can ever run on this host.

Everything Option A actually depends on checks out: the token document is a private regular
file, its directory is writable by the operator account, and that account shares the uid the
containers use — so the writable-token-directory design is sound on this host.

## Preflight — read-only, no mutation

Re-run in the approved window before starting anything:

1. `docker compose -f infra/docker-compose.gateway.yml --profile gateway-live config`
   — renders and validates without creating anything. It fails loudly if
   `SCHWAB_GATEWAY_TOKEN_DIR` is unset, because both its uses carry `:?`.
2. Confirm TCP `127.0.0.1:8011` is unbound.
3. Confirm `secrets/schwab-gateway-keys.json` exists at mode `0600`.
4. Confirm the token document is a regular non-symlink file at mode `0600` in a writable
   directory.
5. Record SPX/NDX/XSP container and image IDs, so the rollback check has a baseline.

## Start

```
docker compose -f infra/docker-compose.gateway.yml --profile gateway-live up -d
```

The explicit `-f` and the non-default profile are both required; neither gateway profile
is in the default set, so no ordinary `docker compose up` can start either service.

**Startup performs exactly one token read and no Schwab request.** `build_live_app` calls
`manager.load()` before returning the application
(`scripts/run_schwab_gateway.py`, `build_live_app`). If the token is missing, expired, or
corrupt, the process exits and the container does not serve — verified by
`tests/test_gateway_live_runner.py::test_live_app_refuses_to_build_when_the_token_is_unusable`.
No client is constructed at startup, verified by
`test_live_app_builds_no_client_and_makes_no_request`.

That startup load is not bookkeeping. `/ready` and every route gate on
`TokenManagerState.READY` (`schwab_gateway/api.py:244`, `:270`, `:315`), and the manager
only reaches READY inside a transaction. Without priming, no request could be admitted to
produce the transaction that would make it ready, and the gateway would answer 503 forever
while looking healthy at the process level.

## Verify

1. `/health` returns 200 — process liveness only.
2. `/ready` returns 200 with `token_state: "ready"`.
3. One authenticated `GET /v1/quotes?symbols=AAPL` returns a typed quote.
4. `/metrics` shows `schwab_gateway_token_state{state="ready"} 1`.
5. Confirm the token document is still a regular non-symlink file at mode `0600`.
6. Confirm SPX/NDX/XSP are on the container and image IDs recorded in preflight and that
   their filtered error counts are unchanged.

## Rollback

```
docker compose -f infra/docker-compose.gateway.yml --profile gateway-live down
```

The gateway is a separate Compose project (`name: butterfly_gateway_foundation`) with its
own container name and port, and no consumer points at it, so stopping it cannot affect
SPX/NDX/XSP. Re-enable the keepalive cron if it was disabled. There is no configuration to
revert: `SCHWAB_ACCESS_MODE` and `SCHWAB_GATEWAY_SHADOW_READS` both still default to values
that ignore the gateway entirely.

## Known limitations — accept or fix before a real shadow period

**1. Token-level failures recover on a 30-second interval, not instantly.** A token-level
failure moves the manager out of READY, and every route then refuses with
`gateway_not_ready` — including the request that would have produced a recovering
transaction. `TokenReadinessRecovery` runs for the application's lifetime and retries
`load()` every 30 seconds while the manager is not ready, so a transient **lock timeout**
— another writer holding the document too long — clears on its own within one interval
rather than requiring a container restart.

What that means in practice:

- a healthy gateway never touches the token document on this path, because the recovery
  checks state before acting;
- a genuinely missing, expired, or corrupt token stays fail-closed and keeps retrying
  harmlessly until an operator fixes it;
- Schwab-side errors never latch it at all: a failed HTTP call raises
  `SchwabClientOperationError`, which is not a `TokenManagerError`, so the manager stays
  READY throughout.

The remaining exposure is the window itself: up to 30 seconds of `gateway_not_ready` after
a transient lock contention. For a shadow reader that is harmless — the direct path is
unaffected and the comparator swallows gateway failures. Re-evaluate the interval before
anything depends on the gateway for a trading decision.

**2. One client and one HTTP session per request.** Each transaction constructs a client
and closes its session. That is the proven adapter lifecycle, but it means per-request
connection setup rather than a pooled session.

**3. The token lock serializes all gateway reads.** Admission capacities
(`protected_capacity`, `background_capacity`) bound queue depth, not parallelism. Two
concurrent consumers do not get concurrent Schwab reads.

**4. No image pin is recorded here.** The service builds from `../Dockerfile` rather than a
recorded image ID. Record the built image ID at first start if you want the restoration
story the trading services have.

**5. `/v1/history` does not exist**, so `get_daily_bars` (`data/collector.py:117`) has no
gateway surface. A consumer needing daily bars still reads direct.
