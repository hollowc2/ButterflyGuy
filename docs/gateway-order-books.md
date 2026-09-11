# SchwabGateway order books

`schwab_gateway_sdk.GatewayMarketDataClient` is the sole typed HTTP and WebSocket
consumer for SchwabGateway's venue-specific Level II snapshots. ButterflyGuy does not
maintain a second transport or model implementation. The SDK does not place, replace,
or cancel orders and it does not read Schwab credentials or the shared token file.

The client treats depth as research data:

- `get_recent_order_book()` accepts only a fresh `stale=false` gateway response;
- `stream_order_books()` validates every WebSocket envelope and rejects unrequested
  symbols;
- `is_consolidated` must be false, because each feed is NASDAQ- or NYSE-specific;
- connection and continuity epochs are preserved for downstream gap analysis;
- authentication, authorization, capacity, feed availability, and contract failures use
  separate exception types;
- no automatic retry is performed, so a research runner can apply an explicit bounded
  backoff and record reconnect boundaries.

## Recent snapshots

```python
import os

from schwab_gateway_sdk import GatewayMarketDataClient


async def load_recent_aapl():
    async with GatewayMarketDataClient(
        os.environ["SCHWAB_GATEWAY_URL"],
        os.environ["SCHWAB_GATEWAY_API_KEY"],
    ) as client:
        response = await client.get_recent_order_book(
            "AAPL", venue="NASDAQ", limit=100
        )
        return response.snapshots
```

## Live WebSocket

```python
import os

from schwab_gateway_sdk import GatewayMarketDataClient


async def consume_aapl():
    async with GatewayMarketDataClient(
        os.environ["SCHWAB_GATEWAY_URL"],
        os.environ["SCHWAB_GATEWAY_API_KEY"],
    ) as client:
        async with client.stream_order_books(
            ["AAPL"], venue="NASDAQ"
        ) as snapshots:
            async for snapshot in snapshots:
                # Hand off to a bounded recorder or research feature pipeline.
                print(
                    snapshot.gateway_received_at,
                    snapshot.bids[:1],
                    snapshot.asks[:1],
                )
```

The API key must belong to a gateway principal with `market_data:read`. Keep the key in
the environment or the deployment's secret store; do not add it to YAML, source control,
logs, evidence manifests, or captured WebSocket payloads.

The gateway intentionally bounds subscriber capacity and each subscriber queue. A slow
consumer may skip intermediate snapshots, so downstream research must use
`connection_id`, `continuity_epoch`, and `sequence` when present and must never infer a
lossless tape from arrival count alone.
