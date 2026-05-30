-- High-frequency quotes for legs of open positions only.
-- This preserves live monitor marks for replay without storing full chains every poll.
CREATE TABLE IF NOT EXISTS monitoring_leg_quotes (
    ts              TIMESTAMPTZ NOT NULL,
    trade_id        INTEGER NOT NULL REFERENCES butterfly_trades(id) ON DELETE CASCADE,
    underlying      TEXT NOT NULL,
    expiration      DATE NOT NULL,
    strike          NUMERIC(10,2) NOT NULL,
    option_type     TEXT NOT NULL,
    bid             NUMERIC(10,4),
    ask             NUMERIC(10,4),
    mark            NUMERIC(10,4),
    symbol          TEXT,
    spot_price      NUMERIC(10,2),
    fly_mark        NUMERIC(10,4),
    peak_value      NUMERIC(10,4),
    drawdown_pct    NUMERIC(8,4)
);

SELECT create_hypertable('monitoring_leg_quotes', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_monitoring_leg_quotes_lookup
    ON monitoring_leg_quotes (underlying, expiration, strike, option_type, ts DESC);

CREATE INDEX IF NOT EXISTS idx_monitoring_leg_quotes_trade
    ON monitoring_leg_quotes (trade_id, ts DESC);
