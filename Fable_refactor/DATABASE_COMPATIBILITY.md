# Database Compatibility

This document captures the structural contracts for historical market-data tables used by
DB-backed replay, backtests, and Fable-style model consumers.

Source of truth:

- Migration DDL: `src/butterfly_guy/db/migrations/001_initial.sql`,
  `002_fix_greeks_precision.sql`, `004_add_chain_fields.sql`, and
  `005_add_daily_bars.sql`
- Live verification: `butterfly_timescaledb`, database `butterfly_guy`, checked
  2026-06-17 UTC

Do not treat these tables as generic OHLC or option quote abstractions. The timestamp
columns, numeric precision, nullable quote fields, and TimescaleDB hypertable boundaries
are part of the compatibility contract.

## Effective Table Contracts

### `option_chain_snapshots`

- Purpose: raw option-chain rows collected at snapshot cadence.
- Time column: `snapshot_time TIMESTAMPTZ NOT NULL`.
- TimescaleDB: hypertable on `snapshot_time`.
- Live row count at verification: `43,314,675`.
- Important query pattern: filter by `underlying`, `expiration`, and nearest
  `snapshot_time <= target_time`; for ET calendar filtering, convert
  `snapshot_time AT TIME ZONE 'America/New_York'`.

```sql
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
    spot_price      NUMERIC(10,2),
    bid_size          INTEGER,
    ask_size          INTEGER,
    rho               NUMERIC(12,6),
    intrinsic_value   NUMERIC(10,4),
    time_value        NUMERIC(10,4),
    in_the_money      BOOLEAN,
    days_to_expiration INTEGER,
    multiplier        NUMERIC(8,2),
    theoretical_value NUMERIC(10,4)
);

SELECT create_hypertable('option_chain_snapshots', 'snapshot_time', if_not_exists => TRUE);

CREATE INDEX IF NOT EXISTS idx_chain_underlying_exp
    ON option_chain_snapshots (underlying, expiration, snapshot_time DESC);

CREATE INDEX IF NOT EXISTS idx_chain_strike_type
    ON option_chain_snapshots (strike, option_type, snapshot_time DESC);
```

Live TimescaleDB also exposes this hypertable-created index:

```sql
CREATE INDEX option_chain_snapshots_snapshot_time_idx
    ON public.option_chain_snapshots USING btree (snapshot_time DESC);
```

Migration history detail: `004_add_chain_fields.sql` adds `bid_size`,
`ask_size`, `rho`, `intrinsic_value`, `time_value`, `in_the_money`,
`days_to_expiration`, `multiplier`, and `theoretical_value` with
`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`. `002_fix_greeks_precision.sql`
ensures `iv`, `delta`, `gamma`, `theta`, and `vega` are `NUMERIC(12,6)`.

### `spot_prices`

- Purpose: underlying spot ticks at collector cadence for SPX, NDX, XSP, `$VIX`, etc.
- Time column: `ts TIMESTAMPTZ NOT NULL`.
- TimescaleDB: hypertable on `ts`.
- Live row count at verification: `99,343`.

```sql
CREATE TABLE IF NOT EXISTS spot_prices (
    ts          TIMESTAMPTZ NOT NULL,
    underlying  TEXT NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    source      TEXT DEFAULT 'schwab'
);

SELECT create_hypertable('spot_prices', 'ts', if_not_exists => TRUE);
```

Live TimescaleDB indexes:

```sql
CREATE INDEX spot_prices_ts_idx
    ON public.spot_prices USING btree (ts DESC);

CREATE INDEX spot_prices_underlying_ts_idx
    ON public.spot_prices USING btree (underlying, ts DESC);
```

### `daily_bars`

- Purpose: daily OHLCV bars for previous-close and VIX regime inputs.
- Key: `(date, underlying)`.
- TimescaleDB: normal table, not a hypertable in the verified database.
- Live row count at verification: `297`.

```sql
CREATE TABLE IF NOT EXISTS daily_bars (
    date        DATE           NOT NULL,
    underlying  TEXT           NOT NULL,
    open        NUMERIC(10,4),
    high        NUMERIC(10,4),
    low         NUMERIC(10,4),
    close       NUMERIC(10,4)  NOT NULL,
    volume      BIGINT         DEFAULT 0,
    PRIMARY KEY (date, underlying)
);
```

Live primary-key index:

```sql
CREATE UNIQUE INDEX daily_bars_pkey
    ON public.daily_bars USING btree (date, underlying);
```

## Explicit Adapter Contracts for Fable 5

The live TimescaleDB tables above are the authoritative schema for this repository.
Fable 5 should read those tables directly for the first milestone. The following block
is not the live schema; it is an optional compact adapter-output shape for a future
ingestion layer that wants to expose one JSON document per chain snapshot.

Important mapping notes:

- Live `option_chain_snapshots` stores one row per option quote, not one JSON blob per
  full chain snapshot.
- Live `option_chain_snapshots.snapshot_time` maps to the Fable-facing
  `snapshot_timestamp` concept.
- Live `spot_prices.underlying` maps to the Fable-facing `symbol` concept.
- Live `spot_prices.ts` maps to the Fable-facing `timestamp` concept.
- The live database does not currently have `option_chain_snapshots.id` or
  `option_chain_snapshots.chain_data`.

```sql
-- Optional compact adapter-output shape, not the live ButterflyGuy schema.
CREATE TABLE option_chain_snapshots (
    id BIGSERIAL PRIMARY KEY,
    underlying VARCHAR(10) NOT NULL,
    snapshot_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    spot_price NUMERIC(12, 4) NOT NULL,
    chain_data JSONB NOT NULL -- Contains the raw snapshot nested by strike/type
);

CREATE TABLE spot_prices (
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    price NUMERIC(12, 4) NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);
```

Equivalent read projection from the live row-oriented schema:

```sql
SELECT
    underlying,
    snapshot_time AS snapshot_timestamp,
    spot_price,
    jsonb_object_agg(
        strike::text || ':' || option_type,
        jsonb_build_object(
            'symbol', symbol,
            'expiration', expiration,
            'strike', strike,
            'option_type', option_type,
            'bid', bid,
            'ask', ask,
            'mark', mark,
            'last', last,
            'volume', volume,
            'open_interest', open_interest,
            'iv', iv,
            'delta', delta,
            'gamma', gamma,
            'theta', theta,
            'vega', vega,
            'bid_size', bid_size,
            'ask_size', ask_size,
            'rho', rho,
            'intrinsic_value', intrinsic_value,
            'time_value', time_value,
            'in_the_money', in_the_money,
            'days_to_expiration', days_to_expiration,
            'multiplier', multiplier,
            'theoretical_value', theoretical_value
        )
        ORDER BY strike, option_type
    ) AS chain_data
FROM option_chain_snapshots
WHERE underlying = $1
  AND snapshot_time = $2
GROUP BY underlying, snapshot_time, spot_price;
```

## Raw Migration DDL

The exact migration snippets that create or alter the three compatibility tables are
included below for consumers that need to replay the project DDL.

### `001_initial.sql`: `option_chain_snapshots`

```sql
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
```

### `001_initial.sql`: `spot_prices`

```sql
CREATE TABLE IF NOT EXISTS spot_prices (
    ts          TIMESTAMPTZ NOT NULL,
    underlying  TEXT NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    source      TEXT DEFAULT 'schwab'
);

SELECT create_hypertable('spot_prices', 'ts', if_not_exists => TRUE);
```

### `002_fix_greeks_precision.sql`

```sql
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
```

### `004_add_chain_fields.sql`

```sql
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS bid_size          INTEGER;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS ask_size          INTEGER;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS rho               NUMERIC(12,6);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS intrinsic_value   NUMERIC(10,4);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS time_value        NUMERIC(10,4);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS in_the_money      BOOLEAN;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS days_to_expiration INTEGER;
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS multiplier        NUMERIC(8,2);
ALTER TABLE option_chain_snapshots ADD COLUMN IF NOT EXISTS theoretical_value NUMERIC(10,4);
```

### `005_add_daily_bars.sql`

```sql
CREATE TABLE IF NOT EXISTS daily_bars (
    date        DATE           NOT NULL,
    underlying  TEXT           NOT NULL,
    open        NUMERIC(10,4),
    high        NUMERIC(10,4),
    low         NUMERIC(10,4),
    close       NUMERIC(10,4)  NOT NULL,
    volume      BIGINT         DEFAULT 0,
    PRIMARY KEY (date, underlying)
);
```

## Anonymized Synchronized Data Slice

This sample came from a live database timestamp where the SPX option chain snapshot
and SPX spot tick have the same timestamp:

```json
{
  "spot_price": {
    "ts": "2026-06-16T19:59:06.903205Z",
    "underlying": "SPX",
    "price": "7516.23",
    "source": "schwab"
  },
  "chain_context": {
    "snapshot_time": "2026-06-16T19:59:06.903205Z",
    "underlying": "SPX",
    "expiration": "2026-06-16",
    "option_type": "CALL",
    "embedded_spot_price": "7516.23",
    "rows_at_timestamp_for_expiration": 540
  }
}
```

Three adjacent zero-DTE CALL rows from that same snapshot are shown below. Contract
symbols are redacted to preserve shape without carrying raw broker contract identifiers.

| snapshot_time | expiration | strike | type | bid | ask | mark | last | volume | open_interest | iv | delta | gamma | theta | vega | bid_size | ask_size | rho | intrinsic_value | time_value | in_the_money | dte | multiplier | theoretical_value | spot_price | symbol_redacted |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|---|
| 2026-06-16T19:59:06.903205Z | 2026-06-16 | 7490.00 | CALL | 24.7000 | 25.7000 | 25.2000 | 26.5000 | 932 | 314 | 18.997000 | 0.993000 | 0.002000 | -0.079000 | 0.011000 | 10 | 10 | 0.004000 | 25.0400 | 1.4600 | true | 0 | 100.00 | 26.4590 | 7516.23 | SPXW 999999C99999999 |
| 2026-06-16T19:59:06.903205Z | 2026-06-16 | 7495.00 | CALL | 19.7000 | 20.7000 | 20.2000 | 22.4200 | 1094 | 187 | 15.839000 | 0.992000 | 0.003000 | -0.080000 | 0.013000 | 10 | 10 | 0.004000 | 20.0400 | 2.3800 | true | 0 | 100.00 | 21.4600 | 7516.23 | SPXW 999999C99999999 |
| 2026-06-16T19:59:06.903205Z | 2026-06-16 | 7500.00 | CALL | 14.7000 | 15.7000 | 15.2000 | 15.2000 | 4521 | 1496 | 12.391000 | 0.990000 | 0.004000 | -0.080000 | 0.016000 | 10 | 10 | 0.004000 | 15.0400 | 0.1600 | true | 0 | 100.00 | 16.2500 | 7516.23 | SPXW 999999C99999999 |

Notable shape details from this slice:

- `snapshot_time` and `spot_prices.ts` can align exactly, but consumers should still
  support nearest-at-or-before joins because collector timing can drift.
- `spot_price` is duplicated inside `option_chain_snapshots` and should be treated as
  the broker chain's embedded underlying reference for that row.
- Same-day expiration appears as `days_to_expiration = 0`.
- Quote fields are nullable by schema even when this sample is fully populated.
- `volume`, `open_interest`, `bid_size`, and `ask_size` are integer-like; prices and
  Greeks are fixed-precision numeric values, not floats in PostgreSQL.

## Daily Bar Shape Example

Recent daily bars from the verified database:

| date | underlying | open | high | low | close | volume |
|---|---|---:|---:|---:|---:|---:|
| 2026-06-15 | `$VIX` | 16.7800 | 16.8500 | 15.9800 | 16.2000 | 0 |
| 2026-06-15 | SPX | 7516.7500 | 7577.9200 | 7516.7500 | 7554.2900 | 0 |
| 2026-06-12 | `$VIX` | 19.5100 | 19.8500 | 17.5900 | 17.6800 | 0 |
| 2026-06-12 | SPX | 7410.8500 | 7456.4000 | 7363.0100 | 7431.4600 | 0 |
