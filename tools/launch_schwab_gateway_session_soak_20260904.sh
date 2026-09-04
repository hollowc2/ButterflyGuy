#!/usr/bin/env bash
# Unattended launcher for the 2026-09-04 full-session SchwabGateway acceptance
# soak. Start this TONIGHT inside a durable tmux session on Helios:
#
#   tmux new -s gateway-session-soak
#   /opt/butterflyguy-gateway-acceptance-tools/launch_schwab_gateway_session_soak_20260904.sh
#   # Ctrl-b d to detach
#
# It sleeps until 06:20 PDT, re-asserts every production invariant, runs the
# flatness gate, then execs the harness (which itself waits for the 09:30 EDT
# open, samples to the 16:00 EDT close, and does the post-close check). Any
# invariant drift aborts BEFORE the harness starts, so a bad run never begins.
set -euo pipefail
umask 077

readonly LOG=/opt/butterflyguy-gateway-acceptance-tools/schwab-gateway-session-soak-2026-09-04.log
exec >>"$LOG" 2>&1
echo "=== launcher started $(date -u --iso-8601=seconds) ==="

# --- frozen target (captured 2026-09-04 00:01 UTC; see runbook) --------------
readonly GW_CONTAINER=schwab_gateway_live
readonly GW_ID=1a2dfa27c6a19ae72c13a87a9fe9ce2d5d42b9f20eb82179c1774fba6b4e433d
readonly GW_IMAGE=sha256:c8540b5c4eb2ab3d0dfa00d85d75a6fb774bcf22ca1d352b38b68507edb17dcd
readonly GW_STARTED_AT=2026-09-03T22:57:45.300059462Z
readonly GW_REVISION='<no value>'   # 0.4.2 build omits the label
readonly SESSION_DATE=2026-09-04
readonly EVIDENCE_DIR=/opt/butterflyguy-gateway-evidence/2026-09-04-session-soak-v0.4.2-efee41f
readonly SOAK=/opt/butterflyguy-gateway-acceptance-tools/schwab_gateway_session_soak_20260904_v7.py
readonly FLATNESS=/opt/butterflyguy-gateway-acceptance-tools/gateway_cutover_flatness_audit_20260828.py
readonly TOKEN_PATH=/opt/butterflyguy-tokens/tokens.json
readonly CONSUMERS=(schwab_gateway_live butterfly_spx_app butterfly_ndx_app butterfly_xsp_app)
readonly TARGET_EPOCH="$(date -u -d '2026-09-04 13:20:00 UTC' +%s)"   # 06:20 PDT

die() { echo "ABORT: $*"; exit 1; }

# --- wait until the preflight window ---------------------------------------
while :; do
  now="$(date -u +%s)"
  (( now >= TARGET_EPOCH )) && break
  remain=$(( TARGET_EPOCH - now ))
  sleep $(( remain < 300 ? remain : 300 ))
done
echo "=== woke $(date -u --iso-8601=seconds); asserting invariants ==="

# --- host / infra ---------------------------------------------------------
[[ "$(date -u +%F)" == "$SESSION_DATE" ]] || die "host date $(date -u +%F) != $SESSION_DATE"
for unit in docker containerd piavpn; do
  [[ "$(systemctl is-active "$unit")" == active ]] || die "$unit not active"
done
[[ -f "$SOAK" ]] || die "soak tool missing: $SOAK"
[[ ! -e "$EVIDENCE_DIR" ]] || die "evidence dir already exists: $EVIDENCE_DIR"

# --- production gateway identity ----------------------------------------
gw() { docker inspect --format "$1" "$GW_CONTAINER"; }
[[ "$(gw '{{.Id}}')"              == "$GW_ID" ]]         || die "gateway container id drift"
[[ "$(gw '{{.Image}}')"           == "$GW_IMAGE" ]]      || die "gateway image drift"
[[ "$(gw '{{.State.StartedAt}}')" == "$GW_STARTED_AT" ]] || die "gateway restarted (StartedAt drift)"
[[ "$(gw '{{.State.Running}}')"   == true ]]             || die "gateway not running"
[[ "$(gw '{{.RestartCount}}')"    == 0 ]]                || die "gateway restart count != 0"
[[ "$(gw '{{if .State.Health}}{{.State.Health.Status}}{{end}}')" == healthy ]] || die "gateway not healthy"
gw_procs="$(docker top "$GW_CONTAINER" -eo pid,args | tail -n +2 | grep -c schwab-gateway || true)"
[[ "$gw_procs" == 1 ]] || die "gateway process count = $gw_procs (want 1)"

# --- readiness / token (0.4.1 warms readiness on a live round-trip) ------
ready="$(curl -fsS --max-time 15 http://127.0.0.1:8011/ready)" || die "/ready not 200"
case "$ready" in
  *'"status": "ready"'*)      ;; *) die "/ready status != ready" ;;
esac
case "$ready" in
  *'"token_state": "ready"'*) ;; *) die "token_state != ready" ;;
esac
curl -fsS -o /dev/null --max-time 15 http://127.0.0.1:8011/health || die "/health not 200"

# --- token mount agreement (no token contents printed) ------------------
host_stat="$(stat -Lc '%i:%a:%u:%g' "$TOKEN_PATH")"
for c in "${CONSUMERS[@]}"; do
  [[ "$(docker inspect --format '{{.State.Running}}' "$c")" == true ]] || die "$c not running"
  [[ "$(docker inspect --format '{{.RestartCount}}' "$c")" == 0 ]]     || die "$c restart count != 0"
  [[ "$(docker exec "$c" stat -Lc '%i:%a:%u:%g' "$TOKEN_PATH")" == "$host_stat" ]] \
    || die "$c token mount disagrees with host ($host_stat)"
done
echo "token_mount_agreement=true metadata=$host_stat"

# --- no retired / competing consumers ---------------------------------
# The routine morning scan (background priority) may run; the scheduler isolates
# it from the protected soak lane, so note it but do not abort.
if pgrep -af '[r]un_morning_scan.py' >/dev/null; then
  echo "NOTE: run_morning_scan.py is running (background lane; not a blocker)"
fi
if docker ps --format '{{.Names}}' | grep -Eiq 'candidate|scanner_candidate|candidate_feed'; then
  die "a retired candidate/scanner container is running"
fi

# --- flatness gate --------------------------------------------------
cd /opt/butterflyguy
flat_json="$(.venv/bin/python "$FLATNESS" --config configs/config.yaml --date "$SESSION_DATE" | tail -n 1)"
echo "$flat_json"
case "$flat_json" in
  *'"flat": true'*) ;; *) die "flatness gate failed" ;;
esac

echo "=== all invariants pass; starting harness $(date -u --iso-8601=seconds) ==="
exec .venv/bin/python "$SOAK" \
  --session-date "$SESSION_DATE" \
  --evidence-dir "$EVIDENCE_DIR" \
  --expected-container-id "$GW_ID" \
  --expected-image-id "$GW_IMAGE" \
  --expected-revision "$GW_REVISION" \
  --expected-started-at "$GW_STARTED_AT" \
  --expected-consumer-priority protected
