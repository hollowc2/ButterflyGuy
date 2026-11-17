# Monitor cadence, exit confirmation and leg fetch: plan and pre-registration

Status: **APPROVED by the owner 2026-11-16 (stop point 1), with the proposed decision rule
in section 4. This commit is the pre-registration.** Section 6's results are added after the
Tuesday 2026-11-17 probe; its criteria are fixed here. No confirmation-set trade exists yet.

Task brief: `docs/research/monitor-cadence-exit-design-prompt.md` (main checkout). Times are
Pacific unless marked; the DB and crontab are UTC.

## Amendment 1 (owner-approved 2026-11-16, before any post-exit trade existed)

**Why:** the Aug–Nov development set cannot score any arm that changes an exit. Polls end at
the recorded exit, so every later exit was valued on 1-minute snapshots
(`monitor-cadence-exit-design-results.md`). No post-exit trade had been recorded or read when
this amendment was made.

**New split.** Both sets use only qualifying post-exit trades, as defined under "Confirmation
set" in section 1:

- `trade_date` ≥ 2026-11-17;
- `direct` access mode;
- an as-live match;
- post-exit coverage with no gap over 30 s.

They are taken in trade-date order:

| Set | Trades | Role | Expected (one trade a session) |
|---|---|---|---|
| Development | 1–30 | Step 1 selection | about end of December 2026 |
| Confirmation | 31–60 | Step 2 confirmation, run once | about mid-February 2027 |

Both sets refuse 1-minute data.

**Everything else is unchanged:** the grid (section 2), pricing (section 3), metric, selection
rule and confirmation rule (section 4). Step 1's "if none qualifies, stop" applies to the new
development set.

**Former development set:** the Aug–Nov 2026 trades become the exploratory *pilot* set. They
are reported, never used for a decision.

**Plumbing:** it ships now and does not wait for the study. Every default reproduces today's
behavior.

## Phase 0 findings this plan relies on

- **Cadence is set by the data path, not just `poll_interval = 2`.** Polls are sleep 2 s +
  work. Direct chain work is about 0.6 s, so the cadence is 2.6 s (trade 415, 3.6% exact
  repeats). Gateway-era paper SPX ran at 2.06 s median, but 75–78% of polls in Oct–Nov
  repeated the previous poll exactly: the gateway answered from a 4 s cache, so new
  information arrived every ~4–6 s. Aug–Sep repeat share was 19–35%.
- **The live pilot adds about 0.7 s to every 5th poll** (the operator-close check reads the
  account and orders). Paper does not.
- **PR #80 went live 2026-11-16 15:20 PT.** `post_exit_leg_quotes` has 0 rows. Paper SPX
  runs `direct` from the next session (Tue 11-17) on.
- **Live exit pricing is not mid.** `execute_exit` (live) anchors on the median of recent fly
  bids and starts at bid + (steps − 1) × 0.10 = **bid + 0.30**, stepping down. Trade 415:
  bid 1.00 → limit 1.30, filled ~1.1 s after the signal (mid 1.85). Paper exits fill at the
  signal mark.
- **Load at the busiest hour (11:00 PT 11-16):** SPX live pilot ~40.5 Schwab req/min
  (chain 22.4, account 8.1, orders 8.1, quotes 2); gateway upstream ~17/min (NDX + XSP);
  ~57/min combined. The repo does not record Schwab's limit.

## 1. Data and split

### Extraction (reproduces the 2026-11-16 inputs exactly)

Run against the Helios DB; it reproduced 109 trades, 1,084,359 poll rows and 112,379 minute
rows. `post_exit.csv.gz` uses the polls query on `post_exit_leg_quotes` (no peak/drawdown).

```sql
-- trades.csv.gz
select id, trade_date, direction, wing_width, lower_strike, center_strike, upper_strike,
       entry_price, entry_time, exit_price, exit_time, exit_reason, pnl, peak_value, quantity
from butterfly_trades t
where underlying = 'SPX' and status = 'CLOSED'
  and exists (select 1 from monitoring_leg_quotes q where q.trade_id = t.id)
order by id;

-- polls.csv.gz
select trade_id, ts, strike, option_type, bid, ask, mark, spot_price, fly_mark,
       peak_value, drawdown_pct
from monitoring_leg_quotes where underlying = 'SPX' order by trade_id, ts, strike;

-- minute.csv.gz (collector snapshots of the three legs, entry to 16:00 ET)
select t.id as trade_id, s.snapshot_time as ts, s.strike, s.bid, s.ask, s.mark, s.spot_price
from butterfly_trades t join option_chain_snapshots s
  on s.underlying = 'SPX' and s.expiration = t.trade_date and s.option_type = t.direction
 and s.strike in (t.lower_strike, t.center_strike, t.upper_strike)
 and s.snapshot_time >= t.entry_time
 and s.snapshot_time <= (t.trade_date + time '16:00') at time zone 'America/New_York'
where t.underlying = 'SPX' and t.status = 'CLOSED'
  and exists (select 1 from monitoring_leg_quotes q where q.trade_id = t.id);
```

Phase 2 commits this as a small extraction script so later runs are reproducible.

### Matching

A trade is usable only if the as-live replay (`PeakTrailer` with the current config, raw
polls, confirmation 1) reproduces the recorded exit: **same reason and within 10 s**, or
both cash-settled. Mismatches are excluded and counted.

Current match rate: 82 of 109. By month: Jun 3/18, Jul 10/21 (older exit config), Aug
20/20, Sep 18/18, Oct 21/21, Nov 10/11.

### Development set (already seen)

Matched SPX trades with `trade_date` 2026-08-01 to 2026-11-16: **69 trades**. Caveats:

- After a recorded exit, a later-exiting arm continues on **1-minute** collector data, so
  its delayed exit can land up to 60 s late. Each arm reports the trades where this
  happened, and results are shown with and without them.
- Most Oct–Nov dev polls are gateway repeats. Results are reported for Aug–Sep and Oct–Nov
  separately.

### Confirmation set (not yet recorded)

Paper SPX trades with `trade_date` ≥ 2026-11-17, `direct` access mode, and an as-live
match. Trade coverage rules:

- A trade that exits needs post-exit polls from the exit to 16:00 ET with **no gap > 30 s**.
  Otherwise it is excluded and counted. The confirmation replay **refuses** minute data.
- A cash-settled trade is covered by its monitor polls (the monitor runs until the close).
- Any live-pilot trade (if live resumes) is reported separately, not pooled: its cadence
  and exit pricing differ.

**Minimum: the first 30 qualifying trades**, analysed once. At about one trade per session,
that is around the end of December 2026. The power section explains the number.

## 2. Candidate grid

Thresholds stay at today's regime values (0.60 / 0.90 / 0.75) in every arm. Nothing in the
evidence justifies moving them, and moving them jointly would multiply the grid.

### Definitions (shared by research and live once shipped)

- **Time-based confirmation, T seconds:** exit at the first poll where the value has been
  beyond the threshold on every poll since the first breach poll, and
  `ts − first_breach_ts ≥ T`. A poll back inside the threshold resets it. T = 0 is today's
  rule. It does not depend on cadence.
- **Quality peak, window W seconds:** the peak is updated from the causal median of fly
  marks over the last W seconds instead of the raw mark. The current value stays raw.
- **Leg filter:** reject a poll if any leg is crossed, missing, or its spread exceeds
  max(0.50, 4 × the median of that leg's previous 30 accepted spreads). Rejected polls
  change neither peak nor value. Same as the 11-16 study.

### Primary candidates (adoption is possible)

| Arm | Rule |
|---|---|
| A0 | Current: T = 0, raw peak, no filter |
| C1 | T = 5 s |
| C2 | T = 10 s |
| C3 | T = 20 s |
| C4 | Quality peak W = 10 s, T = 0 |
| C5 | Quality peak W = 10 s, T = 10 s |
| C6 | Leg filter, T = 0 |

### Diagnostics only (reported, never adopted from this study)

- Decision cadence by subsampling the recorded polls: 5, 10, 15, 30, 60 s, with T = 0.
  These set the price of slowing down. The 2 s poll stays unless a slower cadence is
  needed for load, and today's load does not require it.
- Count-based confirmation: 2 and 3 polls. They behave differently on gateway repeats and
  on direct data, which is why time-based confirmation is the candidate.
- Causal median of 10 s applied to both peak and value.

## 3. Exit pricing

Every arm is valued three ways at its exit poll; settlement is the same in all three.

| Model | Exit price | Role |
|---|---|---|
| Mid | Fly mark at the exit poll | Paper convention; upper bound |
| Natural | lo_bid + up_bid − 2 × ce_ask | Lower bound |
| **Ladder (primary)** | **min(mid, natural + 0.30)** | **What the live ladder's first step submits; ranking model** |

The ladder model is derived from `execute_exit`, not fitted. Three real exit fills exist:
two manual exits at mid on 10-19 and trade 415 at exactly natural + 0.30. When ten or more
bot exits exist, it gets refitted. Commission is $1.15 per contract on every model.

## 4. Primary metric and decision rule (fixed in advance)

**Metric:** the paired per-trade P&L difference, arm minus A0, in $ per 1-lot, under the
ladder model. Confidence intervals use the block bootstrap in `research/evaluate.py` (block
5, 5,000 resamples, seed 20261117).

**Step 1, selection on the development set.** Among C1–C6, keep arms whose dev mean is ≥ 0
under **all three** pricing models. Select the one with the highest ladder-model dev mean.
If none qualifies, stop: keep current values and ship only the plumbing. The confirmation
set is then not needed for this decision.

**Step 2, confirmation of the single selected arm (k = 1).** On the first 30 qualifying
confirmation trades, adopt the arm only if all of the following hold:

1. the paired mean is ≥ 0;
2. the lower one-sided 90% bound is > −$20 per trade (non-inferiority margin);
3. the worst single-trade difference is ≥ −$300;
4. the mean under the natural model is ≥ 0.

Otherwise keep current values and ship the plumbing.

### Why this rule, and not "lower 90% bound > −$2"

The dev-set per-trade SD of the paired difference is about $107 for C-type arms (conf2: 107,
med5: 106, conf3: 150) and about $33 for cadence arms.

| n trades | SE at SD 110 | Min. detectable effect (80% power, one-sided α 0.10) |
|---|---|---|
| 20 | $24.6 | $52 |
| 30 | $20.1 | $43 |
| 60 | $14.2 | $30 |

Effects of a few dollars per trade are undetectable at any reachable sample: +$5 at SD 110
needs about 2,200 trades. Under the "lower bound > −$2" rule with 20 trades, an arm with a
true +$5 effect passes about 16% of the time, so the rule is close to "never adopt".

The proposed rule is honest about that. It asks the confirmation set to show the arm is
**not clearly harmful**: a true −$20 arm passes about 10% of the time. The case for adopting
a rule must also come from mechanism, such as robustness to one-poll spikes like trade 415
and cadence independence, not from a P&L win. **If you prefer the strict rule, say so; it
changes nothing else in the plan.**

## 5. Secondary diagnostics (per arm, descriptive)

- exits changed vs A0, and the median and max change in holding time;
- how often a one-poll spike sets the peak (raw vs arm);
- signal-to-submit and signal-to-fill time, where broker data exists;
- per-regime breakdown (morning / late morning / afternoon) and Aug–Sep vs Oct–Nov;
- trades continued on minute data (dev only);
- request load: SPX monitor requests/min = 60 / cadence per held position. The rules add
  none.

## 6. Fetch design: three leg quotes vs full chain

**Pending the 2026-11-17 08:00 PT probe** (`get_option_chain` vs `get_quotes` for three
SPXW legs, 20 back-to-back pairs). Pre-set criteria to switch the monitor's default to
`quotes` on direct mode:

1. median latency ≤ chain median, with payload smaller;
2. same-moment parity: bid and ask equal or within $0.05 on ≥ 95% of leg pairs;
3. per-leg quote time no older than the chain's on ≥ 95% of pairs;
4. no added request load (one request per poll either way).

**Fallback:** if any held leg is missing or has no quote time in a quotes response, that
poll fetches the chain, as today. Two consecutive fallbacks raise the existing
market-data-degraded path.

**Unchanged:** the full chain stays for the collector, entry, settlement fallback and
`exit_mark_parity_report`.

**Gateway mode** has `/v1/quotes` (`get_available_quotes`, with `event_timestamp`, `stale`
and `missing_symbols`). NDX and XSP are out of scope unless you ask, so gateway mode keeps
the chain.

## 7. Backtest implications

- **Simulating the rules on 1-minute history:** T > 0 confirms at the next bar if the value
  is still beyond the threshold, a 60 s delay instead of T. The quality peak uses the bar
  value, so W ≤ 60 s is a no-op.
- **Documented bias:** 1-minute decisions cost about −$15/trade vs the recorded polls
  (95% CI −21 to −9). Minute backtests of any arm carry a bias of that order. They are fit
  for ranking entry rules, not exit-confirmation rules.
- **Recommendation:** do not switch `run_backtest_db` to `monitoring_leg_quotes`. After
  Phase 3, add an opt-in research dataset that replays monitor polls for SPX sessions since
  2026-08 (as-live matched), for exit-rule studies only.

## What happens next

| Step | When | What |
|---|---|---|
| Probe | Tue 11-17 ~08:00 PT | Run the probe; fill in section 6 |
| Phase 2 pilot analysis | Done 2026-11-16 | Replay extended; Aug–Nov pilot run; no arm scorable (results doc) |
| Phase 3 PR 1 | Now (Amendment 1) | Config plumbing (poll interval into config, defaults unchanged) |
| Development run | After 30 qualifying post-exit trades (~end Dec) | Select one arm, or stop |
| Confirmation run | After trades 31–60 (~mid-Feb 2027) | Run once on the selected arm |
