# F2 draft scorer review — 2026-10-03

The [October 2 draft](f2-shadow-registration-2026-10-02.md) is preserved unchanged.
It and its scorer were uncommitted when reviewed. Their pre-observation freeze
has not been independently established, so the corrected scorer labels its
outputs **exploratory shadow**. Neither the old historical table nor new shadow
results authorize a strategy change. The draft's timer claim was not verified
in this review; no service was installed, restarted, or changed.

The definition remains SPX v2 cohort entries, VIX at least 16 at the entry
decision, and cash settlement at the same-session official close. Costs come
from the frozen cohort's entry price, including entry commission and stress;
cash settlement adds no exit commission or slippage. The endpoint remains the
first chronological sample with at least 60 trades and 8 stressed winners,
with an early stop when stressed drawdown exceeds $8,000. The draft's five
decision gates are retained.

Six failing synthetic tests reproduced counting beyond the endpoint, counting
after an early drawdown stop, rejecting an all-winning sample on profit factor,
using append order for drawdown, and skipping unresolved VIX/settlement evidence
to count later entries. The corrected scorer stops database reads at the first
endpoint, early stop, or unresolved entry. Missing stressed accounting or paired
E0 pricing also blocks later entries rather than biasing the comparison.

The scorer requires the exact original v2 manifest and checks the cohort's
record hashes, trade/session links, configuration, and frozen sources before
reading market inputs. Its own imported shared helpers must match those frozen
sources. The VIX age limit comes from the cohort checkout's frozen config.
Reports record hashes of all four cohort input files, the scorer, the original
draft, and shared dependencies; each derived row retains its cohort record hash,
VIX timestamp/value, and settlement observation. A concurrent ledger update
requires a retry. Previously resolved observations cannot silently change.

The original draft hashes are:

- Document: `da47c54bef0cb13e3a56d1e3e5949eb47f9d18a2a347b0d63deae7d00b74f2ec`
- Scorer before corrections: `ac352c15f1ce58f3b1f5b5cfb5829ba8bec516a0f75076f99a5b1da20b445bfb`

Run the tool from a checkout containing this reviewed version, with the normal
database environment available. The dedicated v2 checkout stays pinned:

```bash
uv run --locked python tools/f2_shadow_report.py \
  --cohort /mnt/Repos/Trading/Butterflyguy/.worktrees/spx-prospective-v2/reports/prospective_execution/spx-prospective-v2-2026-10-02 \
  --out reports/f2_shadow_reviewed
```

Use a separate output directory from the original draft's reports. They are
preserved as historical evidence; their unhashed rows are not silently adopted
by the corrected scorer. Earlier start dates are refused to prevent dry runs
from entering the fixed-window output. A new prospective registration requires
its own auditable pre-observation freeze; this review does not create one.

Verification uses synthetic data and mocked database lookups, including equality
with cohort cash-settlement P&L under every accounting model. No database-backed
performance study was run for this patch.

Validation: 20 focused tests passed; the integrated full suite passed 1,147
tests with one real-database test skipped because `CI_DATABASE_URL` was unset.
Repository-wide Ruff passed. The actual frozen v2 ledger and source hashes
verified without querying market prices. Graphify was refreshed using AST extraction.
