#!/usr/bin/env bash
# Durable, read-only launcher for the 2026-09-09 Schwab Gateway v0.4.6 soak.
set -euo pipefail
umask 077

readonly SESSION_DATE=2026-09-09
readonly TARGET_EPOCH="$(date -u -d '2026-09-09 13:20:00 UTC' +%s)"
readonly TOOL_DIR=/opt/butterflyguy-gateway-acceptance-tools
readonly MONITOR="$TOOL_DIR/schwab_gateway_v046_readiness_soak_20260909_v1.py"
readonly VALIDATOR="$TOOL_DIR/schwab_gateway_session_soak_20260909_validator.py"
readonly LAUNCHER="$TOOL_DIR/launch_schwab_gateway_readiness_soak_20260909.sh"
readonly EVIDENCE_DIR=/opt/butterflyguy-gateway-evidence/2026-09-09-gateway-readiness-v0.4.6-ce4c5e1
readonly LOG="$TOOL_DIR/schwab-gateway-readiness-soak-2026-09-09.log"

exec >>"$LOG" 2>&1
echo "launcher_started_utc=$(date -u --iso-8601=seconds) pid=$$"

die() {
  echo "ABORT $(date -u --iso-8601=seconds): $*"
  exit 1
}

[[ -f "$MONITOR" ]] || die "monitor missing"
[[ -f "$VALIDATOR" ]] || die "validator missing"
[[ -f "$LAUNCHER" ]] || die "launcher missing"
[[ ! -e "$EVIDENCE_DIR" ]] || die "fresh evidence directory already exists"

while :; do
  now="$(date -u +%s)"
  (( now >= TARGET_EPOCH )) && break
  remaining=$((TARGET_EPOCH - now))
  sleep $((remaining < 300 ? remaining : 300))
done

[[ "$(TZ=America/Los_Angeles date +%F)" == "$SESSION_DATE" ]] \
  || die "Helios Pacific date is not $SESSION_DATE"
echo "preflight_start_utc=$(date -u --iso-8601=seconds)"

cd /opt/butterflyguy
exec .venv/bin/python "$MONITOR" \
  --session-date "$SESSION_DATE" \
  --evidence-dir "$EVIDENCE_DIR" \
  --launcher "$LAUNCHER" \
  --sample-seconds 300 \
  --diagnostic-every 3 \
  --post-close-minutes 10
