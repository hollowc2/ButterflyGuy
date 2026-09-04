# SchwabGateway option-chain latency investigation (2026-09-04)

Follow-up to the 2026-09-04 soak's 3 `cache_semantic_mismatch` flags (NDX @14:00Z,
XSP @14:30Z, SPX @17:00Z), ruled false-alarms — no consumer ever saw bad data.
This traces *why* `chain_*_first` fetches take 4.2-6.2s against a 4s cache TTL.
Source reviewed: frozen prod build `/opt/schwab-gateway-releases/efee41f/src/schwab_gateway/`
on Helios. No production config was changed; container was not restarted.

## Request path (cache miss)

One bulk upstream call per `(symbol, expiration)` — no per-strike/per-contract
looping:

- `api.py:option_chain` → `DirectSchwabOptionChainUpstream.get_option_chain`
  (`upstream.py:1146`)
- On miss: `_fetch_option_chain` → `LockedSchwabMarketDataProvider.get_option_chain`
  (`live_provider.py:268`) → **one** `client.get_option_chain(symbol, from_date=exp,
  to_date=exp)` call, then `normalize_schwab_option_chain` (extracts fields
  Schwab already computed, e.g. `theoreticalOptionValue` — no local greeks
  calc), then serialized to bytes for the cache.
- No retries by design (`live_provider.py` docstring: "retrying inside a held
  token lock multiplies the time every other caller waits").

**Q1 answer: single bulk call, sequential-by-construction (there's only one call).**

## Where the time actually goes: scheduler queueing, not the Schwab call itself

Two serialization layers stack on every request, confirmed in `scheduler.py`
and `live_provider.py`:

1. **A brand-new Schwab client per call.** `token_adapter.py:70` constructs a
   fresh `client_from_access_functions` client (and a fresh `requests.Session`,
   closed after — `live_provider.py:_closing_session`) inside every locked
   transaction. No connection/session reuse across requests — TCP+TLS setup is
   paid every single time, for every operation type (spot, quotes, chain,
   history, movers).
2. **One shared, bounded execution scheduler for *all* market-data operation
   types.** `scheduler.py`'s own module docstring: "Bounded strict-priority
   scheduling for the gateway's one Schwab execution slot." Spot, chain,
   history, and session requests all queue and dispatch through the same
   priority-class-bounded pool (empirically ~2-way concurrency per priority
   class, not fully parallel — see below).

This means the `latency_ms` the soak records is **end-to-end**, including
scheduler queue wait behind whatever else is in flight — not pure upstream
fetch time. Evidence from checkpoint `002_20260904T140000Z`
(`raw/002_20260904T140000Z/checkpoint.json`): 16 requests with individually
logged latencies summing to ~28.0s complete in a 14.9s wall-clock checkpoint
(`started_utc` → `finished_utc`) — consistent with ~2 concurrent execution
slots, not 1 and not 16.

The smoking gun: **cache *hits* are slow too.** `chain_ndx_cached` and
`chain_xsp_cached` in that same checkpoint took 1484ms and 1551ms — a cache
hit is just an `OrderedDict` lookup plus a full `OptionChainV1.model_validate_json`
re-parse of the cached payload (`upstream.py:1153`, see below), which should
be low tens of ms even for the largest chain. The only explanation for
1.5s on a cache hit is queueing behind other slow requests dispatched moments
earlier in the same checkpoint burst.

`SCHWAB_GATEWAY_UPSTREAM_TIMEOUT_SECONDS=3` (confirmed on the live container)
looks like it should have 504'd anything over 3s, but it doesn't contradict
the data: `scheduler.py:_run_job` starts the 3s execution budget at
**dispatch**, not at HTTP-request-received time. A request that waits ~1-3s
in queue and then executes in ~2-3s can show ~4-6s end-to-end while staying
inside both its execution budget (≤3s from dispatch) and its queue budget
(`background_queue_timeout_seconds=5` / `protected=7`) — so it succeeds with
200, consistent with what the soak observed.

**Q4 (avoidable overhead) answer: yes, two things stand out:**
- Per-request client/session construction (no keep-alive reuse) — real but
  probably tens-to-~100ms per call, not the multi-second driver.
- Cache-hit path fully re-validates the cached JSON through Pydantic on every
  hit (`upstream.py:1153`, `OptionChainV1.model_validate_json(cached.payload)`)
  instead of caching the already-parsed model or the finished HTTP body —
  wasted work on the one path that's supposed to be cheap.
- Neither of these explains the 4-6s `_first` latencies; the scheduler queue
  contention does.

## Chain size correlation

Payload sizes from checkpoint 002: SPX 376,982 bytes / 4206ms, NDX 495,236
bytes / 5542ms, XSP 371,100 bytes / 5448ms (NDX chain has noticeably more
contracts per the `cache_consistency` diff paths — 800+ `contracts[]`
entries vs fewer for SPX/XSP). NDX being both the largest payload and the
slowest first-fetch in 2 of the 3 flagged checkpoints is consistent with
size adding real (de)serialization cost. But SPX and XSP are near-identical
in size (376,982 vs 371,100 bytes) and their latency spread across
checkpoints was wide (513ms-5548ms) — size alone doesn't explain that
variance; scheduler queue position at the moment of the call dominates.

**Q3 answer: size is a secondary contributor; queueing jitter dominates.**

## Cache TTL is hard-capped at 4s in code, not just config

`config.py:85` (`option_chain_cache_ttl_must_be_bounded`) and
`upstream.py:42` (`MAX_OPTION_CHAIN_CACHE_TTL_SECONDS = 4.0`) both enforce
TTL ≤ 4s. **Raising `SCHWAB_GATEWAY_OPTION_CHAIN_CACHE_TTL_SECONDS` past 4
will fail Pydantic validation at startup** — this isn't a config-only fix,
it needs a code change to the ceiling constant in both places (they must
stay in sync) plus a new release/tag.

## Recommendation

1. **Short term (config, no code change needed):** none available — the 4s
   ceiling is baked into `upstream.py` and `config.py`, so there is no env
   var to bump today. This should be called out explicitly since the
   original soak follow-up assumed a simple TTL bump.
2. **Real fix — raise the TTL ceiling.** Observed first-fetch latency
   (4.2-6.2s across 3 checkpoints, small sample) suggests a p99 comfortably
   above 6s once queue contention is included. Recommend widening
   `MAX_OPTION_CHAIN_CACHE_TTL_SECONDS` to something like 8-10s (needs a
   larger sample than 3 points — pull `schwab_gateway_scheduler_upstream_execution_seconds`
   and `schwab_gateway_scheduler_queue_wait_seconds` histograms for
   `operation="option_chain"` over a full session once the metrics have
   accumulated; the current live container was restarted today at 21:44Z
   and has no historical data yet) — then set
   `SCHWAB_GATEWAY_OPTION_CHAIN_CACHE_TTL_SECONDS` near that new ceiling.
3. **Secondary, real but smaller wins, independent of the TTL question:**
   - Stop re-validating cached payloads through Pydantic on every cache hit;
     cache the parsed model (or a pre-serialized response body) instead of
     re-running `model_validate_json` on every hit.
   - Consider reusing a `requests.Session`/client across calls where the
     token-lock model allows it, to avoid paying TCP+TLS setup per request.
   These won't fix the 4-6s first-fetch numbers (queueing is the dominant
   factor there) but they're free wins on cache-hit latency and general
   per-request overhead.
4. Treat the "one shared execution slot pool across all operation types"
   design as the actual finding here: option-chain latency is coupled to
   how busy spot/quotes/history/session traffic is at the same moment, not
   just to Schwab's own API latency for that one endpoint. Any latency
   budget or TTL decision should be based on the scheduler's queue-wait
   histogram, not just the upstream execution histogram.

No production config was changed and the gateway was not restarted as part
of this investigation.
