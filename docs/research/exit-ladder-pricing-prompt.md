# Implementation prompt: how the live exit order is priced

Written 2026-11-16. Paste everything below the line into a fresh Claude Code session at the
repository root.

---

## Goal

Decide, with evidence, how the bot should price its closing order on a live exit. Today the
first limit is anchored on the fly's **bid**, not its mid. On the first real-money trade that
gave up $0.55 a contract against mid in about one second. Find out:

- whether the bid anchor was deliberate;
- what it costs across real market conditions;
- what a better rule would be, given that a drawdown exit is a stop and a slow fill also
  costs money.

Four phases, each ending at a **stop point where you report to the owner (Corey) and wait**:

| Phase | Content |
|---|---|
| 0 | Verification (read-only) |
| 1 | Plan and pre-registration |
| 2 | Analysis and design decision |
| 3 | Implementation behind a setting whose default reproduces today, then rollout |

**Order pricing is order routing: high-impact.** Do not change live or paper order behavior
without explicit approval. Read `AGENTS.md` first and follow it. A supervised real-money SPX
pilot exists and is paused; paper SPX runs on Helios.

## Background (verified 2026-11-16; re-verify every claim in Phase 0)

### The code (main `a283610`)

`OrderManager.execute_exit` in `src/butterfly_guy/execution/order_manager.py`:

- **Paper:** fills at the signal mark (`_mark_paper_fill`). It still fetches and stores the
  fly's live bid, mark and ask (`spread_bid`, `spread_mark`, `spread_ask` in the fill
  result).
- **Live:** each ladder step does the following.
  1. Fetch the full chain (`_fetch_live_spread`) and append the fly bid to a 3-long deque
     (`EXIT_BID_ANCHOR_WINDOW = 3`).
  2. Set the anchor to the median of those bids. The variable is misleadingly named
     `mid_price`.
  3. Set the limit to `round_credit_limit(max(0.05, anchor + (steps − 1 − i) × step))`.
  4. Submit, then wait `retry_interval_seconds` for a fill. If none, cancel, check for a
     post-cancel fill, and take the next step.

  The loop repeats until `order_timeout_seconds`. With `configs/config.yaml` execution
  settings (step 0.10, 4 steps, 20 s retry, 300 s timeout) the limits are **bid + 0.30,
  +0.20, +0.10, +0.00**, 20 s apart.
- **History:** the original "ratchet price ladder" commit `32dfa7e` anchored on a running
  bid floor. Review item L12 (`docs/reviews/2026-09-25-code-review.md`, fixed in `df0a484`,
  PR #28) changed the floor to a median of the last 3 bids so one bad tick could not pin
  every step lower. **No study chose a bid anchor or the 0.30 offset.** Review item L8
  already noted that paper (fills at mark) is an optimistic bound on live.
- **Entries are different:** `trade_service.py` (about line 478) uses `ask + step × 0.10`,
  capped by `capped_entry_limit`. But trade 415's live entry filled at a **2.00 limit
  against a 2.10 mid and a 2.60 ask**. Find out which path produced that limit (the live
  test has its own settings: `live_test_date`, `live_test_max_debit`).

### Trade 415 (2026-11-16, first real-money exit)

From `broker_order_intents` `execution_observations` (intent ids 3 and 4):

| | Fly bid / mid / ask | Limit | Fill |
|---|---|---|---|
| Entry, 07:00:15 PT | 1.60 / 2.10 / 2.60 | 2.00 | 2.00 in ~4 s |
| Exit, 12:23:27 PT | 1.00 / 1.85 / 2.70 ($1.70 wide) | 1.30 = bid + 0.30 | 1.30 in ~1 s |

- **Exit sequence:** the monitor signalled at 12:23:25.997 PT with a mark of 1.65
  (`drawdown_afternoon`). The chain fetched 0.5 s later for the order showed a 1.85 mid.
- **Fill seconds after the exit:** bid 0.80, mid 1.80, ask 2.80. The fly kept sliding.
- **Cost:** $0.55 a contract against the submit-time mid, $0.35 against the signal mark.

### Other evidence

- **Manual fills, 10-19** (`docs/research/spx-manual-fill-log-2026-10.txt`): two exits on a
  20-wide fly with a fly spread of about $0.20.
  - Test 2: mid 1.30 filled in ~1 s.
  - Test 4: mid + 0.05 worked 82 s without filling; replaced at mid (0.95) and filled in
    5 s.
  - Entries at mid also filled in 4–9 s.
- **Model scale** (exploratory, `reports/research/spx-monitor-cadence-exit/pilot/`, 69
  matched paper SPX trades Aug–Nov 2026), exits priced at the replay's exit poll:
  - mid: +$3,141
  - `min(mid, natural + 0.30)`: +$2,804, about **−$4.9/trade** vs mid
  - natural: +$2,025, about −$16/trade

  The ladder model costs little when the fly spread is ≤ $0.60 and a lot when it is wide,
  as on 415. Exit-time spreads are widest in exactly the fast markets where drawdown exits
  fire.
- **Related study:** `research/monitor-cadence-exit` (pre-registered; see
  `docs/research/monitor-cadence-exit-design-plan.md`). Its post-exit polls
  (`post_exit_leg_quotes`, since 2026-11-16 15:20 PT, about one trade a session) record
  what the fly did in the seconds and minutes after each exit signal. That is the data
  needed to price the risk of waiting at mid. Do not touch that study's development or
  confirmation sets except as its plan allows. Coordinate, don't duplicate.

## Constraints

- **Offline research only.** No shadows, forward tests, cron jobs or timers unless the
  owner asks. No test orders. Never call Schwab write APIs in research.
- **Tokens:** never mint or refresh Schwab tokens or restart token consumers.
- **Hands off:** do not change trading limits, account guards, paper/live mode, or NDX/XSP
  behavior unless asked.
- **Defaults unchanged:** any new pricing rule is opt-in behind a setting whose default is
  today's ladder, until approved.
- **Research and live parity:** the research exit-pricing model must match whatever ships,
  with a test.
- **Statistics:**
  - The real-fill sample is tiny (1 bot exit, 2 manual exits), so say so.
  - Separate what can be measured (quotes after the signal) from what needs a fill model
    (whether a resting limit fills).
  - Use paired per-trade differences with the block bootstrap in `research/evaluate.py`;
    report CIs.
  - Label post hoc work exploratory.
- **Times:** Pacific when talking to the owner; the DB and crontab are UTC.

## Phase 0: verify (read-only)

1. Re-verify the Background against `origin/main` and Helios (`ssh helios`; `uv` is at
   `/home/billy/.local/bin/uv`). Check:
   - the ladder arithmetic and which settings apply on the live pilot;
   - which entry path produced 415's 2.00 limit.
2. **Inventory every exit with a recorded fly spread at the exit moment:**
   - paper fill metadata (`spread_bid/mark/ask`);
   - live `execution_observations`;
   - SPX, plus NDX and XSP for scale only.

   Report the distribution of exit-time fly spread (dollars, and spread / mid) by regime,
   exit reason and VIX bucket. Then report what `min(mid, natural + 0.30)` costs vs mid on
   each.
3. **Measure post-signal drift** on the trades that have it: monitor polls up to the exit,
   then post-exit polls. Mid and natural at signal + 1, 2, 5, 10, 20, 40, 60 s. That drift
   is the cost of waiting.
4. Check whether Schwab order activity (`orderActivityCollection`) or anything stored gives
   fill-relative-to-NBBO information for the 4 live fills.

**Stop point 0:** report the facts, corrections, the spread distribution, the drift curve,
and how many exits have usable evidence. Wait.

## Phase 1: plan and pre-registration

Write `docs/research/exit-ladder-pricing-plan.md`:

1. **Candidate rules** (keep the list small):
   - today: bid + 0.30 stepping to bid every 20 s;
   - start at mid rounded to $0.05, step toward bid on a time schedule;
   - start at `min(mid, bid + k × spread)`;
   - a rule that depends on urgency or spread width (wide spread → start nearer mid).
   - In each case: when to give up and cross, and the hard timeout.
2. **Fill model.** Paper fills cannot reveal this. Define a conservative fill rule and its
   bounds: e.g. a credit limit L fills when a later observed fly bid ≥ L, versus fills at
   mid within T s with probability p. State which evidence each part rests on.
3. **Metric and decision rule,** fixed in advance:
   - per-exit expected credit vs today's ladder under the conservative fill model;
   - a worst-case bound (no fill until timeout, then cross);
   - what would justify adoption given how few real fills exist.
4. **What would need live evidence,** and a supervised protocol for gathering it. Only
   propose it; run it only if the owner asks.
5. **Paper reporting:** whether paper P&L should also report the live-ladder price (review
   L8), so the paper ledger stops overstating live exits.

**Stop point 1:** the owner approves the plan and decision rule.

## Phase 2: analysis and design decision

- Implement the candidate rules and fill model as pure, tested functions under `research/`.
- Run the analysis.
- Write `docs/research/exit-ladder-pricing-results.md`:
  - tables with CIs;
  - per-regime and spread-width breakdowns;
  - the trades most affected;
  - the decision.
- Propose setting names, defaults and validation. The suggested shape is
  `execution.exit_pricing: bid_ladder | mid_ladder | ...`, plus the start, step and timeout
  parameters.

**Stop point 2:** the owner approves the design, or keeps today's ladder (and perhaps only
the paper-reporting change).

## Phase 3: implementation and rollout (after approval)

Small PRs, each green on CI (`validate` and `timescaledb`).

1. **The pricing rule behind a setting.**
   - Default reproduces today exactly; prove it with tests over the ladder steps.
   - Keep the L12 protection against one bad tick.
   - Respect `round_credit_limit` increments and the operator-takeover checks.
   - Keep the research model and live code in parity.
2. **Rollout:**
   - Paper cannot test fills, so a paper rollout only checks plumbing: logs, ladder trace,
     no errors.
   - Live use only when the owner resumes the pilot. Rebuild the pilot image and update
     the staging template (`reports/execution_audits/spx-live-test-2026-11-16/`).
   - Helios release procedure: `docs/live-runbook.md` "Deploy". The latest example is
     `.rollbacks/spx-a283610-20261116/`.

Each PR needs focused tests, `uv run pytest`, `uv run ruff check .`, and a description
covering what, why, risk and rollback. Merge only with the owner's approval.
