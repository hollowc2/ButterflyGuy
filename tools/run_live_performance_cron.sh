#!/usr/bin/env bash
# Regenerate butterfly-spx site at 1:30 PM America/Los_Angeles on weekdays.
# Vixie cron ignores CRON_TZ in user crontabs — schedule at 20:30 and 21:30 UTC.
set -euo pipefail

if [[ "$(TZ=America/Los_Angeles date +%u)" -gt 5 ]]; then
  exit 0
fi
if [[ "$(TZ=America/Los_Angeles date +%H)" != "13" ]]; then
  exit 0
fi
if [[ "$(TZ=America/Los_Angeles date +%M)" != "30" ]]; then
  exit 0
fi

cd /opt/butterflyguy
exec /opt/butterflyguy/.venv/bin/python src/butterfly_guy/scripts/generate_live_performance.py
