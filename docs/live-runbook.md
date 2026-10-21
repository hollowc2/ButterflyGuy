# Live Runbook

Paper is the default. SPX real-money launch requires Gate A in
[SPX go-live readiness](spx-go-live.md) and approval of the exact deployment.
NDX and XSP remain paper during this launch. The historical XSP canary procedure
below is retained for reference; it is not another launch requirement.

## Startup

1. Confirm `SCHWAB_GATEWAY_TOKEN_DIR` is present in the Compose interpolation environment
   (normally `infra/.env`) and resolves to the dedicated absolute host directory containing
   `tokens.json`. It must name the directory, not the document or repository root. Do not print
   token or credential values. The variable is required for the trading stack independently of
   the standalone SchwabGateway service.
2. Confirm only one service is enabled for live-money mode. NDX stays paper/research;
   XSP is allowed only for the supervised one-contract canary below.
3. Run `uv run pytest -q` and `uv run ruff check .`.
4. Run `docker compose -f infra/docker-compose.yml config >/dev/null`.
5. Check the SPX service health: `curl --fail http://127.0.0.1:8000/health`.
6. Confirm there are no OPEN DB trades unless the broker shows the same SPX legs.
7. Confirm there are no same-day unknown working SPX opening or closing orders.
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

## SPX live: one contract

Gate A must be signed off before the first order. The current
[go/no-go record](research/spx-go-no-go-2026-10-20.md) says **NO-GO**. Neither this
runbook nor the existence of a Compose overlay authorizes deployment or an order.

1. Keep `configs/config.yaml` frozen. The final overlay,
   `infra/docker-compose.spx-live.yml`, overrides only SPX to direct market data,
   `paper_trading=false`, and `allow_live_trading=true`. The base file followed by
   `infra/docker-compose.gateway-paper-cutover.yml` still supplies NDX/XSP paper
   gateway settings. Apply the live overlay **last**. Replace `app_spx` in place;
   never start a second live SPX service or a separate Compose project.
2. Use the tested immutable image ID in `BUTTERFLY_SPX_LIVE_IMAGE`. Pin
   `LIVE_EXPECTED_SCHWAB_ACCOUNT_ID` independently from the reviewed account
   record; never derive it from `SCHWAB_ACCOUNT_ID` in a wrapper. Require the
   options approval for index spreads and $20,000 allocation. Confirm
   `LIVE_ACCOUNT_ALLOCATION=20000`, `LIVE_MAX_ACCOUNT_DAILY_LOSS=500`,
   `risk.max_daily_loss=500`, `max_position_size=1`, and `max_trades_per_day=1`.
   The startup guard rejects mismatches, NDX live, and gateway live market data.
3. Corey supervises all ten Stage 1 trades during market hours. In both live
   stages, name the reachable operator in `LIVE_SUPERVISOR` and set
   `LIVE_SUPERVISION_UNTIL` to an ISO timestamp **with UTC offset**, on that
   session date, through its cash close. Example format:
   `2026-10-20T16:30:00-04:00`. Renew it each session. The runtime checks the
   attestation at startup and before entry; this does not prove a phone is
   reachable. Continue supervision until orders and settlement reconcile even
   if that extends beyond the attested timestamp. If nobody can cover the whole
   holding window, keep paper mode.
4. `entry.live_require_leg_bids` remains **false**, the frozen default. A zero
   bid on a purchased wing alone is not evidence that the complex limit cannot
   execute. Enabling this filter would change eligible entries relative to E0;
   it needs a new cohort. Executable leg prices, the debit cap, and broker state
   checks still apply. Require review of this choice before Gate A is signed.
5. Review the existing four $0.10 entry steps, 20-second retry interval and
   300-second timeout against contemporaneous SPX spreads. Save timestamps,
   selected spread bid/ask, each limit, cancellations, and actual fills. Do not
   change the ladder to force a fill. Code rounds SPX limits to $0.05, but that
   is not broker acceptance proof. Use a supported Schwab preview if available;
   otherwise the first approved supervised order is the acceptance test.
6. On the exact release, run the full tests and Ruff, then render the exact
   Compose argv with `config --quiet`. Use protected env files; do not print
   rendered configuration containing secrets. Follow the Deploy section for
   the image, flatness checks, uniqueness check and rollback record. After
   startup, require `/health`, `/ready`, the direct read path and effective
   live mode in the deployment evidence. A successful config render alone
   cannot prove authenticated startup.
7. After every session, compare actual Schwab executions and cash settlements
   with `butterfly_trades`, `broker_order_intents`, `daily_risk_state` and
   `decision_log`. No unknown statuses may remain. A cash settlement must use
   broker transaction evidence; manual DB edits are not a successful M10 test.
   Save the redacted reporter output:

   ```bash
   python -m butterfly_guy.scripts.report_broker_order_statuses \
     --config configs/config.yaml --underlying SPX --date YYYY-MM-DD
   ```

8. Complete ten clean supervised trades for Gate B, then twenty additional
   clean routine trades for Gate C. Keep one contract and one trade/day in
   both stages. Record each trade's broker execution evidence and stressed
   cost comparison. Gate C requires all thirty to reconcile with no manual
   DB edits and average execution costs no worse than the registered bid/ask
   plus $0.05 adverse slippage per option contract per executed side. Include
   fees consistently; cash settlement has no closing execution cost.

## SPX kill procedure and stop rules

Any unknown status, partial fill, cancel-pending state, broker/DB mismatch,
stale chain, missed critical phone alert, or loss of supervision stops live
entries. Do not wait for a second incident or for the daily loss limit.

First latch today's halt and audit the incident in the running SPX container:

```bash
docker exec butterfly_spx_app python -m butterfly_guy.scripts.halt_live_entries \
  --config configs/config.yaml --reason 'INCIDENT-ID: stop-rule reason'
```

This commits `daily_risk_state.halted=true` and a `live_entry_halted` audit event
in one transaction. It does not set a fictitious loss, cancel an order, or
flatten. In-flight orders still need operator attention. The entry risk check
also runs before every live submission under the existing entry lock. Automated
broker/settlement/stale-chain stops exit the entry loop; a broker mismatch
latches its gate for the lifetime of that process, even if later reads agree.
Monitoring and reconciliation continue while the operator takes control.

Once the operator is watching the position directly in Schwab, stop the app:

```bash
docker stop butterfly_spx_app
```

If the DB halt fails or the app is unresponsive, take broker control and stop
the app immediately. Its live overlay uses `restart: "no"`. Follow Manual
Flatten below for working orders and positions. Never assume stopping a
container canceled its broker orders or closed its position.

Reconcile and write an incident record, then return SPX to paper with a targeted,
approved deployment using the existing gateway-paper/release-image overlays
**without** the SPX live overlay. Confirm effective `paper_trading=true`,
`allow_live_trading=false`, `/ready`, no duplicate SPX runtime, and broker/DB
flatness. Preserve NDX/XSP images and services. Never clear the halt or edit
trade/order rows just to resume live. The DB flag is daily, not a permanent
cross-session kill switch: keep the live container stopped until a reviewed
re-entry is approved. Restart the affected stage's clean-trade count at zero.
Previously completed stages need not be repeated. A failure at the registered
60-trade early-failure review uses this same return-to-paper procedure.

## SPX credentials and alert coverage

Reserve **Saturday 10:00 America/Los_Angeles** for Corey's interactive weekly
Schwab reauthorization, outside market hours. This is the operating schedule;
calendar installation and the owner/browser action remain readiness tasks.
Use the established token-owner renewal procedure, preserving shared token
storage and automatic consumer reloads. Do not introduce a second token file
or rewrite credentials as part of a deployment.

The shared gateway's `schwab_gateway_refresh_token_expires_timestamp_seconds`
and `infra/alerts.yml` (in SchwabGateway) provide expiry warning within 24 hours.
Before Gate A, verify that rule is loaded and its route reaches the phone used
for live supervision. Check direct SPX authentication after renewal as well.
An accepted Alertmanager HTTP request is not end-to-end phone delivery. Arrange
an explicitly approved critical-alert drill, record the phone receipt and
acknowledgment time, and halt live on a missed alert. Do not send a real alert
as part of an offline test.

## During Session

Watch logs and health:

```bash
docker logs -f --tail=100 butterfly_spx_app
curl --fail http://127.0.0.1:8000/health
```

Any unknown broker position/order, stale chain snapshot, DB outage, rejected
order, cancel-pending state, or partial fill means stop entries and reconcile
manually before continuing.

Do not increase quantity, repeat orders, or manipulate limits to manufacture a
partial fill. Real partial/cancel-pending payloads are opportunistic evidence;
the synthetic fail-closed tests are the pre-live safety gate.

## Manual Flatten

There is intentionally no in-repo auto-flatten command. The operator owns the
broker action; the app only supplies read-only evidence afterward.

1. Announce manual control and disable new entry. Do not stop monitoring until
   the operator is actively watching the position in Schwab.
2. In Schwab, record the exact option symbols, signed quantities, and working
   orders. Independently compare them with the OPEN `butterfly_trades` row.
3. Cancel only confirmed working orders, then re-check their terminal status.
4. Submit the exact closing complex order in Schwab with human confirmation.
5. Confirm broker flatness and no working child/parent orders in Schwab.
6. Run the read-only status reporter and reconcile `broker_order_intents`,
   `butterfly_trades`, `daily_risk_state`, and `decision_log`. Never edit the DB
   merely to make it agree with an assumed broker outcome.

The 2026-07-14 tabletop passed these steps. On 2026-07-16 the supervised broker
action also passed: the complex close filled, Schwab became flat, and the runtime
failed closed because the external order had no bot-owned EXIT intent. After
reverification, the DB/risk/audit state was reconciled atomically and XSP was
rebuilt paper-only with flat `/ready` proof. Evidence is in
`reports/xsp_manual_flatten_2026-07-16.md`.

## Token Recovery

1. Treat failed authentication as not ready and keep new entry disabled.
2. Confirm open positions and working orders from Schwab before touching a
   service. If either exists, maintain manual supervision.
3. Re-authenticate interactively with `uv run python tools/auth_init.py`; never
   print or copy the token contents.
4. Verify only file ownership/permissions and the expected mounted path.
5. Run `uv run python tools/schwab_token_keepalive.py` and require a successful
   read-only quote before considering a restart.
6. When broker/DB state is flat and reconciled, restart only the affected
   service and require `/ready`, logs, and a read-only broker status check to
   pass before entry is enabled.

The 2026-07-14 recovery tabletop passed. Real re-authentication requires the
owner/browser; mocked expiry and external-alert delivery remain separate tests.

## Deploy

Deploys are manual, on Helios, for one exact commit. No CI runner touches the
host, and the apps do not run the `/opt/butterflyguy` checkout HEAD.

1. Wait for `CI / validate` and `Database Smoke / timescaledb` to pass on the
   commit. Deploy outside market hours, and only the services that changed.
2. Confirm flat: no `butterfly_trades` rows with `status = 'OPEN'`, no
   non-terminal `broker_order_intents`, no live `trade_id` monitor lines in
   `docker logs` (the DB check alone has missed a monitored trade), and
   `docker exec -i butterfly_spx_app python - < tools/deploy_broker_flat_check.py`
   exits 0 (Schwab shows no positions or active orders, read-only).
3. SPX/NDX: `git archive` the commit into a release snapshot, build
   `butterflyguy:release-<sha7>`, write a rollback compose override pinning the
   current image digests, then `up -d --no-deps --no-build --pull never` the
   changed services with a release-image override.
4. XSP runs from `/opt/butterflyguy-releases/<sha7>/`; reuse the argv, rollback
   argv and env from the latest release's `deployment/prepared-deployment.json`.
5. `configs/config.yaml` is bind-mounted from the checkout, so a config change
   ships only by updating that file there. The host cron jobs (report card,
   performance page, realized-vs-implied) run the checkout's code against those
   same configs, so fast-forward the checkout to the deployed commit
   (`git merge --ff-only`, then `uv sync --frozen --no-dev`) whenever a config gains a
   key. A new key with stale checkout code breaks every cron job in
   `load_config()` (2026-10-05 → 10-16). Confirm with
   `.venv/bin/python tools/check_runtime_configs.py`, which also runs daily at
   13:00 UTC under `tools/cron_guard.py` and alerts Discord on failure.
6. Check `docker logs` for `migration_complete` and the expected startup events.
   After hours `/ready` stays 503 (`gateway_market_data_unavailable`) until the
   next open; that is expected.

## Rollback

1. Revert the deployed commit.
2. Rebuild only the affected service.
3. Re-check `/health`, logs, broker positions, unknown broker working orders,
   `broker_order_intents`, and OPEN DB rows.
