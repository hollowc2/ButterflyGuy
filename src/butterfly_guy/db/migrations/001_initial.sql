-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Option chain snapshots hypertable
CREATE TABLE IF NOT EXISTS option_chain_snapshots (
    snapshot_time   TIMESTAMPTZ NOT NULL,
    underlying      TEXT NOT NULL,
    expiration      DATE NOT NULL,
    strike          NUMERIC(10,2) NOT NULL,
    option_type     TEXT NOT NULL,  -- 'CALL' or 'PUT'
    bid             NUMERIC(10,4),
    ask             NUMERIC(10,4),
    mark            NUMERIC(10,4),
    last            NUMERIC(10,4),
    volume          INTEGER DEFAULT 0,
    open_interest   INTEGER DEFAULT 0,
    iv              NUMERIC(12,6),
    delta           NUMERIC(12,6),
    gamma           NUMERIC(12,6),
    theta           NUMERIC(12,6),
    vega            NUMERIC(12,6),
    symbol          TEXT,
    spot_price      NUMERIC(10,2)
);

SELECT create_hypertable('option_chain_snapshots', 'snapshot_time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_chain_underlying_exp
    ON option_chain_snapshots (underlying, expiration, snapshot_time DESC);

CREATE INDEX IF NOT EXISTS idx_chain_strike_type
    ON option_chain_snapshots (strike, option_type, snapshot_time DESC);

-- Spot prices hypertable
CREATE TABLE IF NOT EXISTS spot_prices (
    ts          TIMESTAMPTZ NOT NULL,
    underlying  TEXT NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    source      TEXT DEFAULT 'schwab'
);

SELECT create_hypertable('spot_prices', 'ts', if_not_exists => TRUE);

-- Butterfly trades table (full lifecycle)
CREATE TABLE IF NOT EXISTS butterfly_trades (
    id              SERIAL PRIMARY KEY,
    trade_date      DATE NOT NULL,
    direction       TEXT NOT NULL,  -- 'CALL' or 'PUT'
    wing_width      INTEGER NOT NULL,
    center_strike   NUMERIC(10,2) NOT NULL,
    lower_strike    NUMERIC(10,2) NOT NULL,
    upper_strike    NUMERIC(10,2) NOT NULL,
    entry_price     NUMERIC(10,4) NOT NULL,
    entry_time      TIMESTAMPTZ NOT NULL,
    exit_price      NUMERIC(10,4),
    exit_time       TIMESTAMPTZ,
    exit_reason     TEXT,
    pnl             NUMERIC(10,4),
    peak_value      NUMERIC(10,4),
    lower_symbol    TEXT,
    center_symbol   TEXT,
    upper_symbol    TEXT,
    quantity        INTEGER DEFAULT 1,
    status          TEXT DEFAULT 'OPEN',  -- OPEN, CLOSED, EXPIRED
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_butterfly_trades_date ON butterfly_trades (trade_date);
CREATE INDEX IF NOT EXISTS idx_butterfly_trades_status ON butterfly_trades (status);

-- Decision log (event-based JSONB logging)
CREATE TABLE IF NOT EXISTS decision_log (
    id          SERIAL PRIMARY KEY,
    ts          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type  TEXT NOT NULL,
    data        JSONB NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_decision_ts ON decision_log (ts DESC);
CREATE INDEX IF NOT EXISTS idx_decision_type ON decision_log (event_type);

-- Butterfly candidates hypertable (all scanned, not just traded)
CREATE TABLE IF NOT EXISTS butterfly_candidates (
    scan_time       TIMESTAMPTZ NOT NULL,
    direction       TEXT NOT NULL,
    wing_width      INTEGER NOT NULL,
    center_strike   NUMERIC(10,2) NOT NULL,
    lower_strike    NUMERIC(10,2) NOT NULL,
    upper_strike    NUMERIC(10,2) NOT NULL,
    cost            NUMERIC(10,4) NOT NULL,
    max_profit      NUMERIC(10,4) NOT NULL,
    reward_risk     NUMERIC(10,4) NOT NULL,
    lower_be        NUMERIC(10,2),
    upper_be        NUMERIC(10,2),
    distance_from_spot NUMERIC(10,2),
    spot_price      NUMERIC(10,2),
    selected        BOOLEAN DEFAULT FALSE
);

SELECT create_hypertable('butterfly_candidates', 'scan_time', if_not_exists => TRUE);

-- Daily risk state
CREATE TABLE IF NOT EXISTS daily_risk_state (
    trade_date      DATE PRIMARY KEY,
    trade_count     INTEGER DEFAULT 0,
    realized_pnl    NUMERIC(10,4) DEFAULT 0,
    max_loss_hit    BOOLEAN DEFAULT FALSE,
    halted          BOOLEAN DEFAULT FALSE
);
