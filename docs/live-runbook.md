# Live Runbook

This repo is not cleared for live-money automation until `prelivecheckout.md`
has no Critical/High safety blockers.

## Startup

1. Confirm only one service is enabled for live-money mode. NDX stays paper/research;
   XSP is allowed only for the supervised one-contract canary below.
2. Run `uv run pytest -q` and `uv run ruff check .`.
3. Run `docker compose -f infra/docker-compose.yml config >/dev/null`.
4. Check the SPX service health: `curl --fail http://127.0.0.1:8000/health`.
5. Confirm there are no OPEN DB trades unless the broker shows the same SPX legs.
6. Confirm there are no same-day unknown working SPX opening or closing orders.
   Bot-owned working orders must have a matching `broker_order_intents` row.

## XSP Canary

Do not leave the XSP canary unattended.

1. Keep `risk.max_position_size=1`, `risk.max_trades_per_day=1`, and
   `risk.max_daily_loss=50` in `configs/config_xsp.yaml`.
2. Confirm `LIVE_EXPECTED_SCHWAB_ACCOUNT_ID` matches the configured account,
   `LIVE_ACCOUNT_ALLOCATION=20000`, `LIVE_MAX_ACCOUNT_DAILY_LOSS=50`, and
   `LIVE_XSP_CANARY=true` without printing secret values.
3. Change only `execution.paper_trading` to `false`, then rebuild and restart
   only `butterfly_xsp_app` during the supervised session.
4. Stop the XSP service on any unknown status, partial fill, cancel-pending
   state, broker/DB mismatch, stale data, or loss of supervision.
5. After the order lifecycle completes, collect the redacted evidence:

```bash
uv run python src/butterfly_guy/scripts/report_broker_order_statuses.py \
  --config configs/config_xsp.yaml --underlying XSP --date YYYY-MM-DD
```

6. Restore `execution.paper_trading: true` and rebuild/restart only the XSP
   service before ending supervision.

## During Session

Watch logs and health:

```bash
docker logs -f --tail=100 butterfly_spx_app
curl --fail http://127.0.0.1:8000/health
```

Any unknown broker position/order, stale chain snapshot, DB outage, rejected
order, cancel-pending state, or partial fill means stop entries and reconcile
manually before continuing.

## Manual Flatten

There is no tested in-repo auto-flatten command yet.

1. Disable entry by keeping live mode off or stopping the affected app.
2. Use Schwab directly to close the exact option legs shown by the broker.
3. Confirm the broker is flat for those legs.
4. Compare the broker result to the OPEN row in `butterfly_trades`.
5. Only update DB state after broker flatness is confirmed.

## Rollback

1. Revert the deployed commit.
2. Rebuild only the affected service.
3. Re-check `/health`, logs, broker positions, unknown broker working orders,
   `broker_order_intents`, and OPEN DB rows.
