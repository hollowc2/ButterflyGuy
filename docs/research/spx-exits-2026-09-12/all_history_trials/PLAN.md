# All-history extension fixed before execution

September 13, 2026. Extend the executed exit trials to every one of the 108
recorded SPX long debit butterfly trades, March 17–September 11, 2026 inclusive.
All quantities are one; entries, strikes, directions and ledger entry prices
remain fixed. No live trading, recording, risk, or service changes.

Reuse the parent's immutable Schwab/ButterflyGuy exports and frozen deployed
source. Import the exact three primary variants and six neighbors from
`../exit_trials/run_trials.py`: late-morning drawdown 60% (50%, 70% neighbors),
absolute loss stop 50% (40%, 60%), observed breach confirmation 5 seconds
(2, 10), max inter-observation gap 10 seconds. No combinations or retuning.
The comparator is today's frozen 60/90/75 exit policy applied retrospectively,
not a claim to reconstruct every historical runtime setting or fill ladder.

Attempt every trade separately on monitoring and collector paths. Preserve all
missing outcomes. Additionally form `best_available` by choosing monitoring
whenever raw monitoring rows exist, otherwise collector, before examining any
outcome. Never stitch paths or fall back after a failed replay. This composite
is exploratory, not a validated 108-trade counterfactual.

Keep the prior five fill scenarios and commissions unchanged. Signal decisions
depend only on marks, so evaluate a policy once and apply the five fill scenarios
to its resulting signal. Require regression against every original source's
baseline scenario and every result of the prior 33-trade experiment. Settlement
reuse and censoring retain their original rules. Never infer a fill at a threshold
or a final available quote. Entry execution remains fixed; legacy entry commission
attribution is uncertain. Report arithmetic-only extra $2.60/legacy-entry and
$5.20/all-entry fee sensitivities, not attested historical fees.

Report the full 108, legacy 75, and mark_v1 33 as separate cohorts. Compare each
candidate only against baseline on identical resolved IDs. Show attempted,
resolved, paired, excluded, and ledger-parity counts. Ledger parity uses net P/L
within $0.01, reason equal, timestamp within 10 seconds; separately flag material
P/L errors over $5. Keep all mismatches and unresolved rows visible.

Metrics: net P/L, expectancy, win rate, profit factor, average win/loss, closed
drawdown, exposure, trade-P/L standard deviation and mean/SD, modeled costs,
monthly and direction concentration, same-ID replay-baseline top-five retention,
and outcomes for the ten largest recorded winners (including those absent from
paired aggregates). No annualized account Sharpe, marked equity drawdown, or
account returns: necessary capital/calendar/equity evidence is unavailable.

The entire history is examined development data. No new significance claim,
bootstrap-based promotion, held-out claim, or live deployment follows from this
extension. Verify focused behavior tests, exact historical regressions, independent
CSV aggregation/coverage, Ruff, and graph update. Save the report and all derived
data here; preserve the previous research results unchanged.
