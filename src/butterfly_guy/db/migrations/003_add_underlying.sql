-- Add underlying column to butterfly_trades
ALTER TABLE butterfly_trades ADD COLUMN IF NOT EXISTS underlying TEXT NOT NULL DEFAULT 'SPX';
CREATE INDEX IF NOT EXISTS idx_butterfly_trades_underlying ON butterfly_trades (underlying);

-- Add underlying column to butterfly_candidates
ALTER TABLE butterfly_candidates ADD COLUMN IF NOT EXISTS underlying TEXT NOT NULL DEFAULT 'SPX';
CREATE INDEX IF NOT EXISTS idx_candidates_underlying ON butterfly_candidates (underlying);

-- Add underlying column to daily_risk_state and change PK to (trade_date, underlying)
ALTER TABLE daily_risk_state ADD COLUMN IF NOT EXISTS underlying TEXT NOT NULL DEFAULT 'SPX';
ALTER TABLE daily_risk_state DROP CONSTRAINT IF EXISTS daily_risk_state_pkey;
ALTER TABLE daily_risk_state ADD PRIMARY KEY (trade_date, underlying);
