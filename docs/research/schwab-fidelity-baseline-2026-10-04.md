# Schwab recording fidelity baseline (2026-10-04)

The "before" numbers for the recording-timing work (Part A: timing metadata, Part B: fixed
minute cadence) in
[schwab-recording-fidelity-implementation-prompt.md](schwab-recording-fidelity-implementation-prompt.md).
Report only: no threshold applies (`thresholds: null`). Pass/fail limits need an
owner-approved plan written before metrics are computed, as with
[vendor-data-quality-plan-2026-09-28.md](vendor-data-quality-plan-2026-09-28.md).

## Run

```bash
export BUTTERFLY_RESEARCH_CACHE=$PWD/data/research_cache
uv run python -m butterfly_guy.research schwab-fidelity \
  --vendor-dataset spx_0dte_local_durable_validation_20261001 \
  --start 2026-03-13 --end 2026-09-25
```

- Helios recording `spx_0dte` @ `c7fff54a1ffa`, ThetaData
  `spx_0dte_local_durable_validation_20261001` @ `0f1fbcc08fda`.
- Artifact (gitignored):
  `reports/data_management/schwab_fidelity/2026-10-04/spx_0dte_local_durable_validation_20261001/e56fa5e4bbda/`
  (`summary.json` sha256 `f18f6f72…`). A second run reproduced the same artifact identity
  and the same bytes.
- 126 sessions compared. Helios only (no vendor session in the dataset): 2026-03-13,
  03-16, 03-18, 04-27, 05-04, 05-18, 06-02. Vendor only (too few Helios snapshots to
  export): 2026-09-03, 09-04.

## How approximate this is

Every session has `timing_basis: snapshot_time`. The recorded stamp is taken **before** spot,
VIX and the chain are fetched, so the chain's quotes are several seconds younger than their
stamp. A snapshot `x` seconds past a minute mark is paired with ThetaData's state at that
mark, which is `x` seconds older than the stamp and older still than the quotes. These
numbers mix real disagreement with timing mismatch, and the lateness split below shows the
timing mismatch is large. Treat them as an upper bound on disagreement, not as the vendor's
or Schwab's error.

## Headline numbers

All differences are Helios minus ThetaData. Percentiles are pooled over every cell.

**Matching.** 49,108 in-session snapshots, all matched to a vendor minute. Lateness after the
minute mark: 0–5 s 6.8%, 5–15 s 15.3%, 15–30 s 25.4%, 30–60 s 52.5%. The 60 s sleep after
each ~1.5 s pass makes the stamp drift through the minute, and more than half the snapshots
land in the second half. 3,074 of 49,140 scheduled minutes (median 16 a session) have no
snapshot, because a ~61.5 s period skips a minute about every 40.

**Option prices** (integer strikes within ±200 of spot, 7.72M cells):

| Bucket | \|Δmid\| median | \|Δmid\| p95 | Δspread p95 | Within $0.05 bid & ask |
|---|---:|---:|---:|---:|
| all | 0.15 | 2.45 | 0.30 | 42.1% |
| \|K−S\| ≤ 25 | 0.30 | 1.90 | 0.10 | 13.5% |
| \|K−S\| 25–50 | 0.20 | 2.30 | 0.15 | 31.4% |
| \|K−S\| 50–100 | 0.10 | 2.50 | 0.20 | 44.1% |
| \|K−S\| 100–200 | 0.05 | 2.65 | 0.40 | 51.1% |
| open (before 10:30) | 0.30 | 3.50 | 0.40 | 33.6% |
| midday | 0.10 | 2.25 | 0.20 | 42.5% |
| last hour | 0.05 | 2.20 | 0.30 | 48.5% |
| 0–5 s late | 0.05 | 1.05 | 0.20 | 48.8% |
| 30–60 s late | 0.20 | 2.90 | 0.30 | 40.4% |

Signed Δmid has a median of 0.00 in every bucket, so the disagreement is noise from timing,
not a bias of either source.

**Butterflies the live config could select** (calls and puts, widths 10–65, centers within
±100 of spot, 34.8M fly-minutes):

| Set | \|Δ\| median | \|Δ\| p95 | \|Δ\| > $0.05 | \|Δ\| > $0.10 |
|---|---:|---:|---:|---:|
| all | 0.100 | 1.050 | 63.5% | 49.9% |
| width 20 | 0.050 | 0.400 | 48.2% | 31.2% |
| width 30 | 0.100 | 0.675 | 59.7% | 44.7% |
| width 50 | 0.200 | 1.250 | 75.1% | 63.7% |
| 0–5 s late | 0.075 | 0.500 | 51.5% | 35.2% |
| 5–15 s late | 0.100 | 0.700 | 57.9% | 42.9% |
| 15–30 s late | 0.100 | 0.950 | 63.1% | 49.3% |
| 30–60 s late | 0.150 | 1.200 | 66.8% | 54.1% |

The p95 of fly |Δ| more than doubles from the freshest lateness bucket to the stalest. That
is the evidence for Parts A and B: matching on quote time and collecting on a fixed grid
should move most snapshots into the low-lateness rows.

**Coverage.** Of 3.9M vendor-quoted cells within ±100 of spot at matched minutes, 411
(0.01%) are missing or unquoted on Helios.

**Quality on matched rows** (Q2/Q3 rules): no crossed quotes on either side. Arbitrage
violations: Helios 51 of 22.7M checks, ThetaData 9 of 21.4M.

**Spot.** Helios SPX spot against ThetaData's put-call-parity spot: |Δ| median 0.77, p95
3.51 points, signed median 0.00. The spot is fetched at the stamp, before the chain, so this
also includes timing skew.

**VIX.** Median 375 observations a session. The largest gap was 737 s (2026-03-25).

## After Parts A and B

Rerun on a recorded session after deployment (`tools/run_schwab_fidelity_daily.sh <date>`)
and compare against this page. Success means the match share moves into the 0–5 s bucket,
the fly |Δ| p95 falls toward the 0–5 s row above, and `timing_basis` becomes
`quote_event_ts`.
