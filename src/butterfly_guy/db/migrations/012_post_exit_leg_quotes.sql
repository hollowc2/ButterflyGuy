-- Migration 012: keep polling a closed fly's legs until the session close.
-- Research only: lets exit-rule variants that would have exited later (confirmation
-- polls, smoothing) be replayed at monitor cadence instead of falling back to the
-- 1-minute collector. Kept apart from monitoring_leg_quotes, whose readers assume its
-- rows end at the exit.
CREATE TABLE IF NOT EXISTS post_exit_leg_quotes (
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
    fly_mark        NUMERIC(10,4)
);

SELECT create_hypertable('post_exit_leg_quotes', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_post_exit_leg_quotes_trade
    ON post_exit_leg_quotes (trade_id, ts);
