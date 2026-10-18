BEGIN READ ONLY;
SET LOCAL statement_timeout='45s';
COPY(SELECT ts,underlying,event_type,data FROM decision_log
WHERE underlying='NDX' AND ts>='2026-09-01' AND ts<'2026-10-15'
AND event_type IN ('trade_entered','trade_exited','exit_signal_fired','exit_mark_parity','exit_ladder_trace','entry_ladder_trace','entry_selection_parity','position_market_data_recovered','position_market_data_unavailable')
ORDER BY ts) TO STDOUT WITH(FORMAT CSV,HEADER TRUE);
COMMIT;
