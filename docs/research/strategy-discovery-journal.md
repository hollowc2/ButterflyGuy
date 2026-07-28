# Options strategy discovery journal

## 2026-07-14 — data audit and research design

### Verified data

- Live PostgreSQL 16 / TimescaleDB contains 18 public tables; nine are hypertables.
- Historical options are limited to 0-DTE SPX, NDX, and XSP chains. No SPY, QQQ,
  individual-equity, weekly, monthly, calendar, diagonal, or LEAPS history exists.
- `option_chain_snapshots` contains 55,401,575 rows (SPX 19,688,764; NDX 23,060,601;
  XSP 12,652,210) and occupies 3,573 MB including indexes and TOAST.
- Chain coverage: SPX 83 dates from 2026-03-13 through 2026-07-14; NDX 78 dates from
  2026-03-20; XSP 70 dates from 2026-04-01. Several early/incident days are partial.
- Stored fields are bid, ask, mark, last, volume, open interest, IV, delta, gamma,
  theta, vega, rho, bid/ask size, intrinsic/time value, moneyness, multiplier,
  theoretical value, symbol, strike, type, expiration, timestamp, and spot.
- Bid, ask, mark, IV, delta, gamma, theta, vega, volume, and open interest have no
  nulls. Bid/ask size is missing in 2,289,882 SPX rows and 1,105,884 NDX rows; XSP
  sizes are complete.
- `spot_prices` covers SPX, NDX, XSP, and VIX intraday. `daily_bars` has 92 SPX/NDX/XSP
  dates and 95 VIX dates beginning 2026-03-02. No breadth, futures, dealer positioning,
  or durable macro-event table was found.
- Relationships: `monitoring_leg_quotes.trade_id` cascades to `butterfly_trades.id`;
  `broker_order_intents.trade_id` sets null on trade deletion. Other market-data
  tables are related by symbol/date/time rather than foreign keys.

### Data limitations and leakage controls

- Four months is insufficient to demonstrate stability across multiple long-run
  regimes. SPX and XSP are the same economic exposure; NDX is correlated, so they
  are not three independent samples.
- The first pass uses only entry-time fields and rolling IV percentiles built from
  prior dates. Chronological 60/20/20 train/validation/test segments are reported.
- Every option leg buys at ask or sells at bid on entry, then sells at bid or buys
  at ask on exit. Round-trip commission is $0.65 per contract per side. Missing or
  illiquid entry quotes are rejected; no midpoint-fill assumption is used.

### Predeclared hypotheses (no tuning yet)

1. Long ATM straddle: realized intraday movement exceeds the crossed-spread premium.
2. Long 25-delta strangle: cheaper convexity improves long-vol expectancy.
3. Short iron fly: intraday decay exceeds tail and spread costs.
4. Short 20/5-delta iron condor: defined-risk volatility carry survives execution.
5. 55/25-delta debit spread following the 09:35–10:00 move: momentum continuation.
6. The same debit spread against that move: intraday mean reversion.
7. Strong-trend debit spread: momentum only after a 0.15% opening move.
8. Long ATM straddle only below the trailing IV 35th percentile.
9. Iron condor only above the trailing IV 65th percentile.

### First-pass result

- Volatility selling failed decisively. Iron fly and iron condor expectancy was
  negative on every underlying after crossing the recorded spread.
- Unconditional long straddles/strangles were mildly positive in some full samples,
  but chronological holdout performance changed sign across NDX and XSP.
- The filtered IV variants produced too few trades and contradictory segments; very
  high Sharpe values on three to eight observations were rejected as small-sample
  artifacts.
- Sensitivity at 09:45/10:00/10:30 entries and 15:15/15:30/15:45 exits did not
  preserve a long-vol edge across assets. SPX 10:30 trend debit reached full-sample
  Sharpe 2.06, but training Sharpe was -0.72 and NDX/XSP full samples were negative.
  It is regime-local, not robust.

### Second structural pass

Four fixed candidates were added before any additional result was inspected: ATM
butterfly, 25-delta directional butterfly, trend-following opposite-side credit
spread, and reversal-side credit spread. Wing distance for butterflies is 0.30% of
spot so the rule scales across SPX, NDX, and XSP.

All four failed: every full-sample butterfly result was negative, and neither credit
spread generalized across markets or chronological segments.

### Final data-driven pass

Two volatility hypotheses use fields not consumed by the structural pass:

1. Buy the ATM straddle only when its ask premium as a fraction of spot is below the
   trailing 20-session median absolute 10:00–15:45 underlying move.
2. Buy the ATM straddle only when entry gamma per absolute theta is at or above its
   trailing 65th percentile.

Both features are calculated from the current entry snapshot and prior sessions;
the current exit is appended to history only after that day's decision.

The filters also failed. At 10:00 the XSP variants exceeded Sharpe 2 on only 12–14
trades while their training segments were negative and NDX lost. Moving entry to
10:30 reversed the signs. This is regime/timing instability, not confirmation.

## 2026-07-14 — diminishing returns checkpoint

Fifteen fixed hypotheses were tested on three assets. Five nearby entry/exit timing
combinations were evaluated for the surviving families. Every additional structural
or feature filter either remained negative, reduced the sample to single digits, or
reversed sign across time/underlying. Further filtering would be in-sample curve
fitting, so research stops here pending materially more history.

The best observed result is the SPX 10:30 trend-following 55/25-delta debit spread,
but it is rejected: full Sharpe 2.06 and positive expectancy coexist with train
Sharpe -0.72, an April–May walk-forward Sharpe of -4.61, NDX Sharpe -2.17, XSP
Sharpe -0.12, and a bootstrap Sharpe 95% interval of -1.73 to 5.69.

Entry is 10:00 ET and exit is 15:45 ET. These values and delta targets are fixed for
the first pass. Only strategies with positive holdout expectancy and cross-underlying
support advance to sensitivity and robustness testing.
