#!/usr/bin/env bash
# Read-only liveness check for a running live session; run every few minutes from a timer.
# The live container restarts on a crash at most three times; after that, if it dies holding
# a fly, nothing manages the exit until someone looks. This posts to the live channel when it
# is down or unhealthy, again when the problem changes, and once on recovery. Each Docker
# restart is posted once, because a restarted bot otherwise looks healthy. It never starts, stops or execs into
# anything that writes. It stays silent until activation has verified the container
# (VERIFIED) and after a deliberate stop (STOPPED).
set -uo pipefail
source "$(dirname "$0")/common.sh"

[ "$(date -u +%F)" = "$DATE" ] || exit 0
[ -e "$D/VERIFIED" ] || exit 0
[ -e "$D/STOPPED" ] && exit 0
open_log health

restarts=$(docker inspect -f '{{.RestartCount}}' "$LIVE_C" 2>/dev/null || echo 0)
seen=$(cat "$D/restarts.seen" 2>/dev/null || echo 0)
if [ "${restarts:-0}" -gt "${seen:-0}" ]; then
  echo "$restarts" >"$D/restarts.seen"
  echo "$(ts) health live restarts=$restarts"
  notify "⚠️ $LABEL $DATE: the live bot crashed and Docker restarted it (restart $restarts of at most 3). On startup it reconciles with the broker and re-adopts any open fly. Check its log and ToS. Log: $D/health.log"
fi

state="$D/health.state"
last=$(cat "$state" 2>/dev/null)
p0=$(cat "$D/paper.fingerprint" 2>/dev/null)

fail=""
if [ "$(running "$LIVE_C")" != 1 ]; then
  fail="live container is NOT running ($(docker inspect -f 'exit {{.State.ExitCode}} at {{.State.FinishedAt}}' "$LIVE_C" 2>/dev/null || echo 'missing'))"
elif [ "$(docker inspect -f '{{.Image}}' "$LIVE_C")" != "$CAND" ]; then
  fail="live image is not $CAND"
elif ! curl -sf --max-time 5 "http://127.0.0.1:$LIVE_PORT/health" >/dev/null; then
  fail="metrics port $LIVE_PORT not answering"
elif ! token_match "$LIVE_C"; then
  fail="token file differs between host and live container"
elif [ "$(running "$PAPER_C")" != 1 ]; then
  fail="paper container is not running"
elif [ -n "$p0" ] && [ "$(paper_fingerprint)" != "$p0" ]; then
  fail="PAPER CONTAINER CHANGED since activation"
fi
echo "$(ts) health fail=${fail:-none}"

if [ -z "$fail" ]; then
  if [ -n "$last" ]; then
    notify "✅ $LABEL $DATE health recovered (was: $last)"
  fi
  : >"$state"
  exit 0
fi

[ "$fail" = "$last" ] && exit 1
echo "$fail" >"$state"
if [ "$(running "$LIVE_C")" != 1 ]; then
  if db_tool check "${CHECK_ARGS[@]}" >/dev/null; then
    held="$LIVE_DB is flat"
  else
    held="$LIVE_DB may hold an OPEN live fly that nothing is managing"
  fi
  notify "🚨 $LABEL $DATE: $fail; $held. Check ToS and Helios now. Log: $D/health.log"
else
  notify "⚠️ $LABEL $DATE health: $fail. Log: $D/health.log"
fi
exit 1
