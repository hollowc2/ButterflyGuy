# Concurrent SPX live pilot scripts (v2)

Run the real-money SPX pilot **beside** paper, not instead of it. Design and rollout:
`docs/operations/concurrent-paper-live-spx-design.md`.

| Script | When | Does |
|---|---|---|
| `activate.sh` | 06:35 PT, or by hand with Corey present | Gates, tops up `daily_bars`, starts `butterfly_spx_live_app`, verifies it, and checks that paper is unchanged |
| `closeout.sh` | 13:45 PT | Exports evidence and the paired paper/live report; stops live only when the broker and live DB are flat |
| `health.sh` | every 5 min while live runs | Read-only. Alerts the live channel if the live container is down, its metrics port or token is wrong, or paper changed; says whether the live DB still holds an open fly. Silent before activation is verified and after a deliberate stop |
| `stop-live.sh` | manual rollback | Stops live once flat. `FORCE=1` stops it anyway, which leaves any open position **unmanaged** |

None of them creates, recreates, restarts or stops `butterfly_spx_app`.
`tests/test_spx_live_scripts.py` enforces this for every path.

## Per session

1. Copy this directory to `/opt/butterflyguy-releases/spx-live-<DATE>-<sha7>/`.
2. Fill in `session.env` from `session.env.example`. `REHEARSAL=1` is the Phase 3 paper-mode
   run on `butterfly_guy_spx_live_rehearsal`.
3. Preview without changing anything: `DRY_RUN=1 ./activate.sh`. All reads and gates run;
   commands that would change anything are printed, compose ones in full.
4. Schedule timers only with the owner's approval for that session. The live container has
   `restart: "no"`, so a session needs the health check even when it is run by hand.
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
