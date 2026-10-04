#!/usr/bin/env bash
# One session of the report-only Schwab-vs-ThetaData fidelity check
# (`research schwab-fidelity`, docs/research/schwab-recording-fidelity-implementation-prompt.md).
#
#   tools/run_schwab_fidelity_daily.sh [YYYY-MM-DD] [--notify]
#
# The date defaults to the previous trading session in Cboe's official SPX daily file (the
# exchange's own record, not time_utils.is_trading_day). Steps:
#   1. download that day's spxw_0dte history (tools/thetadata_download.py; needs the Theta
#      Terminal on 127.0.0.1:25503; a day already on disk is not requested again);
#   2. export the Helios session read-only into a separate recorded dataset (default
#      spx_0dte_fidelity_recorded, never the canonical spx_0dte);
#   3. snapshot its supporting observations and fetch Cboe's daily closes;
#   4. import the vendor day into a dated local dataset spx_0dte_local_fidelity_<date>;
#   5. run schwab-fidelity, and with --notify send its one-line summary to Telegram.
# Every dataset is immutable or append-only, so a rerun reuses what is already there.
# Nothing here is installed in cron; see the PR for a suggested crontab line.
set -euo pipefail

REPO=$(cd "$(dirname "$0")/.." && pwd)
UV=${UV_BIN:-uv}
SOURCE=${FIDELITY_EXPORT_SOURCE:-tunnel}   # tunnel | docker
RECORDED=${FIDELITY_RECORDED_DATASET:-spx_0dte_fidelity_recorded}
export BUTTERFLY_RESEARCH_CACHE=${BUTTERFLY_RESEARCH_CACHE:-$REPO/data/research_cache}
STATE=$REPO/reports/data_management/schwab_fidelity/daily
mkdir -p "$STATE"
cd "$REPO"

DAY="" NOTIFY=0
for arg in "$@"; do
    case "$arg" in
        --notify) NOTIFY=1 ;;
        [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) DAY=$arg ;;
        *) echo "usage: $0 [YYYY-MM-DD] [--notify]" >&2; exit 2 ;;
    esac
done
if [ -z "$DAY" ]; then
    DAY=$("$UV" run --locked python - <<'EOF'
import datetime as dt, sys
sys.path.insert(0, "tools")
from thetadata_download import cboe_sessions
print(max(d for d in cboe_sessions() if d < dt.date.today()))
EOF
)
fi
research() { "$UV" run --locked python -m butterfly_guy.research "$@"; }
echo "$(date -Is) schwab fidelity for $DAY"

if [ ! -f "$REPO/data/thetadata/spxw_0dte/quote_1m/${DAY:0:4}/$DAY.parquet" ]; then
    "$UV" run tools/thetadata_download.py --sets spxw_0dte --start "$DAY" --end "$DAY"
fi
research --dataset "$RECORDED" export --start "$DAY" --end "$DAY" --source "$SOURCE"

SUPPORT=local_support_fidelity_$DAY
VENDOR=spx_0dte_local_fidelity_$DAY
if [ ! -d "$BUTTERFLY_RESEARCH_CACHE/$SUPPORT" ]; then
    research --dataset "$SUPPORT" cache-inputs --output-cache "$BUTTERFLY_RESEARCH_CACHE" \
        --input-dataset "$RECORDED" --start "$DAY" --end "$DAY" --out "$STATE"
fi
if [ ! -d "$BUTTERFLY_RESEARCH_CACHE/$VENDOR" ]; then
    DAILY=$(research cache-daily --directory "$STATE/cboe-daily" \
        | sed -n 's/^cached daily observations: //p')
    research --dataset "$VENDOR" import-local --archive "$REPO/data/thetadata" \
        --set spxw_0dte --support "$SUPPORT" --daily-cache "$DAILY" --start "$DAY" \
        --end "$DAY" --out "$STATE"
fi

OUT=$(research schwab-fidelity --vendor-dataset "$VENDOR" --reference "$RECORDED" \
    --start "$DAY")
echo "$OUT"
LINE=$(printf '%s\n' "$OUT" | grep '^Schwab fidelity ' | tail -1)
if [ "$NOTIFY" = 1 ] && [ -n "$LINE" ]; then
    "$UV" run --locked python -c 'import sys; from dotenv import load_dotenv; load_dotenv(); from butterfly_guy.notify import send; sys.exit(0 if send(sys.argv[1]) else 1)' "$LINE" \
        || echo "telegram send failed (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID set?)" >&2
fi
