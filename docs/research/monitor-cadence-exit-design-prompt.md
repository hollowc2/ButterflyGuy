# Implementation prompt: a designed position-monitor cadence, exit confirmation and leg fetch

Written 2026-11-16. Paste everything below the line into a fresh Claude Code session at the
repository root.

---

## Goal

Replace three accidental choices in the live position monitor with one deliberate,
evidence-backed design:

1. **Poll cadence.** It is a hard-coded `poll_interval = 2` today. Make it a validated
   setting.
2. **Exit confirmation and value quality.** Today one poll beyond the drawdown threshold
   exits, and one bad quote can set the peak. Choose a confirmation rule, a peak/value
   quality rule and the drawdown thresholds *together with* the cadence, using the
   stored high-frequency data.
3. **Leg fetch.** Today every poll downloads the whole 0DTE chain (~1,000 contracts) to
   value three legs. Fetch quotes for the three held leg symbols instead, if the evidence
   supports it.

The work runs in four phases, each ending at a **stop point where you report to the owner
(Corey) and wait for approval**:

- **Phase 0:** verification.
- **Phase 1:** investigation and pre-registration.
- **Phase 2:** analysis and design decision.
- **Phase 3:** implementation, behind settings whose defaults reproduce today's behavior,
  then a paper rollout.

Do not skip a stop point. Do not change live trading behavior without explicit approval.

Read `AGENTS.md` first and follow it. This code runs a PAPER SPX bot on Helios. A supervised
real-money SPX pilot exists and is currently paused. Treat position-monitor, exit,
provider, schema and config changes as high-impact.

## Background (verified 2026-11-16; re-verify every claim in Phase 0)

### How live handles data today (main `4e05f14`)

| Component | What it does | Cadence | Stored in |
|---|---|---|---|
| Collector (`data/collector.py`) | Full 0DTE chain + spot + VIX | 60 s, aligned to the minute (`collector.snapshot_interval_seconds`) | `option_chain_snapshots`, `chain_snapshot_meta` |
| Entry (`services/trade_service.py`, `execution/order_manager.py`) | Fresh chain at decision time; price ladder 0.10 x 4 steps, 20 s apart | per attempt | `broker_order_intents` (leg quotes at submit, ack and fill) |
| Position monitor (`services/position_service.py`, `_monitor_loop`) | Fetch full chain, extract 3 legs, value fly at leg marks, update peak, `ProfitStateMachine.evaluate`, act | sleep 2 s **after** the work, so a median of about 2.6 s direct (max seen 5.8 s) | `monitoring_leg_quotes` (3 legs, spot, fly_mark, peak, drawdown per poll) |
| Post-exit recorder (PR #80, deployed to paper SPX 2026-11-16) | After an exit, keeps polling the closed fly's legs until the close; recording only | same `poll_interval` | `post_exit_leg_quotes` (migration 012) |

- **`poll_interval = 2`:** hard-coded at `src/butterfly_guy/services/position_service.py`
  (about line 379), not in config. It was set by commit `38a8667` (2026-03-27) after the
  2026-03-26 trade. That fly peaked at $5.65 on a $2.18 entry and exited at $2.12 because a
  10 s poll skipped through the drawdown threshold. The original value was 10 s. No study
  chose 2 s.
- **Full-chain fetch:** `SchwabClientWrapper.get_option_chain` (`data/schwab_client.py`)
  requests `from_date=to_date=expiration` with no strike limit, so the whole chain.
  `_extract_quotes` then keeps three strikes. The wrapper has no option-quote method today.
  `get_equity_quotes` exists, and the underlying schwab-py client's `get_quotes([...])`
  returned SPXW leg quotes fine on 2026-11-16.
- **Gateway mode:** NDX and XSP still use the gateway. Paper SPX used it until 2026-11-16
  15:02 PT. The gateway caches option chains with a 4 s TTL while upstream fetches take
  4–6 s (`docs/archive/schwab-gateway/runbooks/schwab-gateway-option-chain-latency-investigation.md`).
  In Oct–Nov, 76% of paper SPX polls were exact repeats of the previous poll; the live trade
  on direct data had 4%. Paper SPX now runs `SCHWAB_ACCESS_MODE=direct` (set in Helios's
  untracked `infra/.env`; the repo compose default is already `direct`). Whether the
  gateway exposes a per-symbol option quote endpoint is **unknown**: check it.
- **Exit rules** (`configs/config.yaml` `profit_management`): `peakvaluetrailer`.
  - Regimes by minutes after the open: morning 0–120 at 0.60 drawdown, late_morning 120–240
    at 0.90, afternoon 240–390 at 0.75.
  - `confirmation_polls: 1` in every regime; `min_peak_profit_ratio: 1.0`.
  - `quote_quality.enabled: false`.
  - The live logic is `position/state_machine.py` and `position/profit_policy.py`. The
    research engine's `PeakTrailer` in `research/exits.py` mirrors it and **reproduced 82 of
    109 recorded SPX exits to the millisecond** (all Aug–Nov 2026; June/July used an
    older config).
- **Research and backtests run on 1-minute data** (collector snapshots and ThetaData 1m).
  Live decides at about 2.6 s, so the exit thresholds were effectively tuned at a different
  cadence from the one they run at.

### Evidence so far (exploratory, post hoc)

From `tools/research_studies/monitor_replay_study.py`, output in
`reports/research/spx-monitor-replay-20261116/`, on 82 matched SPX trades:

| Variant | vs live (2.6 s, conf 1) | Note |
|---|---|---|
| Decide only once a minute (backtest cadence) | **−$15/trade**, 95% CI −21 to −9 | Fast polling helps: it exits falling flies sooner |
| Leg-spread filter (reject a poll when a leg's spread > max(0.50, 4x its recent median)) | −$63 total, 5 exits changed; rejects 0.08% of polls | Neutral |
| One-poll spike sets the peak | 3 of 109 trades; net +$30 if filtered | Rare, mixed |
| conf2 / conf3 / median-of-5 | +$3–5/trade, CI includes 0 | **Not measurable yet:** polls ended at the exit, so delayed exits fell back to 1-minute data. Post-exit polls (PR #80) fix this going forward |
| Exit valued at bid instead of mid | about −$15.6/trade | Fill quality is a larger lever than cadence |

- **Trade 415 (first real-money trade, 2026-11-16):**
  - The peak of 6.95 came from one poll where the 7460 put quoted 35.10/39.80; neighbors put
    the fly at about 4.85, and the 1-minute peak was 5.65.
  - The exit fired on one poll (2.15 → 1.65, 76.3% drawdown against 6.95).
  - Its exit filled at 1.30 against a 1.85 mid and 1.00 bid.
  - On that day the bad peak happened to help: the fly settled at 0.
- **Width study** (`tools/research_studies/width_selection_study.py`): unrelated to this
  task, but it shows the expected scale. Effects of a few dollars per trade are within noise
  at this sample size.

### Data available

- **`monitoring_leg_quotes`:** SPX 109 trades / about 361k polls since 2026-06-04; also
  XSP (about 104 trades) and NDX (about 96).
- **`post_exit_leg_quotes`:** empty until the first paper SPX exit after 2026-11-16.
  Accrues roughly one trade per session.
- **`broker_order_intents`:** execution observations for live orders. Trade 415 is the only
  real-money exit so far.
- The extraction used on 2026-11-16 (three SQL dumps, `trades`, `polls`, `minute`, run inside
  `butterfly_spx_app` with asyncpg and `load_config`) is described in the replay script's
  docstring. Add `post_exit_leg_quotes` as `post_exit.csv.gz`; the script already continues
  on it when present.
- **Housekeeping:** both research scripts and their reports are **uncommitted** in the
  main checkout (branch `research/direction-vix-oos`, which also carries unrelated work).
  Move them onto a clean branch off `main` first.

## Constraints

- **The owner prefers offline research.** Do not create shadows, forward tests, cron jobs or
  timers unless asked.
- **Tokens:** never mint or refresh Schwab tokens, and never restart token consumers just
  to pick up a token. Consumers hot-reload.
- **Schwab rate limits:** count every consumer (collector, monitor, the post-exit recorder,
  NDX/XSP via the gateway, the gateway itself) before adding request load. Show the budget.
- **Do not change** trading limits, account guards, order routing or paper/live mode. Do
  not change NDX or XSP behavior unless the owner asks.
- **Keep current behavior as the default:** poll 2 s, confirmation by poll count 1, no value
  filter, full-chain fetch. Any new behavior is opt-in until approved.
- **Research and live must stay in parity.** Whatever rule ships must be implemented
  identically in `position/state_machine.py` and `research/exits.py`, with a parity test.
- **Statistics:** 2020–2026 history has all been looked at, and the monitor data starts
  2026-06. Label results exploratory unless pre-registered on data not yet seen. Use paired
  per-trade differences with the block bootstrap in `research/evaluate.py`. Report effect
  sizes with CIs, not just totals.
- **Times:** tell the owner times in Pacific; crontab and the DB are UTC.

## Phase 0: verify (read-only)

1. Re-verify every fact in Background against `origin/main` and Helios. Use `ssh helios`;
   `uv` is at `/home/billy/.local/bin/uv`. Check:
   - the poll loop and where time is spent per poll;
   - the `post_exit_leg_quotes` row count and which trades have it;
   - the paper SPX access mode;
   - whether the stale-repeat share dropped after the 2026-11-16 switch to direct data.
2. Measure per-poll latency on paper SPX from `monitoring_leg_quotes` timestamps, before and
   after 2026-11-16 15:02 PT.
3. Read-only, inside the paper container: time `get_option_chain` against `get_quotes` for
   three SPXW symbols, about 20 each, spaced out and only while the market is open. Compare:
   - latency and payload size;
   - field parity: bid/ask/mark, plus per-leg quote time (`quoteTimeInLong` or equivalent);
   - whether chain and quote values match at the same moment.

   Confirm the request count against the rate budget first. Check whether the gateway
   offers an equivalent per-symbol endpoint.
4. Commit the two research scripts on a fresh research branch (no other files).

**Stop point 0:** report the verified facts, any corrections to this prompt, the latency and
parity numbers, and how many trades have post-exit data. Wait.

## Phase 1: investigation plan and pre-registration

Write `docs/research/monitor-cadence-exit-design-plan.md` with:

1. **Data and split.**
   - Use matched trades only: the as-live replay must reproduce the recorded exit within 10 s
     with the same reason. Report the match rate and exclude mismatches.
   - Choose a development set: existing Aug–Nov trades with monitor data, where delayed
     exits still fall back to 1-minute data, so flag them.
   - Choose a confirmation set: trades recorded **after** PR #80 with post-exit polls, not
     looked at until the plan is approved.
   - State the minimum trade count before Phase 2 runs (suggest at least 20 post-exit trades;
     justify it with a power estimate from the development set's per-trade SD).
2. **The candidate grid. Keep it small, because each extra arm costs power.**
   - Decision cadence, by subsampling the recorded polls: 2.6 s as recorded, 5 s, 10 s,
     15 s, 30 s, 60 s.
   - Confirmation: by poll count (1, 2, 3) and **by time** (value beyond the threshold for
     ≥ 0, 5, 10, 20 s). Time-based is cadence-independent, which makes research and live
     parity easier.
   - Value quality: none; reject polls with leg-spread blowouts or crossed/missing legs;
     causal median of the last N seconds. Apply it to the peak only, or to both peak and
     current value.
   - Thresholds: by default keep today's regime thresholds. Include threshold changes only
     if justified, and only jointly with confirmation (they interact).
3. **Exit pricing for every arm:** at mid; at the fly bid (natural credit); and at a
   slippage model fitted to the observed live and paper exits. Rank arms on the realistic
   model, not mid.
4. **Primary metric and decision rule, fixed in advance.** Example:
   - Adopt arm X only if its paired mean difference vs current is > 0 on the confirmation
     set, with the lower 90% bound above −$2/trade.
   - It must not be worse on the development set.
   - The worst day may be no worse by more than $Y.

   Otherwise keep current values and ship only the plumbing.
5. **Secondary diagnostics:** exits changed, holding-time change, how often a one-poll spike
   sets the peak, time between signal and fill, and request load per arm.
6. **Fetch design:** quotes-for-three-legs vs full chain.
   - Decide by latency, freshness (per-leg quote time), parity and rate load.
   - Keep the full chain where something else needs it: the collector, entry, settlement
     fallback, and `exit_mark_parity_report`.
   - Define the fallback if a leg quote is missing.
7. **Backtest implications:** how the research engine will simulate the chosen design on
   1-minute history, and the documented bias of doing so (the −$15/trade cadence effect is
   the scale to expect). Decide whether `run_backtest_db` and the research core should use
   `monitoring_leg_quotes` for recent sessions.

**Stop point 1:** the owner approves the plan, grid, split and decision rule. Do not look at
the confirmation set before this.

## Phase 2: analysis and design decision

1. Extend the replay script.
   - Add the grid, time-based confirmation, the value-quality options and the slippage
     model.
   - Continuation after the recorded exit must use post-exit polls; refuse to mix in 1-minute
     data on the confirmation set.
   - Add tests for the new rule logic under `tests/`, following existing research tests.
2. Run on the development set, then **once** on the confirmation set. Write
   `docs/research/monitor-cadence-exit-design-results.md` with:
   - tables;
   - CIs;
   - per-regime breakdowns;
   - a short list of the trades the chosen arm changes, with before/after exit times and
     values;
   - the request-load numbers;
   - the decision against the pre-registered rule.
3. Write the design: setting names, defaults, units, validation, and how research and live
   share the rule. Suggested shape (adjust to the code):
   - `profit_management.poll_interval_seconds` (validated range, e.g. 1–10);
   - confirmation in seconds per regime (e.g. `confirmation_seconds`), keeping
     `confirmation_polls` for backward compatibility or migrating it explicitly;
   - a `quote_quality`-style value filter;
   - `position_data.leg_fetch: chain | quotes`.

**Stop point 2:** the owner approves the decision and design, or decides to keep the current
values and ship only the plumbing.

## Phase 3: implementation and rollout (after approval)

Small PRs, each green on CI (`validate` and `timescaledb`), in this order:

1. **Config plumbing, no behavior change.** Move `poll_interval` into config with today's
   value as the default. The post-exit recorder uses the same setting. Tests prove defaults
   reproduce the current loop.
2. **Leg-quote fetch (if approved).**
   - Add `get_option_quotes(symbols)` to `SchwabClientWrapper` and the direct provider, and
     the gateway equivalent if one exists; otherwise gateway mode keeps the chain.
   - Record per-leg quote times. Add nullable `quote_time` columns via a new migration to
     `monitoring_leg_quotes` and `post_exit_leg_quotes`, so readers keep working.
   - Default `chain`.
   - Tests: parsing, a missing leg, a stale leg, fallback.
3. **Confirmation and value rule (if approved).**
   - Implement it identically in `position/state_machine.py` and `research/exits.py`.
   - Add a parity test that runs both over the same synthetic poll sequence.
   - Defaults off.
   - Update `tools/update_grafana_exit_trigger.py` or the dashboards only if they display
     the rule.
4. **Rollout on paper SPX only.**
   - Deploy with the Helios release pattern: git-archive snapshot in `.releases/`, pinned
     image override, rollback dir in `.rollbacks/`. See `docs/live-runbook.md` "Deploy" and
     the 2026-11-16 deployment in `.rollbacks/spx-4e05f14-20261116/`.
   - Check flatness first: the DB check and `tools/deploy_broker_flat_check.py`.
   - Deploy only after hours; verify `migration_complete`, startup events, no error logs,
     and one SPX container.
   - Turn the approved values on in `configs/config.yaml`. It is bind-mounted from the
     Helios checkout; see the config-drift note in the runbook.
   - Watch one to two weeks of paper: realized cadence, request load, rule behavior.
5. **Live pilot.**
   - Rebuild the pilot image from the merged main.
   - Update the live-test staging scripts: `reports/execution_audits/spx-live-test-2026-11-16/`
     is the template. `BASE_IMG`, `BASE_ID`, `CAND` and the rollback override must point at
     the new images.
   - Only when the owner asks to resume live tests.

Each PR: focused tests; `uv run pytest`; `uv run ruff check .`; a PR description with what,
why, load and rollback. Merge only with the owner's approval.

## Deliverables checklist

- [ ] Phase 0 report (stop point 0)
- [ ] `docs/research/monitor-cadence-exit-design-plan.md` (stop point 1)
- [ ] Extended replay study plus tests; `docs/research/monitor-cadence-exit-design-results.md`
      (stop point 2)
- [ ] PRs: config plumbing → leg-quote fetch → confirmation/value rule (each approved)
- [ ] Paper SPX rollout with a rollback directory and a post-rollout check
- [ ] Updated live-test staging template (when live resumes)
