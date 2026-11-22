# Concurrent SPX live pilot scripts (v2)

Run the real-money SPX pilot **beside** paper, not instead of it. Design and rollout:
`docs/operations/concurrent-paper-live-spx-design.md`.
The [original pilot overlay](../../docs/archive/spx-live/docker-compose.spx-live-test.yml)
is archived with the historical deployment records.

| Script | When | Does |
|---|---|---|
| `activate.sh` | 06:35 PT, or by hand with Corey present | Runs the startup gates, tops up `daily_bars`, starts `butterfly_spx_live_app`, and verifies it and paper's fingerprint. Requires an image with `spx_live_db halt-entries`. On failed verification it tries to halt and drain new entries. It stops live only after a successful drain and flatness checks. Otherwise it keeps the bot running to manage any position. |
| `closeout.sh` | 13:45 PT | Exports evidence and the paired paper/live report; stops live only when the broker and live DB are flat |
| `health.sh` | every 5 min | Watches from `ACTIVATED` through a confirmed `STOPPED`. Alerts if verification has no outcome after `WAIT_SECONDS` plus one minute. Also alerts on a stopped or halted bot, failed metrics or token checks, or a changed paper container. Alerts for a potentially unmanaged fly or an unresolved `ENTRY_HALT_FAILED` repeat every 15 min (`ALERT_REPEAT_MIN`). |
| `stop-live.sh` | manual rollback | Stops live once flat. `FORCE=1` stops it anyway, which leaves any open position **unmanaged** |

None of them creates, recreates, restarts or stops `butterfly_spx_app`.
`tests/test_spx_live_scripts.py` enforces this for every path.

## Per session

1. Copy this directory to `/opt/butterflyguy-releases/spx-live-<DATE>-<sha7>/`.
2. Fill in `session.env` from `session.env.example`. `REHEARSAL=1` is the Phase 3 paper-mode
   run on `butterfly_guy_spx_live_rehearsal`.
   `OBSERVE=1` runs the real live bot with every entry blocked
   (`infra/docker-compose.spx-live-observe.yml` pins its live-test date to 2000-01-01), so it
   sends no orders: startup reconcile, broker checks, collector and health only. Activation
   verifies the blocked date and stops a container that could still enter.
   `EXIT_PRICING` picks the live exit rule. Leave it empty on the first concurrent live day
   (default bid ladder). From the second live day on, set `EXIT_PRICING=mid_walk` to pilot
   the exit-ladder study's R3 rule (owner, 2026-11-18). That adds
   `infra/docker-compose.spx-live-mid-walk.yml`, and verification then requires
   `EXECUTION__EXIT_PRICING=mid_walk` instead of forbidding it. Any other value, or
   mid_walk on a rehearsal, aborts activation. Pilot rules
   (`docs/research/exit-ladder-pricing-plan.md`, Amendment 1 and §5, on
   `research/exit-ladder-pricing`): go back to the bid ladder if an exit is still unfilled
   when its natural step is due (+60 s), or if 2 of the first 5 exits fill later than the bid
   ladder would have. After 10 pilot exits, refit the fill model and re-run Step 1. Making
   mid_walk the default needs owner approval.
3. Preview without changing anything: `DRY_RUN=1 ./activate.sh`. All reads and gates run;
   commands that would change anything are printed, compose ones in full.
4. Schedule timers only with the owner's approval for that session. The live container has
   `restart: "on-failure:3"`: a crash restarts it (reconcile, then re-adopt any open fly), a
   `docker stop` never does, and after three failed starts it stays down. A session needs the
   health check even when it is run by hand: it reports each restart and a container that
   stays down.
   It is silent outside the session, so a wide window is safe across PST and PDT:

   ```sh
   systemd-run --user --unit "spx-live-health-$DATE" \
     --on-calendar '*-*-* 13..21:00/5:00 UTC' "$PWD/health.sh"
   ```

   Stop it after the session with `systemctl --user stop "spx-live-health-$DATE.timer"`.
5. Set `CLOSEOUT_PT` in `session.env` to the close-out timer's time; the activation message
   quotes it.

## Prerequisites on Helios (one-time, each needs approval)

- The release image is built and `REL` is its `git archive` snapshot.
- `DISCORD_WEBHOOK_URL_SPX_LIVE` is in `/opt/butterflyguy/.env`. The live container and
  `notify.py` refuse to post without it.
- `data/chains-live` (or `data/chains-live-rehearsal`) exists and is owned by uid 1001.
- The DB exists:
  `docker compose ... --profile tools run --rm -T spx_live_db_tool python -m butterfly_guy.scripts.spx_live_db bootstrap --db butterfly_guy_spx_live --copy-live-trade 415`.
- Prometheus job `butterfly_spx_live` (design §8).
