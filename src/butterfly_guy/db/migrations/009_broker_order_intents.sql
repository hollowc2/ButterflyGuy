CREATE TABLE IF NOT EXISTS broker_order_intents (
    id                  BIGSERIAL PRIMARY KEY,
    underlying          TEXT NOT NULL,
    trade_date          DATE NOT NULL,
    trade_id            INTEGER REFERENCES butterfly_trades(id) ON DELETE SET NULL,
    side                TEXT NOT NULL CHECK (side IN ('ENTRY', 'EXIT')),
    status              TEXT NOT NULL,
    broker_order_id     TEXT,
    limit_price         NUMERIC(10,4),
    quantity            INTEGER NOT NULL DEFAULT 1,
    order_spec          JSONB NOT NULL DEFAULT '{}'::jsonb,
    candidate_snapshot  JSONB NOT NULL DEFAULT '{}'::jsonb,
    last_broker_status  TEXT,
    raw_broker_payload  JSONB,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_broker_order_intents_order_id
    ON broker_order_intents (broker_order_id)
    WHERE broker_order_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_broker_order_intents_active
    ON broker_order_intents (underlying, trade_date, status);

CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_order_intents_active_entry
    ON broker_order_intents (underlying, trade_date)
    WHERE side = 'ENTRY'
      AND status NOT IN ('FILLED', 'CANCELED', 'REJECTED', 'EXPIRED');

CREATE UNIQUE INDEX IF NOT EXISTS idx_broker_order_intents_active_exit
    ON broker_order_intents (trade_id)
    WHERE side = 'EXIT'
      AND trade_id IS NOT NULL
      AND status NOT IN ('FILLED', 'CANCELED', 'REJECTED', 'EXPIRED');
