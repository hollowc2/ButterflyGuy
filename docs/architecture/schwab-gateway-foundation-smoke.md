# Schwab Gateway Foundation Smoke Test

## Result

**PASS (local-process proof); Docker runtime proof deferred for deployment safety.**

The read-only foundation was exercised on 2026-08-03 from the isolated worktree
`/tmp/butterfly-schwab-gateway` on branch `codex/schwab-gateway-foundation`. The
test did not read Schwab credentials, token files, account identifiers, or live
configuration, and it did not call Schwab or expose an order endpoint.

## Safety Boundary

- The existing repository checkout and production deployment were not modified.
- The local Docker daemon was disabled and inactive. It was deliberately not started,
  because doing so could restart unrelated `unless-stopped` containers.
- Port 8010 was already owned by an existing SSH process and was left untouched. The
  proof bound only to `127.0.0.1:18010`.
- The runner used the explicit `--demo` upstream, which returns unmistakable fake data
  carrying the `demo_data_not_for_trading` quality flag.
- `SCHWAB_GATEWAY_ORDER_WRITES_ENABLED` remained `false`; the application has no order
  route.

## Temporary Authentication

One random smoke-test API key was generated. The raw key and curl configuration were
stored in mode-0600 temporary files; the gateway received only its SHA-256 digest and
the `market_data:read` capability. Logs contained the bounded caller ID
`butterfly-guy-smoke`, never the key or digest. All three temporary secret-bearing files
were deleted after shutdown.

## Observed Contract

| Probe | Expected | Observed |
| --- | --- | --- |
| `GET /health` | Process liveness | HTTP 200, `status=ok` at `2026-08-03T21:13:23.975581Z` |
| `GET /ready` | Foundation readiness | HTTP 200, `status=ready` at `2026-08-03T21:13:26.002621Z` |
| Unauthenticated `GET /v1/quotes?symbols=AAPL` | Reject anonymous caller | HTTP 401, `authentication_required` |
| Authenticated `GET /v1/quotes?symbols=AAPL,MSFT` | Versioned fake quote response | HTTP 200; AAPL and MSFT in request order, `source=foundation_demo` |
| Authenticated `POST /v1/orders` | No order surface | HTTP 404 |
| `GET /metrics` after missing order route | Correct audit status | `operation=unknown,status=404` incremented once |

Nullable quote fields remained `null`; no missing market value was silently converted
to zero. The demo mark of 100.0 is explicitly marked non-trading test data.

## Defect Found During Proof

The first run returned HTTP 404 for the absent order route but recorded it as status 500
in the request metric. The audit middleware now classifies `aiohttp.web.HTTPException`
using its actual HTTP status. A contract regression assertion verifies that the absent
order route is returned and metered as 404.

## Shutdown and Residual State

The localhost process exited cleanly before the temporary key material was removed.
No live container, database, Schwab token, Schwab session, account, position, or order
was read or changed. Compose rendering remains covered separately; starting the Docker
daemon and running the overlay should occur only on a host where container restart
impact has first been inventoried.
