#!/usr/bin/env bash
# Manual rollback: stop the live SPX container once the broker and the live DB are flat.
# FORCE=1 stops it even when not flat; that leaves any open live position UNMANAGED, so it
# is the operator's decision only. Never touches app_spx.
set -uo pipefail
source "$(dirname "$0")/common.sh"
open_log stop-live
echo "=== $(ts) stop-live start: $LABEL $DATE"

if [ "$(running "$LIVE_C")" = 0 ]; then
  echo "$(ts) live container not running"
  exit 0
fi
if [ "${FORCE:-0}" != 1 ]; then
  broker_flat || { echo "$(ts) REFUSED: broker not flat (FORCE=1 to override)"; exit 1; }
  db_tool check "${CHECK_ARGS[@]}" || { echo "$(ts) REFUSED: $LIVE_DB not flat (FORCE=1 to override)"; exit 1; }
fi
act save_logs "$D" || echo "$(ts) saving container logs FAILED"
if stop_live; then
  notify "⏹️ $LABEL $DATE: live container stopped by operator${FORCE:+ (FORCE=$FORCE)}; paper untouched."
else
  notify "🚨 $LABEL $DATE: stop-live did not stop the live container. Check Helios: $D/stop-live.log"
  exit 1
fi
echo "=== $(ts) stop-live done"
