# NDX-01 evidence and baseline reconciliation — 2026-10-15

**Decision: reference baseline reproduced; refine evidence/execution fidelity.**
NDX-01 establishes the named offline reference and explicit eligibility. It does
not establish complete runtime parity, official settlement, or a strategy
candidate. None of the six rejected variants was rerun or promoted. Runtime
source, settings, services, orders and credentials were left unchanged.

The [reproduction guide](README.md) owns commands and recovery paths. The
[final contract](evidence/2026-10-15/r0-reproduction-final.json) and
[summary](evidence/2026-10-15/summary.json) link inputs to results. The living plan
remains the project handoff.

## Freeze and identities

Starting HEAD was `6a33d170c09f7ff68d7edb733b74c087b27c0227`. Existing changes
included `docs/README.md`, the living NDX plan/evidence, four generated graph files
and pending graph labels. Their original bytes/status/patch were preserved before
implementation. No existing work was reset, cleaned, committed or discarded.

All 29 historical final-file hashes and 15 historical input hashes passed before
copying. The snapshot also hashes `manifest.json` and `path-quality.csv`, which
were not themselves covered by the historical final-file map. The entire original
bundle, including superseded results, remains unchanged. New source pins cover
138 Python/dependency/test files; a changed pin refuses historical reproduction.

Four policies/implementations must remain distinct:

1. **Dated deployed policy:** the captured `deployed-config.yaml` is the October 14
   remote configuration, SHA-256 `4438f5c0…`. Current October 15 NDX container and
   host config match these bytes. Checked-out YAML differs in formatting but has
   the same parsed values. This does not attest every trade's effective settings.
2. **Policy actually used for trades:** entries, quantities, fills, reasons and
   later entry-policy metadata are observed records. No trade has a full recorded
   `profit_management` snapshot. The 113 trades span evolving fill conventions,
   code, restarts and diagnostics. No complete per-trade effective policy,
   environment overrides or deployment timeline is available. Historical Git
   source can explain mechanics; a commit date alone cannot prove deployment.
3. **Current checkout:** the three local source hashes in the historical manifest
   still matched at the start. The manifest's `code_sha256` was produced from
   **local** files, not a deployed-container source inventory. The checkout has
   later service/data changes and is not interchangeable with the host's Git SHA.
4. **Research approximation:** the archived replay used local
   `ProfitManagementSettings`, `PositionState`, `ProfitStateMachine`,
   `profit_policy` and calendar helpers, plus numpy/pandas/yaml/structlog. It
   reconstructed a raw running mark peak, fixed regime boundaries, reset drawdown
   confirmations across gaps, held entries fixed, and used the next recorded
   observation or terminal diagnostic for a fill. It did not execute
   `PositionManager` peak confirmation/quality/recovery, service orchestration,
   actual order timing, skipped opportunities or risk-state feedback.

Read-only runtime inspection added an important distinction: Helios's repository
HEAD is `288d6cb321e611a94acc819fa96fc5e429ff836e` (September 25) and its source
files are older than its running container. The observed NDX image is
`sha256:1fbc1ab3aed0aec85bcccab9e5009679789baab10fc333cfd0e4636ef1e7cc61`,
created October 8 at 00:20:52 UTC. Among seven inspected Python files, container
state machine, position manager, order manager, time utilities and profit policy
match the current local files; config and position service differ. The six
relevant profit/execution schema class ASTs match, while other config/service
changes exist. See [source comparison](evidence/2026-10-15/source-comparison.json),
[schema comparison](evidence/2026-10-15/schema-comparison.json), and
[current container environment](evidence/2026-10-15/runtime-environment.json).
These selected files, an image identity and current dependencies **do not prove
full runtime parity or identify all prior deployments**. No environment/credential
values were inspected. Original full runtime dependency versions were not
recorded. New runs preserve the checked-in lock and their actual environment.

The historical SQL, scripts and YAML all remain in `raw/`. Versioned SQL copies
make extraction reviewable. The new implementation removes absolute import paths,
`exec` prefixes and `/tmp` fallback dependencies. Verification, normalization,
fixed-entry replay, accounting and coverage/report generation are separate
functions; SSH extraction is a separate command.

## Tolerances and reproduction

Before numerical assessment the contract fixed:

- Composite mark comparison: 0.00011 option points, reflecting four-decimal stored
  composite precision and a small floating-point allowance.
- Dollar accounting/reproduction: $0.01 per trade. Aggregate differences are also
  reported; no aggregate allowance hides opposing trade discrepancies.
- Historical signal/fill timestamp reproduction: one microsecond, matching stored
  timestamp precision. Exit reasons and statuses must match exactly.

The 30-second continuity/fill window and 120-second final-coverage gate are dated
R0 assumptions. They are not runtime-parity tolerances or exchange-freshness
proofs. Differences versus recorded runtime prices/times remain visible even
when the archived research model reproduces exactly. No tolerance was widened.

Final run **run-03** reproduced every archived baseline status, reason, signal
and exit time, paper P&L and available stressed P&L on all 75 recorded paths.
The 38 trades without paths are explicit missing observations. Results:

- 514,551 groups; 4,377 incomplete groups excluded; 510,174 complete groups;
  zero complete composite-mark mismatches.
- All 113 recorded trades: −$9,832.40; 53 `mark_v1` recorded trades: +$9,254.84;
  stored marketable-price stress on those 53: −$30,978.16.
- Modern replay: 34 settlements, 17 exits, one censored fill, one censored
  continuation. The 51 resolved paths produce +$10,592.84, compared with
  +$10,481.84 recorded on **those same 51**, a +$111 difference explained below.
  Neither number replaces the 53-trade recorded result.
- Frozen historical common cohort: 49 trades, +$7,969.59 paper and −$29,848.41
  stress. The historical uninterrupted common cohort has 32 trades.

The common IDs come from the verified parent metrics. This reproduces the parent
cohort without executing candidates; it does not remove its complete-case bias.

Run-01 failed: the initial port added a nonnegative bound to `close-last_tick`,
incorrectly censoring 12 historical settlement paths (nine modern) whose final
monitor tick occurred after the close but before recorded settlement. The exact
R0 condition was restored, and a dedicated independent fixture now covers this
case. Its failed output, contract and source remain preserved. Run-02 reproduced
the baseline; a combined test exposed a library logging-configuration side effect.
The final runner configures suppression only in its CLI, preserves source copies,
and adds stricter eligibility/reinitialization evidence in run-03. These are
port/audit revisions, not new strategy tests. Earlier output/contract files have
not been rewritten.

## Trade 222: August 6

The contract supplement verifies `NDXP 260806` PUTs at 29080/29180/29280.
Entry was 7.78; recorded settlement was zero at 20:00:02.258387 UTC, −$778.
The paper settlement source identifies the 15:59 Eastern minute at index
29377.7583; the put butterfly payoff is zero. This is not verified official XQC.

The running raw peak and recorded peak both reach 14.30; incorrect peak magnitude
is not the explanation. R0 signals `drawdown_afternoon` at 19:40:55.224372 UTC,
then fills at 19:40:58.013390 using mark 1.53 and bid 0.55. Rounded paper proceeds
are 1.50, giving −$628 (**+$150** versus the recorded settlement); stressed
proceeds are 0.47, giving −$1,451 (**+$47** versus the recorded stressed
settlement). The replay exit is 1,144.244997 seconds earlier.

Four gaps exceed 30 seconds: 65.458799, 117.675961, 42.407321 and 39.422652
seconds. Resetting pending confirmations across those gaps does not restore the
runtime state that existed after monitor reinitialization.

The recovered state log has `from: null` at 16:00:50, 17:17:09 and 18:01:32 UTC,
in addition to the initial observation. The latter two are LOSS states below
entry while retaining peak 14.30. After the 17:17 event, the highest subsequent
complete mark is 7.05, below entry 7.78; after 18:01 it is 4.75. The pre-September
26 service called `state_machine.reset()` on monitor adoption, clearing
`_ever_in_profit` even when a recovered peak existed. Restoring that flag from
recovered peak was subsequently fixed in commit `c0b229e`.

**Supported explanation:** reinitialized historical monitors could retain a peak
while disarming drawdown exits until value returned to entry; it never did after
the later reinitializations. R0 carries its profit-history flag continuously and
therefore exits. `from: null` supports monitor reinitialization; it is not an
attested process-restart/deployment record. No complete August 6 process log or
per-trade source attestation was recovered. Trade 222 remains explicitly excluded
from strict runtime-parity claims and the uninterrupted cohort. The original
baseline is preserved; no synthetic restart schedule or corrected strategy P&L
was substituted. See [reinitialization evidence](evidence/2026-10-15/reinitializations.jsonl).

## Other fills and independent accounting examples

The three remaining material modern price differences have matching reasons and
recorded exit times. Existing `trade_exited` events independently identify the
mark passed into the paper fill and the separately fetched diagnostic mark:

- Trade 294: signal mark 1.32 → `round(1.32−0.026,2)=1.29`, the actual recorded
  fill. Terminal diagnostic mark 1.48 → replay 1.45: **+$16** per fly.
- Trade 306: signal 3.74 → recorded 3.71; diagnostic 3.39 → replay 3.36:
  **−$35**.
- Trade 316: signal 2.82 → recorded 2.79; diagnostic 2.62 → replay 2.59:
  **−$20**.

Together these are −$39, offsetting $39 of trade 222's +$150. Seven modern
`trade_exited` records in the exported event window reconcile their fill to the
signal mark less rounded commission, with zero accounting difference. A
`trade_exited`/`exit_signal_fired` log timestamp can occur after fill time; it is a
telemetry-write time, not a causal exchange quote or order-submission timestamp.

Matching examples include trades 226 and 233, whose terminal diagnostics produce
recorded fills 2.06 and 1.22. October 13 trade 346 has mark 2.80 → paper exit 2.77;
entry 7.28 already includes entry commission, so P&L is `(2.77−7.28)×100=−$451`.
Stress uses bid 1.10 → `round(1.10−0.05−0.026,2)=1.02`; stored entry estimate
11.18 already includes entry cost, so stressed P&L is −$1,016. There is no further
fee deduction. The historical `recorded_gross` key is commission-inclusive.

For October 14 trade 349, recorded index proxy 29960.7966 gives payoff 30.7966
on the 29930/30030/30130 PUT butterfly. `(30.7966−7.83)×100=+$2,296.66`;
stress versus embedded entry estimate 14.38 is +$1,641.66. October 8 trade 336's
96.0246 settlement payoff gives +$8,814.46. Settlement precision is preserved;
no closing commission is charged. All 49 attributed proxy payoffs with known
contract identity reconcile; 13 older settlements lack an attributed source.
None becomes an official settlement observation.

Negative exit proceeds are floored at zero exactly as in R0; negative raw fly
bids are clipped before the stress-price deduction. The model can therefore be
more favorable than paying to close. **Zero** stored 53-trade stress exits and
**zero** modern baseline exits exercise the proceeds floor in this sample;
independent negative-credit fixtures verify counting and behavior. This is not
permission to remove that assumption from future disclosures.

Trade 194's stored marketable exit estimate uses a mark fallback because observed
bid/ask are missing. Thus the 53-trade stored stress result is not uniformly an
observed leg-bid calculation. R0 correctly leaves its simulated fill censored
when the terminal bid is unavailable; missing diagnostics are not invented.

## Coverage and research eligibility

The ledger covers **138 exchange sessions**, **113 trades on 112 sessions**,
including **26 sessions with no trade in the export**. This is the observed
calendar range, not an expanded research window. Unknown opportunity or skipped-day
evidence is never assigned a zero price or zero-P&L session.

- **Entry:** 53 selected-trade composite diagnostics are available. None of the
  138 sessions has a verified full opportunity/skip set in this snapshot, so no
  entry-selection experiment is eligible. 103 trades have decoded consistent
  symbols; ten early trades have no recoverable symbol identity in the DB
  supplement. Held-leg rows verify NDXP roots/expirations on all 75 covered paths.
- **Exit:** 52 modern trades pass R0's first/final coverage windows; one of those
  still has a censored fill. The broader uninterrupted sensitivity has 33
  modern paths, including a censored one. **32 resolved paths** meet the stricter
  predeclared complete observed-exit definition: verified NDXP same-session
  identity, prompt first/final coverage, no incomplete groups and no gap over
  30 seconds. Their IDs coincide with the historical uninterrupted common set.
  Strict full-runtime parity eligibility is false for every trade.
- **Incomplete observations:** 3,103 groups have two legs and 1,274 have one;
  none has an additional invalid-leg count. They belong to trades 278 (281
  groups), 280 (1,044), and 284 (3,052). Excluding them leaves missing intervals,
  not evidence of a zero butterfly value. The complete paths have **468**
  gaps over 30 seconds including entry delays; their times/durations and
  implications for confirmation/peak decisions are in the per-trade ledger.
- **Censoring:** July 23 trade 194 lacks a usable post-signal fill/bid diagnostic.
  September 14 trade 287 ends 355.699057 seconds before recorded exit and has no
  timely terminal path. Both simulated P&Ls remain null. A recorded outcome is
  retained separately even when its simulated path is censored.
- **Timestamps:** held-leg `ts` is a monitor collection/evaluation timestamp.
  Constituent exchange event time and availability/publication time were not
  stored there or exported. Decision logs sometimes contain DB snapshot times
  and lag diagnostics, which are not constituent quote-event times. A 30-second
  monitor gap sensitivity cannot establish exchange freshness or exact fill
  latency. Historical event-time/availability gaps cannot be recreated later.
- **Settlement:** 49 attributed source/spot/timestamp observations support
  recomputing the recorded **paper proxy** payoff. No official XQC observations
  are verified. Historical metadata omitted settlement time in R0's CSV; the
  read-only supplement recovered those 49 timestamps without altering R0.
  Thirteen older settlement sources remain missing. Unsupported live-quote or
  wrong-expiration chain fallback is not used by the offline replay.
- **Continuation:** the held-leg table and R0 extraction have zero post-exit
  observations. No counterfactual hold-after-exit path is eligible in the named
  snapshot. A separate read-only inventory found exact-symbol, same-expiration,
  complete **minute-chain** observations after all **17** modern discretionary
  exits (1–143 timestamps each). See
  [continuation inventory](evidence/2026-10-15/continuation-inventory.json) and
  [recovery ledger](evidence/2026-10-15/recovery-ledger.jsonl). Those prices have
  not been imported or assessed for cadence, gaps or freshness. They are
  recoverable evidence for a new snapshot, not a silent continuation of monitor
  polls. Official settlement and complete entry opportunity data require their
  own attributed acquisition/validation; source counts do not make them eligible.

The raw extracts are already aggregated. Exact constituent quotes/timestamps
cannot be recovered from a composite alone. Some original leg rows still exist
on Helios, but absence of event-time fields is a schema limitation, not a
recoverable CSV omission. Historical deployment state remains partially
unattributed. Independent minute histories are a separate recoverable source;
no assumption was made that their cadence matches the monitor stream.

## Validation and next bounded task

44 tests passed: 16 new focused tests (including the private full-snapshot test)
and 28 existing state-machine/position-manager tests. Independent fixtures cover
embedded/rounded fees, settlement precision/attribution, missing/incomplete data,
gap confirmations, next-observation/terminal fills, censoring, unsupported
fallbacks, hash/source mismatch, overwrite refusal and explicit-directory offline
operation. Full repository lint passed. See the
[verification record](evidence/2026-10-15/verification.json) for exact commands,
source/output hashes and graph update. No broker-connected test or service
restart was needed or performed.

The full-snapshot test blocks network sockets and every external command except
local Git. A separate local Git clone of starting HEAD with only the proposed
new source/test/docs files overlaid reproduced run-03 using explicit evidence
paths and the existing locked Python environment. This is an isolated-checkout
source/input check; a new dependency installation from an empty package cache was
not repeated. The snapshot remains required alongside a fresh checkout.

**Next: bounded NDX-02 accounting/execution calibration**, beginning with the
17 discretionary exits: separate signal mark, later diagnostic mark and stored
marketable estimate; identify mark fallback and timing coverage. Before any
hold-after-exit experiment, import the inventoried continuation prices into a
new attributed snapshot and predeclare its cadence/eligibility. Do not optimize
exits, rerun rejected settings or activate a service. Official XQC attribution
and original full effective-policy history remain explicit evidence limits.
