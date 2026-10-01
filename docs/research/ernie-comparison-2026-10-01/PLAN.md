# Ernie (@0DTE) comparison — variant plan (not run)

Status: design notes only, 2026-10-01. Nothing here has been backtested. No live config,
cohort source or service was changed. Backtests are paused pending a data-route decision
(see the end).

## Source

Transcripts of the YouTube channel @0DTE ("Coach Ernie", Fat Tail / Fly on the Wall service):
all 2026 short videos, the core rule videos back to 2023, and the 20 most recent
livestreams, pulled as auto-captions with yt-dlp. Many recent livestreams are
machine-translated captions, so the numbers below are approximate. Each one was repeated
in several videos. The figures are his own claims, not audited results.

Butterflyguy's VIX zones are his: Zombieland < 17, Goldilocks 1 17–24.5, Goldilocks 2
24.5–32, Chaos > 32.

## Ernie's rules, as stated

| Area | Rule | Where he says it |
|---|---|---|
| Structure | Long OTM call fly above or put fly below, SPX 0DTE, one per morning | `6KQktM1Jyao`, `gJxOV24LsOE` |
| Width | Zombieland 20–30, G1 30–40 ("30–35 probably"), G2 40–50, Chaos 50; wider than 50 makes risk/reward worse | 2026-05-01/04/17 streams, `ZM9zw9fgP78` |
| Cost | Debit ≤ 10% of width (ceiling); aim for 5–10%; sweet spot risk/reward 1:9–1:15; how far OTM doesn't matter | `vdXumtsowb0`, `65jVWgoxXFo`, `sdspYgKI3ro` |
| Convexity | Step one strike further out when cost drops sharply (30–40%) for a similar payoff | `2F4XhFjQtd0`, `vKMgEaEETSs` |
| Direction | With the trend, from a trend indicator: 50 EMA on hourly (2023), Hull Suite (~3 yrs), sine-weighted MA (since 2026-07). Tool matters less than consistency. | `vdXumtsowb0`, `V5Rf0EigtIE` |
| Entry | Morning session (9:30–12:30). Pre-marked structural levels (ES volume-profile nodes and gaps, roughly matching GEX walls); enter after price pulls back into a level and moves off it | `nj4TdlpiT1s`, `i1ttAOG2dLU` |
| Losers | No stop; let them expire | `tTM9Uo7dydE`, `gJxOV24LsOE` |
| Trail start | Start managing profit once unrealized gain reaches ~75% of the debit | `N548S4tSdLE` |
| Trail size | Give back about 75% of peak profit in the early morning, ~45–50% near noon, ~20% after 2 pm; take profit faster in Zombieland | `osxwjtjJ8pk`, 2026-09-12 stream |
| Sizing | ~1% of capital at risk per day; size so a 10-loss streak stays within 5–10% drawdown; drop SPX → ES → XSP in losing streaks | 2026-09-23 stream, `WthGqNVWydQ` |
| Extra trades | Batman (call fly plus put fly) more often as VIX rises; Time Warp (1DTE Batman, 20 wide, entered the afternoon before) in Zombieland | `ikbQaAoxLwc`, `OECxxW9mwQs`, `cl-R5jY-pa0` |

## Constraints

- `configs/config.yaml` and 16 sources, including `run_backtest_db.py`,
  `butterfly_builder.py`, `simulation_engine.py`, `position_manager.py` and
  `profit_policy.py`, are hash-frozen by cohort `spx-prospective-2026-09-22` (it runs from
  `../Butterflyguy-cohort`). Do all variant work in this worktree
  (`research/ernie-comparison`). Change live only after the cohort's endpoint.
- Before running, copy the variant list below into a registry, as the 09-25 sweep did.
  Use development data only. Report stressed-marketable net, both halves, max drawdown and
  share of profit from the top 3 trades. A variant passes only if it beats baseline in
  both halves.

## Variants

### W — widths (decided: apply live after the cohort endpoint)

- **W0** baseline buckets: `[20,25,30] [20,30,40] [40,45,50] [50,55,65]`.
- **W1** Ernie: `[20,25,30] [30,35,40] [40,45,50] [50]`.

Sigma anchors are positional (`_bucket_sigmas`), so G1's 30/35/40 get 0.25/0.50/0.75 and the
single Chaos width gets 0.50. Expect W1 to change only G1 and Chaos sessions. Report those
buckets separately.

### T — trail start and basis (likely the largest gap)

Current: `peakvaluetrailer`. The trail arms once peak value ≥ entry × `min_peak_profit_ratio`
(1.0, so any profit). It exits when `(peak − value) / peak` ≥ 60% / 90% / 75% for the first
2 h / next 2 h / rest of the day (`position_manager.py:242`).

Worked example (peak = 3× entry): the baseline exits at 1.2× / 0.3× / 0.75× by window.
Ernie's rule exits at 1.5× / 2.1× / 2.6×.

- **T1** start only: `min_peak_profit_ratio = 1.75` (needs no code; `--min-peak-profit-ratio`).
- **T2** profit basis only: exit when `(peak − value) ≥ g × (peak − entry)`, with g = 0.75
  from 09:30 to 11:30, 0.45 from 11:30 to 14:00 and 0.20 from 14:00, using the baseline's
  any-profit start. Needs a `drawdown_basis: value | profit` setting with `value` as
  default, so live behaviour doesn't change.
- **T3** = T1 + T2 (Ernie's rule as stated).
- **T4** = T3, but in Zombieland g is halved (his "take profit faster" in low VIX;
  interpretation, mark it post-hoc if added later).

The window edges (11:30, 14:00) are my reading of "towards noon" and "after 2 pm".

**Exploratory result, 2026-10-01** (Schwab export, 2026-03-13 → 2026-09-18, the same 118
baseline entries; `spx-idea-sweep-2026-09-25/trail_compare.py`; stressed net; H2 from
2026-06-19). T1–T3 were defined before running; the start-level sweep is post-hoc.

| Variant | Stressed net | H1 | H2 | Settled | Midpoint net |
|---|---:|---:|---:|---:|---:|
| B baseline | 9,831 | 17,031 | −7,201 | 22 | 17,635 |
| T1 start at +75% | 10,678 | 16,593 | −5,915 | 59 | 17,405 |
| T2 Ernie giveback | −8,240 | −4,126 | −4,114 | 7 | 224 |
| T3 Ernie full | −3,909 | −1,065 | −2,845 | 42 | 3,631 |

None beats baseline in both halves. Ernie's 45%/20% giveback sells flies before they land
in the tent, and settlement is where this strategy earns its money. T3's midpoint win rate
is 61%, close to the profile Ernie reports. The start-level sweep (1.0–3.0×) moves the net
between 8.4k and 10.7k with no consistent pattern, so T1's +$847 is noise-sized.

**Post-hoc middle ground** (defined after seeing the table above; same 118 trades). Exit at
breakeven (mark ≤ entry) once the peak has reached +75%, otherwise ours:

| Rule | Stressed net | H1 | H2 | Midpoint net | Max DD | Settled |
|---|---:|---:|---:|---:|---:|---:|
| B baseline | 9,831 | 17,031 | −7,201 | 17,635 | 7,661 | 22 |
| T5 start +75% + breakeven floor | 15,980 | 19,533 | −3,552 | 22,981 | 3,970 | 58 |
| T6 ours + breakeven floor after +75% | 14,758 | 19,971 | −5,213 | 22,835 | 5,559 | 21 |

T5 beats baseline in both halves, but the halves test was not pre-registered for this rule.
Gain +$6,150: 48 trades better (+$9,789), 38 worse (−$3,639). Two sessions (2026-08-20,
2026-03-20) supply +$3,397; without the top 3 the gain is +$2,413. Floor exits average
−$101 stressed, against about −$400 for the same trades under baseline. The losers are flies that
peaked at 1.3–1.6× and now ride to zero. Candidate for a pre-registered test on ThetaData
2022–24 or a future cohort; not a live change.

### P — strike placement

- **P0** baseline: VIX-sigma target ±15 pts, risk/reward ≥ 8, cost ≤ 10% of width; pick
  risk/reward closest to 10.
- **P1** cost-target: per width, the fly whose cost is closest to 10% of width with no
  distance anchor (`select_best_by_target_cost` already exists).
- **P2** convexity: per width, walk outward from the first strike with cost ≤ 10% of width.
  Take the strike with the largest relative cost drop versus the strike one step closer,
  keeping cost ≥ 5% of width.
- Diagnostics: center distance in σ, debit as a % of width, P&L by bucket. The journal
  measured centers at about 1.58σ, so expect P0 and P1 to agree most days. P2 is the real
  test.

### D — direction

- **D0** gap vs prior close (baseline).
- **D1** 50 EMA on 60-minute bars (his 2023 rule).
- **D2** Hull MA on 60-minute and 15-minute bars. The TradingView "Hull Suite" default
  length is believed to be 55; confirm before registering.
- **D3** sine-weighted MA. He gave no length or timeframe, so leave it out unless he states
  one.

Wiring today: live has gap (default) and `BiasScoreFilter` (`use_bias_filter`: gap, VWAP,
EMA 9/21, opening-range breakout). Only the backtest has `--direction-ma N`, on daily
closes. Daily MA20–200 already lost to the gap rule with about twice the drawdown (journal,
2026-09-25). D1 and D2 use intraday bars, which is a different signal and not yet tested.
Bars: owner `spx_1min.csv` (Chicago bar-end; see conventions).

### E — entry trigger (structural levels)

- **E0** baseline: first qualifying snapshot 10:00–10:45 ET.
- **E1** price levels: prior-day high/low/close, the 09:30–09:45 opening range, and
  25-point round numbers. Trigger: within 09:45–12:30, price comes within 3 pts of a level,
  then closes 5 pts back away from it in the trend direction within 15 min. Enter on the
  next snapshot.
- **E2** GEX walls: per-strike dealer gamma from chain open interest × gamma. It's
  computable from our own snapshots; ThetaData has OI but no greeks, so solve IV from
  quotes. Use the top two walls per side as levels with the E1 trigger.
- Volume profile (his main tool) needs ES or SPY minute volume, which we don't have for
  SPX. Skip it unless a source turns up.
- Report trigger rate. The 09-25 sweep found risk/reward ≥ 8 rarely exists after 10:45, so
  a later trigger may leave many days with no trade.

### TW — Time Warp (1DTE Batman), from the full transcript read

Ernie's rules, as he stated them across 2024–2026 videos and the 2026-09-11 → 10-01 livestreams:

- **When:** low-VIX "edge case". His playbook starts it in Zombieland (< 17) but allows it up
  to about 19. Toward VIX 10 he goes out to 2–3 DTE. Friday entries are naturally Monday
  expiries (3 DTE).
- **Why (his reasoning):** in low VIX, 0DTE premium has already decayed by the morning, the
  move happens overnight (gaps followed by doji days), and an extra day adds σ√T.
- **Entry:** end of the prior session. He has done it 2:00–3:15 pm ET and says the last hour
  is "a little better". Futures or 24h brokers allow after-close entry. He uses hanging limit
  orders below mid. If one side doesn't fill, he abandons it or trades 0DTE instead.
- **Structure:** 20-wide call fly above plus 20-wide put fly below, on next-day SPXW (PM-settled).
  He has said the outer wings sit near the 1σ expected move, with both flies inside 2σ.
- **Price:** about 5% of width per side ($1.00–1.40), combined ≤ 10–12.5% ($2.00–2.50); combined
  risk/reward about 1:7–1:10. Strikes are chosen by price only, using the convexity heatmap to
  step one strike further for a 20–40% discount. Puts are usually cheaper (skew).
- **Exit:** "opportunistic" in low VIX. If he wakes up in profit, he closes, often at or soon
  after the open; with ES or IBKR, before it. Otherwise he trails, wider early and narrower later,
  and often closes leftovers by about noon. The 2025 rule of thumb: at about +50% of risk on
  a 1–2 DTE trade, "start getting very interested" in closing. Losers expire.
- **Variant:** a single directional 1DTE fly with the trend. He says it makes "a little more"
  with a lower win rate and needs more management.
- **His expectations:** 45–55% win rate; 12–15% finish in the tent; winners 2.5–4.5R; about
  one big winner a week; streaks up to about 10 either way; cut size after 3 losers.
- **Evidence:** developed in August 2023 with a roughly 6-month member experiment into early
  2024 ("worked fantastically"; no statistics shown). He claims 30–40% CAGR from a 2023 study
  and 40–70%/yr "empirically". He admits he is "not usually a big fan of backtesting" and is
  only now building a backtest lab.

His live show log (self-reported; discretionary, time-constrained exits; VIX about 15–19): he
claims Time Warp went 9 of 11–12 and about 28R across all show trades, including scalps,
over three weeks. Trades include losses of −1.5R (9/24 entry), a full loss (9/21) and one
single-side trade (9/28); the winners were mostly closed in the morning.

Test design (draft, for ThetaData `spxw_1dte` + `spxw_0dte`, 2022-05 → 2024-06):
- **TW0:** entry 15:30 ET when VIX < 17. Next-session SPXW, 20-wide call fly above and put fly
  below; each at the first strike outward with mark ≤ 6% of width ($1.20).
- **Exit A:** at 09:45 next day, close each side whose bid exceeds its entry; hold the rest to
  settlement.
- **Exit B:** close everything by 12:00.
- **Exit C:** hold both sides to settlement.
- **Comparisons:** (a) frozen 0DTE baseline on the same next-day sessions; (b) skipping them
  (H-LV1-style); (c) a single trend-direction 1DTE fly at the same cost.
- **Sensitivities:** VIX < 19; entry 14:30.
- **Report:** win rate, R per trade, the 2023-08 → 2024-02 period separately (his discovery
  window, likely flattering), and stressed costs on all 8 legs.
- **Limits:** no overnight or pre-market exits (SPX quotes are 09:30–16:15 only), so his "close
  before the open" fills can't be reproduced. Exits at 09:30–09:45 face the widest spreads.
  Settlement needs the Cboe close.

## Order

T (cheapest; T1 needs no code) → W → P → D → E.

## Data route (pending owner decision)

1. **Schwab export** (133 sessions, 2026-03-13 → 2026-09-24, about 140 MB read-only Helios
   query run by the owner) and the 09-25 harness (`sim.py`). Fast to set up, but there are
   almost no Chaos sessions, so W1 is barely tested.
2. **Local ThetaData** 2022-05 → 2024-06 (~540 sessions, includes high-VIX 2022) via the
   `feat/thetadata-local-replay` pipeline (`/tmp/butterfly-thetadata-implementation`). Needs
   one Cboe daily-close download, a validation import and quality gate, then a development
   import. No production reads.
3. The sealed 2024-07-01 → 2026-03-12 files stay unread unless the owner releases them.
