#!/usr/bin/env bash
# Gate equity morning scan to 6:00 AM America/Los_Angeles on weekdays.
# Vixie cron (Ubuntu) ignores CRON_TZ in user crontabs — schedule this at
# 13:00 and 14:00 UTC so one slot hits 6 AM during PDT and PST.
set -euo pipefail

if [[ "$(TZ=America/Los_Angeles date +%u)" -gt 5 ]]; then
  exit 0
fi
if [[ "$(TZ=America/Los_Angeles date +%H)" != "06" ]]; then
  exit 0
fi

cd /opt/butterflyguy

# A same-session parity reference must finish before the gateway-backed candidate
# starts. The dedicated config disables the broad RVOL/news/movers phases; dry-run
# still archives the JSON reference without posting a second Discord report.
readonly parity_date="$(TZ=America/New_York date +%F)"
if [[ "$parity_date" == "2026-09-01" || "$parity_date" == "2026-09-02" ]]; then
  readonly parity_input_dir="/opt/equity-scanner/parity/$parity_date/input"
  readonly reference_archive="/opt/butterflyguy/reports/equity_scans/$parity_date.json"
  (
    cd "$parity_input_dir"
    sha256sum --check --strict input.sha256
  )
  if [[ -e "$reference_archive" ]]; then
    echo "$parity_date parity reference already exists; refusing to overwrite" >&2
    exit 1
  fi
  deadline_epoch="$(TZ=America/New_York date -d "$parity_date 09:09:00" +%s)"
  remaining_seconds="$((deadline_epoch - $(date +%s)))"
  if (( remaining_seconds <= 0 )); then
    echo "$parity_date parity reference deadline has passed; failing closed" >&2
    exit 1
  fi
  exec timeout --signal=TERM --kill-after=15s "${remaining_seconds}s" \
    /opt/butterflyguy/.venv/bin/python \
    src/butterfly_guy/scripts/run_morning_scan.py \
    --scan-config "$parity_input_dir/equity_scan.reference.yaml" \
    --dry-run \
    --log-level WARNING
fi

exec /opt/butterflyguy/.venv/bin/python src/butterfly_guy/scripts/run_morning_scan.py --log-level WARNING
