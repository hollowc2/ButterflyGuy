# Configuration Matrix

This document summarizes the current SPX, NDX, and XSP runtime profiles that Fable must
understand before reproducing strategy behavior. Values come from:

- `configs/config.yaml`
- `configs/config_ndx.yaml`
- `configs/config_xsp.yaml`

Do not treat this as a recommendation to merge the profiles. SPX, NDX, and XSP are
separate operating profiles with different scale, liquidity, strike grids, quote-quality
requirements, and risk settings.

## Shared Defaults

| Setting | SPX | NDX | XSP |
| --- | --- | --- | --- |
| Schwab token path | `tokens.json` | `tokens.json` | `tokens.json` |
| Max token age | `518400` seconds | `518400` seconds | `518400` seconds |
| Entry start | `07:00` | `07:00` | `07:00` |
| Entry end | `07:45` | `07:45` | `07:45` |
| Entry timezone | `America/Los_Angeles` | `America/Los_Angeles` | `America/Los_Angeles` |
| Strike selection | `VIX` | `VIX` | `VIX` |
| Profit strategy | `peakvaluetrailer` | `peakvaluetrailer` | `peakvaluetrailer` |
| Paper trading | `true` | `true` | `true` |
| Paper fill buffer | `0.00` | `0.00` | `0.00` |
| Price ladder steps | `4` | `4` | `4` |
| Retry interval | `20` seconds | `20` seconds | `20` seconds |
| Order timeout | `300` seconds | `300` seconds | `300` seconds |
| Snapshot cadence | `60` seconds | `60` seconds | `60` seconds |
| Max trades per day | `1` | `1` | `1` |
| Max position size | `1` | `1` | `1` |

## Strategy Profile

| Setting | SPX | NDX | XSP |
| --- | --- | --- | --- |
| Underlying | `SPX` | `NDX` | `XSP` |
| Static wing widths | `[10, 20, 30]` | `[80, 100, 150]` | `[3, 4, 5]` |
| VIX buckets | Yes | No | Yes |
| Spot scan range | `100` | `250` | `10` |
| Center tolerance | `15.0` | `100.0` | `1.5` |
| Minimum debit | `0.05` inherited from `StrategySettings` | `0.05` inherited from `StrategySettings` | `0.25` |
| Reward/risk minimum | `8.0` | `8.0` | `8.0` |

## VIX Width Buckets

SPX:

| VIX condition | Active widths |
| --- | --- |
| `< 17.0` | `[20, 25, 30]` |
| `< 24.5` | `[20, 30, 40]` |
| `< 32.0` | `[40, 45, 50]` |
| catch-all | `[50, 55, 65]` |

XSP:

| VIX condition | Active widths |
| --- | --- |
| `< 17.0` | `[3, 4]` |
| `< 24.5` | `[3, 4, 5]` |
| `< 32.0` | `[4, 5]` |
| catch-all | `[4, 5]` |

NDX currently uses static widths `[80, 100, 150]` and must keep widths compatible with
the NDX 10-point strike grid.

## Max Cost Per Width

| Asset | Width | Max cost |
| --- | ---: | ---: |
| SPX | 10 | 1.00 |
| SPX | 20 | 2.00 |
| SPX | 25 | 2.50 |
| SPX | 30 | 3.00 |
| SPX | 35 | 3.50 |
| SPX | 40 | 4.00 |
| SPX | 45 | 4.50 |
| SPX | 50 | 5.00 |
| SPX | 55 | 5.50 |
| SPX | 65 | 6.50 |
| NDX | 80 | 6.00 |
| NDX | 100 | 8.00 |
| NDX | 150 | 12.00 |
| XSP | 3 | 0.30 |
| XSP | 4 | 0.40 |
| XSP | 5 | 0.50 |

## Profit Management Regimes

| Asset | Regime | Minutes after open | Drawdown | Confirmation polls | Min peak ratio | Min hold |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| SPX | morning | `0-120` | `0.60` | `1` | `1.0` | `0` |
| SPX | late_morning | `120-240` | `0.90` | `1` | `1.0` | `0` |
| SPX | afternoon | `240-390` | `0.75` | `1` | `1.0` | `0` |
| NDX | morning | `0-120` | `1.00` | `3` | `1.5` | `0` |
| NDX | late_morning | `120-240` | `0.95` | `2` | `1.5` | `0` |
| NDX | afternoon | `240-390` | `0.90` | `2` | `1.5` | `0` |
| XSP | morning | `0-120` | `0.80` | `3` | `1.25` | `30` |
| XSP | late_morning | `120-240` | `0.90` | `3` | `1.25` | `45` |
| XSP | afternoon | `240-390` | `0.85` | `3` | `1.25` | `45` |

Shared profit-management defaults:

| Setting | Value |
| --- | --- |
| Exit before close minutes | `0` |
| Absolute loss stop enabled | `false` |
| Max loss from cost | `0.50` |
| Breakeven activation profit | `1.00` |
| Breakeven floor profit | `0.00` |
| Profit-lock activation profit | `2.00` |
| Profit-lock floor profit | `0.75` |
| Large peak profit ratio | `2.00` |
| Large peak drawdown threshold | `0.50` |

## Quote Quality And Peak Tracking

| Setting | SPX | NDX | XSP |
| --- | --- | --- | --- |
| Quote quality enabled | `false` | `true` | `true` |
| Min bid-to-mark ratio | `0.0` | `0.35` | `0.75` |
| Max spread width ratio | `null` | `1.5` | `0.50` |
| Min mark value | unset | unset | `0.25` |
| Max leg spread to mark ratio | unset | unset | `1.00` |
| Max leg spread absolute | unset | unset | `0.20` |
| Peak tracking confirmation | default | default | `3` |
| Peak confirmation tolerance ratio | default | default | `0.10` |
| Peak requires quote quality | default | default | `true` |
| Peak max jump ratio | default | default | `0.50` |
| Peak max jump absolute | default | default | `0.10` |

Fable must preserve the distinction between quote-quality checks for exit signals and
spread-quality checks for paper fill realism. `BEHAVIORAL_SPEC.md` defines the stricter
target behavior.

## Execution And Risk Differences

| Setting | SPX | NDX | XSP |
| --- | --- | --- | --- |
| Price ladder step | `0.10` | `0.10` | `0.01` |
| Paper slippage per spread | `0.05` inherited from `ExecutionSettings` | `0.05` inherited from `ExecutionSettings` | `0.005` |
| Paper commission per contract | `0.65` inherited from `ExecutionSettings` | `0.65` inherited from `ExecutionSettings` | `0.65` inherited from `ExecutionSettings` |
| Max daily loss | `500.0` | `500.0` | `50.0` |
| Max weekly loss | unset | unset | `150.0` |
| Max consecutive losses | unset | unset | `10` |
| Min buying power | unset | unset | `200.0` |
| Fail safe on balance error | default | default | `true` |

## Refactor Requirements

- Config loading must validate each profile independently.
- Missing optional settings must resolve through explicit defaults, not accidental null
  behavior.
- Inherited replay-sensitive defaults such as `min_debit`, paper slippage, and paper
  commission must be materialized in loaded profile tests.
- Unit tests must prove SPX, NDX, and XSP profiles load with their current defaults.
- Strategy tests must cover both bucketed-width profiles and the static-width NDX
  profile.
- Risk tests must cover XSP's extra weekly-loss, consecutive-loss, buying-power, and
  balance-error settings.
- Live-trading approval settings must be added separately and must default to disabled.
