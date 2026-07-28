-- Decision events are partitioned by underlying in dashboards and diagnostics.
-- Keep the column nullable for legacy rows and events without an asset context.
ALTER TABLE decision_log
    ADD COLUMN IF NOT EXISTS underlying TEXT;

CREATE INDEX IF NOT EXISTS idx_decision_underlying_ts
    ON decision_log (underlying, ts DESC);
