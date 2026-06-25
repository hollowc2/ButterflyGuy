CREATE UNIQUE INDEX IF NOT EXISTS idx_butterfly_trades_one_open_per_underlying_day
    ON butterfly_trades (underlying, trade_date)
    WHERE status = 'OPEN';
