-- Each database belongs to one account. account_key is the fixed literal
-- 'brokerage_account', with no derivation from an account number or broker hash.
CREATE TABLE IF NOT EXISTS account_monitor_state (
    account_key TEXT PRIMARY KEY,
    state JSONB NOT NULL DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
