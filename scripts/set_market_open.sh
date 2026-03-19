#!/usr/bin/env bash
# Pins the trading dashboard time range to start at market open (8:30 AM ET).
# Runs at 8:30 AM ET on trading days via cron.

set -euo pipefail

GRAFANA_URL="http://localhost:3000"
GRAFANA_USER="admin"
GRAFANA_PASS="butterfly"
DASHBOARD_UID="butterfly-trading"

# Current epoch in milliseconds — this IS 8:30 AM ET when cron fires
FROM_MS=$(date +%s000)

# Fetch current dashboard JSON
CURRENT=$(curl -sf "${GRAFANA_URL}/api/dashboards/uid/${DASHBOARD_UID}" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}")

FOLDER_ID=$(echo "$CURRENT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['meta'].get('folderId', 0))")

# Build updated dashboard: set time.from to exact epoch ms, keep time.to as now
PAYLOAD=$(echo "$CURRENT" | python3 -c "
import sys, json
d = json.load(sys.stdin)
dash = d['dashboard']
dash['time']['from'] = '${FROM_MS}'
dash['time']['to'] = 'now'
dash['version'] = dash.get('version', 0) + 1
print(json.dumps({'dashboard': dash, 'folderId': ${FOLDER_ID}, 'overwrite': True}))
")

curl -sf -X POST "${GRAFANA_URL}/api/dashboards/db" \
  -u "${GRAFANA_USER}:${GRAFANA_PASS}" \
  -H "Content-Type: application/json" \
  -d "$PAYLOAD" > /dev/null

echo "$(date): Trading dashboard pinned to market open (${FROM_MS})"
