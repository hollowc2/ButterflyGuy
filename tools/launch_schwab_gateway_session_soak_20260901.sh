#!/usr/bin/env bash
set -euo pipefail

umask 077
readonly LAUNCH_LOG="/opt/butterflyguy-gateway-acceptance-tools/schwab-gateway-session-soak-2026-09-01.log"
exec >>"$LAUNCH_LOG" 2>&1

# Start after the sequential 09:00-09:20 ET parity captures, leaving eight minutes
# for the final invariant/flatness checks before the 09:30 ET opening checkpoint.
readonly TARGET_EPOCH="$(date -u -d '2026-09-01 13:22:00 UTC' +%s)"
readonly NOW_EPOCH="$(date -u +%s)"
if (( NOW_EPOCH < TARGET_EPOCH )); then
  sleep "$((TARGET_EPOCH - NOW_EPOCH))"
fi

cd /opt/butterflyguy

for unit in docker containerd piavpn; do
  [[ "$(systemctl is-active "$unit")" == "active" ]]
done

for container in schwab_gateway_live butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  [[ "$(docker inspect --format '{{.State.Running}}' "$container")" == "true" ]]
  [[ "$(docker top "$container" -eo pid,args | tail -n +2 | wc -l)" -eq 1 ]]
done

# Both parity jobs are deadline-bounded before this launcher wakes. Refuse to freeze
# the soak while either the direct reference or an ephemeral candidate remains.
! pgrep -af 'run_morning_scan.py.*equity_scan.reference.yaml' >/dev/null
[[ -z "$(docker ps -q --filter label=com.docker.compose.project=equity_scanner_candidate)" ]]

readonly TOKEN_PATH="/opt/butterflyguy-tokens/tokens.json"
host_stat="$(stat -Lc '%i:%s:%a:%u:%g' "$TOKEN_PATH")"
host_digest="$(sha256sum "$TOKEN_PATH" | awk '{print $1}')"
for container in schwab_gateway_live butterfly_spx_app butterfly_ndx_app butterfly_xsp_app; do
  [[ "$(docker exec "$container" stat -Lc '%i:%s:%a:%u:%g' "$TOKEN_PATH")" == "$host_stat" ]]
  [[ "$(docker exec "$container" sha256sum "$TOKEN_PATH" | awk '{print $1}')" == "$host_digest" ]]
done
printf 'token_agreement=true metadata=%s fingerprint=%s\n' "$host_stat" "${host_digest:0:12}"

.venv/bin/python \
  /opt/butterflyguy-gateway-acceptance-tools/gateway_cutover_flatness_audit_20260828.py \
  --config configs/config.yaml \
  --date 2026-09-01

exec .venv/bin/python \
  /opt/butterflyguy-gateway-acceptance-tools/schwab_gateway_session_soak_20260828_v3.py \
  --session-date 2026-09-01 \
  --evidence-dir /opt/butterflyguy-gateway-evidence/2026-09-01-order-book-aa9d6e6-refreeze-032625 \
  --expected-container-id ccd2b0d2d2b3dc928bdfba46ba80a73ab6831cb6e955582ec50df5c1f9b39768 \
  --expected-image-id sha256:f1d287294864c05b00ca201d1d86f8344f0d6f61121074982f92667468fec7f0 \
  --expected-revision aa9d6e65a91c14eadf70df1c3da15101fb84d3f9 \
  --expected-started-at 2026-08-31T03:26:25.514589924Z
