# Schwab Gateway Foundation: Local Run

This is an isolated fake-data smoke test. It does not read `.env`, a Schwab token, an
account ID, or Schwab credentials, and it has no account/order routes. Do not use its demo
quote for trading.

## Prepare an internal key file

Copy `configs/schwab_gateway_keys.example.json` to the ignored path
`secrets/schwab-gateway-keys.json`. Replace the all-zero placeholder digest with the
lowercase SHA-256 digest of a newly generated internal API key and make the file non-writable
by group/other. Keep the raw key outside Git and pass it only to the client.

## Run locally

```bash
SCHWAB_GATEWAY_INTERNAL_KEYS_PATH=secrets/schwab-gateway-keys.json \
uv run python -m butterfly_guy.scripts.run_schwab_gateway --demo
```

The default bind is `127.0.0.1:8010`. Safe unauthenticated probes:

```bash
curl --fail http://127.0.0.1:8010/health
curl --fail http://127.0.0.1:8010/ready
```

`/v1/quotes` requires `X-Internal-API-Key` and returns data marked
`demo_data_not_for_trading`.

## Run the separate Compose proof

```bash
docker compose -f infra/docker-compose.gateway.yml \
  --profile gateway-foundation up --build schwab_gateway_foundation
```

This overlay creates only `butterfly_schwab_gateway_foundation`; it does not reference,
recreate, stop, or share a network with the existing SPX/NDX/XSP services. It binds the
demo endpoint to host loopback and mounts only the hashed internal-key file. It mounts no
project `.env`, `tokens.json`, account ID, or Schwab credential.

Stop it with the same file/profile and service name. Do not use the production Compose file
for this proof.
