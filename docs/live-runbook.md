# Live Runbook

Treat SPX, NDX, and XSP as paper-only unless the owner explicitly authorizes a supervised live
canary.

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

## SPX Live: Bot Halted With An Open Fly

A halt stops the live bot's monitor and entries; it sends no more orders.

- **Releases from `audit/spx-live-halt-20261119` on:** a live halt exits the process
  with code 1. Docker (`on-failure:3`) restarts it, and the startup reconcile decides.
  - If every bot order is final and the broker matches the DB, it re-adopts the fly
    and carries on.
  - If not, it refuses and stops again. After three restarts it stays down.
  - You see `⚠️ … stopped … and Docker restarted it` for each restart. If it stays
    down, you see the 🚨 "live container is NOT running".
- **bd870ae and earlier:** the container stays up but halted, and the fly is unmanaged
  until a human acts.

Either way, health.sh's 🚨 in the live channel repeats every 15 min. Alertmanager's
`ButterflyGuyBrokerAmbiguity` (instance_role live) also posts to the live channel since
2026-11-19. On 2026-11-19 the halt came at 07:20 PT and the first human action at 13:03 PT.

An `IntentPersistenceError` with `entry intent creation outcome is unknown; no broker
order submitted; manual reconciliation required` (or `exit intent creation outcome
is unknown; no broker order submitted; manual reconciliation required`) halts on the
first failed INSERT reply, even if the database is still unreachable. This attempt
sent no broker order, but the intent may have committed. Do not retry it manually
until the database is reachable and its intents and broker state have been checked.
A surviving SUBMITTING row is refused at startup; resolve it only through the guarded
operator procedure below. If no row survived, startup can reconcile normally.

The health warning `live entries BLOCKED by an active intent; manual reconciliation
required` clears after a later `entry_intent_created` log event proves that the
active-entry index allowed a new intent. Health then posts `✅ … health recovered
(was: …)` once. A no-op `entry_loop_recovered` is insufficient proof. A later block
warns again. Any `*_stopped_unknown_broker_state` event stays sticky for that container
run and keeps its repeating 🚨 alert; only a restart scopes it out.

1. **Read state (read-only).** `docker logs butterfly_spx_live_app 2>&1 | grep -E
   'stopped_unknown|monitor_task_error|post_cancel|order_'` names the order and the
   reason. In ToS, record the fly's legs and any working order on them.
2. **Close or hold in ToS.** The bot will not act. Cancel any working order on the
   legs and confirm it reads Canceled. Then either send the closing butterfly
   yourself or decide to hold to settlement. Holding to settlement is fine for a
   cash-settled 0DTE fly when its remaining value is small.
3. **Do not restart the bot to "resume" while an order on the legs is working.**
   Startup refuses on any bot-owned order that is not final (working, PENDING_CANCEL,
   partial). On bd870ae it accepts a bot-owned working order, then hands the exit to
   you as if that order were yours. After you cancel it in ToS, a stopped container
   needs `docker start butterfly_spx_live_app`.
   - **Refusal "exit intent that cannot be matched to a broker order" or "unresolved exit intent":** an exit submit
     whose outcome is unknown. It covers the OPEN trade's exit intents of any date,
     including an earlier session's still-open fly. First confirm in ToS that no order
     is working on the fly's legs and no fill is missing from the DB. Only then close the intent in the
     live DB; it must update exactly one row:
     `UPDATE broker_order_intents SET status = 'CANCELED', raw_broker_payload = '{"operator_resolved": "<reason>", "previous_status": "<old>"}'::jsonb, updated_at = NOW() WHERE id = <id> AND status NOT IN ('FILLED','CANCELED','REJECTED','EXPIRED') AND broker_order_id IS NULL;`
     For `REPLACED` or `order not found` with a recorded order id, first confirm in ToS
     that that order and every replacement are final and no fill is missing from the DB.
     Use this variant instead; it must also update exactly one row:
     `UPDATE broker_order_intents SET status = 'CANCELED', raw_broker_payload = '{"operator_resolved": "<reason>", "previous_status": "<old>"}'::jsonb, updated_at = NOW() WHERE id = <id> AND broker_order_id = '<order id>' AND status NOT IN ('FILLED','CANCELED','REJECTED','EXPIRED');`
     Then `docker start butterfly_spx_live_app`. This is the only sanctioned manual DB
     edit, and only after the ToS check.
   - **Refusal "entry intent that cannot be matched to a broker order" or "unresolved entry intent":**
     today's entry, e.g. one you replaced in ToS (the bot halts on that). It blocks
     every entry today. Check ToS the same way for today's SPX orders and positions,
     then use the same UPDATE with its id.
4. **After you close in ToS:** a restarted bot adopts nothing that it did not send.
   Close the DB row from Schwab's fill (Manual Flatten, step 6).
5. **If it expires:** after 16:02 ET, run the settle tool. Do the dry run first:
   ```bash
   docker exec -i butterfly_spx_live_app python - --trade-id <id> \
     < $REL/tools/spx_live_settle_expired.py
   docker exec -i butterfly_spx_live_app python - --trade-id <id> --apply \
     < $REL/tools/spx_live_settle_expired.py
   ```
   It settles from Schwab's posted expiration transactions when they exist. The
   same day, it settles only a fly that expired at least 20 SPX points out of the
   money. It also updates `daily_risk_state`.
6. **Stop the container.** A running live bot books the settlement at the close,
   marked provisional; the next startup replaces it with Schwab's posting. Close-out
   and `stop-live.sh` ignore legs whose expiry has passed (`--ignore-expired`). On
   bd870ae they don't: Schwab lists expired legs until overnight, so stop with
   `FORCE=1`, and only after step 5 shows the row CLOSED and ToS shows no working
   orders. Record why in the session dir.
7. **Before the next live day,** the activation gates (broker flat, live DB flat)
   must pass on their own. Never edit the gates.

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
