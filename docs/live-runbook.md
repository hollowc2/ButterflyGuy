# Live Runbook

This repo is not cleared for live-money automation until `prelivecheckout.md`
has no Critical/High safety blockers.

## Startup

1. Confirm only SPX is enabled for live-money mode. NDX and XSP stay paper/research.
2. Run `uv run pytest -q` and `uv run ruff check .`.
3. Run `docker compose -f infra/docker-compose.yml config >/dev/null`.
4. Check the SPX service health: `curl --fail http://127.0.0.1:8000/health`.
5. Confirm there are no OPEN DB trades unless the broker shows the same SPX legs.
6. Confirm there are no same-day working SPX opening or closing orders.

## During Session

Watch logs and health:

```bash
docker logs -f --tail=100 butterfly_spx_app
curl --fail http://127.0.0.1:8000/health
```

Any unknown broker position, stale chain snapshot, DB outage, rejected order, or
partial fill means stop entries and reconcile manually before continuing.

## Manual Flatten

There is no tested in-repo auto-flatten command yet.

1. Disable entry by keeping live mode off or stopping the SPX app.
2. Use Schwab directly to close the exact SPX option legs shown by the broker.
3. Confirm the broker is flat for those legs.
4. Compare the broker result to the OPEN row in `butterfly_trades`.
5. Only update DB state after broker flatness is confirmed.

## Rollback

1. Revert the deployed commit.
2. Rebuild only the affected service.
3. Re-check `/health`, logs, broker positions, broker working orders, and OPEN DB rows.
