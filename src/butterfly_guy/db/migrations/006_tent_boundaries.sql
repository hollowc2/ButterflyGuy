-- Dynamic profit tent boundary tracking (shrinking intraday breakevens)
CREATE TABLE IF NOT EXISTS tent_boundaries (
    ts          TIMESTAMPTZ NOT NULL,
    underlying  TEXT NOT NULL,
    lower_tent  NUMERIC(10,2),
    upper_tent  NUMERIC(10,2)
);

SELECT create_hypertable('tent_boundaries', 'ts', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_tent_underlying
    ON tent_boundaries (underlying, ts DESC);
