-- Migration 011: record when collected quotes were made, not only when collection started.
-- Idempotent. New hypertable columns are nullable with no default, so on the compressed
-- option_chain_snapshots and spot_prices hypertables the ALTER is metadata-only.
-- snapshot_time keeps its meaning: the collector's stamp at the start of a pass.

ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS quote_event_ts TIMESTAMPTZ;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS quote_age_s    REAL;

ALTER TABLE spot_prices ADD COLUMN IF NOT EXISTS event_ts TIMESTAMPTZ;
ALTER TABLE spot_prices ADD COLUMN IF NOT EXISTS age_s    REAL;

-- One row per collected snapshot (scheduled_at is filled once collection runs on a fixed
-- minute grid, NULL before).
CREATE TABLE IF NOT EXISTS chain_snapshot_meta (
    snapshot_time              TIMESTAMPTZ NOT NULL,
    underlying                 TEXT        NOT NULL,
    expiration                 DATE        NOT NULL,
    scheduled_at               TIMESTAMPTZ,
    spot_fetch_started_at      TIMESTAMPTZ,
    spot_fetch_completed_at    TIMESTAMPTZ,
    vix_fetch_started_at       TIMESTAMPTZ,
    vix_fetch_completed_at     TIMESTAMPTZ,
    chain_fetch_started_at     TIMESTAMPTZ,
    chain_fetch_completed_at   TIMESTAMPTZ,
    chain_gateway_received_at  TIMESTAMPTZ,
    chain_event_ts             TIMESTAMPTZ,
    chain_age_s                REAL,
    chain_source               TEXT,
    chain_flags                TEXT[],
    spot_event_ts              TIMESTAMPTZ,
    spot_age_s                 REAL,
    vix_event_ts               TIMESTAMPTZ,
    vix_age_s                  REAL,
    contracts_delivered        INTEGER,
    contracts_stored           INTEGER,
    contracts_omitted          INTEGER,
    omitted                    JSONB,
    strikes_within_spot_range  INTEGER,
    PRIMARY KEY (snapshot_time, underlying, expiration)
);
