# C3 — wiring shadow reads into `run_live.py`

Status: **implemented locally, default-off, not deployed.** The code and Compose wiring are
reviewable without changing any running service. Enabling the XSP canary remains a separate,
explicit deployment decision.

C3 makes gateway code reachable from a live trading entry point for the first time. Everything
before it (the gateway image, the token manager, the comparator) is inert with respect to trading:
the default path in `run_live.py` constructs no gateway client.

## The wiring point

`src/butterfly_guy/scripts/run_live.py` now calls `_build_collector_market_data` after initializing
the existing Schwab client. With the default settings it returns the same
`DirectSchwabMarketDataProvider` and constructs no gateway HTTP client. With
`SCHWAB_GATEWAY_SHADOW_READS=true`, it returns:

```python
ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)
```

Every collector read goes through this object. `ShadowComparingMarketDataProvider`
(`gateway_client/shadow.py:113`) is a drop-in wrapper around it: same protocol
(`CollectorMarketDataProvider`, `data/providers.py:54`), direct read always returned, gateway
observed and never trusted.

The collector reaches it at four call sites — `data/collector.py:117` (`get_daily_bars`), `:151` and
`:157` (`get_spot_price` for `$SPX` and `$VIX`), and `:164` (`get_option_chain`).

## Two corrections to the received design points

The Window C brief and `CODEX_STATE.md` (Next Exact Action) both carry design points that no longer
match the code. Re-derived from `shadow.py` directly:

### 1. The latency claim is stale — the comparator does *not* add gateway latency

The brief states "the comparator awaits the gateway read after the direct read returns, so it adds
gateway latency to every collector cycle." **This is not what the code does.** `get_spot_price`
(`shadow.py:188`) and `get_option_chain` (`shadow.py:224`) each create the direct task, spawn the
comparison via `_spawn_background` (`shadow.py:142`), and `return await direct_task`. The docstring
at `shadow.py:143` is explicit: "Run a shadow comparison off the caller's critical path."

The collector cycle is therefore **not** slowed by the gateway read. This was presumably true of an
earlier revision and was fixed; the prose was never updated. Both the brief and `CODEX_STATE.md`
should be corrected rather than carried forward.

The real costs are different, and smaller:

- Each shadowed call issues a second concurrent HTTP request, so the collector's outbound work
  roughly doubles for spot and chain reads (three of the four call sites, since `$SPX` and `$VIX`
  spot are separate calls).
- Comparison tasks outlive the call that spawned them. They are tracked in a `_background_tasks` set
  and self-discard on completion (`shadow.py:150-160`), and the client's default timeout is 5.0s
  (`gateway_client/client.py:54`) against a 60s collector cycle, so unbounded accumulation is not a
  realistic failure — but the bound depends on that timeout staying well under the cycle.
- `wait_for_shadow_reads` (`shadow.py:162`) exists for tests and graceful shutdown only. Whether
  `run_live.py` should call it on shutdown is an open question; not calling it means in-flight
  comparisons are dropped at exit, which is harmless but loses the last cycle's observations.

### 2. The no-shadow-surface set is larger than "just history"

The brief says `GET /v1/history` is deliberately absent so `get_daily_bars` has no shadow surface.
Correct, but incomplete: **three** of the six provider methods pass straight through to direct with
no comparison at all —

| Method | `shadow.py` | Shadowed? |
|---|---|---|
| `get_spot_price` | `:188` | yes |
| `get_option_chain` | `:224` | yes (metadata only, not full chain) |
| `get_intraday_bars` | `:281` | **no — pass-through** |
| `get_intraday_bars_for_day` | `:286` | **no — pass-through** |
| `get_daily_bars` | `:299` | **no — pass-through** |

So C3 buys observation of spot and chain metadata only. `get_daily_bars` feeds the regime
classifier, which is one of the strategy's inputs, and it would remain entirely unobserved. That is
a deliberate consequence of `/v1/history` being disabled, not an oversight — but it should be stated
as "shadow covers two of four collector call sites", not "history is missing".

Note also that the chain comparison is on *extracted metadata* (`underlying_price` plus count
fields, `shadow.py:262-272`), not a strike-by-strike diff. A gateway that returned a plausible chain
with wrong individual strikes would compare clean.

## Reachability and observability are resolved

The live gateway and trading services share the external `monitoring_net`. XSP reaches the gateway
by container DNS at `http://butterfly_schwab_gateway_live:8011`; the loopback publish remains for
host-only diagnostics. Prometheus counters for comparisons and discrepancies already exist, so a
canary can be evaluated without scraping logs for every result.

Only `app_xsp` receives gateway client settings. Compose maps
`SCHWAB_GATEWAY_SHADOW_READS_XSP` to the process setting
`SCHWAB_GATEWAY_SHADOW_READS`, defaulting to `false`, and pins `SCHWAB_ACCESS_MODE=direct`.
Putting the URL and scoped consumer key in `infra/.env` therefore cannot enable SPX or NDX.

As a separate least-privilege correction, the live gateway no longer imports the whole application
`../.env`. Compose passes only the required `SCHWAB_API_KEY` and `SCHWAB_SECRET_KEY` credentials,
with required-value guards. Account, database, and notification secrets are not admitted to the
gateway container.

## Prerequisites, in order

1. Review and deploy the local code/Compose changes; deployment is not part of this implementation.
2. Rotate/reissue the scoped `butterfly-guy` consumer key. The live keys document contains its
   digest, but the corresponding plaintext key was intentionally destroyed and cannot be
   recovered. Atomically install the newly rendered digest document, recreate the gateway so it
   reloads the document, and complete an authenticated read proof before retaining the new
   plaintext key only in operator-owned `infra/.env` as `SCHWAB_GATEWAY_API_KEY`. Never commit or
   print it. Append-safe issuance protects future second consumers; it cannot recover this key.
3. Keep `SCHWAB_API_KEY` and `SCHWAB_SECRET_KEY` in the root application `.env`; do not duplicate
   them into `infra/.env`. Render and deploy the gateway Compose file with both inputs, in this
   order, so the root file supplies app credentials and `infra/.env` supplies gateway deployment
   values:

   ```bash
   docker compose --env-file .env --env-file infra/.env \
     -f infra/docker-compose.gateway.yml --profile gateway-live config >/dev/null
   ```

   A successful exit proves interpolation without printing or capturing credential values.
4. Leave `SCHWAB_GATEWAY_SHADOW_READS_XSP=false` through deployment validation. Turn it on only for
   the approved XSP market-session canary.

`GatewayClientSettings` (`gateway_client/config.py`) already refuses `shadow_reads` without both a
URL and a key (`:40`), and refuses `shadow_reads` together with `access_mode="gateway"` (`:48`) since
comparing the gateway against itself is meaningless. Those guards are in place and need no work.

## Implemented steps and remaining operator gate

1. **Construct the client and wrapper in `run_live.py` — implemented.** Load `GatewayClientSettings`; when
   `shadow_reads` is off (the default), wrap nothing and leave `DirectSchwabMarketDataProvider` in
   place unchanged — the no-flag path must be byte-for-byte the behaviour it is today.
   *Verify:* a test asserting that with no gateway env set, `run_live` builds the direct provider and
   constructs no gateway client at all.
2. **Wrap when enabled — implemented.** `ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)`.
   *Verify:* a test that the wrapper returns the direct value even when the gateway raises, for each
   of the four collector call sites.
3. **Expose discrepancy counts — implemented.** Prometheus counters cover comparison results and
   discrepancies by operation/code/classification.
4. **Graceful shutdown — implemented.** `run_live` awaits tracked comparisons, then closes the
   gateway HTTP client before closing the direct Schwab client and database pool.
5. **Enable on one service first — operator gate.** XSP is the only wired canary. Enable it for one
   approved session while the market is open.
   *Verify:* discrepancy counts by code; `gateway_unavailable` should be zero if the deployment is
   sound, and a non-zero `gateway_stale_value` or `gateway_value_mismatch` count is the actual
   finding C3 exists to produce.

## What C3 does not do

It does not route any trading read through the gateway — `access_mode` stays `direct`, and the
direct provider remains the only source of every returned value on every path (`shadow.py:116`). It
does not touch order or account operations. It does not enable `/v1/history`. It is an observation
exercise whose output is a discrepancy count, and its purpose is to decide whether a future cutover
is safe — not to perform one.
