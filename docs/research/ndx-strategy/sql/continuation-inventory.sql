-- Inventory only. These independent minute snapshots are NOT R0 monitor quotes.
BEGIN READ ONLY;
SET LOCAL statement_timeout='60s';
COPY (
 SELECT t.id,t.trade_date,t.exit_time,c.complete_timestamps,c.first_ts,c.last_ts
 FROM butterfly_trades t LEFT JOIN LATERAL (
  SELECT count(*) AS complete_timestamps,min(snapshot_time) AS first_ts,
         max(snapshot_time) AS last_ts
  FROM (
   SELECT snapshot_time FROM option_chain_snapshots q
   WHERE q.underlying='NDX' AND q.expiration=t.trade_date
   AND q.snapshot_time>t.exit_time
   AND q.snapshot_time<=(t.trade_date+time '16:00') AT TIME ZONE 'America/New_York'
   AND q.snapshot_time>=t.trade_date::timestamp AT TIME ZONE 'America/New_York'
   AND q.symbol IN (t.lower_symbol,t.center_symbol,t.upper_symbol)
   AND q.option_type=t.direction AND q.bid>=0 AND q.ask>=q.bid AND q.mark IS NOT NULL
   GROUP BY snapshot_time HAVING count(DISTINCT strike)=3 AND count(*)=3
  ) complete
 ) c ON TRUE
 WHERE t.underlying='NDX' AND t.trade_date BETWEEN '2026-07-22' AND '2026-10-14'
 AND t.metadata->>'paper_fill_model'='mark_v1' AND t.exit_reason<>'cash_settled'
 ORDER BY t.id
) TO STDOUT WITH (FORMAT CSV,HEADER TRUE);
COMMIT;
