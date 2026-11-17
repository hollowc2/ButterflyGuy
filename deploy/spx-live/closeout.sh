#!/usr/bin/env bash
# 13:45 PT close-out: export live evidence and the paired paper/live report, then stop the
# live container only if the broker and the live DB are flat. Never touches app_spx.
set -uo pipefail
source "$(dirname "$0")/common.sh"
open_log closeout
echo "=== $(ts) close-out start: $LABEL $DATE"

if [ "$(running "$LIVE_C")" = 0 ]; then
  echo "$(ts) live container not running; nothing to close out"
  exit 0
fi

out="$D/evidence-$(date -u +%Y%m%dT%H%M%SZ)"
act mkdir -p "$out"
if act export_evidence "$out"; then
  ev="evidence saved to $out"
else
  ev="evidence export FAILED"
fi
act save_logs "$out" || echo "$(ts) saving container logs FAILED"
act paired_report "$out" || echo "$(ts) paired report FAILED"
echo "$(ts) $ev"

p0=$(cat "$D/paper.fingerprint" 2>/dev/null)
paper_note="paper untouched"
[ -n "$p0" ] && [ "$(paper_fingerprint)" != "$p0" ] && paper_note="⚠️ PAPER CONTAINER CHANGED since activation"

if broker_flat && db_tool check "${CHECK_ARGS[@]}"; then
  if stop_live; then
    notify "🏁 $LABEL $DATE closed: broker & $LIVE_DB flat, $ev, live container stopped, $paper_note."
  else
    notify "🚨 $LABEL $DATE: flat but the live container did not stop. Check Helios: $D/closeout.log"
  fi
else
  notify "⚠️ $LABEL $DATE: not flat yet (broker positions/orders or an open live trade, e.g. settlement not posted). Live container left running (no new entries after today). $ev. Stop it once flat: $D/stop-live.sh. $paper_note."
fi
echo "=== $(ts) close-out done"
