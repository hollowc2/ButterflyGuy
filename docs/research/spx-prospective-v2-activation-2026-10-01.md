# SPX prospective execution validation v2 registration

The corrected harness merged in PR #39 at
`f4fad7d9f97e966d9e76d72d67a1ff5a76d61ece`. This dedicated branch preserves
those Python sources, configs, and dependency lockfile. The only updater changes
select this separate study and require `uv run --locked`.

Study: `spx-prospective-v2-2026-10-02`.
First eligible session: October 2, 2026 (US Eastern exchange date).
Checkout: `/mnt/Repos/Trading/Butterflyguy/.worktrees/spx-prospective-v2`.
Branch: `cohort/spx-prospective-v2-2026-10-02`.
Timer: `butterfly-cohort-v2-update.timer`, weekdays at 18:30 Pacific, with up to
five minutes of randomized delay. State/logs: `~/.local/state/butterfly-cohort-v2`.
The existing database tunnel is reused. Authentication remains in the existing
protected environment file; its values are not copied into research artifacts.

## Registered experiment

SPX, one-lot frozen entry and exit rules from `configs/config.yaml`; recorded
Schwab evidence in the existing Helios TimescaleDB. Compare corrected midpoint,
marketable bid/ask, and stressed marketable accounting on the same decisions.
Keep the existing costs and rejection/endpoint criteria: $0.65 commission per
contract, $0.05 adverse stress per leg, 120 eligible trades, at least 20 cash
settlements and 15 stressed winners, and a $12,000 maximum acceptable stressed
drawdown. These are research criteria, not changed runtime trading limits.
Registration happens before observing October 2 data. Development baseline:
March 13 through September 18, 2026; no newer data is used in that replay.

Missing session evidence pauses the updater at the first incomplete date. It
records a hashed deferral and retries before later sessions. Integrity failures
block updates. The endpoint stops additional observations; the 20- and 60-trade
operator reviews remain manual. No observations from v1 are pooled into v2.

## Retiring v1

Disable `butterfly-cohort-update.timer` when v2 has been registered, verified,
and its new timer installed. The original checkout, branch, manifest and ledgers
remain intact at `/mnt/Repos/Trading/Butterflyguy-cohort`. This closes v1 as an
unfinished experiment with the documented version 1 harness limitations; it
does not mean v1 reached its registered endpoint or established profitability.

## Operational checks

Run from the dedicated v2 checkout:

```bash
uv run --locked python -m butterfly_guy.scripts.run_prospective_execution verify \
  --cohort reports/prospective_execution/spx-prospective-v2-2026-10-02
systemctl --user status butterfly-cohort-v2-update.timer
systemctl --user list-timers butterfly-cohort-v2-update.timer
```

Do not rebase this branch, merge a later main into it, or edit frozen source,
configuration or dependency files. Close and register a separate study if they
must change. Ledger/report commits stay on this cohort branch.

## Activation and paper deployment evidence

Registered at `2026-10-02T01:45:53.345174Z` (October 1 Pacific/Eastern), from
clean commit `8b276f18cbab99874c316e773e3ad1e594983284`. Manifest schema 2;
initial ledgers contain zero sessions, trades, and deferrals. Report and ledger
verification passed. The updater also passed a no-eligible-session run through
October 1. The v2 timer is enabled; its first scheduled run is October 2 at
18:31:35 Pacific. The original v1 timer is disabled.

V1 is preserved at `d6d4da8ddaeb213908e1587fbed132a59ef2145c` on its original
branch and checkout; the pinned v1 CLI passed ledger verification. Its final
recorded dates are September 22–30: seven trades, two settlements, one stressed
winner, stressed net -$174.20 and drawdown $1,113.40. October 1 was attempted but
deferred because official settlement was not yet available. Its absence from the
ledger must not be interpreted as a verified no-signal
session. No v1 artifact was rewritten for this closure.

Helios paper services `infra/app_spx`, `infra/app_ndx`, and `infra/app_xsp` were
targeted individually with `up --no-deps --no-build --pull never`, using the
existing Compose configuration plus an image-only overlay. Deployment source:
`f4fad7d9f97e966d9e76d72d67a1ff5a76d61ece`; image:
`sha256:8d6f67ba1812488836aa66f2d61af69e6220514e745ae5e4b7e6999f64db5d58`.
The unrelated staged gateway-backfill checkout was preserved. Runtime configs,
paper mode, account/order routing, mounts and data services were retained.
All migration checksums already matched, so no new migration was required.

The initial SPX attempt rolled back when `/ready` failed. Investigation showed
the restored release fails the same gateway spot-freshness check after the market
close. The final rollout therefore validated `/health` and normal startup while
accepting only the explicit after-close stale-spot condition; it did not bypass or
change the freshness guard. All three apps remain entry-gated until fresh market
data is available. `/ready` during a regular session remains a follow-up check.
Pre- and post-deployment read-only audits found no open database trades,
nonterminal intents, broker option positions, or active orders. Each strategy has
one running app; the existing SPX candidate container remains stopped.

Helios rollback record and overlays:
`/opt/butterflyguy/.rollbacks/prospective-v2-20261001/`.
Restore the recorded app images with:

```bash
bash /opt/butterflyguy/.rollbacks/prospective-v2-20261001/rollback.sh
```

The original images are retained. No pruning or persistent-volume cleanup was run.

The new user service was run manually on October 1 at 18:50 Pacific. It returned
`Result=success`, `ExecMainStatus=0`, verified all ledgers, and committed and pushed
its empty report on the dedicated cohort branch. The tunnel and both frozen
checkouts remain available; the old timer remains disabled.

## Completed development baseline

The candidate image completed the March 13–September 18 read-only replay with
118 trades and 23 cash settlements. Full output is in
`spx-v2-baseline-20260313-20260918.txt`; command, source/config/lock hashes,
coverage and output checksum are in its `.provenance.json` companion. All 39
registered source/lock hashes match deployed commit `f4fad7d`.

Corrected midpoint: net $21,952.20, expectancy $186.04, profit factor 2.344,
win rate 19.5%, drawdown $3,789.80. Marketable: net $18,468.20, expectancy
$156.51, profit factor 1.952, win rate 16.1%, drawdown $5,048.80. Stressed
marketable: net $14,208.20, expectancy $120.41, profit factor 1.611, win rate
15.3%, drawdown $7,108.00. Midpoint commission drag is $553.80 and exposure is
42.9% of available session time; average winner/loser are $1,664.55/-$171.92.
The 23 settlements contribute $36,005.20 under midpoint, leaving intraday exits
negative in aggregate. This is already-seen development evidence.

The historical CLI discovered 128 dates against 131 calendar sessions. It skipped
two discovered dates for missing usable data and eight for no qualifying entry.
All 118 entries were executable, but 17 of 22,182 exit-path observations lacked
required quotes and were skipped. No raw quote export was created; database-row
immutability is not established by this replay's output checksum. These historical
coverage limitations remain disclosed separately from v2's future calendar-first
completion guard.

This reproduces the newly frozen source against current database evidence, and
does **not** reproduce the older September 20 fixture's $17,691.60 midpoint net
and 22 settlements. Midpoint net is $4,260.60 higher; the contribution of earlier
shared-code changes versus database revisions has not been attributed. Preserve
both records. Do not treat that difference as strategy improvement or pool this
historical run with the new prospective cohort. Its registered parameters and
decision criteria were not tuned using this replay.
