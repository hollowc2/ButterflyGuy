# Batman XSP — expanded history, November 13, 2026

**Decision: insufficient evidence.** User explicitly requested extending the date
range after the prior bounded study. Exactly the same eight Batman cells were
reused; no economic parameter, geometry, entry gate, size, fee, stress or exit
was tuned. No runtime configuration, services, credentials or orders changed.

- [Standalone HTML report](../../reports/research/xsp-batman-2026-11-13/index.html)
- [Retained summary and hashes](xsp-batman-history-2026-11-13.summary.json)
- [Frozen specification](../../reports/research/xsp-batman-2026-11-13/run-01/specification.json)
- [All trial results](../../reports/research/xsp-batman-2026-11-13/run-01/summary.json)
- [Complete journal](../../reports/research/xsp-batman-2026-11-13/run-01/journal.jsonl)
- [Verification](../../reports/research/xsp-batman-2026-11-13/verification.json)

## Coverage and source qualifications

Window January3,2022–September28,2026; **1,118** genuine XSP option dates,
**1,035** feature-covered sessions, 82 missing prefixes and one invalid straddle.
2022–2025 SPX/10 comes from the owner minute CSV, original third-party provider
unknown, with the documented America/Chicago bar-end mapping. Start label is
end minus one minute; availability stays at the bar end. 2026 keeps the original
recorded tick feed. No native intraday XSP or new complex-order fill evidence.

The same documented30-comparison stale threshold is enforced causally. On first
detected repeated/full invalid OHLC, observations become unavailable through
that day. Earlier entries remain admitted and use the original gap/fill-window
settlement fallback. No future whole-day stale exclusion or interpolation.
The first29 repeated comparisons may remain undetected. Detection receipts are
preserved. This source handling is a disclosed adaptation, not a threshold search.

Native Cboe W/S/M settlement JSON was acquired for2022–2025; original2026 native
values/receipt were retained. Exact XSP trading and settlement identities are
required. **44 archive dates lack native terminal values**, chiefly early2022,
plus2022-09-06 and2023-07-11. They were not dropped based on future coverage.
Any admitted unresolved position remains in the journal with opening cash/risk
and payoff bounds. No missing terminal cash becomes zero. Priced-only metrics
are explicitly incomplete and must not be promoted as full-cohort performance.

Older dates have been inspected in other SPX research; the2024–2026 SPX holdout
is spent. All2026 Batman outcomes were previously known. No untouched holdout is
claimed. 2020–2021 remain outside the documented joint source/calendar scope.
The fixed expanded-period split is2024-07-01, not a median accepted-trade split.

## Complete frozen matrix

- `all_strikes_movement_settlement`: 74 accepted, 72 priced, 2 unresolved; priced stressed net $-1,641.40; full-cohort bounds [$-1,934.80, $-1,134.80]; **insufficient evidence**.
- `all_strikes_movement_zone_exit`: 74 accepted, 72 priced, 2 unresolved; priced stressed net $-2,498.40; full-cohort bounds [$-2,791.80, $-1,991.80]; **insufficient evidence**.
- `all_strikes_unconditional_settlement`: 861 accepted, 822 priced, 39 unresolved; priced stressed net $-22,447.40; full-cohort bounds [$-28,161.20, $-12,561.20]; **insufficient evidence**.
- `all_strikes_unconditional_zone_exit`: 861 accepted, 827 priced, 34 unresolved; priced stressed net $-30,207.20; full-cohort bounds [$-35,192.00, $-21,592.00]; **insufficient evidence**.
- `body_movement_settlement`: 80 accepted, 78 priced, 2 unresolved; priced stressed net $-6,073.60; full-cohort bounds [$-6,930.00, $-6,030.00]; **insufficient evidence**.
- `body_movement_zone_exit`: 80 accepted, 80 priced, 0 unresolved; priced stressed net $-11,744.20; full-cohort bounds [$-11,744.20, $-11,744.20]; **reject**.
- `body_unconditional_settlement`: 990 accepted, 949 priced, 41 unresolved; priced stressed net $-79,424.80; full-cohort bounds [$-100,247.00, $-80,447.00]; **insufficient evidence**.
- `body_unconditional_zone_exit`: 990 accepted, 962 priced, 28 unresolved; priced stressed net $-148,767.20; full-cohort bounds [$-164,448.80, $-150,748.80]; **insufficient evidence**.

Each policy uses two flies/eight gross contracts; rows are correlated alternatives,
not a combined portfolio. Full-cohort bounds add the contract-payoff minimum and
maximum for unresolved settlement positions. They are not synthetic fills or
imputed settlements. Missing outcomes force insufficient evidence under the
frozen decision rule, even when a priced subset is positive or negative.
**Every cell's full-cohort upper bound is negative under the frozen component
execution model. Even granting each missing settlement its maximum theoretical
payoff cannot produce a positive total.** Exact expectancy remains unavailable
for incomplete cells; the economic upper-bound failure is separately established.
Monthly, yearly, source-separated, costs, risk units, top-three sensitivity,
matched participation and sampled payoff-zone reach are in the report. DD is
once-per-terminal-outcome, not intraday; incomplete DD cannot bound the full cohort.

## Verification and reproduction

All **1,480** original2026 date/cell rows reproduce exactly before adding source
labels. All **3862** completed cash records and
**148** unresolved openings reconcile independently
to raw quote sides/quantities and individual option intrinsic, zero discrepancies.
The journal retains **8,944** date/cell rows including exclusions/no-signals.
**67 focused tests**, full Ruff and desktop/mobile HTML controls/downloads pass.
Graphify updated with the existing missing SQL-parser warning; no SQL changed.
The original study's80 artifact hashes still match; unrelated tracked changes
are preserved. Native downloads, source/input hashes and initial dirty-tree patch
are retained in fresh directories; never overwrite a completed or partial run.

```bash
uv run python -m tools.research_studies.xsp_independent.batman_history acquire --out /tmp/batman-history-acquisition-new
uv run python -m tools.research_studies.xsp_independent.batman_history prepare --out /tmp/batman-history-inputs-new --acquisition /tmp/batman-history-acquisition-new
uv run python -m tools.research_studies.xsp_independent.batman_history freeze --out /tmp/batman-history-run-new --prepared /tmp/batman-history-inputs-new
uv run python -m tools.research_studies.xsp_independent.batman_history run --out /tmp/batman-history-run-new
uv run python -m tools.research_studies.xsp_independent.batman_history_report review --run /tmp/batman-history-run-new
uv run python -m tools.research_studies.xsp_independent.batman_history_report render --run /tmp/batman-history-run-new --out /tmp/batman-history-run-new/index.html
uv run pytest tests/test_xsp_batman_history.py tests/test_xsp_batman.py tests/test_xsp_quiet_flies.py tests/test_xsp_settlement_data.py -q
uv run ruff check .
graphify update .
```

Stop the same fixed matrix here. Further research needs materially new evidence
or separately frozen changes; this extension authorizes no promotion/activation.
