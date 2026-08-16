# Schwab gateway deployment options

> **Historical decision brief:** The selected service was extracted and deployed from
> [`hollowc2/SchwabGateway`](https://github.com/hollowc2/SchwabGateway). Embedded runner, Compose,
> and credential-proof references below no longer exist in Butterfly Guy.

Status: decision brief. Nothing here is a recommendation to act, and nothing here has been
run. Its purpose is to make "where does the gateway run" decidable by an operator.

Phase 3 of `docs/architecture/schwab-gateway-migration.md` (lines 119–135) names four
dependencies, restated in `CODEX_STATE.md:300-301`:

1. a production-capable single token manager;
2. **a safe gateway deployment host**;
3. capability probe approval;
4. a read-only consumer key.

Dependency 1 is met in substance — `AtomicTokenManager` plus `LockedSchwabClientAdapter`
retrieved a real Schwab quote through the real token document during the
`2026-08-06T21:10:00Z`–`23:10:00Z` window, returning `credential_proof_passed`
(`CODEX_STATE.md:253-260`). This brief is about dependency 2 only. It states plainly which
of the remaining dependencies each host option moves and which it leaves exactly where it
is.

## The prerequisite that is common to every option

**No host option is sufficient on its own, because no real-backed gateway runner exists.**

`src/butterfly_guy/scripts/run_schwab_gateway.py:47-48` refuses to start without `--demo`:

```
    if not args.demo:
        parser.error("the foundation runner supports only --demo")
```

and `--demo` serves `DemoQuoteUpstream` (`run_schwab_gateway.py:21-35`), which returns a
constant `mark=100.0` flagged `demo_data_not_for_trading`. Nothing in the process
constructs `AtomicTokenManager`, `LockedSchwabClientAdapter`, `DirectSchwabQuoteUpstream`,
`DirectSchwabSpotUpstream`, or `DirectSchwabChainMetadataUpstream`.

Second missing input: `infra/docker-compose.gateway.yml:19` mounts
`../secrets/schwab-gateway-keys.json`, and no `secrets/` directory exists in this
repository. The internal-key file that `InternalKeyAuthenticator.from_file`
(`run_schwab_gateway.py:52`) requires has never been created. That file is also exactly
what Phase 3 dependency 4 — a read-only consumer key — consists of.

So the honest cost of "deploy the gateway" on any host is:

- a non-demo mode for the runner, which wires the proven manager/adapter to the three
  upstreams and is a reviewed source change subject to its own approval;
- an internal-keys file provisioned outside the repository;
- then the host-specific work below.

Choosing a host does not shorten the first two. It only changes the third, and it changes
the blast radius of getting the first two wrong.

## Option A — Helios, containerized

**What it requires.** Bring up `infra/docker-compose.gateway.yml` with an explicit `-f`
and the non-default `gateway-foundation` profile (`infra/docker-compose.gateway.yml:5`)
on the host that runs SPX/NDX/XSP, plus a `secrets/schwab-gateway-keys.json` readable by
uid/gid 1001 (`infra/docker-compose.gateway.yml:11`).

**What it risks.** Helios runs live trading. The recorded history of touching Docker there
is the single most expensive thread in this project: `CODEX_STATE.md:8-301` records
roughly a dozen supervised windows, of which the ones that mutated container state
produced a destroyed-and-unprovable SPX baseline (`CODEX_STATE.md:495-504`), a fail-closed
pause of all three services (`CODEX_STATE.md:145-149`), and a multi-window detour to
re-establish an accepted runtime baseline at all (`CODEX_STATE.md:44-74`). The gateway
Compose project is separately named (`name: butterfly_gateway_foundation`,
`infra/docker-compose.gateway.yml:1`) and binds only to `127.0.0.1:8010`
(`infra/docker-compose.gateway.yml:40`), so the *intended* isolation is real; the risk is
that operating Docker on Helios at all has repeatedly been where surprises happen.

**Evidence for.** The container hardening is already written and test-pinned:
`read_only: true`, `cap_drop: ALL`, `no-new-privileges`, non-root user, `tmpfs /tmp`,
read-only secret mount, and a `/ready` healthcheck — asserted by
`tests/test_gateway_compose.py:7-20`. Image pinning and Compose-level isolation come free.

**Evidence against.** `CODEX_STATE.md:221-224` records that the trading containers set
`read_only: true` with `/app/tokens.json` writable only as its own bind mount, which broke
the in-container credential proof outright — `AtomicTokenManager` could not create its
lock sibling, and `os.replace` cannot cross filesystems. A containerized gateway that owns
the token document inherits exactly that problem and needs a writable token *directory*
mount, which is a new bind on the live host.

**Phase 3 dependencies moved.** Dependency 2 only. 1 is already met, 3 and 4 untouched.

**Smallest safe first step.** In an approved window, a read-only `docker compose -f
infra/docker-compose.gateway.yml --profile gateway-foundation config` — which renders and
validates without creating anything — and a bounded check that TCP `127.0.0.1:8010` is
unbound. No `up`, no build.

## Option B — zeus, containerized

**What it requires.** Starting the Docker daemon on zeus, then the same Compose invocation
as Option A.

**What it risks.** `CODEX_STATE.md:342-343` records the standing decision:

> Do not start the inactive local Docker daemon because unrelated `unless-stopped`
> containers could restart; use the equivalent localhost demo runner for this proof.

Starting `dockerd` starts every `unless-stopped` container the host has ever been given,
which is unenumerated. That is the whole objection, and it has not been retired.

**Evidence for.** zeus does not run live trading, so a gateway fault there cannot reach
SPX/NDX/XSP. If the daemon-start objection were resolved, this is strictly safer than
Option A.

**Evidence against.** No inventory of zeus's `unless-stopped` containers exists anywhere in
this repository, so the objection cannot currently be evaluated — only respected.

**Phase 3 dependencies moved.** Dependency 2 only, and only if the daemon question is
settled first.

**Smallest safe first step.** A bounded read-only enumeration of what would start:
`docker` need not run for this — reading the container config directory listing under the
daemon's state root and counting entries by restart policy, emitting counts only. That
converts a blanket refusal into a decidable list. It is a check to request in an approved
window, not something to run here.

## Option C — a separate/new host

**What it requires.** Everything in "the prerequisite common to every option", plus the
three items still open at `CODEX_STATE.md:536`: a final production gateway host, a
private-network route, and an OAuth callback domain. Concretely: a provisioned machine, a
container runtime or Python 3.12 environment, a private route from Helios to the gateway's
`127.0.0.1`-equivalent (the gateway refuses to bind a public address —
`schwab_gateway/config.py:29-38` rejects any host that is not loopback, private, or
unspecified), a copy of the Schwab credential environment, and a token document that is
*the same document* the trading services use or a deliberately separate one.

**What it risks.** The token is the sharp edge. Today one `tokens.json` is shared by the
trading containers (`CODEX_STATE.md:320`). Moving the gateway to a different host either
splits the token across hosts — two independent refresh paths against a seven-day refresh
token, which is precisely the "concurrent token refresh/file overwrite" critical risk in
the migration doc's register — or requires a network-mounted token document, which is
worse. The OAuth callback domain is a second unbounded item: it is a Schwab developer
portal change, and `CODEX_STATE.md:276-280` records that the portal offers no in-place
regeneration, so portal changes are not cheap to undo.

**Evidence for.** None recorded. No such host is named anywhere in the repository.

**Evidence against.** The three items at `CODEX_STATE.md:536` have been open since the
Open Questions section was written and none has been closed.

**Phase 3 dependencies moved.** Dependency 2, at the cost of reopening the token-ownership
question that dependency 1 just closed.

**Smallest safe first step.** Not a technical check — an operator statement of whether a
second host is even available, and whether a second Schwab app (and therefore a second
callback domain) is acceptable. Without that answer the option cannot be costed.

## Option D — Helios, as a `systemd --user` service, not containerized

**What it requires.** A user unit that runs the gateway from a checkout on Helios under
the same account the containers already run as, with `SCHWAB_GATEWAY_*` settings supplied
by the unit's environment and the internal-keys file at a path that account can read.

**What it risks — and why the risk is smaller than it looks.** This is the option with the
most direct host-proven evidence behind it, and the evidence was produced incidentally by
the credential proof:

- `CODEX_STATE.md:112-116`: an authorized bounded capability probe confirmed a `--user`
  transient unit *arms, reports active, cancels, and leaves no residual unit*, and the
  account has `Linger=yes` with a running user manager.
- `src/butterfly_guy/scripts/credential_proof_fingerprint.py:64-65` is the committed
  result: `_SYSTEMD_RUN_COMMAND = ("systemd-run", "--user")` and
  `_SYSTEMCTL_COMMAND = ("systemctl", "--user")`, with all `sudo` use removed.
- `CODEX_STATE.md:119-122`: that path then ran successfully on Helios under
  `cc614567b035f8a62cd9355ed3302eb11db44012`, arming and cancelling the watchdog for real.

So the user-manager mechanism on Helios is not a hypothesis. It has armed, reported,
cancelled, and left nothing behind, without privilege escalation, in a real window.

It also sidesteps the Docker daemon entirely: no `docker` command, no Compose project, no
container recreation, and therefore none of the failure modes that cost this project a
dozen windows. And it sidesteps the read-only-filesystem defect at `CODEX_STATE.md:221-224`
outright — the credential proof already had to relocate the probe to the host for exactly
that reason (`CODEX_STATE.md:224-233`), where `/opt/butterflyguy` is writable by the same
uid the containers use, and it worked.

**What it costs.** This must be stated honestly, because it is a genuine downgrade:

- **No image pinning.** A container runs a recorded image ID that restoration can verify;
  a user unit runs whatever is in the checkout and whatever `.venv` resolves at the time.
  The entire baseline-evidence apparatus in `CODEX_STATE.md` is built on image and Compose
  hashes and does not apply.
- **No Compose-level isolation.** The container gives `read_only: true`, `cap_drop: ALL`,
  `no-new-privileges`, a non-root uid, and a read-only secret mount for free
  (`infra/docker-compose.gateway.yml:11-26`, pinned by `tests/test_gateway_compose.py:7-20`).
  A user unit gets none of that unless the unit file restates it via systemd hardening
  directives, and none of that has been written or tested.
- **A different restoration story.** Rollback for a container is "stop the project, the
  recorded image is untouched". Rollback for a user unit is `systemctl --user stop` plus
  whatever the checkout was — there is no recorded artifact to restore *to*. Every
  restoration check this project has built verifies containers.
- **Shared blast radius on the same host.** A user unit runs under the same account as the
  trading services' Docker client and can reach the same files, including the token
  document. The container at least has to be handed that access explicitly.

**Phase 3 dependencies moved.** Dependency 2, and it is the only option that moves it using
evidence already recorded rather than evidence still to be gathered. 3 and 4 untouched.

**Smallest safe first step.** A bounded read-only check that a `--user` unit can bind a
loopback port on Helios: `systemd-run --user --wait` a command that opens and immediately
closes `127.0.0.1:8010`, reporting only success/failure and residual-unit absence. This is
the same shape as the capability probe already run at `CODEX_STATE.md:114-116`, and it
answers the one thing that probe did not: whether a `--user` unit can hold a socket, not
just a timer.

## Reading

| Option | Moves dep. 2 | Evidence already recorded | New unknowns introduced |
|---|---|---|---|
| A — Helios, containerized | yes | hardening written and test-pinned | writable token dir on live host; Docker operations on Helios |
| B — zeus, containerized | conditionally | none | unenumerated `unless-stopped` set |
| C — separate host | yes | none | host, private route, OAuth callback domain, token ownership |
| D — Helios, `systemd --user` | yes | `--user` arm/cancel/no-residual, `Linger=yes`, host-writable dir | no image pin, no compose isolation, unwritten hardening |

D is the cheapest to *prove safe*, because its host-level mechanism is the only one already
demonstrated on the target machine and it requires no Docker action on a live-trading host.
It is not the cheapest to *operate safely* — A is, if the Docker risk is accepted, because
the isolation A gives is already written down and tested while D's would have to be
authored from scratch. The two are not in conflict: D is a reasonable way to run a shadow
gateway that reads and is never trusted, and A is the right shape for anything that a
trading decision eventually depends on.

None of this is worth acting on before the runner has a non-demo mode. That is a source
change, it is reviewable offline, and it is the actual next unit of work.

## The one bounded read-only check to ask for next

`systemd-run --user --wait` on Helios, running a command that binds and closes
`127.0.0.1:8010`, emitting only a boolean for bind success and a boolean for residual-unit
absence. Nothing else. It costs one short window, touches no container, reads no
credential, and it is the single fact that separates Option D from being fully evidenced.

## Explicitly not established here

- No host is recommended for production. Option D is identified as cheapest to prove, which
  is not the same claim.
- No claim is made that a gateway on any host is currently reachable by any service.
  `SCHWAB_GATEWAY_SHADOW_READS` defaults to false (`gateway_client/config.py:26-29`) and no
  service constructs `ShadowComparingMarketDataProvider`.
- No credential, token, secret value, or account identifier appears in this document, and
  none is required to act on any first step above.
