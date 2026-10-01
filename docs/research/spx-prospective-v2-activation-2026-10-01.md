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
