#!/usr/bin/env bash
# Gate the weekly universe refresh to Sunday 8:00 PM America/Los_Angeles.
# The UTC cron slots cover PDT and PST; exactly one passes this local-time gate.
set -euo pipefail

if [[ "$(TZ=America/Los_Angeles date +%u)" != "7" ]]; then
  exit 0
fi
if [[ "$(TZ=America/Los_Angeles date +%H)" != "20" ]]; then
  exit 0
fi

cd /opt/butterflyguy
/opt/butterflyguy/.venv/bin/python \
  src/butterfly_guy/scripts/refresh_equity_universes.py
printf '%s equity_universe_refresh_success\n' "$(date -Is)"
