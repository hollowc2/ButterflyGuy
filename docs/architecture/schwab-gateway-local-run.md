# Schwab Gateway Foundation: Local Run

> **Historical embedded-service instructions:** The local demo, key-management, and Compose
> workflow moved to [`hollowc2/SchwabGateway`](https://github.com/hollowc2/SchwabGateway). The
> commands below are preserved as extraction history and no longer run from Butterfly Guy.

This is an isolated fake-data smoke test. It does not read `.env`, a Schwab token, an
account ID, or Schwab credentials, and it has no account/order routes. Do not use its demo
quote for trading.

## Prepare an internal key file

Copy `configs/schwab_gateway_keys.example.json` to the ignored path
`secrets/schwab-gateway-keys.json`. Replace the all-zero placeholder digest with the
lowercase SHA-256 digest of a newly generated internal API key, and replace the other placeholder
digests with two different generated-key digests. Set the file mode to `0600`. Keep all three raw
keys outside Git and give each only to its named client. Do not share one key between applications.

The three configured identities are `butterfly-guy` (protected), `equity-scanner` (background),
and `afterhours-lab` (background). The default protected/background capacities are bounded local
concurrency controls and do not represent a measured Schwab quota.

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
SCHWAB_GATEWAY_UID="$(id -u)" SCHWAB_GATEWAY_GID="$(id -g)" \
  docker compose -f infra/docker-compose.gateway.yml \
  --profile gateway-foundation up --build schwab_gateway_foundation
```

The UID/GID override makes the unprivileged container process match the owner of the
mode-`0600` key file. Omitting it retains the image default `1001:1001`, which is appropriate
only when the mounted file is owned by that numeric identity. Do not loosen the key file to
group/world-readable as a workaround.

This overlay creates only `butterfly_schwab_gateway_foundation`; it does not reference,
recreate, stop, or share a network with the existing SPX/NDX/XSP services. It binds the
demo endpoint to host loopback and mounts only the hashed internal-key file. It mounts no
project `.env`, `tokens.json`, account ID, or Schwab credential. A container health check
reports healthy only after the process loads authentication configuration and serves
`/ready`.

Stop it with the same file/profile and service name. Do not use the production Compose file
for this proof.
