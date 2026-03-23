-- Migration 004: Add additional option chain fields
-- Idempotent: uses ADD COLUMN IF NOT EXISTS

ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS bid_size          INTEGER;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS ask_size          INTEGER;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS rho               NUMERIC(12,6);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS intrinsic_value   NUMERIC(10,4);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS time_value        NUMERIC(10,4);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS in_the_money      BOOLEAN;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS days_to_expiration INTEGER;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS multiplier        NUMERIC(8,2);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS theoretical_value NUMERIC(10,4);
