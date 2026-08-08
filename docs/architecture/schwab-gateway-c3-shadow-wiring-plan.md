# C3 — wiring shadow reads into `run_live.py`

Status: **plan only, nothing implemented.** Written during Window C at the operator's request.
C3 remains its own decision and probably its own window.

C3 would make gateway code reachable from a live trading entry point for the first time. Everything
before it (the gateway image, the token manager, the comparator) is inert with respect to trading:
nothing in `run_live.py` constructs a gateway client today.

## The wiring point

`src/butterfly_guy/scripts/run_live.py:743`:

```python
market_data = DirectSchwabMarketDataProvider(schwab)
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

## The blocker C3 shares with monitoring: the gateway is unreachable

`infra/docker-compose.gateway.yml` has **no `networks:` section**. The gateway runs on its own
isolated Compose project network and publishes only to `127.0.0.1:8011` on the host. The trading
containers are on `monitoring_net`. **They cannot reach the gateway**, exactly as Prometheus cannot.

This is the same decision as the Window C monitoring question and should be settled once, for both:

- **Join the gateway to `monitoring_net`** — then Prometheus scrapes it *and* the trading containers
  reach it at `butterfly_schwab_gateway_live:8011`. One change solves both. Cost: reachability
  widens from host loopback to every container on `monitoring_net` (turtlequant, pdfbillr,
  halt_scanner, grafana, node_exporter). `/v1/` still requires a key (`auth.py:130`); what opens up
  is unauthenticated `/health`, `/ready`, `/metrics` plus the auth surface itself.
- **Host-boundary access** — `extra_hosts: host.docker.internal:host-gateway` on the consumers, each
  reaching `http://host.docker.internal:8011`. Preserves the gateway's isolation. Cost: applied to
  Prometheus (in `/opt/monitoring/docker-compose.yml`, outside this repo) *and* to all three trading
  services.

**This materially affects the Window C monitoring choice.** The isolation-preserving option is
cheaper when only Prometheus needs access; joining `monitoring_net` gets relatively better once
trading consumers need it too. Worth deciding with C3 in view rather than separately.

## Prerequisites, in order

1. The gateway is deployed and durably running (Window C left it **down** pending the monitoring
   decision). Shadow reads against a gateway that is not up produce only `gateway_unavailable`
   discrepancies — noise, not signal.
2. Network reachability resolved per above.
3. A `butterfly-guy` consumer key issued and distributed into the three trading services as
   `SCHWAB_GATEWAY_API_KEY`. Note `issue_gateway_keys.py` has no append mode (`:93`, `:50`), so if
   `equity-scanner` is ever added the `butterfly-guy` key rotates and must be redistributed.
4. `SCHWAB_GATEWAY_URL` set per the reachability decision.

`GatewayClientSettings` (`gateway_client/config.py`) already refuses `shadow_reads` without both a
URL and a key (`:40`), and refuses `shadow_reads` together with `access_mode="gateway"` (`:48`) since
comparing the gateway against itself is meaningless. Those guards are in place and need no work.

## Proposed steps

1. **Construct the client and wrapper in `run_live.py`.** Load `GatewayClientSettings`; when
   `shadow_reads` is off (the default), wrap nothing and leave `DirectSchwabMarketDataProvider` in
   place unchanged — the no-flag path must be byte-for-byte the behaviour it is today.
   *Verify:* a test asserting that with no gateway env set, `run_live` builds the direct provider and
   constructs no gateway client at all.
2. **Wrap when enabled.** `ShadowComparingMarketDataProvider(direct, gateway, shadow_reads=True)`.
   *Verify:* a test that the wrapper returns the direct value even when the gateway raises, for each
   of the four collector call sites.
3. **Expose the discrepancy counts.** `ShadowDiscrepancyRecorder` is in-memory and `_record`
   (`shadow.py:172`) only logs `gateway_shadow_discrepancy`. There are **no Prometheus metrics in
   `gateway_client/` at all** (verified: no `Counter`/`Gauge` anywhere in the package). Without a
   metric, a shadow run's results can only be read out of logs. Adding one counter keyed by
   operation and code is the smallest thing that makes C3 answerable.
   *Verify:* metric increments on a forced mismatch.
4. **Decide shutdown behaviour** — whether `run_live` awaits `wait_for_shadow_reads` on graceful
   exit.
5. **Enable on one service first**, XSP rather than SPX or NDX, for one session, market open.
   *Verify:* discrepancy counts by code; `gateway_unavailable` should be zero if the deployment is
   sound, and a non-zero `gateway_stale_value` or `gateway_value_mismatch` count is the actual
   finding C3 exists to produce.

## What C3 does not do

It does not route any trading read through the gateway — `access_mode` stays `direct`, and the
direct provider remains the only source of every returned value on every path (`shadow.py:116`). It
does not touch order or account operations. It does not enable `/v1/history`. It is an observation
exercise whose output is a discrepancy count, and its purpose is to decide whether a future cutover
is safe — not to perform one.
