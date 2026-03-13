-- Fix NUMERIC(8,6) → NUMERIC(12,6) for greeks columns.
-- NUMERIC(8,6) overflows for SPX theta/vega which can exceed ±99.
-- Wrapped in a DO block so re-running is safe (idempotent).
DO $$
BEGIN
    IF (
        SELECT numeric_precision
        FROM information_schema.columns
        WHERE table_name = 'option_chain_snapshots' AND column_name = 'iv'
    ) = 8 THEN
        ALTER TABLE option_chain_snapshots
            ALTER COLUMN iv    TYPE NUMERIC(12,6),
            ALTER COLUMN delta TYPE NUMERIC(12,6),
            ALTER COLUMN gamma TYPE NUMERIC(12,6),
            ALTER COLUMN theta TYPE NUMERIC(12,6),
            ALTER COLUMN vega  TYPE NUMERIC(12,6);
    END IF;
END $$;
