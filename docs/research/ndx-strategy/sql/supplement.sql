-- NDX-01 identity and provenance supplement; no quote reconstruction.
BEGIN READ ONLY;
SET LOCAL statement_timeout='120s';
COPY (
 SELECT t.id,t.trade_date,t.lower_symbol,t.center_symbol,t.upper_symbol,
 t.metadata->>'settlement_spot_time' AS settlement_spot_time,
 t.metadata->>'settlement_source' AS settlement_source,
 t.metadata->>'settlement_spot' AS settlement_spot,
 (t.metadata ? 'profit_management') AS has_recorded_exit_settings,
 q.expirations,q.roots,q.first_ts,q.last_ts,q.post_exit_leg_rows,
 q.pre_entry_leg_rows
 FROM butterfly_trades t LEFT JOIN LATERAL (
  SELECT string_agg(DISTINCT expiration::text,'|') AS expirations,
  string_agg(DISTINCT split_part(trim(symbol),' ',1),'|') AS roots,
  min(ts) AS first_ts,max(ts) AS last_ts,
  count(*) FILTER (WHERE ts>t.exit_time) AS post_exit_leg_rows,
  count(*) FILTER (WHERE ts<t.entry_time) AS pre_entry_leg_rows
  FROM monitoring_leg_quotes WHERE trade_id=t.id AND underlying='NDX'
 ) q ON TRUE
 WHERE t.underlying='NDX' AND t.trade_date BETWEEN '2026-03-30' AND '2026-10-14'
 ORDER BY t.id
) TO STDOUT WITH (FORMAT CSV,HEADER TRUE);
COMMIT;
