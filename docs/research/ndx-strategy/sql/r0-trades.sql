BEGIN READ ONLY;
SET LOCAL statement_timeout='45s';
COPY (SELECT id,trade_date,direction,wing_width,lower_strike,center_strike,upper_strike,entry_price,exit_price,entry_time,exit_time,exit_reason,pnl,peak_value,quantity,status,
metadata->>'paper_fill_model' AS fill_model,metadata->'entry_execution_diagnostics' AS entry_diagnostics,metadata->'exit_execution_diagnostics' AS exit_diagnostics,
metadata->>'settlement_source' AS settlement_source,metadata->>'settlement_spot' AS settlement_spot,metadata->>'entry_spot' AS entry_spot,metadata->>'vix' AS vix,
metadata->'entry_strategy' AS entry_strategy
FROM butterfly_trades WHERE underlying='NDX' AND trade_date<='2026-10-14' ORDER BY entry_time) TO STDOUT WITH(FORMAT CSV,HEADER TRUE);
COMMIT;
