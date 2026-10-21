# SPX launch decision — 2026-10-20

Decision: **NO-GO / insufficient evidence** for the first one-contract live SPX
order. This is an implementation-time record awaiting owner review and merge;
it is not a claim that a favorable go/no-go record has already been merged.

The verified dedicated cohort checkout at
`cohort/spx-prospective-v2-2026-10-02` now contains twelve eligible trades through
October 19, +$1,158.00 stressed net, $853.00 realized drawdown and four cash
settlements. The frozen updater resolved October 19 during this implementation.
The scheduled updater subsequently committed the evidence as `2eaf522` and its
report generated 2026-10-21T01:32:24Z defers October 20 because official settlement
was unavailable. Stressed intraday exits total −$1,726.60; settlements total
+$2,884.60. The top three winners represent 100% of gross profit, failing the
registered concentration gate. Twelve trades cannot complete the registered
twenty-trade integrity review. The existing deferral audit history remains intact.

The October 18 activation study reports 823 E0 trades over 1,070 eligible
observations in 2022–2026: −$39,319 stressed net and $53,430 maximum realized
drawdown. Its annual stressed results are +$3,524 (2022), −$16,228 (2023),
−$9,562 (2024), −$23,137 (2025) and +$6,084 (available 2026 coverage).
These are unequal coverage windows, not directly comparable full-year returns.
The study is present as uncommitted research in the source checkout when this
branch was prepared; its artifacts have not been copied or modified here.

The recent forward result is favorable, but the small settlement-dependent
sample does not establish that 2026 conditions will persist or outweigh the
multi-year executable-cost losses. The longer record is retrospective and
one-minute leg quotes do not prove complex-order fills, but those limitations
also prevent using the favorable recent simulation as fill proof. There is
currently no evidenced basis to waive the conflict or call E0 a demonstrated
live edge. Keep the frozen strategy and current paper services unchanged.

Revisit this decision after unresolved sessions are recorded with official
evidence and the registered twenty-trade integrity review is signed. Preserve
the original cohort's 120 eligible trades, twenty settlements, fifteen stressed
winners and other registered tests. The launch decision uses the twenty-trade
review as Corey specified; the sixty-trade review continues and can return a
live app to paper. Do not tune E0 with these results and still label v2 untouched.

For the next decision, attach the verified manifest/ledger hashes, review
artifact, original replay journals and cost assumptions, annual/period results,
profit concentration, settlement dependence, observed live execution evidence
if available, every open operational gate, reviewer and date. A favorable record
needs an explicit explanation of why forward evidence should outweigh the
losing replays. If that explanation remains unsupported, retain NO-GO.

Read-only ledger verification (run from the dedicated pinned v2 checkout):

```bash
uv run --locked --no-sync python -m butterfly_guy.scripts.run_prospective_execution \
  verify --cohort reports/prospective_execution/spx-prospective-v2-2026-10-02
```

The append-only updater retries unresolved dates before later sessions. The
successful manual retry used that checkout's frozen CLI with
`update --cohort reports/prospective_execution/spx-prospective-v2-2026-10-02
--through 2026-10-19`. Continue using the pinned updater; never substitute
settlement, rewrite ledgers, or rebase the cohort onto these launch-control edits.
