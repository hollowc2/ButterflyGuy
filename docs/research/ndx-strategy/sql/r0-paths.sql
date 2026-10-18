BEGIN READ ONLY;
SET LOCAL statement_timeout='120s';
COPY (
SELECT q.trade_id,q.ts,count(*) AS legs,
 sum((CASE WHEN q.strike=t.center_strike THEN -2 ELSE 1 END)*q.mark) AS raw_mark,
 sum(CASE WHEN q.strike=t.center_strike THEN -2*q.ask ELSE q.bid END) AS raw_bid,
 sum(CASE WHEN q.strike=t.center_strike THEN -2*q.bid ELSE q.ask END) AS raw_ask,
 max(q.ask-q.bid) AS max_leg_spread_abs,
 max(CASE WHEN q.mark>0 THEN (q.ask-q.bid)/q.mark END) AS max_leg_spread_to_mark_ratio,
 max(q.fly_mark) AS recorded_mark,max(q.peak_value) AS recorded_peak,max(q.spot_price) AS spot,
 count(*) FILTER(WHERE q.bid IS NULL OR q.ask IS NULL OR q.mark IS NULL OR q.bid<0 OR q.ask<q.bid) AS invalid_legs
FROM monitoring_leg_quotes q JOIN butterfly_trades t ON t.id=q.trade_id
WHERE q.underlying='NDX' AND t.underlying='NDX' AND t.trade_date<='2026-10-14'
AND q.ts>=t.entry_time AND q.ts<=t.exit_time AND q.option_type=t.direction
AND q.strike IN(t.lower_strike,t.center_strike,t.upper_strike)
GROUP BY q.trade_id,q.ts ORDER BY q.trade_id,q.ts
) TO STDOUT WITH(FORMAT CSV,HEADER TRUE);
COMMIT;
