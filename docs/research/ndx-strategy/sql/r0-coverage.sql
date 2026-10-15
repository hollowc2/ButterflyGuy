BEGIN READ ONLY;
SET LOCAL statement_timeout='120s';
COPY (SELECT trade_id,count(*) AS leg_rows,count(DISTINCT ts) AS observations,min(ts) AS first_ts,max(ts) AS last_ts
FROM monitoring_leg_quotes WHERE underlying='NDX' AND ts<'2026-10-15' GROUP BY trade_id ORDER BY trade_id) TO STDOUT WITH(FORMAT CSV,HEADER TRUE);
COMMIT;
