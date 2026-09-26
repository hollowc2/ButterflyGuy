#!/usr/bin/env bash
# Append every completed session to the open prospective cohort, then commit the
# ledgers. Safe to run repeatedly: recorded sessions are skipped, and sessions
# whose data is incomplete are deferred until a later run.
set -uo pipefail

REPO=${BUTTERFLY_REPO:-/mnt/Repos/Trading/Butterflyguy}
COHORT=${BUTTERFLY_COHORT:-reports/prospective_execution/spx-prospective-2026-09-22}
UV=${UV_BIN:-/home/corey/.local/bin/uv}
STATE=${XDG_STATE_HOME:-$HOME/.local/state}/butterfly-cohort
LOG=$STATE/update.log

mkdir -p "$STATE"
cd "$REPO" || { echo "$(date -Is) FATAL: no repo at $REPO" >>"$LOG"; exit 1; }

# One run at a time; a slow run must not overlap the next timer firing.
exec 9>"$STATE/update.lock"
flock -n 9 || { echo "$(date -Is) SKIP: another update is running" >>"$LOG"; exit 0; }

echo "$(date -Is) === update start ===" >>"$LOG"

# Ledgers belong on main only; never commit or push onto a feature branch.
BRANCH=$(git symbolic-ref --short -q HEAD)
if [ "$BRANCH" != "main" ]; then
    echo "$(date -Is) SKIP: checkout is on '${BRANCH:-detached HEAD}', not main" >>"$LOG"
    exit 0
fi

if ! timeout 1800 "$UV" run python src/butterfly_guy/scripts/run_prospective_execution.py \
        update --cohort "$COHORT" >>"$LOG" 2>&1; then
    echo "$(date -Is) FAILED: update returned non-zero" >>"$LOG"
    exit 1
fi

# Verify before trusting what we are about to commit.
if ! timeout 300 "$UV" run python src/butterfly_guy/scripts/run_prospective_execution.py \
        verify --cohort "$COHORT" >>"$LOG" 2>&1; then
    echo "$(date -Is) FAILED: ledger integrity check" >>"$LOG"
    exit 1
fi

if [ -n "$(git status --porcelain -- "$COHORT")" ]; then
    git add -- "$COHORT"
    git commit -q -m "Record prospective cohort sessions through $(date +%F)" \
                  -m "Automated append by cohort_daily_update.sh. Ledger verified before commit." \
        >>"$LOG" 2>&1 || echo "$(date -Is) WARN: commit failed" >>"$LOG"
    if git push -q origin HEAD:main >>"$LOG" 2>&1; then
        echo "$(date -Is) committed and pushed" >>"$LOG"
    else
        echo "$(date -Is) WARN: push failed (commit is local; ssh key may be locked)" >>"$LOG"
    fi
else
    echo "$(date -Is) no new sessions recorded" >>"$LOG"
fi

echo "$(date -Is) === update done ===" >>"$LOG"
