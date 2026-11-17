# Shared settings and helpers for a concurrent SPX live (or rehearsal) session. Sourced.
#
# v2 of the live-test scripts: the live bot is its own container (butterfly_spx_live_app,
# compose project butterfly-spx-live) beside paper. Nothing here creates, recreates,
# restarts or stops butterfly_spx_app; every script proves paper is untouched.
# docs/operations/concurrent-paper-live-spx-design.md §10.
#
# Per-session values live in session.env next to the scripts (see session.env.example).
# DRY_RUN=1 runs every read and gate but only prints the commands that change anything.

D=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
# shellcheck source=/dev/null
source "$D/session.env"

: "${DATE:?set DATE in session.env}" "${REL:?set REL in session.env}" "${CAND:?set CAND in session.env}"
REHEARSAL=${REHEARSAL:-0}
DRY_RUN=${DRY_RUN:-0}
ROOT=${ROOT:-/opt/butterflyguy}
INFRA=${INFRA:-$ROOT/infra}
DATA=${DATA:-$ROOT/data}
PY=${PY:-$ROOT/.venv/bin/python}
WAIT_SECONDS=${WAIT_SECONDS:-120}
LIVE_PORT=8002
PAPER_C=butterfly_spx_app
PAPER_DB=butterfly_guy
LIVE_C=butterfly_spx_live_app
CONTAINER_UID=${CONTAINER_UID:-1001}
# A path, not a secret: the host directory every token consumer binds.
TOKEN_DIR=${TOKEN_DIR:-$(sed -n 's/^SCHWAB_GATEWAY_TOKEN_DIR=//p' "$INFRA/.env" | tr -d '"')}

COMPOSE_FILES=(-f "$REL/infra/docker-compose.spx-live.yml")
if [ "$REHEARSAL" = 1 ]; then
  LABEL="SPX live REHEARSAL (paper mode)"
  LIVE_DB=butterfly_guy_spx_live_rehearsal
  CHAINS=chains-live-rehearsal
  CHECK_ARGS=(--allow-paper-trades)
  COMPOSE_FILES+=(-f "$REL/infra/docker-compose.spx-live-rehearsal.yml")
  EXPECT_ENV=(
    BUTTERFLY_INSTANCE_ROLE=live_rehearsal
    "DATABASE__NAME=$LIVE_DB"
    EXECUTION__PAPER_TRADING=true
    ALLOW_LIVE_TRADING=false
    EXECUTION__ALLOW_LIVE_TRADING=false
  )
  FORBID_ENV=(EXECUTION__LIVE_TEST_DATE LIVE_ACCOUNT_ALLOCATION LIVE_MAX_ACCOUNT_DAILY_LOSS
              EXECUTION__EXIT_PRICING)
else
  LABEL="SPX live"
  LIVE_DB=butterfly_guy_spx_live
  CHAINS=chains-live
  CHECK_ARGS=()
  # Exactly the replace-paper pilot's limits; exits on the default bid ladder.
  EXPECT_ENV=(
    BUTTERFLY_INSTANCE_ROLE=live
    "DATABASE__NAME=$LIVE_DB"
    EXECUTION__PAPER_TRADING=false
    "EXECUTION__LIVE_TEST_DATE=$DATE"
    EXECUTION__LIVE_TEST_MAX_DEBIT=4.0
    EXECUTION__RECORD_LIVE_EXECUTION=true
    EXECUTION__LIVE_TEST_QUOTE_MAX_AGE_SECONDS=10
    RISK__MAX_POSITION_SIZE=1
    RISK__MAX_TRADES_PER_DAY=1
    LIVE_ACCOUNT_ALLOCATION=20000
    LIVE_MAX_ACCOUNT_DAILY_LOSS=500
    SCHWAB_ACCESS_MODE=direct
  )
  FORBID_ENV=(EXECUTION__EXIT_PRICING)
fi

ts() { date -u +%FT%TZ; }

open_log() {
  # Dry runs print to the terminal; real runs append to the session log.
  [ "$DRY_RUN" = 1 ] || exec >>"$D/$1.log" 2>&1
}

act() {
  # Runs a command that changes something; a dry run prints it instead. Compose calls
  # print their exact docker command line.
  if [ "$DRY_RUN" != 1 ]; then
    "$@"
    return
  fi
  case "$1" in
    compose | db_tool) PRINT_ONLY=1 "$@" ;;
    *) echo "DRY_RUN: $*" ;;
  esac
}

notify() { act "$PY" "$D/notify.py" "$1" || echo "$(ts) notify failed"; }

compose() {
  local cmd=(env "SPX_LIVE_IMAGE=$CAND" "SPX_LIVE_TEST_DATE=$DATE"
    docker compose --project-directory "$INFRA" "${COMPOSE_FILES[@]}" "$@")
  if [ "${PRINT_ONLY:-0}" = 1 ]; then
    echo "DRY_RUN: ${cmd[*]}"
  else
    "${cmd[@]}"
  fi
}

db_tool() {
  local sub=$1
  shift
  compose --profile tools run --rm -T spx_live_db_tool \
    python -m butterfly_guy.scripts.spx_live_db "$sub" --db "$LIVE_DB" "$@"
}

running() {
  docker ps --filter "name=^$1\$" --filter status=running --format '{{.Names}}' | wc -l | tr -d ' '
}

container_env() { docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$1"; }

paper_fingerprint() {
  docker inspect -f '{{.Id}} {{.Image}} {{.State.StartedAt}} {{.RestartCount}} {{.State.Running}}' "$PAPER_C"
}

paper_is_paper() {
  local env
  env=$(container_env "$PAPER_C") || return 1
  grep -qx "DATABASE__NAME=$PAPER_DB" <<<"$env" && ! grep -qx "EXECUTION__PAPER_TRADING=false" <<<"$env"
}

token_match() {
  # Same inode and digest on the host and inside container $1. Compared silently; the
  # token document is never printed or copied. One retry rides out a concurrent refresh.
  local host inside attempt
  for attempt in 1 2; do
    host="$(stat -c %i "$TOKEN_DIR/tokens.json") $(sha256sum <"$TOKEN_DIR/tokens.json" | cut -d' ' -f1)"
    inside=$(docker exec "$1" sh -c 'echo "$(stat -c %i "$SCHWAB_TOKEN_PATH") $(sha256sum <"$SCHWAB_TOKEN_PATH" | cut -d" " -f1)"')
    [ "$host" = "$inside" ] && return 0
    [ "$attempt" = 1 ] && sleep 2
  done
  return 1
}

broker_flat() {
  # Read-only and account-wide (SPX, NDX, XSP), so the paper container is a valid host.
  docker exec -i "$PAPER_C" python - <"$REL/tools/deploy_broker_flat_check.py"
}

verify_live() {
  # Prints the first failed check, nothing when the live container is healthy.
  local p0=$1 env logs mount errs k kv
  [ "$(docker inspect -f '{{.Image}}' "$LIVE_C" 2>/dev/null)" = "$CAND" ] || { echo "live image is not $CAND"; return; }
  [ "$(docker inspect -f '{{.State.Running}} {{.RestartCount}}' "$LIVE_C")" = "true 0" ] || { echo "live container is not running cleanly"; return; }
  env=$(container_env "$LIVE_C")
  for kv in "${EXPECT_ENV[@]}"; do
    grep -qxF "$kv" <<<"$env" || { echo "live env lacks $kv"; return; }
  done
  for k in "${FORBID_ENV[@]}"; do
    grep -q "^$k=" <<<"$env" && { echo "live env must not set $k"; return; }
  done
  mount=$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/data/chains"}}{{.Source}}{{end}}{{end}}' "$LIVE_C")
  [ "$mount" = "$DATA/$CHAINS" ] || { echo "chain journal mount is '$mount', not $DATA/$CHAINS"; return; }
  token_match "$LIVE_C" || { echo "token file differs between host and live container"; return; }
  logs=$(docker logs "$LIVE_C" 2>&1)
  grep -q '"live_trading_starting"' <<<"$logs" || { echo "no live_trading_starting log"; return; }
  errs=$(grep -E '"level": "(error|critical)"|Traceback' <<<"$logs" | head -3)
  [ -z "$errs" ] || { echo "errors at startup: $errs"; return; }
  curl -sf "http://127.0.0.1:$LIVE_PORT/health" >/dev/null || { echo "metrics port $LIVE_PORT not answering"; return; }
  [ "$(running "$PAPER_C")" = 1 ] && [ "$(running "$LIVE_C")" = 1 ] \
    || { echo "container count paper=$(running "$PAPER_C") live=$(running "$LIVE_C")"; return; }
  [ "$(paper_fingerprint)" = "$p0" ] || { echo "PAPER CONTAINER CHANGED"; return; }
}

export_evidence() {
  # report_spx_live_test.py runs inside the live container, so it reads the live DB only.
  # docker cp cannot read the container's tmpfs /tmp, so stream it out with tar.
  docker exec -i "$LIVE_C" python - --date "$DATE" --out-dir /tmp/spx-live-evidence \
    <"$REL/tools/report_spx_live_test.py" \
    && docker exec "$LIVE_C" tar -C /tmp/spx-live-evidence -cf - . | tar -C "$1" -xf -
}

save_logs() { docker logs "$LIVE_C" >"$1/container.log" 2>&1; }

paired_report() {
  # Read-only on both databases; see butterfly_guy.reports.spx_paired.
  compose --profile tools run --rm -T spx_live_db_tool \
    python -m butterfly_guy.scripts.spx_live_db compare --date "$DATE" --live-db "$LIVE_DB" \
    >"$1/paired-report.md"
}

stop_live() {
  # The v2 rollback: stop (never rm) the live container so its logs survive; never paper.
  echo "$(ts) stopping $LIVE_C"
  act compose stop app_spx_live
  [ "$DRY_RUN" = 1 ] || [ "$(running "$LIVE_C")" = 0 ]
}
