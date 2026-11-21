#!/usr/bin/env bash
# Read-only liveness check for a running live session; run every few minutes from a timer.
# The live container restarts on a crash or a safety halt (the bot then exits 1) at most
# three times; after that, if it dies holding a fly, nothing manages the exit until someone
# looks. This posts to the live channel when it
# is down or unhealthy, again when the problem changes, and once on recovery. Each Docker
# restart is posted once, because a restarted bot otherwise looks healthy. A bot that is up but
# has halted on unknown broker state counts as down: it leaves an open fly unmanaged (live
# 2026-11-19). It never starts, stops or execs into anything that writes. It stays silent
# until activation has verified the container (VERIFIED) or left an unverified one running
# to manage a fly (VERIFY_FAILED), and after a confirmed deliberate stop (STOPPED). An entry
# halt that activation could not apply (ENTRY_HALT_FAILED) alerts on its own track,
# whatever else this check finds.
set -uo pipefail
source "$(dirname "$0")/common.sh"

[ "$(date -u +%F)" = "$DATE" ] || exit 0
[ -e "$D/VERIFIED" ] || [ -e "$D/VERIFY_FAILED" ] || exit 0
[ -e "$D/STOPPED" ] && exit 0
open_log health

restarts=$(docker inspect -f '{{.RestartCount}}' "$LIVE_C" 2>/dev/null || echo 0)
seen=$(cat "$D/restarts.seen" 2>/dev/null || echo 0)
if [ "${restarts:-0}" -gt "${seen:-0}" ]; then
  echo "$(ts) health live restarts=$restarts"
  if notify "⚠️ $LABEL $DATE: the live bot stopped (a crash, or a safety halt on unknown broker state) and Docker restarted it (restart $restarts of at most 3). On startup it reconciles with the broker and re-adopts any open fly, or refuses and stops again. Check its log and ToS. Log: $D/health.log"; then
    echo "$restarts" >"$D/restarts.seen"
  fi
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
    | grep -E '"event": "((monitor|entry_loop)_stopped_unknown_broker_state|entry_blocked_active_intent|entry_intent_created)"'
}

# Optional readiness confirmation. This file records observations, not alert delivery.
# Clear it on every run so skipped/failed checks break the consecutive-read streak.
ready_state="$D/health.ready"
previous_ready=$(cat "$ready_state" 2>/dev/null)
: >"$ready_state"
ready_reason=""
ready_problem() {
  [ "${CHECK_READY:-0}" = 1 ] || return 1
  # /ready returns its reason with HTTP 503, so do not use curl -f here.
  ready_reason=$(curl -sS --max-time 5 "http://127.0.0.1:$LIVE_PORT/ready" \
    | "$PY" -c '
import json, sys
try:
    data = json.load(sys.stdin)
except ValueError:
    sys.exit(1)
if not isinstance(data, dict) or data.get("status") != "not_ready":
    sys.exit(0)
reason = data.get("reason")
if isinstance(reason, str):
    reasons = {part.strip() for part in reason.split(",") if part.strip()}
    if not reasons.intersection({"starting", "shutting_down"}):
        print(",".join(sorted(reasons)))
') || return 1
  [ -n "$ready_reason" ] || return 1
  local started current
  started=$(docker inspect -f '{{.State.StartedAt}}' "$LIVE_C" 2>/dev/null) || return 1
  [ -n "$started" ] || return 1
  current="$started $ready_reason"
  printf '%s\n' "$current" >"$ready_state"
  [ "$current" = "$previous_ready" ]
}

fail=""
if [ "$(running "$LIVE_C")" != 1 ]; then
  fail="live container is NOT running ($(docker inspect -f 'exit {{.State.ExitCode}} at {{.State.FinishedAt}}' "$LIVE_C" 2>/dev/null || echo 'missing'))"
elif [ "$(docker inspect -f '{{.Image}}' "$LIVE_C")" != "$CAND" ]; then
  fail="live image is not $CAND"
elif broker_events=$(broker_state_events) \
    && [[ "$broker_events" == *"_stopped_unknown_broker_state"* ]]; then
  fail="live bot HALTED on unknown broker state; it is up but not managing exits"
elif ! curl -sf --max-time 5 "http://127.0.0.1:$LIVE_PORT/health" >/dev/null; then
  fail="metrics port $LIVE_PORT not answering"
elif ! token_match "$LIVE_C"; then
  fail="token file differs between host and live container"
elif [ "$(running "$PAPER_C")" != 1 ]; then
  fail="paper container is not running"
elif [ -n "$p0" ] && [ "$(paper_fingerprint)" != "$p0" ]; then
  fail="PAPER CONTAINER CHANGED since activation"
elif ready_problem; then
  fail="live bot NOT READY: $ready_reason (same reason on two consecutive health checks)"
elif [[ "$(printf '%s\n' "${broker_events:-}" \
    | grep -E '"event": "entry_(blocked_active_intent|intent_created)"' \
    | tail -n 1)" == *'"entry_blocked_active_intent"'* ]]; then
  # Last: only the latest block/create event decides; other health problems win.
  fail="live entries BLOCKED by an active intent; manual reconciliation required"
fi
halt_unresolved=0
[ -e "$D/ENTRY_HALT_FAILED" ] && halt_unresolved=1
echo "$(ts) health fail=${fail:-none} entry_halt_failed=$halt_unresolved"

# Entries that may still be enabled stay critical whatever else is wrong, so this alert has
# its own dedup and never yields to another problem. It repeats every ALERT_REPEAT_MIN
# minutes until someone halts entries by hand and removes ENTRY_HALT_FAILED, or a
# confirmed stop-live.sh writes STOPPED. A failed post records nothing and retries next run.
halt_alerted="$D/health.entry_halt.alerted"
if [ "$halt_unresolved" = 1 ]; then
  halt_since=$(( $(date +%s) - $(cat "$halt_alerted" 2>/dev/null || echo 0) ))
  if [ ! -e "$halt_alerted" ] || [ "$halt_since" -ge $(( ${ALERT_REPEAT_MIN:-15} * 60 )) ]; then
    halt_repeat=""
    [ -e "$halt_alerted" ] && halt_repeat=" STILL UNRESOLVED after $(( halt_since / 60 )) min."
    if notify "🚨 $LABEL $DATE: live entries may still be ENABLED: activation failed verification and could not halt them.$halt_repeat Stop live once flat ($D/stop-live.sh), or halt entries by hand and remove $D/ENTRY_HALT_FAILED. Log: $D/health.log"; then
      date +%s >"$halt_alerted"
    fi
  fi
elif [ -e "$halt_alerted" ]; then
  notify "✅ $LABEL $DATE: live entry halt resolved ($D/ENTRY_HALT_FAILED removed)" \
    && rm -f "$halt_alerted"
fi

if [ -z "$fail" ]; then
  if [ -n "$last" ]; then
    notify "✅ $LABEL $DATE health recovered (was: $last)" || exit 1
  fi
  : >"$state"
  exit "$halt_unresolved"
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
if [ "$unmanaged" = 1 ]; then
  if db_tool check "${CHECK_ARGS[@]}" >/dev/null; then
    held="$LIVE_DB is flat"
    [ -n "$repeat" ] && exit 1  # nothing left to manage; the first post said so
  else
    held="$LIVE_DB may hold an OPEN live fly that nothing is managing"
  fi
  notify "🚨 $LABEL $DATE: $fail; $held.$repeat Check ToS and Helios now. Log: $D/health.log" || exit 1
  date +%s >"$alerted"
else
  notify "⚠️ $LABEL $DATE health: $fail. Log: $D/health.log" || exit 1
fi
# Deduplication records delivery, not a failed attempt. Leave old state for a retry.
echo "$fail" >"$state"
exit 1
