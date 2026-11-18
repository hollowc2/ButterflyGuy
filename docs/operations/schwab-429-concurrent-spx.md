# Schwab 429s with paper and live SPX side by side

Investigation of 2026-11-18. Read-only: nothing was restarted, recreated or reconfigured, and no token
was touched. Times are Pacific unless marked UTC. The data runs to about 10:00 PT on 11-18; the rehearsal
kept running until its 13:15 close-out.

Sources:
- `docker logs` of `butterfly_spx_app` (started 11-16 16:36 PT) and `butterfly_spx_live_app`
  (rehearsal, started 11-18 06:25 PT);
- `schwab_gateway_live` logs since 11-03;
- `chain_snapshot_meta`, `monitoring_leg_quotes` and `post_exit_leg_quotes` in `butterfly_guy` and
  `butterfly_guy_spx_live_rehearsal`;
- Prometheus, whose retention starts 11-03.

The analysis scripts were throwaway session scratch files and were not committed.

## 1. Summary

- **The 429s are a Schwab option-chain throttle that depends on the time of day.** Our request volume is
  not what triggers them.
  - All 52 recorded 429s (gateway since 11-03, plus both SPX bots) were on option-chain calls, for all three
    symbols. None were on quotes, spot or history, although those make up about a quarter of the app's
    traffic.
  - On 11-18, a chain request's chance of a 429 depended almost entirely on the second of the minute:

    | When the chain request starts | Chain requests | 429s | Rate |
    |---|---|---|---|
    | First 15 s of a minute divisible by 5 (:00, :05, …) | 592 | 11 | **1.86 %** |
    | First 15 s of any other minute | 2,440 | 8 | 0.33 % |
    | Second 15 or later | 7,826 | 1 | 0.013 % |

  - Our own load is the same at 5-minute marks as in other minutes: 20.6 vs 20.9 requests in seconds 0–15.
    The app-wide peak was 74 requests in any 60 s. Schwab Trader API Support's own written limit is
    "120 requests per minute for non-order endpoints … per account, each restful endpoint request counts
    as 1" (§2.5).
  - The same pattern holds on the gateway over 12 sessions (§2.4a): 0.93 % hot-zone vs 0.003 % late.
    That includes 11-03 to 11-09, when nothing called Schwab directly.
  - It does not rise with our concurrent load. Adding the direct SPX bots on 11-16/17 left the gateway's
    rate unchanged.
  - The likely cause is load-based throttling of Schwab's chain service at round clock times. That is an
    inference: Schwab documents only the 120/min quota, and we are under it.
- **The "both collectors fetch at :00" hypothesis is only a small part of it.** Only 3 of the 16 SPX 429s
  had the other bot's chain request in flight at the same moment. Two of those were the two collectors
  both fetching at HH:MM:00.0. The rest were monitor or post-exit polls that happened to land in the
  hot window.
- **11-18 was elevated compared with every earlier day on record, but so was the gateway.**
  - App-wide 429s per session have been 0–5 since 11-03 (mean about 2.9).
  - On 11-18 there were 20 by 10:00 PT: paper 6, rehearsal 8, gateway 6.
  - The gateway's own load *fell* that day, yet four of its 429s came between 06:35 and 06:50. Total app
    load then was about 12–15 requests/min.
  - The gateway's hot-zone rate was 2.76 % (4 of 145) against its 12-day mean of 0.93 %. That points to a
    Schwab-side day effect. Within the hot zone, the 429 rate does not rise with the number of app
    requests in the prior 3 s (§2.4a), so there is no evidence the rehearsal's load caused it.
- **Paper SPX → gateway (Phase B): no-go.**
  - It does not remove the cause, since the gateway's upstream chain calls hit the same throttle.
  - It turns a 429 that today recovers in 1 s into a read that fails at the client. The failed read also
    starts a cooldown of at least 1 s that blocks NDX and XSP reads too.
  - It brings back the 8 s chain cache that made 76 % of paper's monitor polls stale repeats in Oct–Nov.
    What that does to exits is unknown: the study's 5 s and 10 s arms read −$2.9 and −$7.7 per trade,
    with CIs spanning 0, and cadence can't be measured until post-exit trades accumulate.
  - It breaks the monitor-cadence study's qualifying set, which is "paper SPX ≥ 11-17, direct, as-live".
  - Paper SPX went direct on 11-16 for exactly these reasons.
- **The 7455 vs 7450 fly split at 07:00 was not caused by a 429 or by chain timing at Schwab.**
  - The entry loop sleeps 15 s on a relative clock (`run_live.py:898`), so each bot's first check after
    07:00 lands at a phase set by its start time: paper evaluated at 07:00:05.6, the rehearsal at 07:00:11.2.
  - Their live chains were fetched 4.9 s apart, with spot at 7360.16 vs 7358.14 and VIX (each bot's own
    collector read) at 24.49 vs 24.33.
  - There was no 429 between 06:51:01 and 07:01:13.
- **Recommendation:**
  - Keep both SPX bots direct.
  - Accept the current 1 s retry for now: 0 final failures in 52 events.
  - Add the input-timing fields to the paired report.
  - If 429s need to come down, the structural fix is to stop polling the **full chain** to value three held
    legs. That is the monitor-cadence study's leg-quote step, and quotes have never been throttled.
  - A live collector offset is a small, optional, opt-in addition (§5).

### Corrections to the brief

| Brief said | Evidence |
|---|---|
| Paper alone on 11-17 had 2 429s over the same window | Both 11-17 429s were at **12:00:03 and 12:16:05**; 06:30–09:35 on 11-17 had **0** |
| The gateway logged no 429s | The gateway had **36** upstream 429s in 30 days (`schwab_gateway_upstream_failures_total{cause="rate_limited"}`), 6 of them on 11-18. It does not retry them: it returns 503 `upstream_rate_limited` to the client |
| 4 s option-chain TTL, fetches take 4.2–5.5 s | The deployed `SCHWAB_GATEWAY_OPTION_CHAIN_CACHE_TTL_SECONDS` is **8**. Direct full-SPX-chain fetches take p50 0.62–0.70 s and p99 1.3–2.5 s. The 4–5 s figure is from the September gateway soak |
| 13 SPX 429s | 13 up to 09:35; **16** up to 10:00, after paper's 09:40:07 |

## 2. Phase A: evidence

### 2.1 Chain call sites (SPX)

| Site | Cadence / trigger | Path | Effect of a 429 (direct: wait 1, 2, 4 s; observed: always ok after 1 s) |
|---|---|---|---|
| `data/collector.py:275` `fetch_chain` in `_collect_timed_snapshot`, called from `run_aligned_loop` (`:217` is the untimed path, unused while `record_timing: true`) | Wall-clock grid HH:MM:00 + `align_offset_seconds`. Offsets are SPX **0.0**, NDX 2.0, XSP 4.0. Chain first, then spot, then VIX | Data. It feeds the live entry gate (snapshot ≤ 180 s, `entry.max_chain_snapshot_age_seconds`), the VIX input (≤ 300 s), research and replays | 1 s: the snapshot keeps its pass-start stamp, and its quotes are about 1.7 s later. 3×429: about 7 s of sleeps, then a raise; `snapshot_failed`, the tick is lost and not caught up. The entry gate tolerates 2 lost ticks |
| `services/trade_service.py:365` | Entry ladder, one fetch per step. The entry loop runs every **15 s on a relative clock** (`run_live.py:898`), so its phase depends on container start | **Entry** | 1 s: entry is about 1.7 s later at a slightly different price. 3×429: `chain_fetch_failed`, then `break`, then the next attempt 15 s later, about 25 s late in total |
| `services/position_service.py:441/445` `_monitor_loop` | Relative: `sleep(poll_interval=2.0)` after each poll's work, so about 2.6 s per cycle. Live also does account snapshot + orders-for-day every 5 polls (`MANUAL_CLOSE_CHECK_POLLS`) | **Exit / monitor** | 1 s: the exit decision comes about 1 s later. 3×429: poll fails, `market_data_failures += 1`, sleep 2 s; about 11 s without valuation |
| `services/position_service.py:1070` | Once, at close, only if settlement spot is unavailable | Settlement fallback | Irrelevant to the 429s |
| `services/position_service.py:1649` `_post_exit_recording` | Relative, 2 s, from the exit until the close | Recording only | A lost row |
| `data/providers.py` | `DirectSchwabMarketDataProvider` → `SchwabClientWrapper._retry` (`schwab_client.py:233`). `GatewayAuthoritativeMarketDataProvider` → `_transient_read`: 2 attempts, 0.25 s backoff | — | — |

Two retry details in `_retry` matter here:
- After the **third** 429 it still sleeps 4 s before raising, which wastes 4 s.
- A 429 does not increment `butterfly_schwab_api_errors_total`, so **429s are visible only in logs**. No
  metric counts them.

`place_order` is not retried. A 429 on it would surface as `OrderRejectedError`, because it is a 4xx
with no Location header. No order-side 429 has been seen, and the 11-16 pilot made 1 `place_order` call.

### 2.2 Every 429 with its owner and neighbours

Times are when the 429 response was logged. For monitor polls, the start is inferred as the previous
row + 2.0 s.

| Bot | Time | s | Own request | Other bot's chain request in flight? |
|---|---|---|---|---|
| paper | 11-17 12:00:03.4 | 3 | monitor | (alone) |
| paper | 11-17 12:16:05.8 | 5 | monitor | (alone) |
| rehearsal | 11-18 06:51:00.9 | 0 | **collector** | **yes, paper collector at :00.0** |
| paper | 07:01:14.0 | 13 | monitor | no |
| rehearsal | 07:16:00.8 | 0 | **collector** | **yes, paper collector at :00.0** |
| paper | 07:21:05.6 | 5 | post-exit | no |
| rehearsal | 07:30:05.2 | 5 | post-exit | no |
| rehearsal | 07:32:03.9 | 3 | post-exit | no |
| paper | 07:40:05.6 | 5 | post-exit | no |
| rehearsal | 07:45:05.3 | 5 | post-exit | no |
| rehearsal | 08:00:11.0 | 11 | post-exit | no |
| rehearsal | 08:01:11.1 | 11 | post-exit | no |
| rehearsal | 08:02:05.6 | 5 | post-exit | no |
| paper | 08:15:09.9 | 9 | post-exit | **yes** |
| paper | 08:35:05.4 | 5 | post-exit | no |
| paper | 09:40:07.6 | 7 | post-exit | no |

### 2.3 Per-second timing

Direct SPX chain requests, 06:30–13:00. For 11-18 the data runs to about 10:00.

| | 11-17 (paper alone) | 11-18 (both) |
|---|---|---|
| Chain requests per minute | 21.8 | 22.1 (paper exited 07:09 and the rehearsal 07:10; post-exit polling continues) |
| Starts in seconds :00–:04 vs any other 5 s bucket | 1,036 vs about 680 | 1,097 vs about 685 |
| Share of time with ≥ 2 direct chain fetches in flight, :00–:04 | 3 % | 11 % |
| Same share, other buckets | 0 % | 3 % |
| Fetch duration p50 / p99 | 0.63 / 1.24–1.50 s | 0.64–0.70 / 1.3–2.5 s |

Comparing the app-wide load at each 429 (both bots plus gateway upstream, 11-18 06:30–10:00) against
5,000 random instants:

| Trailing window | Mean load at the 429s | Mean load at random | Random p99 |
|---|---|---|---|
| 1 s | 1.8 | 1.0 | 4 |
| 10 s | 13.8 | 10.0 | 19 |
| 60 s | 53.4 | 59.5 | 71 (max 74) |

So the 429s are not associated with high per-minute load. They are associated with the busy first
seconds of the minute, and above all with 5-minute marks, where our own load is no higher (§1).

Across all 52 recorded 429s, by minute mod 15:
- :00 → 26
- :05 → 9
- :10 → 5
- 12 elsewhere, all within 1–2 minutes after one of those marks.

Every one landed within the first 15 s of its minute. Helios cron has nothing running every 5 or 15
minutes against Schwab: polymarket runs every 10 minutes and doesn't use Schwab, and the token keepalive
runs hourly. The only Schwab callers are paper SPX, the rehearsal and `schwab_gateway_live` (which serves
NDX, XSP and afterhours-lab). There is one token file, and the candidate bots are not running.

### 2.4 Baseline by day

App-wide upstream 429s, from gateway logs and SPX container logs. Request counts are Prometheus totals
for the hours ending 07–13 PT.

| Session | Gateway 429 | Direct SPX 429 | App requests | Notes |
|---|---|---|---|---|
| 11-03 … 11-13 (9 sessions) | 2, 3, 5, 3, 2, 4, 3, 0, 4 | — | 5.1–9.3 k | Paper SPX was on the gateway |
| 11-16 | 2 | unknown (pilot logs lost on recreate; 0 exceptions) | about 20.7 k | Live pilot replaced paper: 7,366 chain, 2,995 account snapshot, 2,995 orders-for-day, 780 quote |
| 11-17 | 2 | 2 | about 13.7 k | Paper direct from 11-16 15:02 |
| 11-18 (to 10:00) | 6 | 14 | about 12.9 k | Paper + rehearsal direct |

Per request, 11-18's chain 429 rate was about 4× that of earlier days. This is one session. Two
explanations remain open: the extra direct load counts against a shared per-app bucket, or 11-18 was a
congested day at Schwab. The evidence for the second is the gateway's four 429s at 06:35–06:50, which
came before the 07:00 entry when total load was about 12–15/min. Telling them apart needs more paired
days, or a paper-alone day measured over the same hours. §2.4a settles most of this.

### 2.4a Gateway alone over 12 sessions, and load dependence

Every gateway upstream call since 11-03 (`gateway_scheduler_execution_finished`, 125 k lines) was
matched against its 429s. Session hours are 06:30–13:00. "Hot" means the first 15 s of a minute
divisible by 5; "early" the first 15 s of other minutes; "late" second 15 or later.

| Session | Gateway chain requests (hot / early / late) | Gateway 429s (hot / early / late) | Hot rate | Direct SPX bots |
|---|---|---|---|---|
| 11-03 | 304 / 1258 / 3111 | 2 / 0 / 0 | 0.66 % | none |
| 11-04 | 322 / 1308 / 3698 | 3 / 0 / 0 | 0.93 % | none |
| 11-05 | 305 / 1216 / 3030 | 5 / 0 / 0 | 1.64 % | none |
| 11-06 | 310 / 1312 / 3752 | 1 / 2 / 0 | 0.32 % | none |
| 11-09 | 254 / 1016 / 1043 | 2 / 0 / 0 | 0.79 % | none |
| 11-10 | 344 / 1312 / 4028 | 4 / 0 / 0 | 1.16 % | none |
| 11-11 | 340 / 1412 / 4648 | 3 / 0 / 0 | 0.88 % | none |
| 11-12 | 323 / 1325 / 3815 | 0 / 0 / 0 | 0.00 % | none |
| 11-13 | 270 / 1119 / 1899 | 3 / 1 / 0 | 1.11 % | none |
| 11-16 | 234 / 990 / 3541 | 2 / 0 / 0 | 0.85 % | live pilot |
| 11-17 | 202 / 815 / 1956 | 2 / 0 / 0 | 0.99 % | paper |
| 11-18 (to 10:00) | 145 / 565 / 2001 | 4 / 1 / 1 | 2.76 % | paper + rehearsal |
| **All** | 3,353 / 13,648 / 36,522 | 31 / 4 / 1 | **0.93 %** (early 0.029 %, late 0.003 %) | |

The table shows three things:
- **The time-of-minute effect is about 300×, and it is stable.** It was present on days when the gateway
  was the only Schwab caller.
- **Adding direct SPX bots did not raise the gateway's rate.** 11-16 and 11-17 sit at the mean. 11-18 is
  high (4 of 145; about 1.4 expected), which looks like a day effect.
- **Concurrent load does not predict a 429.** Pooling every chain request (gateway and direct), the
  429 rate does not rise with the number of app requests in the prior 3 s:

| App requests started in the prior 3 s | 0 | 1 | 2 | 3 | 4 | 5 | 6+ |
|---|---|---|---|---|---|---|---|
| Hot zone | 0.43 % | 0.16 % | 1.03 % | 1.54 % | 0.34 % | 1.27 % | 1.14 % |
| Early zone | 0.04 % | 0.06 % | 0.04 % | 0.04 % | 0.15 % | 0.18 % | 0.05 % |

At our scale, our own load is not what trips the throttle.

### 2.5 Schwab's limits

**Schwab's own words.** Schwab Trader API Support's emails of 2026-10-06 were saved verbatim by another
developer in
[evargas963/Ed-s-Console-App `docs/schwab/schwab_support_emails_2026_10_06.txt`](https://github.com/evargas963/Ed-s-Console-App/blob/main/docs/schwab/schwab_support_emails_2026_10_06.txt).
The question each reply answers is not included.
- "120 requests per minute for non-order endpoints."
- "It is per account, each restful endpoint request counts as 1. The 800 is the total across all accounts
  per minute."
- On large chains: "You would need to break up the request by adding additional filters for symbol with
  large option chains." and "You can filter by expiration, call / put, number of strikes."

**What other developers measured.** In
[l3a0/marketlake PR #791](https://github.com/l3a0/marketlake/pull/791), 24 real 429s from 10-01 to 10-07
were inspected:
- 23 were on chain requests.
- Every one had a body of only whitespace.
- None had a `Retry-After` header, a rate-limit header or a `429-NNN` sub-code.

That contradicts the 429-001/429-005 sub-codes claimed in
[a secondhand article](https://mylinedchart.com/resources/articles/schwab-api-rate-limits-and-token-expiry).

**Order throttle.** It is set per account at app registration, anywhere from 0 to 120 per minute
([schwab-py](https://schwab-py.readthedocs.io/en/stable/getting-started.html),
[TDA forum](https://apiforums.tdameritrade.com/node/116)). This app's value can be read on its page in the
Schwab developer portal.

**What that leaves.** The documented quota is 120 per minute per account, and every request counts as 1.
Our peak is 74, and a live day is estimated at about 83. Our 429s therefore come from an **undocumented,
load-based chain throttle**, consistent with §2.4a and with the other developer's chains-only 429s.
Nothing public documents:
- a per-second or burst limit;
- a chain-endpoint limit;
- `Retry-After` semantics.

The only way to get an authoritative answer is to ask Trader API Support directly, as that developer did.

### 2.6 The gateway

These details come from the `SchwabGateway` repo (v0.8.3+) and the deployed container env.
- **One serialized Schwab execution slot.** It never sends concurrent upstream requests.
- **Priorities:** strict-priority admission, with protected and background pools of 8 each. Butterflyguy
  keys are protected.
- **Option-chain cache:** keyed by (symbol, expiration). TTL is **8 s** as deployed; the ceiling is 8.
  Concurrent misses are coalesced. On 11-18, bots made 9,593 chain requests, of which 2,367 went upstream,
  so 75 % were served from cache.
- **429 handling: no retry.**
  - The gateway returns 503 `upstream_rate_limited`.
  - It sets an app-wide read cooldown of at least 1 s (`api.py:657`), during which every read gets
    `cooldown_rejected`. There were 74 of these in total.
  - The SDK maps that 503 to `GatewayUnavailableError`. Butterflyguy retries once after 0.25 s, which still
    lands inside the cooldown, so **each upstream 429 becomes a failed read for the client**, plus
    `gateway_market_data_unavailable` readiness. 173 client-visible 503s since 11-03, including 23 SPX
    chain 503s while paper was on the gateway.
- **The 3 s `upstream_timeout` budget includes queue wait.**
  - Gateway-era (11-11, 6 h): worker busy 21 %, about 19 upstream calls/min, protected queue wait p99 1.5 s,
    p99.9 3.8 s.
  - 11-18: 9.5 % busy, 7.7/min, p99.9 2.3 s.
  - There were 36 option-chain `scheduler_timeout` failures in 30 days.
- **Why the gateway saw fewer 429s than the direct bots on 11-18:** it sent fewer chain requests (75 %
  cache hits), and they were serialized. It did see 429s; its count was not zero.

### 2.7 The 07:00 fly divergence

| | Paper 420 | Rehearsal 100000 |
|---|---|---|
| Collector 07:00 snapshot complete | 07:00:02.27 | 07:00:02.59 |
| VIX (own collector) | 24.49 | 24.33 |
| `direction_inputs` (first entry-loop check after 07:00) | 07:00:05.60 | 07:00:11.24 |
| `chain_fetched_at` / spot | 07:00:07.43 / 7360.16 | 07:00:12.32 / 7358.14 |
| Live pick (`per_width_bests`) | 7455 × 40, cost 3.45, RR 10.59 | 7450 × 40, cost 3.77, RR 9.61 (limit capped at 4.00) |
| DB-snapshot pick (07:00:00, spot 7354.48) | 7450 × 40 | 7450 × 40 |

**Cause:** the 15 s relative entry loop put the two checks 5.6 s apart, and the market moved in between.
Paper's live re-scan saw spot 2 points higher and moved the center up by one strike. The two collectors'
VIX reads also differ by 0.16, because each reads its own value about 1 s apart. No 429 was involved.

## 3. Phase B: paper SPX on the gateway, live direct

**Why SPX paper is direct today.**
- On 11-16 at 15:02 PT the owner moved paper SPX to direct (Helios `infra/.env`
  `SCHWAB_ACCESS_MODE_SPX=direct`; backup `.rollbacks/infra.env.pre-spx-direct-20261117`).
- The trigger was the monitor replay study: under the gateway's chain cache, 76 % of paper's monitor polls
  were stale repeats, against 4 % on direct data.
- The brief quoted 1-minute cadence as −$15/trade against 2.6 s. The study's 11-16 results withdrew that
  as an artifact. Its 5 s and 10 s arms read −$2.9 [−14.4, 5.5] and −$7.7 [−17.1, 1.8], and it concluded
  that the existing data cannot measure cadence.
- The monitor-cadence study's qualifying set was then defined as "paper SPX trades ≥ 2026-11-17, **direct,
  as-live**".

The change itself is env-only:
- The Helios `infra/.env` has the variable.
- `infra/docker-compose.yml:37` reads it.
- The paper container already has a non-empty `SCHWAB_GATEWAY_API_KEY`.

| Question | Answer |
|---|---|
| 1. Fixes or moves the 429s? | **It moves and reduces them.** The gateway uses the same token, and so presumably the same app. Its cache would cut paper's upstream SPX chain calls from about 22/min to about 7/min (8 s TTL), so expect roughly a third fewer chain requests in the hot window app-wide. Live's 429 exposure is unchanged, because it depends on time of minute, not on paper. Each remaining paper 429 becomes a failed read (§2.6), and the cooldown of at least 1 s also blocks NDX/XSP reads. The gateway has no budget of its own against Schwab: it serializes and caches, it does not pace to a quota |
| 2. Capacity | It returns the gateway to its 11-03…11-13 state (about 19/min upstream, 21 % busy, queue p99.9 3.8 s), which it carried. The alerts (`SchwabGatewayProtectedQueueWaitHigh`, `…OptionChainEndToEndLatencyHigh`, `…TimeoutDrainHigh`) exist in `/opt/monitoring/prometheus-alerts/schwab-gateway.yml`. Minutes firing per session, 11-03 → 11-18:
- `ProtectedRequestFailure`: 20–40 on every gateway-era day (paper SPX on the gateway), 10–35 since. This is the client-visible 429 and timeout pass-through.
- `ProtectedSchedulerFailure`: 5–25 before, 10 since.
- `ProtectedQueueWaitHigh`: 5–15 on 5 days.
- `TimeoutDrainHigh`: 5 on 3 days.

Expect a return to roughly gateway-era levels. SPX chain fetches (p50 about 0.65 s) queue ahead of NDX/XSP in the single slot. A p99.9 queue wait of 3.8 s exceeds the 3 s budget, so expect more NDX/XSP `scheduler_timeout`s |
| 3. Paper fidelity | Paper's chains would be up to 8 s old (mean about 4 s). Paper's 07:00 entry would most likely be served the collector's :00 chain from cache. Mark fills come from cached marks. Drawdown exits would effectively decide on about 8 s data, against live's 2.6 s. That effect cannot be measured yet: the study's cad5/cad10 arms span 0, and scoring needs post-exit trades, expected around end of December. `chain_snapshot_meta` stays the same shape (`chain_source` becomes `gateway`, and `chain_age_s`/`chain_event_ts` are filled), but paper history gains a third segment (gateway → direct 11-17 → gateway) |
| 4. Paper vs live comparison | Input timing and staleness would differ by design, so trade-by-trade differences could no longer be blamed on fills. **This breaks the monitor-cadence qualifying set.** |
| 5. Failure modes | A gateway outage leaves paper SPX blind; live is unaffected (it is direct by override and builds no gateway client in direct mode). Paper still builds `SchwabClientWrapper` (`run_live.py:1097`), so it stays a token consumer: inode/digest checks and hot reload are unchanged. Gateway mode routes only market data; account and order calls stay direct, and paper makes no account calls (the manual-close checks are `live`-only) |
| 6. Rollout | Possible on D4 (§3.1), but **not recommended** |

**Verdict: no-go.** It does not address the time-of-minute throttle on the chain endpoint. It worsens the
failure mode and paper's data quality. It reverses the owner's 11-16 decision and invalidates the
monitor-cadence qualifying set. If the owner still wants it, the study would first need to be re-scoped,
or paper's cache bypassed (gateway force-fresh, which needs gateway code and would remove the request
saving).

### 3.1 If approved anyway: rollout on D4

Requirements:
- off-hours;
- paper flat (DB OPEN = 0, non-terminal intents = 0, broker flat via `tools/deploy_broker_flat_check.py`,
  and no live `trade_id` monitor lines in `docker logs`);
- live not running.

```bash
# on Helios, /opt/butterflyguy
cp infra/.env .rollbacks/infra.env.pre-spx-gateway-$(date -u +%Y%m%dT%H%MZ)
curl -fsS http://127.0.0.1:8011/ready    # gateway ready
grep ^SCHWAB_ACCESS_MODE_SPX= infra/.env    # expect =direct
# edit: SCHWAB_ACCESS_MODE_SPX=gateway   (the D4 step also adds BUTTERFLY_INSTANCE_ROLE=paper)
docker compose --project-name infra -f infra/docker-compose.yml -f <D4 rollback dir>/release-image.yml \
  up -d --no-deps --no-build --pull never app_spx
```

After the change:
- `docker inspect butterfly_spx_app` shows `SCHWAB_ACCESS_MODE=gateway`, and the log shows
  `gateway_market_data_authoritative`.
- At the next session the readiness surfaces become ready.
- `chain_snapshot_meta.chain_source` for SPX is not `schwab_direct`.
- `rate(butterfly_schwab_api_calls_total{job="butterfly_spx",endpoint="get_option_chain"}[5m])` is about 0.
- Gateway upstream SPX chains appear, with no new gateway alerts.

**Rollback:** restore the `.env` backup (or set `SCHWAB_ACCESS_MODE_SPX=direct`) and run the same `up -d`
for `app_spx`. Both directions need a paper recreate.

## 4. Phase C: options

"Paper redeploy" means a recreate of `app_spx`, which is a token consumer. The only planned one is D4.

| Option | Removes 429s? | Paper/live comparability | Entry / exit latency | Live-safety risk | Paper redeploy | Code | Requests ± per min |
|---|---|---|---|---|---|---|---|
| A. Do nothing | No. About 0–2 per bot per day normally, 6–8 on 11-18; all recovered in 1 s | Unchanged | +1.7 s on a hit. Entry fetch at 07:00:05–12 sits in the worst zone, about 2 % per fetch on 11-18 | None new | No | 0 | 0 |
| B. Paper → gateway (8 s TTL) | Moves and reduces them (about −⅓ hot-window chain calls); live unchanged; paper 429s become failed reads | **Worse**: different path and age; breaks the cadence-study set | Paper decides on cached data | Low for live (live stays direct); NDX/XSP lose reads to the cooldown | Yes (env + recreate) | 0 | About −15 chain upstream |
| B′. Gateway with tuning (lower TTL, retry-on-429, force-fresh) | Lower TTL brings back the request count; retry-on-429 is gateway code | Better than B, still a different path | — | — | Yes, plus a gateway release | Gateway repo | Up to 0 saving |
| C. Live collector offset N s (new env, default 0) | Removes only collector-on-collector collisions (2 of 16 on 11-18); one chain per minute moves out of the hot window | Live DB snapshots at :N vs paper :00, so `selection_parity` and the VIX input at 07:00 come from a snapshot N s different (or from the previous minute's if entry runs before :N) | None | Low: entry gate is ≤ 180 s, VIX ≤ 300 s | No | About 15 lines + tests. Needs a new env var, because YAML's explicit `align_offset_seconds: 0.0` beats `COLLECTOR__…` (checked) | 0 |
| D. Offset paper instead | Same as C | **Breaks** paper's minute-mark alignment with ThetaData (`chain_first` at :00), replays and the monitor-cadence 1-minute joins | None | None | Yes | Same as C | 0 |
| E. Retry tuning, market-data endpoints only (env, opt-in): jittered first wait of 0.3–0.8 s; no sleep after the final attempt; order/status endpoints untouched | No; recovery is shorter | Unchanged | 429 recovery about 1.0–1.4 s instead of 1.7; the 3-failure worst case shortens by 4 s | Low if `get_order`/orders are excluded; a shorter wait may retry into the same congested second | Only if paper should get it too | About 25 lines + tests | +0 (same retries, sooner) |
| F. Live reads paper's or the gateway's chain | No (same upstream) | Identical inputs | Live depends on paper or the gateway | **High**: couples real money to the paper bot; the overlay forbids real-money gateway chains without force-fresh | — | Large | About −22 |
| G. Value held legs with the quotes endpoint, not the full chain (the monitor-cadence leg-quote step) | **Mostly**: about 90 % of chain calls are monitor or post-exit polls; quotes had 0 of 52 429s | Preserved if both bots switch; it is the study's own planned change, so sequence it with the study | Smaller payload; likely faster polls | Moderate: exit valuation input changes, so it needs a supervised rollout | Yes | Planned PR | About −22 chain, +22 quote per bot holding a position |
| H. Paired-report input timing (report only) | No | **Better**: shows each bot's `chain_fetched_at`, spot and VIX at entry, monitor poll count and 429 count, so timing differences aren't mistaken for fill differences | None | None | No | Small, in `spx_paired` | 0 |

H′ is a variant of H: align the 15 s entry loop to a wall-clock grid (opt-in env) so both bots evaluate at
the same instant. That removes the 07:00 phase split, but puts both entry chain fetches in the same second
of the hottest window. Prefer H first.

### Worst cases for doing nothing

- **07:00 entry:**
  - A single 429 delays the entry by about 1.7 s.
  - Three in a row (never observed) give about 25 s, with an entry at a different price.
  - On 11-18 the per-fetch 429 risk in that window was about 1.9 %; on 11-17 the same window had 0 429s.
- **Drawdown or stop exit:**
  - A 429 on the deciding poll delays the decision by about 1 s.
  - Three in a row leave the monitor without valuation for about 11 s.
  - The per-poll risk averages about 0.16 % (11-18 direct), so the expected delay per exit is in the
    milliseconds.
- **Live exit order flow:**
  - `get_order` status polls use the same retry, so a 429 adds 1 s.
  - `place_order` is not retried, and a 429 there would surface as a rejection. No order-side 429 has been
    observed (order throttle unknown, likely 0–120/min per account).

## 5. Recommendation and owner decisions

1. **Do not move paper SPX to the gateway (Phase B).** Keep both SPX bots `direct`. Nothing to deploy.
2. **Accept the 1 s retry for now (A).** Measure on the next paired days before changing anything. 11-18
   alone cannot separate our load from a congested Schwab day.
   - **Owner decision:** whether to add a `butterfly_schwab_rate_limited_total{endpoint}` counter (no
     behavior change). Today 429s are logs-only. It takes effect only after each bot's next deploy, so for
     paper it would ride D4.
3. **Add H** (input timing in the paired report). This is the real fix for paper/live comparability.
4. **If 429s must come down, G is the structural fix.**
   - **Owner decision:** whether to sequence the leg-quote change, already planned in the monitor-cadence
     study, with this goal in mind.
   - **Owner decision:** whether C (live-only collector offset, opt-in env, default 0, about 20 s) is worth
     its small snapshot-parity cost. It addresses only collector collisions.
5. **E is optional.**
   - **Owner decision:** whether to cap the wasted 4 s sleep after the final attempt. If yes, it ships as
     opt-in like everything else.

### Owner decisions, 2026-11-18

| Decision | Choice |
|---|---|
| Phase B (paper SPX → gateway) | **Dropped.** Both SPX bots stay `direct` |
| 429 action now | **Add the counter only.** `butterfly_schwab_rate_limited_total{endpoint}`, incremented in `_retry`'s 429 branch. Metrics only, no behavior change, so no env gate. No offset (C), no retry tuning (E), and no reprioritized leg quotes (G) for now |
| Paired report | **Add input timing (H).** Each bot's entry chain-read time, spot, and the time of the collector's VIX row it used; the live-minus-paper gap, flagged at ≥ 2 s; monitor poll count and median poll gap; each bot's 429 count, taken from its container logs at close-out (`deploy/spx-live/common.sh` `rate_limited_count`) |
| Ask Schwab Trader API Support | No |

Both changes ship in the same PR as this report. Neither changes trading behavior. The counter starts
counting on each bot's next deploy: D4 for paper, the next live release for live.

### What was resolved on 11-18, and what remains

Resolved:
- **Documented quota:** 120 non-order requests per minute per account; each request counts as 1 (Schwab
  support, §2.5). We peak at 74.
- **Our load as a cause:** none detected. The gateway's 12-day data and the request-level dose test
  (§2.4a) show no dependence on our own load.
- **Rehearsal effect on 11-18:** no evidence it caused the rise. The gateway alone was also high that day.
- **Gateway alert history:** see §3, question 2.
- **Effect of an 8 s exit cadence:** not measurable with today's data, per the cadence study (§3).

Remaining, answerable only by Schwab or by time:
- The undocumented chain throttle (window, trigger, scope). Ask Trader API Support (§5).
- This app's configured order throttle. It is visible on the app's page in the developer portal.
- The exit effect of cadence. The cadence study's post-exit trades 1–30 (about end of December) will
  answer it.
