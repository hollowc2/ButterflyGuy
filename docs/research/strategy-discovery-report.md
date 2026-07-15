# Options strategy discovery report

## Executive summary

No strategy satisfies the full objective on the available data. One SPX candidate
has full-sample Sharpe 2.06 and positive expectancy, but it fails the predeclared
stability tests. It must not be promoted to paper/live trading as a validated edge.

The limiting fact is longitudinal coverage: 70–83 option-chain sessions per asset,
all between March and July 2026, all 0-DTE. This is enough to falsify many ideas but
not enough to establish multi-regime robustness. Fifteen hypotheses across long
volatility, short volatility, momentum, mean reversion, butterflies, verticals,
credit spreads, IV filters, realized/implied filters, and Greek filters were tested.

## Best observed candidate (rejected)

- Underlying: SPX 0-DTE
- Entry: 10:30 ET
- Signal: follow the 09:35–10:30 underlying move (call spread after a rise, put
  spread after a decline)
- Structure: buy approximately 55-delta option, sell approximately 25-delta option
- Exit: 15:45 ET
- Execution: long legs at ask and short legs at bid; reverse sides on exit
- Costs: $0.65 per contract per side; one percent of equity risked per trade in
  return/risk metrics

| Metric | Full sample |
|---|---:|
| Trades | 74 |
| CAGR (annualized from four months) | 35.7% |
| Sharpe | 2.06 |
| Sortino | 3.56 |
| Calmar | 3.45 |
| Profit factor | 1.36 |
| Win rate | 45.9% |
| Expectancy | $189.22/contract |
| Maximum drawdown | -10.36% |
| Recovery factor | 1.00 |
| Average trade | $189.22 |
| Average winner | $1,551.66 |
| Average loser | -$968.85 |
| Exposure | 80.8% of available session time |
| Total P/L | $14,002.60/one-lot |

The annualized figures are mechanically correct but economically unreliable because
the sample spans only four months.

## Out-of-sample and walk-forward evidence

| Segment | Trades | Sharpe | Expectancy |
|---|---:|---:|---:|
| Train through 2026-05-22 | 44 | -0.72 | $10.01 |
| Validation 2026-05-26–06-18 | 15 | 3.61 | $282.40 |
| Test 2026-06-22–07-13 | 15 | 7.89 | $621.73 |

The increasing result is a regime shift, not stable history. Four chronological
18-trade windows had Sharpes 2.86, -4.61, 3.00, and 3.64. The negative middle window
is fatal to a stable-regime claim.

Cross-underlying confirmation also failed at the same times and delta rules:

| Underlying | Full Sharpe |
|---|---:|
| SPX | 2.06 |
| NDX | -2.17 |
| XSP | -0.12 |

## Parameter sensitivity and rolling selection

SPX trend-debit results were not smooth around the selected times:

| Entry / exit ET | Full Sharpe | Train | Validation | Test |
|---|---:|---:|---:|---:|
| 09:45 / 15:45 | -2.00 | -3.24 | -4.11 | 3.20 |
| 10:00 / 15:15 | 0.06 | -1.35 | 3.75 | 0.09 |
| 10:00 / 15:30 | 0.27 | -1.46 | 4.95 | 0.18 |
| 10:00 / 15:45 | -0.11 | -1.12 | 1.69 | 0.91 |
| 10:30 / 15:45 | 2.06 | -0.72 | 3.61 | 7.89 |

An expanding-window selector would choose no trade because every entry time had
negative training Sharpe. If forced to select the least-bad value, it chooses 10:30;
that is the candidate reported above, not evidence that the training objective was
met.

## Bootstrap, Monte Carlo, and risk

Deterministic 5,000-path tests (seed 20260714) on the 74 candidate trades found:

- Mean R 95% bootstrap interval: -0.109 to +0.383
- Sharpe 95% bootstrap interval: -1.73 to +5.69
- Bootstrap probability of positive expectancy: 87.5%
- 252-trade ending equity 95% Monte Carlo interval at 1% risk/trade: 1.018–1.942
- 252-trade maximum-drawdown 95% interval: -19.1% to -5.5%
- Simulated probability of a 50% drawdown: 0% under IID resampling

The ruin estimate is not reassuring: IID resampling cannot represent regime change,
and the observed walk-forward sign reversal is more important than the simulated
zero. The bootstrap intervals include both negative expectancy and negative Sharpe.

Monthly fixed-risk returns were +6.67% (March), -6.58% (April), -2.58% (May),
+8.04% (June), and +5.24% (partial July). Two consecutive losing months further
contradict stable performance.

## Failed hypotheses and weaknesses

- Iron flies and iron condors lost on all assets after realistic spread crossing.
- Unconditional straddles/strangles changed sign across chronological holdouts.
- Momentum and mean-reversion verticals did not generalize across assets.
- ATM/directional butterflies and one-sided credit spreads were negative.
- IV-percentile, realized-versus-implied, and gamma/theta filters produced small,
  unstable samples whose signs changed with entry time.
- Calendars, diagonals, weekly/monthly structures, SPY/QQQ/equity options, futures,
  breadth, and dealer-gamma studies cannot be tested with the stored data.
- SPX and XSP are economically duplicate exposures; they are not independent tests.
- No ML was retained. With fewer than 100 sessions per asset, ML would add selection
  degrees of freedom without credible independent validation.

## Production implementation plan

There is no production implementation recommendation yet. Keep this research path
separate from runtime strategy, risk, and order-routing code.

1. Continue collecting full SPX/NDX/XSP chains until at least 12–24 months and
   several volatility/trend regimes are present.
2. Freeze the candidate definitions and this adverse-side execution model before
   rerunning; do not tune on the newly collected holdout.
3. Require positive train, validation, and untouched test expectancy; bootstrap
   lower Sharpe bound above zero; nearby-time stability; and cross-regime support.
4. Only then shadow the frozen candidate without broker writes, reconcile quoted
   versus achievable fills, and establish live slippage distributions.
5. Paper trade with explicit risk caps before any live-trading review.

## Future research roadmap

- Highest value: more time, not more parameters.
- Add durable macro-event flags (CPI/FOMC/OpEx), breadth, futures basis, and dealer
  positioning only if historical timestamps can be obtained without look-ahead.
- Store non-0-DTE expirations before researching calendars, diagonals, weeklies, or
  term-structure trades.
- Revisit realized-versus-implied long gamma after the holdout grows; it was the
  most economically grounded filtered hypothesis, but current training results fail.
- Consider ML only after a simple frozen benchmark survives multiple regimes and
  sample size supports nested walk-forward validation.

## Reproducible artifacts

- Runner: `src/butterfly_guy/scripts/discover_options_strategy.py`
- Focused checks: `tests/test_discover_options_strategy.py`
- Journal: `docs/research/strategy-discovery-journal.md`
- Machine-readable metrics/trades/charts: `reports/strategy_discovery/` (local,
  intentionally gitignored)
