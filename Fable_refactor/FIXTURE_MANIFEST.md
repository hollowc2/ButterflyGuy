# Fixture Manifest

This manifest names the deterministic fixtures Fable must use before implementing
strategy, execution, runtime writes, or live broker boundaries. Fixtures should be
exported from the existing database as small redacted records, not as full database
dumps.

Secrets, account ids, token values, and raw broker credentials must not appear in any
fixture. If a field is not required for deterministic behavior, omit it.

## Config Hashes

The fixture package must include redacted copies of these profile files and verify their
SHA-256 hashes before running parity tests:

| Profile | Source file | SHA-256 |
| --- | --- | --- |
| SPX | `configs/config.yaml` | `f8c8d66b2a8500a1925e556da05653875e10953db0934e52a6a7a44601a41ffb` |
| NDX | `configs/config_ndx.yaml` | `4461ccbcbac45cc28c7a93469855c2ff84412a19ddd97bbb3869ac851bf9b1db` |
| XSP | `configs/config_xsp.yaml` | `41a9b6df42f2a019d32723e67c64aa778711c4a29bda3ba327a5edc03df749df` |

If any source config changes, regenerate this manifest and the expected candidate
outputs in the same commit.

## Phase 1 Market-Data Fixtures

These snapshots are the minimum read-only adapter fixtures. Each fixture must include
the full row-oriented `option_chain_snapshots` rows for the exact timestamp, matching
nearest spot rows, the `$VIX` spot used by the trade metadata, and prior `daily_bars`
needed for previous-close context.

| Fixture id | Asset | Expiration | Snapshot time UTC | Rows | Spot | Config profile |
| --- | --- | --- | --- | ---: | ---: | --- |
| `spx_2026_06_16_135923432370` | SPX | `2026-06-16` | `2026-06-16T13:59:23.432370Z` | 540 | 7553.43 | SPX |
| `ndx_2026_06_16_140003581774` | NDX | `2026-06-16` | `2026-06-16T14:00:03.581774Z` | 928 | 30490.27 | NDX |
| `xsp_2026_06_17_140013523132` | XSP | `2026-06-17` | `2026-06-17T14:00:13.523132Z` | 560 | 750.77 | XSP |

Phase 1 adapter tests must prove exact-timestamp loads and nearest-at-or-before loads
return these same row counts, expiration dates, and Decimal spot values.

## Selection Fixtures

These expected candidates are derived from recorded trade metadata and DB selection
parity. They are intentionally fixed before Fable implements selection logic.

| Fixture id | Direction | VIX | Active widths | Expected candidate | Expected cost | Expected reward/risk | Notes |
| --- | --- | ---: | --- | --- | ---: | ---: | --- |
| `spx_2026_06_16_135923432370` | PUT | 15.95 | `[20, 25, 30]` | width 25, center 7510, lower 7485, upper 7535 | 2.14 | 10.6822 | DB selection parity for trade 130; live retry later selected width 30. |
| `ndx_2026_06_16_140003581774` | PUT | 15.95 | `[80, 100, 150]` | width 100, center 30270, lower 30170, upper 30370 | 7.50 | 12.3333 | DB selection parity for trade 132. |
| `xsp_2026_06_17_140013523132` | CALL | 16.57 | `[3, 4]` | width 3, center 759, lower 756, upper 762 | 0.25 | 11.0000 | Current XSP config with `min_debit=0.25`; trade 133. |

Candidate tests should also preserve the per-width winners when exported from metadata:

| Fixture id | Per-width winners |
| --- | --- |
| `spx_2026_06_16_135923432370` | 20 -> center 7515 cost 1.63 RR 11.2699; 25 -> center 7510 cost 2.14 RR 10.6822; 30 -> center 7505 cost 2.50 RR 11.0000 |
| `ndx_2026_06_16_140003581774` | 80 -> center 30300 cost 5.95 RR 12.4454; 100 -> center 30270 cost 7.50 RR 12.3333 |
| `xsp_2026_06_17_140013523132` | 3 -> center 759 cost 0.25 RR 11.0000; 4 -> center 760 cost 0.34 RR 10.7647 |

## Golden Replay Cases

These trade and decision ids are the first golden replay set. They should not be used by
Phase 1 except as identifiers for fixture export; later phases must replay them without
broker writes.

| Case id | Source id | Asset | Trade date | Purpose | Expected result |
| --- | --- | --- | --- | --- | --- |
| `spx_cash_settled_130` | `butterfly_trades.id=130` | SPX | `2026-06-16` | Cash-settled index lifecycle | Status `CLOSED`, exit reason `cash_settled`, final PnL `20.4000`. |
| `xsp_drawdown_131` | `butterfly_trades.id=131` | XSP | `2026-06-16` | XSP drawdown and ladder replay | Status `CLOSED`, exit reason `drawdown_morning`, final PnL `-0.1100`. |
| `ndx_end_of_day_132` | `butterfly_trades.id=132` | NDX | `2026-06-16` | Static-width NDX and end-of-day lifecycle | Status `CLOSED`, exit reason `end_of_day`, final PnL `-10.0300`. |
| `ndx_no_candidates_66068` | `decision_log.id=66068` | NDX | `2026-06-17` | No-trade candidate rejection | Event `no_candidates`, direction `CALL`, spot `30033.5067`. |
| `xsp_quote_quality_reject_66140` | `decision_log.id=66140` | XSP | `2026-06-17` | Peak update blocked by quote quality | Event `peak_update_rejected`, trade id `133`, reason `quote_quality`. |

## Export Rules

- Store fixture timestamps in UTC ISO-8601 format and preserve original `TIMESTAMPTZ`
  precision.
- Store money, strikes, greeks, and ratios as strings or Decimals, never binary floats.
- Keep row-oriented option-chain fixtures row-oriented; do not convert the source
  fixture into a JSON blob shape.
- Redact metadata fields that contain account ids, order ids, token material, or broker
  secrets.
- Preserve source ids and config hashes in every generated fixture file so failures can
  be traced back to the exact historical case.
