#!/usr/bin/env bash
# Read-only liveness check for a running live session; run every few minutes from a timer.
# The live container restarts on a crash or a safety halt (the bot then exits 1) at most
# three times; after that, if it dies holding a fly, nothing manages the exit until someone
# looks. This posts to the live channel when it
# is down or unhealthy, again when the problem changes, and once on recovery. Each Docker
# restart is posted once, because a restarted bot otherwise looks healthy. A bot that is up but
# has halted on unknown broker state counts as down: it leaves an open fly unmanaged (live
# 2026-11-19). It never starts, stops or execs into anything that writes. It stays silent
# until activation has verified the container (VERIFIED) and after a deliberate stop (STOPPED).
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
  notify "⚠️ $LABEL $DATE: the live bot stopped (a crash, or a safety halt on unknown broker state) and Docker restarted it (restart $restarts of at most 3). On startup it reconciles with the broker and re-adopts any open fly, or refuses and stops again. Check its log and ToS. Log: $D/health.log"
fi

state="$D/health.state"
last=$(cat "$state" 2>/dev/null)
p0=$(cat "$D/paper.fingerprint" 2>/dev/null)

# Broker-state halts and blocked entries. Only this run counts; a restart reconciles
# with the broker before it trades again.
broker_state_events() {
  local started
  started=$(docker inspect -f '{{.State.StartedAt}}' "$LIVE_C" 2>/dev/null)
  # grep reads to the end: an early `grep -q` exit SIGPIPEs docker logs, and pipefail then
  # reports "not halted" (it did on 2026-11-19's 1 MB log).
  docker logs --since "${started:-${DATE}T00:00:00Z}" "$LIVE_C" 2>&1 \
    | grep -E '"event": "((monitor|entry_loop)_stopped_unknown_broker_state|entry_blocked_active_intent)"'
}

fail=""
if [ "$(running "$LIVE_C")" != 1 ]; then
  fail="live container is NOT running ($(docker inspect -f 'exit {{.State.ExitCode}} at {{.State.FinishedAt}}' "$LIVE_C" 2>/dev/null || echo 'missing'))"
elif [ "$(docker inspect -f '{{.Image}}' "$LIVE_C")" != "$CAND" ]; then
  fail="live image is not $CAND"
elif broker_events=$(broker_state_events); then
  if [[ "$broker_events" == *"_stopped_unknown_broker_state"* ]]; then
    fail="live bot HALTED on unknown broker state; it is up but not managing exits"
  else
    fail="live entries BLOCKED by an active intent; manual reconciliation required"
  fi
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

# A dead or halted bot with an open fly leaves it unmanaged, so that alert repeats every
# ALERT_REPEAT_MIN minutes until the fly is flat or the bot recovers; one post was missed for
# six hours on 2026-11-19. Everything else posts once per problem.
unmanaged=0
{ [ "$(running "$LIVE_C")" != 1 ] || [[ "$fail" == "live bot HALTED"* ]]; } && unmanaged=1
alerted="$D/health.alerted"
repeat=""
if [ "$fail" = "$last" ]; then
  [ "$unmanaged" = 1 ] || exit 1
  since=$(( $(date +%s) - $(cat "$alerted" 2>/dev/null || echo 0) ))
  [ "$since" -ge $(( ${ALERT_REPEAT_MIN:-15} * 60 )) ] || exit 1
  repeat=" STILL UNRESOLVED after $(( since / 60 )) min."
fi
echo "$fail" >"$state"
if [ "$unmanaged" = 1 ]; then
  if db_tool check "${CHECK_ARGS[@]}" >/dev/null; then
    held="$LIVE_DB is flat"
    [ -n "$repeat" ] && exit 1  # nothing left to manage; the first post said so
  else
    held="$LIVE_DB may hold an OPEN live fly that nothing is managing"
  fi
  notify "🚨 $LABEL $DATE: $fail; $held.$repeat Check ToS and Helios now. Log: $D/health.log"
  date +%s >"$alerted"
else
  notify "⚠️ $LABEL $DATE health: $fail. Log: $D/health.log"
fi
exit 1
