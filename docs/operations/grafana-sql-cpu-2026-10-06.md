# Helios Grafana SQL CPU investigation — 2026-10-06

Deployed three SQL-field edits in `infra/grafana/dashboards/butterfly_trading.json`, loaded as Trading version 28. No service restart, DDL, extension, global logging, trading setting, timer, compression policy, retention policy, or autovacuum change. All existing health-check, autovacuum, and dashboard refresh fixes remain active.

The provided 17:10:06–17:15:06 UTC market-hours sample established that Grafana backends consumed 61.23 of 76.14 PostgreSQL CPU-seconds (80.4%), with 61.2% host steal. Those pooled-backend totals guide prioritization; they are not per-statement timings.

The strongest finding is Trading panel 2, **Position Value**, when the selected symbol has no eligible OPEN trade. Its original ordered join can scan all monitoring history before establishing that the trade set is empty. The first marker-only after window unexpectedly captured that exact live request, establishing a bottleneck beyond the earlier last-query snapshots.

- Grafana container PID 13178, host PID 1128725, process start ticks 145635970; client 172.23.0.12.
- Query start `2026-10-06 17:49:28.109684+00:00`; the same query, query-start timestamp, process identity, and active state appeared in 71 consecutive two-second samples.
- From first to last active sample, elapsed 140.092 seconds, backend CPU rose **26.53 seconds**. Total observed backend CPU in the five-minute window was **26.95 seconds**, including completion; its last-query timestamp stayed unchanged afterward. The query had started about 58 seconds before the window, so this is not a measurement of its whole lifetime.
- Many samples waited on `DataFileRead`. Ordinary EXPLAIN had an ordered monitoring ChunkAppend outside an inner materialized eligible-trade relation. With no OPEN SPX trade, the LIMIT cannot stop after finding a match.
- Confidence is high for CPU during this observed continuous execution. The earlier 51.01 seconds on PID 12402 remain unattributed to individual statements; its latest-VIX snapshot is insufficient evidence.

Trading panel 24, **$underlying vs Breakevens**, also performs avoidable work in its entry/exit marker targets (zero-based target indexes 2 and 3). The entry marker's monitoring fallback ran despite an available spot price. A bounded original SPX benchmark used 0.97 CPU-seconds, 21,500 buffer hits and 1,700 reads, and examined 17,439 plus 66,719 nonmatching rows in two older chunks. The fallback touched all 19 monitoring chunks. Its ordinary plan used timestamp index scans with trade/underlying as residual filters on those two chunks, despite the existing trade/time index elsewhere. This is a demonstrated query defect, not an attribution of the earlier largest pooled-backend total.

The deployed edits are:

1. **Position Value:** select today's eligible OPEN trades first; use a correlated LATERAL query with `ORDER BY ts DESC LIMIT 1` to obtain each trade's latest monitoring quote. Keep the outer `ORDER BY q.ts DESC LIMIT 1` to choose the latest quote across eligible trades. With no eligible trade, the quote lookup is never executed. Both statements leave equal-timestamp ties unspecified; no new tie-breaker or filter was introduced. Missing quotes still exclude that trade; a NULL latest fly mark still falls through the original COALESCE-to-zero behavior. Multiplication by 100 and quantity, the float type, `NOW()` timestamp, and `Current Value` column are unchanged.
2. **Entry marker:** move spot and monitoring lookups into scalar subqueries inside COALESCE. Priority stays historical spot → nonempty metadata entry spot → earliest non-NULL monitoring spot for this trade and underlying.
3. **Exit marker:** use scalar subqueries inside COALESCE, preserving historical spot → latest non-NULL monitoring spot for the trade at or before exit.

[PostgreSQL documents](https://www.postgresql.org/docs/16/functions-conditional.html) that COALESCE evaluates only arguments required to obtain the first non-NULL result. The marker fallbacks retain their full historical searches. No recent-only bound was added. The same chart time filters, identity predicates, statuses, ordering, columns, dollar units, and quantity handling remain. No cohort or fill-model filter changed; Performance and Trade Detail files have their original inspected hashes.

The Position Value audit used read-only transactions, application name `grafana_sql_audit_position`, one-second lock timeout, a 1.5-second statement timeout for the original empty-SPX case, and five-second timeouts for other cases. Only the audit's own statement was timed out; no other client's backend was cancelled.

- Empty SPX, original: intentionally hit the 1.5-second statement timeout; 1.08 observed CPU-seconds, 1.699 seconds client wall time. No returned rows or completed EXPLAIN ANALYZE plan are claimed.
- Empty SPX, optimized: 1.122 ms execution time; four shared buffer hits, zero reads; 0.0107 seconds client wall time; CPU delta below one 10-ms accounting tick in this run. The monitoring child plan had zero execution loops.
- Active NDX, original/optimized: 0.537/0.738 ms execution; 0.10/less-than-one-tick observed CPU-seconds; 0.0994/0.00990 seconds client wall time.
- Active XSP, original/optimized: 0.725/0.531 ms execution; 0.10/0.01 observed CPU-seconds; 0.1008/0.00866 seconds client wall time.

Planning and client/transaction overhead explain why CPU and client wall time are not interchangeable with EXPLAIN execution time. All inspected selected plans were serial; the benchmark instrumentation also observed any parallel-worker titles belonging to its backend, and recorded none for these queries.

The measurement windows were:

- Fresh natural baseline: 2026-10-06T17:29:41Z–2026-10-06T17:34:41Z (300.193 s): 18.925 container CPU-seconds, 6.30% of one core; host steal 82.56%; 8,199 inserts (1639/min). Grafana backends used 0.00 CPU-seconds; no active Grafana statement was sampled. This idle dashboard window is not a pre-fix load benchmark.
- Original marker/control replay: 2026-10-06T17:40:42Z–2026-10-06T17:45:42Z (300.089 s): 39.790 container CPU-seconds, 13.26% of one core; host steal 85.09%; 9,326 inserts (1865/min). Replay backend 11.01 CPU-seconds; Grafana backends 0.20; monitoring connection 4.16.
- Marker-only after replay: 2026-10-06T17:50:26Z–2026-10-06T17:55:27Z (300.249 s): 66.112 container CPU-seconds, 22.02% of one core; host steal 62.63%; 9,667 inserts (1932/min). Replay backend 10.15 CPU-seconds; Grafana backends 26.95; monitoring connection 4.95. The extra live Position Value request accounts for almost all observed Grafana CPU. Total container load rose because workload and steal differed; this is not evidence of a regression or a matched overall improvement.
- Final verification replay: 2026-10-06T18:03:35Z–2026-10-06T18:08:35Z (300.055 s): 27.129 container CPU-seconds, 9.04% of one core; host steal 54.83%; 10,686 inserts (2137/min). Replay backend 7.70 CPU-seconds; Grafana backends 0.00; monitoring connection 3.31. This synthetic run adds ten optimized Position Value queries; its total workload differs from the earlier runs.

Successive one-minute container CPU averages, one core = 100%:

- Natural baseline: 5.82%, 5.90%, 4.67%, 8.49%, 6.63%.
- Original marker/control replay: 19.43%, 10.14%, 15.01%, 10.71%, 10.92%.
- Marker-only after replay: 34.17%, 35.92%, 20.06%, 9.44%, 10.50%.
- Final verification: 11.57%, 8.40%, 6.41%, 9.45%, 9.36%.

The first two scripted replay runs used the same 60 SELECTs, selected SPX, fixed Trading range `2026-10-06T07:00:00Z`–`2026-10-06T17:10:46.802Z`, one persistent read-only connection, no statement caching, one query at a time, ten 30-second Trading slots and five 60-second Performance slots. This was a small subset of dashboard traffic, not a full browser/dashboard load test. The six unchanged controls were Performance latest SPX/NDX/XSP/VIX, Trading spot history, and the spot-path UNION ALL/DISTINCT ON target. The final run used the same controls/markers plus ten Position Value SELECTs. Every replay SELECT had a 10-second statement timeout and one-second lock timeout.

Observed query totals for ten calls per marker:

- Entry marker CPU: 5.04 → 3.61 seconds; client wall totals 16.97 → 10.44 seconds.
- Exit marker CPU: 1.79 → 1.98 seconds; client wall totals 6.97 → 8.57 seconds. Exit CPU did not improve in this sample.
- Both markers: 6.83 → 5.59 CPU-seconds. The paired ordinary/analyzed plans show the entry marker dropping from about 23,200 execution buffer hits to 32 when spot data is available, with the fallback subplan unexecuted. Steal changed and the second run had the additional live query; these observed reductions are not a controlled percentage guarantee.
- Final Position Value: 10 successful calls; 0.67 measured CPU-seconds and 2.0180 seconds total client wall time. Each returned a single row with the preserved column schema; the separate live empty-SPX result check and Grafana API returned zero. This verifies the empty-position path under repeated execution; it does not imply a matched whole-dashboard CPU reduction.

Backend CPU uses cumulative `/proc` utime+stime and process-start-tick keys, with container namespace PIDs matched to pg_stat_activity. Process/cgroup counters were sampled every 250 ms; a persistent read-only monitoring connection sampled activity every two seconds. It retained backend start time, client, application, state, wait events, query start and the server's sampled SQL. PostgreSQL's query text limit was 1,024 bytes. Short-lived or exited process totals remain lower bounds; the cgroup total is the cross-check, not a sum inferred from last queries. Host steal uses cumulative host CPU counters, excluding duplicate guest counters. Table insert counters cover all Butterfly user relations including chunks and can lag briefly. Monitoring CPU is reported explicitly.

Correctness and validation:

- 128 exact original/optimized ordered-row comparisons passed; 126 also explicitly checked PostgreSQL column names and type OIDs. Grafana frames verified the preserved live column schema. Marker cases covered SPX/NDX/XSP current session (active NDX/XSP, closed SPX), completed October 5 trades, empty Sunday, multiple trades, and actual nonempty September 25 compressed-history trades. An additional March 13 case had no trade and is recorded as empty, not as proof of a nonempty historical view.
- Read-only CTE fixtures exercised prior-session prices, absent/NULL spot rows, metadata priority, blank metadata, quote-only and entirely missing sources, other trade/underlying quotes, and quote timestamps beyond exit.
- Position fixtures covered empty eligibility, OPEN with no quote, one and multiple eligible trades, CANCELLED/prior-session trades, NULL latest marks, and incorrect underlying identity. NDX/XSP live rows matched; empty SPX was checked against the original query's mathematically required zero result without repeating an unbounded legacy scan.
- `uv run pytest tests/test_performance_dashboard.py tests/test_candidate_dashboards.py -q`: 11 passed. `uv run ruff check tests/test_candidate_dashboards.py` and `git diff --check`: passed. The regression tests guard lazy marker fallbacks and trade-first Position Value lookup; both guards were also verified to fail against the original deployed definitions.
- Grafana `/api/ds/query` returned HTTP 200 with correct Entry/Exit frames and Position Value frames for all three symbols. Datasource health returned OK. All final synthetic queries returned rows with no error/timeout; the original-SPX timeout above was a deliberate bounded profiling result.
- All app metrics endpoints remained HTTP 200; collection counters advanced in each five-minute window and entry-loop error counters stayed zero. The final summaries contain their exact before/after metric samples and DB write deltas.
- Final checks assert identical container IDs, image digests, host process IDs and start times for DB, Grafana, and all three trading apps. Local and remote Trading JSON equal the inspected initial dashboard plus exactly the three SQL fields. No unrelated remote work was overwritten.

Workload mapping and remaining costs:

- PostgreSQL 16.11 / TimescaleDB 2.25.2; Grafana 12.4.1. Docker health check 60 seconds; autovacuum naptime 60 seconds; worker limit 10. Refresh remains Trading 30s, Performance 60s, Trade Detail 60s. File provisioning polls every 30 seconds; no service restart was used.
- Verified client addresses: Grafana 172.23.0.12; SPX .7; NDX .6; XSP .10; TimescaleDB .4 on monitoring_net. Dashboard file/API SQL matched at initial inspection. Trading default range is now/d–now (sampled expansion started at 07:00 UTC, Los Angeles midnight); Performance now-90d–now; Trade Detail now-1d–now with selected-trade SQL. None of these SQL panels repeat.
- Trading has 24 SQL targets, Performance 46, Trade Detail 14: at most 108 configured SQL executions/minute with all targets rendered at their present refresh settings, before variable queries. This is not measured request traffic. Trade Detail's two SQL variables load available underlyings and the selected underlying's trades; datasource variables use Grafana lookup. The primary datasource does not specify pool limits in jsonData; no default concurrency limit is assumed here.
- Initial live pooled-backend last queries identify Trading range expansions; their dates/ranges stayed unchanged during idle samples. The later Position Value request was continuous with sampled active concurrency one. Neither dashboard-open versus refresh trigger nor browser overlap can be established from backend state alone. Grafana docker logs did not return promptly; the audit's own log-reader process was terminated without signalling a database client. No logging settings changed.
- Latest-price queries already use ordered ChunkAppend and the underlying/time index. Warm latest-VIX execution was 0.746 ms, three buffer hits, zero reads; five original replay calls consumed 0.33 CPU-seconds total including planning/protocol work. Cold first-query planning was much larger. Latest prices remain unbounded and preserve overnight/holiday fallback.
- Trading spot/monitoring/tent histories already prune to the selected time bounds in representative plans. DB Snapshots Today still selects Timescale SkipScan. Its data source and collector-coverage semantics were preserved.
- Trade Detail lifecycle queries lack a trade-ID expression index: underlying is an index condition; JSON trade ID and event type are residual filters. One cold SPX run took 2.40 CPU-seconds/8.309 seconds client wall, with 26,160 nonmatching rows filtered. Warm paired runs were substantially cheaper (0.10–0.28 CPU-seconds). Forcing the existing event-type index via a materialized CTE increased buffer visits and warm CPU; that rewrite was rejected and never deployed. This remains a possible next bottleneck if that dashboard is actively used. No index DDL is necessary for the deployed fixes, and none was executed or requested.
- No provider-throttle recovery time or matched whole-dashboard performance improvement is established by these observations.

Deployment and rollback:

- Helios Butterfly Git baseline `288d6cb321e611a94acc819fa96fc5e429ff836e`; monitoring baseline `f6999eae3c8c51855c071e535868bc98beb21449`; monitoring project `/opt/monitoring/docker-compose.yml`, project `monitoring`. No Compose action was run after the initial read-only status check.
- Original Trading file SHA-256: `d62b02616cb7a020165274dde3b716ab9776f6ad85a1857fe7a3295916308993`.
- After marker edits/version 27: `519449340f816407bbc3050a72808e903e401e677b1014ea48a256ed0748f94f`.
- Final/version 28: `654c7b6c964610dc2b36bb3b09d2b0487e2a49d4d60c75dc30890e969c715af1`.
- Marker rollback: `/opt/monitoring/rollback/grafana-sql-20261006T174844Z`.
- Position rollback: `/opt/monitoring/rollback/grafana-sql-20261006T180026Z`.
- Each folder contains the pre-edit dashboard, hashes, container identities, exact SQL edits and a hash-guarded `rollback.py`. Restore the position edit first with `/opt/butterflyguy/.venv/bin/python /opt/monitoring/rollback/grafana-sql-20261006T180026Z/rollback.py`. To restore all task edits, then run the equivalent marker rollback script in the first folder. Allow the provisioning poll to load each restoration and verify through Grafana's API. Scripts refuse to overwrite a file with subsequent unrelated changes; review and reverse only the affected SQL fields if a hash guard fails. Restarts are unnecessary.

Task source changes are the three Trading SQL fields and two test functions plus updated fallback assertions. Performance/Trade Detail local refresh changes predated this task and were preserved. The mandated AST-only graphify update refreshed four generated graph files; its existing missing SQL-parser warning was retained without installing an extra parser.

Raw observations, plans, comparisons, replay method and API validation are archived under `reports/operations/helios-grafana-20261006/` as gzip files with SHA-256 checksums. `summary.json` retains every window's minute data, attribution, insert deltas, metrics, per-target CPU/wall/row counts, deployments and position benchmarks. `sql-changes.json` contains all three exact original/optimized statements. The same archived evidence is saved on Helios under `/opt/monitoring/rollback/grafana-sql-20261006T180026Z/evidence/`, with this report beside it as `report.md`; local `reports/` output follows the existing Git ignore convention. Original uncompressed evidence and audit scripts also remain in `/tmp/grafana_*`. No credentials were included.
