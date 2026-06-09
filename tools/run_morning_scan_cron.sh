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
exec /opt/butterflyguy/.venv/bin/python src/butterfly_guy/scripts/run_morning_scan.py --log-level WARNING
