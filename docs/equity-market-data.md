# Equity candles and order-book recording

ButterflyGuy can backfill recent one-minute equity candles from Schwab and can
record raw Schwab streaming messages for later review. These tools are read-only:
they do not place, replace, or cancel orders.

## Historical limitation

Schwab price history can be requested after a session and includes OHLCV candles.
Level II is different: NYSE and Nasdaq book services are live snapshots. They are
not exposed by Schwab or Yahoo as a historical replay endpoint. The recorder must
therefore be running while the market is open.

The installed `schwab-py` version supports:

- one-minute `CHART_EQUITY` updates,
- Level I equity quote updates,
- NYSE and Nasdaq Level II book snapshots.

It does not expose a separate equity time-and-sales subscription. Level I messages
include the latest trade price, size, venue, and timestamp, but those state updates
must not be described as a complete tape.

Level II messages are also venue-specific, not a guaranteed consolidated view of
every displayed and hidden order in the U.S. market.

## Backfill candles

From the repository root:

```bash
uv run python -m butterfly_guy.scripts.backfill_equity_candles BMNR 2026-07-23
```

The default output is:

```text
data/equity_market_data/BMNR/2026-07-23/candles_1m.json
```

The file contains source metadata plus raw Schwab candle objects sorted by their
millisecond timestamps. Re-running the command replaces that session snapshot.

## Record a future BMNR session

Start the recorder before the desired premarket/opening window:

```bash
uv run python -m butterfly_guy.scripts.record_equity_market_data BMNR --venue nyse
```

Stop it with `Ctrl-C`. For a bounded connectivity test:

```bash
uv run python -m butterfly_guy.scripts.record_equity_market_data \
  BMNR --venue nyse --duration-seconds 60
```

Each Schwab service is appended to its own JSONL file:

```text
data/equity_market_data/BMNR/YYYY-MM-DD/chart_equity.jsonl
data/equity_market_data/BMNR/YYYY-MM-DD/level_one_equity.jsonl
data/equity_market_data/BMNR/YYYY-MM-DD/nyse_book.jsonl
data/equity_market_data/BMNR/YYYY-MM-DD/run-HHMMSS.json
```

Every line preserves the raw relabeled Schwab message and adds `received_at`,
`symbol`, `kind`, `source`, and `schema_version`. The run manifest records received,
written, and dropped message counts.

## Operational caution

Run the recorder as a supervised, separate process until a complete session proves
stream stability and token behavior. Do not start multiple recorders for the same
account and token file. The existing trading services use Schwab HTTP APIs; the
recorder adds one authenticated WebSocket session but does not change their
strategy or execution paths.

The equity report's current depth background is explicitly labeled schematic. It
does not consume these JSONL files yet. A later integration should only display
Level II when the requested symbol and chart time range have matching recorded
events.
