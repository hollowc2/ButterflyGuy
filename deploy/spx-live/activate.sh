#!/usr/bin/env bash
# Start the live SPX container beside paper for one approved session (06:35 PT, or by hand
# with Corey present). Every gate must pass or nothing starts. Never touches app_spx.
set -uo pipefail
source "$(dirname "$0")/common.sh"
open_log activation
echo "=== $(ts) activation start: $LABEL $DATE"

abort() {
  echo "$(ts) ABORT: $1"
  notify "🛑 $LABEL $DATE NOT started: $1 (paper bot untouched)"
  exit 1
}

[ "$(date -u +%F)" = "$DATE" ] || abort "wrong date $(date -u +%F)"
[ -z "$EXIT_PRICING_ERROR" ] || abort "$EXIT_PRICING_ERROR"
[ -z "$OBSERVE_ERROR" ] || abort "$OBSERVE_ERROR"
[ -e "$D/ACTIVATED" ] && abort "activation already attempted"
[ "$(running "$PAPER_C")" = 1 ] || abort "expected exactly one running paper SPX container"
paper_is_paper || abort "paper container is not paper on $PAPER_DB"
p0=$(paper_fingerprint)
[ "$(running "$LIVE_C")" = 0 ] || abort "live container is already running"
docker image inspect "$CAND" >/dev/null 2>&1 || abort "live image $CAND missing"
[ -d "$DATA/$CHAINS" ] && [ "$(stat -c %u "$DATA/$CHAINS")" = "$CONTAINER_UID" ] \
  || abort "chain journal $DATA/$CHAINS missing or not owned by uid $CONTAINER_UID"
token_match "$PAPER_C" || abort "token file differs between host and paper container"
broker_flat || abort "broker flat/auth check failed"
db_tool check "${CHECK_ARGS[@]}" || abort "$LIVE_DB gate failed (schema, flatness or paper rows)"
act db_tool seed-daily-bars || abort "daily bar top-up failed"

echo "$(ts) gates passed; starting $LIVE_C"
act touch "$D/ACTIVATED"
[ "$DRY_RUN" = 1 ] || echo "$p0" >"$D/paper.fingerprint"
act compose up -d --no-build --pull never app_spx_live
up_rc=$?
if [ "$DRY_RUN" = 1 ]; then
  echo "=== $(ts) DRY_RUN: verification skipped"
  exit 0
fi

sleep "$WAIT_SECONDS"
fail=""
[ "$up_rc" = 0 ] || fail="compose up exit $up_rc"
[ -n "$fail" ] || fail=$(verify_live "$p0")
echo "$(ts) verify fail=${fail:-none}"
container_env "$LIVE_C" | grep -E '^(BUTTERFLY_INSTANCE_ROLE|DATABASE__NAME|EXECUTION__|RISK__|LIVE_ACCOUNT|LIVE_MAX)'

if [ -n "$fail" ]; then
  if stop_live; then
    notify "🛑 $LABEL $DATE failed verification ($fail). Live container stopped; paper untouched. Log: $D/activation.log"
  else
    notify "🚨 $LABEL $DATE failed verification ($fail) AND the live container did not stop. Check Helios now: $D/activation.log"
  fi
  exit 1
fi
if [ "$OBSERVE" = 1 ]; then
  notify "✅ $LABEL $DATE RUNNING beside paper: entries BLOCKED (live-test date $OBSERVE_DATE), no orders; startup reconcile, broker checks and health only. DB $LIVE_DB. Close-out $CLOSEOUT_PT PT."
else
  notify "✅ $LABEL $DATE RUNNING beside paper: 1 fly max, ≤4.00 debit, $EXITS, entries 07:00–07:45 PT, DB $LIVE_DB. Close-out $CLOSEOUT_PT PT."
fi
act touch "$D/VERIFIED"
echo "=== $(ts) activation done"
