# SchwabGateway order books

`GatewayOrderBookClient` gives ButterflyGuy a read-only, authenticated consumer for
SchwabGateway's venue-specific Level II snapshots. It does not place, replace, or cancel
orders and it does not read Schwab credentials or the shared token file.

The client treats depth as research data:

- `recent()` accepts only a fresh `stale=false` gateway response;
- `stream()` validates every WebSocket envelope and rejects unrequested symbols;
- `is_consolidated` must be false, because each feed is NASDAQ- or NYSE-specific;
- connection and continuity epochs are preserved for downstream gap analysis;
- authentication, authorization, capacity, feed availability, and contract failures use
  separate exception types;
- no automatic retry is performed, so a research runner can apply an explicit bounded
  backoff and record reconnect boundaries.

## Recent snapshots

```python
import os

from butterfly_guy.data.gateway_order_book import GatewayOrderBookClient


async def load_recent_aapl():
    async with GatewayOrderBookClient(
        os.environ["SCHWAB_GATEWAY_URL"],
        os.environ["SCHWAB_GATEWAY_API_KEY"],
    ) as client:
        response = await client.recent("AAPL", venue="NASDAQ", limit=100)
        return response.snapshots
```

## Live WebSocket

```python
import os

from butterfly_guy.data.gateway_order_book import GatewayOrderBookClient


async def consume_aapl():
    async with GatewayOrderBookClient(
        os.environ["SCHWAB_GATEWAY_URL"],
        os.environ["SCHWAB_GATEWAY_API_KEY"],
    ) as client:
        async for snapshot in client.stream(["AAPL"], venue="NASDAQ"):
            # Hand off to a bounded recorder or research feature pipeline.
            print(snapshot.gateway_received_at, snapshot.bids[:1], snapshot.asks[:1])
```

The API key must belong to a gateway principal with `market_data:read`. Keep the key in
the environment or the deployment's secret store; do not add it to YAML, source control,
logs, evidence manifests, or captured WebSocket payloads.

The gateway intentionally bounds subscriber capacity and each subscriber queue. A slow
consumer may skip intermediate snapshots, so downstream research must use
`connection_id`, `continuity_epoch`, and `sequence` when present and must never infer a
lossless tape from arrival count alone.
