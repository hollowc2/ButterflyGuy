-- Literal per-session predicates for bounded TimescaleDB pruning. Exact cohort only.
-- No price, completeness or duplicate filtering.
BEGIN READ ONLY;
SET LOCAL statement_timeout='60s';
COPY ( SELECT * FROM (
SELECT 194 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-07-23'::date AND q.snapshot_time>'2026-07-23 19:59:14.834267+00'::timestamptz AND q.snapshot_time<='2026-07-23T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260723P28230000','NDXP  260723P28330000','NDXP  260723P28430000')
UNION ALL
SELECT 226 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-10'::date AND q.snapshot_time>'2026-08-10 18:45:27.369042+00'::timestamptz AND q.snapshot_time<='2026-08-10T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260810P29370000','NDXP  260810P29470000','NDXP  260810P29570000')
UNION ALL
SELECT 233 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-12'::date AND q.snapshot_time>'2026-08-12 17:50:30.850165+00'::timestamptz AND q.snapshot_time<='2026-08-12T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260812C29925000','NDXP  260812C30025000','NDXP  260812C30125000')
UNION ALL
SELECT 236 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-13'::date AND q.snapshot_time>'2026-08-13 17:56:00.274497+00'::timestamptz AND q.snapshot_time<='2026-08-13T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260813C30210000','NDXP  260813C30310000','NDXP  260813C30410000')
UNION ALL
SELECT 245 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-18'::date AND q.snapshot_time>'2026-08-18 19:28:02.836732+00'::timestamptz AND q.snapshot_time<='2026-08-18T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260818P29240000','NDXP  260818P29340000','NDXP  260818P29440000')
UNION ALL
SELECT 248 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-19'::date AND q.snapshot_time>'2026-08-19 17:30:14.03521+00'::timestamptz AND q.snapshot_time<='2026-08-19T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260819C29620000','NDXP  260819C29720000','NDXP  260819C29820000')
UNION ALL
SELECT 249 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-20'::date AND q.snapshot_time>'2026-08-20 19:23:22.47545+00'::timestamptz AND q.snapshot_time<='2026-08-20T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260820P28930000','NDXP  260820P29030000','NDXP  260820P29130000')
UNION ALL
SELECT 254 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-21'::date AND q.snapshot_time>'2026-08-21 18:06:32.156456+00'::timestamptz AND q.snapshot_time<='2026-08-21T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260821C29380000','NDXP  260821C29480000','NDXP  260821C29580000')
UNION ALL
SELECT 258 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-26'::date AND q.snapshot_time>'2026-08-26 18:19:09.143385+00'::timestamptz AND q.snapshot_time<='2026-08-26T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260826P28920000','NDXP  260826P29020000','NDXP  260826P29120000')
UNION ALL
SELECT 267 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-08-31'::date AND q.snapshot_time>'2026-08-31 19:13:23.149106+00'::timestamptz AND q.snapshot_time<='2026-08-31T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260831P29060000','NDXP  260831P29160000','NDXP  260831P29260000')
UNION ALL
SELECT 294 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-09-17'::date AND q.snapshot_time>'2026-09-17 18:22:35.881973+00'::timestamptz AND q.snapshot_time<='2026-09-17T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260917C29510000','NDXP  260917C29610000','NDXP  260917C29710000')
UNION ALL
SELECT 306 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-09-23'::date AND q.snapshot_time>'2026-09-23 19:57:53.57635+00'::timestamptz AND q.snapshot_time<='2026-09-23T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260923P30250000','NDXP  260923P30350000','NDXP  260923P30450000')
UNION ALL
SELECT 316 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-09-28'::date AND q.snapshot_time>'2026-09-28 18:49:52.73782+00'::timestamptz AND q.snapshot_time<='2026-09-28T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260928P30030000','NDXP  260928P30130000','NDXP  260928P30230000')
UNION ALL
SELECT 317 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-09-29'::date AND q.snapshot_time>'2026-09-29 19:14:10.73657+00'::timestamptz AND q.snapshot_time<='2026-09-29T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  260929C30480000','NDXP  260929C30580000','NDXP  260929C30680000')
UNION ALL
SELECT 339 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-10-09'::date AND q.snapshot_time>'2026-10-09 19:36:17.189427+00'::timestamptz AND q.snapshot_time<='2026-10-09T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  261009C30940000','NDXP  261009C31040000','NDXP  261009C31140000')
UNION ALL
SELECT 343 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-10-12'::date AND q.snapshot_time>'2026-10-12 19:35:19.351639+00'::timestamptz AND q.snapshot_time<='2026-10-12T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  261012P30440000','NDXP  261012P30540000','NDXP  261012P30640000')
UNION ALL
SELECT 346 AS trade_id,to_jsonb(q) AS raw_quote,CASE WHEN m.snapshot_time IS NULL THEN NULL ELSE to_jsonb(m)-'omitted' END AS raw_meta
FROM option_chain_snapshots q LEFT JOIN chain_snapshot_meta m ON m.snapshot_time=q.snapshot_time AND m.underlying=q.underlying AND m.expiration=q.expiration
WHERE q.underlying='NDX' AND q.expiration='2026-10-13'::date AND q.snapshot_time>'2026-10-13 18:10:42.390412+00'::timestamptz AND q.snapshot_time<='2026-10-13T16:00:00-04:00'::timestamptz AND q.symbol IN ('NDXP  261013P30260000','NDXP  261013P30360000','NDXP  261013P30460000')
) imported ORDER BY trade_id,raw_quote->>'snapshot_time',raw_quote->>'symbol'
) TO STDOUT WITH (FORMAT CSV,HEADER TRUE);
COMMIT;
