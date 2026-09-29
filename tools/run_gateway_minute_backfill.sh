#!/usr/bin/env bash
# Monthly archive of Schwab 1-minute index bars before they leave the gateway's
# ~30-session retention (tools/gateway_minute_backfill.py has the details). Read-only
# gateway GETs, run inside the SPX app container with its own key.
#
# Writes data/gateway_minute/<ET date>-spx.jsonl and <ET date>-vol.jsonl. The VIX-family
# file is the one `research export-vol --gateway-dump` ingests. On a failure the records
# written are kept and a Telegram alert is sent.
set -uo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT"
CONTAINER=${BACKFILL_CONTAINER:-butterfly_spx_app}
LOOKBACK_DAYS=${LOOKBACK_DAYS:-60}
OUT=data/gateway_minute
END=$(TZ=America/New_York date +%F)
START=$(date -d "$END - $LOOKBACK_DAYS days" +%F)
mkdir -p "$OUT"

failed=()
run() {  # run NAME SYMBOL...
    local name=$1
    shift
    local dest="$OUT/$END-$name.jsonl"
    echo "$(date -Is) $name: $START -> $END ($*)"
    if ! docker exec -i "$CONTAINER" python - "$START" "$END" "$@" \
            < tools/gateway_minute_backfill.py > "$dest.tmp"; then
        failed+=("$name")
    fi
    if [ -s "$dest.tmp" ]; then
        mv "$dest.tmp" "$dest"
        echo "$(date -Is) $name: wrote $dest ($(wc -l < "$dest") records)"
    else
        rm -f "$dest.tmp"
    fi
}

run spx '$SPX'
run vol '$VIX' '$VIX9D' '$VIX3M'

if [ ${#failed[@]} -eq 0 ]; then
    echo "$(date -Is) OK"
    exit 0
fi

echo "$(date -Is) FAILED: ${failed[*]}"
msg="Gateway minute backfill FAILED (${failed[*]}) on $END. Schwab keeps ~30 sessions, so re-run within ~10 days: cd $ROOT && tools/run_gateway_minute_backfill.sh. Log: $ROOT/gateway_minute_backfill.log"
.venv/bin/python - "$msg" <<'EOF' || echo "$(date -Is) WARN: Telegram alert not sent"
import os
import sys

from dotenv import dotenv_values

os.environ.update({k: v for k, v in dotenv_values(".env").items() if v is not None})
from butterfly_guy.notify import send

sys.exit(0 if send(sys.argv[1]) else 1)
EOF
exit 1
