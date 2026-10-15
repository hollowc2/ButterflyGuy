BEGIN READ ONLY;
SET LOCAL statement_timeout='30s';
COPY (
 SELECT ts,event_type,jsonb_build_object(
 'trade_id',data->'trade_id','from',data->'from','to',data->'to',
 'regime',data->'regime','pnl',data->'pnl','mark_value',data->'mark_value',
 'peak_value',data->'peak_value') AS data
 FROM decision_log WHERE underlying='NDX' AND ts>='2026-08-06' AND ts<'2026-08-07'
 AND event_type IN ('profit_state_transition','exit_signal_fired','trade_exited')
 ORDER BY ts
) TO STDOUT WITH (FORMAT CSV,HEADER TRUE);
COMMIT;
