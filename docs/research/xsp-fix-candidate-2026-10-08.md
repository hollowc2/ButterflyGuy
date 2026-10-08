# XSP protection and fresh-quote recovery candidate — October 8, 2026

Research decision: **refine**. This implements a reviewable paper-only candidate.
The owner subsequently requested commit, push and deployment. That authorizes
activation but does not change the research result or waive the flatness gate.

## Observed causes and boundaries

Trade 337's 768 put retained its 16:29:25.707 UTC event timestamp in both
option-chain and targeted-quote responses. Once older than five minutes, the
gateway marked it stale and the position monitor refused incomplete valuation.
Recovery was recorded after 221.3 seconds and 97 failed attempts. A fresh HTTP
response is not proof of a fresh option quote. Targeted requests did **not** cure
the actual October 8 interval.

The 1.74 accepted peak occurred after the outage. The active afternoon trailer
allows an 85% fall in butterfly value, placing its trigger at about 0.261, below
the 0.37 entry debit. The configured profit-protector settings were inactive
because the selected strategy was `peakvaluetrailer`.

A stale wing's historical ask is not a guaranteed upper bound on its current
value. No bounded-price substitution, zero-price fabrication, stale-quote
relaxation or order-routing change is included. Solving an outage where **both**
endpoints remain stale still requires trustworthy new pricing or a separately
specified emergency execution policy; this candidate does not solve that case.

## Candidate contract

`configs/research/config_xsp_protection.yaml` copies the existing XSP config and
changes only two values:

- Select existing `profitprotector` management. Retain every existing numerical
  threshold, hold time, peak confirmation and trailing quality gate. Its existing
  semantics cap drawdown at 50% once the accepted peak reaches twice the entry
  debit. Its breakeven floor arms after a 1.00-point gain and its 0.75-point profit
  floor after a 2.00-point gain. Those are option-price points, not percentages.
  Existing floor exits do not require the trailing exit's three-poll confirmation
  or trailing quality gate; they still require a complete usable valuation and
  the regime minimum hold. This is a policy candidate, not a mechanical bug fix.
- Enable `position_data.recover_held_quotes`. When an otherwise readable chain
  lacks a held leg, request **all three** exact held symbols, at most once per
  30 seconds with a three-second timeout. Accept only one complete response with
  no missing/duplicate symbols, stale flags, quality flags, unknown timestamps,
  crossed/invalid prices, or events/receipts older than 30 seconds. Construct all
  three marks at bid/ask midpoint; never mix partial targeted data with chain
  legs. Failed or unusable recovery retains the existing outage behavior.

Recovery is disabled by default and configuration validation restricts it to
XSP paper trading. Source, timestamp, raw quote values and rejection outcomes
are recorded. Diagnostic DB writes are bounded and occur after exit action,
or when valuation has already failed. Readiness clears only after valuation
actually succeeds. Cancellation propagates normally. No broker write API is
used by the recovery helper.

The research config is not mounted by Compose. The optional
`infra/docker-compose.xsp-protection.yml` overlay mounts a staged config only
for `app_xsp`, after the existing gateway-paper overlay. Set
`XSP_PROTECTION_CONFIG_PATH` to a copy of the host's current XSP config with
only those two candidate values changed. Nested environment overrides alone
cannot select the policy because YAML initialization takes precedence.
Omit the overlay to retain the baseline policy. Entry policy, sizing, limits,
paper/live guards, settlement and
execution accounting are unchanged. Recreate only `app_xsp`, and only after the
live runbook's flatness and reconciliation gates pass.

## Frozen development evidence and mechanics replay

Baseline Git revision: `4ed0987246a2491d42afffea6159919f2a1cae3e` (clean before
this work). Inputs and SHA-256 hashes are preserved in
`reports/research/xsp-fix-2026-10-08/manifest.json`, with raw source evidence,
baseline/candidate configs, normalized monitor CSV and trade JSONL. Acquisition
used explicit read-only database transactions, no broker APIs or secret exports.
The tables were exported in separate transactions, not one common snapshot.

Evidence retrieved at 18:39:32 UTC covers 14:00:09–18:39:31 UTC: 21,828 held-leg
rows, grouped into 7,276 complete recorded observations. Failed polls are absent
from monitor quotes; the largest gap is 223.519 seconds, consistent with the
separately recorded outage. Nothing is interpolated into it.

The baseline reproduces all accepted peaks exactly and produces no exit, matching
the recorded OPEN position. The candidate's first hypothetical signal occurs
at **18:15:55.634766 UTC / 11:15:55 a.m. Pacific**, `drawdown_afternoon`, with
recorded mark 0.85 and component bid 0.81. The existing replay's stressed closing
estimate is 0.78 after fee/slippage/rounding, compared with the recorded 0.40
marketable entry estimate: **+$38 hypothetical net**, not a fill. No settlement
or complete-session baseline P&L is invented for the open trade.

The replay evaluates exit policy only; it does not simulate targeted recovery.
Recovery mechanics have separate unit and monitor-integration regressions,
including the observed stale-wing failure shape. All fields, source/input hashes,
coverage gaps and policy settings are preserved in `replay-final.json` (the first
run's `replay.json` is retained separately).

This inspected session is development data. This result does not establish
expected profitability, fillability or superiority over holding to settlement.
The October 6 study already rejected a simple 50% trailer on coverage/sensitivity
grounds; this record does not overturn that result. No new threshold search or
historical profitability claim is made. Further economic evaluation needs the
settlement and forward coverage prerequisites in that earlier work record.

Falsification criteria: reject recovery if any stale/partial response reaches
valuation; reject the replay if baseline accepted peaks or recorded exits differ;
do not promote the policy from one inspected partial session. Fresh forward
evidence with complete coverage is required before a promotion decision.

## Reproduce

Use a new output filename; the replay refuses to overwrite evidence:

```bash
uv run python -m butterfly_guy.scripts.replay_xsp_exits \
  --trades reports/research/xsp-fix-2026-10-08/trades.jsonl \
  --quotes reports/research/xsp-fix-2026-10-08/monitor-quotes.csv \
  --candidate-config configs/research/config_xsp_protection.yaml \
  --include-open --output /tmp/xsp-protection-replay-new.json
```

Raw session artifacts remain local and untracked under the repository's existing
research-output policy. The config, implementation, regression tests and this
record are versionable. Running a replay never connects to Schwab or a database.

## Verification

Full suite: **1,218 passed, one skipped**. The real-database smoke test requires
`CI_DATABASE_URL`, which is unavailable. Tests ran with `DATABASE__PORT=5432`
to keep local dotenv settings (15432) from changing the test's default-port
expectation. After the final exit-ordering regression and comment updates,
the focused recovery/monitor/replay targets pass **40 tests**. Ruff and
`git diff --check` pass. Final replay still has exact baseline parity.

Graphify's AST update completed. As in the earlier work record, its SQL extractor
is unavailable because `tree_sitter_sql` is not installed; Python changes are
included in the updated graph.
