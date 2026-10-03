# Canonical research datasets

This folder is the stable research cache root. It holds only the canonical normalized
datasets, as symlinks into the private caches where they were built:

| Dataset | Range | Role |
|---|---|---|
| `spx_0dte_local_durable_development_20261001` | 2022-01-03 → 2024-06-28 | Development, 585 sessions, quality Q1–Q6 pass |
| `spx_0dte_local_durable_spent_holdout_20261003` | 2024-07-01 → 2026-03-12 | The spent H-TS1 holdout. Post hoc only, never an unseen test |
| `spx_0dte_local_durable_validation_20261001` | 2026-03-13 → 2026-09-25 | Validation, 128 sessions, Q1–Q4 and Q6 pass (Q5 not evaluable) |
| `local_support_v1` | — | Supporting index observations and daily inputs; not a strategy dataset |
| `spx_0dte` | — | Recorded Helios dataset; the reference for `vendor-quality` |

The links point into `reports/thetadata_completion/2026-10-01/thetadata-cache/`, which also
holds earlier, non-canonical imports kept as evidence. The dated records cite that path, so
nothing was moved. See [docs/data-management.md](../../docs/data-management.md).

Use it from the repository root of the main checkout:

```bash
export BUTTERFLY_RESEARCH_CACHE=$PWD/data/research_cache
uv run python -m butterfly_guy.research \
  --dataset spx_0dte_local_durable_development_20261001 verify
```

The datasets are vendor-derived and private (personal-use licence): never commit them.
