"""Render all-history results, emphasizing coverage and ledger mismatch limits."""

import csv
import html
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent
sys.path.insert(0, str(PARENT / "exit_trials"))
from build_report import money, table  # noqa: E402

LABELS = {"trail_60": "Trailer 60/60/75", "stop_50": "50% loss stop",
          "confirm_5": "5-second confirmation"}


def main():
    comparisons = json.loads((HERE / "results/comparisons.json").read_text())
    index = {(r["source"], r["cohort"], r["variant"], r["stress"]): r for r in comparisons}
    parity = json.loads((HERE / "results/parity_summary.json").read_text())
    rows = list(csv.DictReader((HERE / "results/trade_results.csv").open()))
    lookup = {(r["source"], int(r["id"]), r["variant"], r["stress"]): r for r in rows}
    recorded = list(csv.DictReader((HERE / "results/recorded_trades.csv").open()))
    breakdowns = json.loads((HERE / "results/breakdowns.json").read_text())
    baseline = index["best_available", "all_108", "trail_60", "mark"]
    assert baseline["attempted"] == 108 and baseline["paired_count"] == 98
    assert baseline["paired_candidate"]["net_pnl"] == -679
    assert lookup["best_available", 61, "trail_60", "mark"]["pnl"] == "139.0"
    styles = re.search(r"<style>(.*?)</style>",
                       (PARENT / "exit_trials/REPORT.html").read_text(), re.S).group(1)
    body = ["""
    <p class='eyebrow'>Butterfly Guy / All-history exit experiments</p>
    <h1>All 108 trades attempted. The larger history adds a tail-risk warning.</h1>
    <p class='muted'>September 13, 2026 · March 17–September 11 development history
    <br>108 entries · 75 legacy + 33 mark_v1 · same three primary tests and six sensitivities</p>
    <div class='decision'><strong>Decision: no exit change qualifies for promotion.</strong>
    The tighter late-morning trailer improves the combined exploratory comparison, but its
    same-ID top-five winner retention falls below the prior 80% guardrail. The 50% loss stop
    improves legacy results while worsening the validated mark cohort. Confirmation remains
    too incomplete to assess as a strategy.</div>
    <p>All entries were attempted on both quote sources. The combined <code>best_available</code>
    view selects monitoring for 64 trades and collector for 44 based only on whether raw
    monitoring exists. It is not a third independent dataset. There is no source fallback
    after a failed outcome, no stitching of quote paths, and no missing-outcome zero fill.</p>
    <p><strong>98 comparable trades is not a validated 108-trade result.</strong> Only 39 of
    those 98 baseline replays match recorded P/L, exit reason, and time within ten seconds;
    53 have P/L discrepancies over $5. Historical configuration and execution differences,
    quote gaps, and unresolved exits prevent a reliable full-history counterfactual.</p>
    """]

    def result_table(source, cohort, stress, caption, variants=LABELS):
        data = []
        for name in variants:
            r = index[source, cohort, name, stress]
            data.append([LABELS.get(name, name), f"{r['paired_count']}/{r['attempted']}",
                         money(r["paired_baseline"]["net_pnl"]),
                         money(r["paired_candidate"]["net_pnl"]), money(r["paired_delta_pnl"]),
                         r["paired_baseline_ledger_matches"]])
        return table(["Policy", "Paired / attempted", "Paired baseline", "Candidate",
                      "Difference", "Baseline ledger matches"], data, caption)

    body.append(result_table("best_available", "all_108", "mark",
                             "Combined exploratory view · mark fills, embedded commissions"))
    body.append("""<p class='muted'>Each row has its own paired ID set. In particular, the
    confirmation row's positive survivor P/L cannot be compared with the 98-trade rows.
    These are current-policy replays on historical entries. The actual recorded ledger
    totals +$1,835 across all 108 trades; subtracting a partial candidate total from that
    ledger would mix execution models and missing outcomes.</p>""")
    body.append(result_table("best_available", "all_108", "quarter_halfspread_005",
                             "Same combined comparison · 25% concession plus 0.05 points"))
    body.append("""<p>Moderate cost stress deducts 25% of positive mark-to-synthetic-bid
    concession plus 0.05 option points. All quote exits also retain the prior four-contract
    commission and paper rounding. Entry prices remain fixed. Synthetic concessions are
    assumptions, not measured executable complex-order fills. Full crossing and next-quote
    latency are separately reported; negative stressed fill prices are severe diagnostics.</p>
    <h2>What changes when legacy trades are included?</h2>
    <p><strong>60/60/75 trailer:</strong> paired mark P/L improves by $1,108, from −$1,787
    to −$679, while realized drawdown falls from $3,957 to $3,024. At moderate costs, P/L
    remains −$2,255 versus baseline −$3,424. This is relative improvement, not positive edge.</p>
    <p>The important new failure is <strong>May 6, trade 61: +$2,217 becomes +$139</strong>
    on its collector path. The combined replay retains only <strong>77.3%</strong> of the
    same baseline top-five winners' aggregate P/L, versus 110.1% in the recent validated
    cohort. The broad result fails the earlier 80% tail-retention guardrail. The May 6
    settlement is conditionally reused from the ledger; collector-path evidence remains
    lower confidence than monitoring. This is a warning that needs better evidence, not
    proof of a future loss.</p>
    <p>June 16, trade 130, is another unresolved risk: its recorded +$2,040 becomes a
    candidate quote exit of −$13, but the replayed baseline is unresolved. It is shown in
    the winner audit and excluded from paired performance. We do not call the difference
    a validated $2,053 loss caused by the new rule.</p>
    <p><strong>50% loss stop:</strong> combined paired mark P/L improves by $767 to −$1,020,
    unlike the recent mark_v1 result, which worsens by $314. The legacy paired improvement
    is $1,081, but only six of the 65 legacy baseline pairs meet ledger parity. Under
    moderate costs the combined stop loses $2,274. This evidence does not override the
    validated cohort or justify enabling the stop.</p>
    <p><strong>Five-second confirmation:</strong> only 18 of 108 pairs resolve, leaving 90
    missing. Ten resolved candidates are cash settlements. The resulting +$7,329 survivor
    total is not a full strategy result. Longer data coverage and sufficiently frequent
    observations are needed: collector gaps often reset the unchanged ten-second gap rule,
    and monitoring usually ends at the actual exit.</p>
    <h2>Keep quote sources separate</h2>
    <p>The tighter trailer improves monitoring replay by $1,941 but worsens collector replay
    by $881. The subsets differ as well as their sampling. They cannot be treated as two
    independent confirmations of one estimate. The collector's attractive loss-stop result
    is also undermined by its poor baseline reproduction.</p>""")
    for source in ("monitor", "collector"):
        body.append(result_table(source, "all_108", "mark", source + " only · mark fills"))
    body.append(table(["Source / cohort", "Attempted", "Baseline resolved", "Ledger matches",
                       "P/L errors > $5"],
                      [[r["source"] + " / " + r["cohort"], r["attempted"], r["resolved"],
                        r["ledger_matches"], r["material_pnl_errors"]] for r in parity],
                      "Baseline evidence audit · matches require P/L, reason and timing"))
    body.append("""<p>Small historical fee differences can fail exact parity without being
    material P/L errors. Conversely, matching P/L alone does not establish timing parity.
    The 33 monitoring mark_v1 trades still all reproduce their ledger outcomes. Earlier
    matched rows are not independently certified: settlement reuse remains conditional.</p>
    <h2>Separate the legacy and validated cohorts</h2>""")
    for cohort in ("legacy_75", "mark_v1_33"):
        body.append(result_table("best_available", cohort, "mark", cohort + " · mark fills"))
    body.append("""<h2>Do missing winners change the conclusion?</h2>
    <p>All ten largest recorded winners are retained below, including trades absent from
    paired aggregates. “Unresolved” means no supported result, not zero P/L. Values use the
    fixed combined source selection and mark fills. The complete audit includes each source
    and every sensitivity variant.</p>""")
    top = sorted(recorded, key=lambda r: float(r["pnl"]), reverse=True)[:10]
    winners = []
    for r in top:
        row = [r["date"] + " / " + r["id"], money(float(r["pnl"]))]
        for name in ("baseline", "trail_60", "stop_50", "confirm_5"):
            result = lookup["best_available", int(r["id"]), name, "mark"]
            row.append(money(float(result["pnl"])) if result["pnl"] else "Unresolved")
        winners.append(row)
    body.append(table(["Session / ID", "Recorded", "Replay baseline", "60/60/75",
                       "50% loss stop", "Confirm 5s"], winners, "Ten largest recorded winners"))
    missing = baseline["excluded_ids"]
    body.append("<p>IDs missing from the 98-pair trailer/stop comparison: <code>"
                + html.escape(", ".join(map(str, missing))) + "</code>. The tighter trailer itself "
                "resolves 100 outcomes and the loss stop resolves 104; candidate-only outcomes "
                "cannot be used to complete a paired result when baseline is unresolved.</p>")
    body.append("<h2>Monthly consistency</h2><p>The tighter trailer improves six monthly "
                "paired totals and worsens May by $1,336. The stop improves five months and "
                "worsens July and August. These remain small development slices with mixed "
                "evidence quality.</p>")
    for name in ("trail_60", "stop_50"):
        monthly = [r for r in breakdowns if r["source"] == "best_available"
                   and r["variant"] == name and r["stress"] == "mark" and r["dimension"] == "month"]
        body.append(table(["Month", "Paired / attempted", "Baseline", "Candidate", "Difference"],
                          [[r["value"], f"{r['paired_count']}/{r['attempted']}",
                            money(r["paired_baseline"]["net_pnl"]),
                            money(r["paired_candidate"]["net_pnl"]), money(r["paired_delta_pnl"])]
                           for r in monthly], LABELS[name] + " · combined mark comparison"))
    body.append("<details><summary>All predeclared sensitivities and cost scenarios</summary>"
                "<p>These remain sensitivity checks, not selected recommendations. Every row "
                "shows its own paired baseline. Next-quote results and confirmation have severe "
                "coverage limitations. No combinations or new parameters were introduced.</p>")
    names = ("trail_50", "trail_60", "trail_70", "stop_40", "stop_50", "stop_60",
             "confirm_2", "confirm_5", "confirm_10")
    for stress in ("mark", "quarter_halfspread_005", "halfspread_005", "crossed_010",
                   "next_quote_halfspread_005"):
        body.append(result_table("best_available", "all_108", stress,
                                 "Combined exploratory view · " + stress, names))
    body.append("</details><details><summary>Full metrics for the combined primary "
                "comparisons</summary>"
                "<p>Metrics are on paired resolved IDs only. Dollar P/L is not account return; "
                "mean/SD is not annualized Sharpe. Fee sensitivities are additional "
                "assumptions.</p>")
    fields = ("trades", "net_pnl", "expectancy", "win_rate", "profit_factor", "average_win",
              "average_loss", "closed_trade_drawdown", "exposure_hours", "mean_hold_minutes",
              "pnl_sample_sd", "trade_mean_over_sd", "largest_winner_share", "exit_drag_dollars",
              "net_excluding_top_1", "net_excluding_top_2", "net_excluding_top_5",
              "net_after_additional_520_fee", "net_extra_legacy_entry_fee")
    for name in LABELS:
        for stress in ("mark", "quarter_halfspread_005", "halfspread_005"):
            r = index["best_available", "all_108", name, stress]
            data = []
            for field in fields:
                values = [r[k][field] for k in ("paired_baseline", "paired_candidate")]
                data.append([field.replace("_", " ")] + [
                    "Unavailable" if v is None else f"{v:,.4f}" for v in values])
            body.append(table(["Metric", "Paired baseline", "Candidate"], data,
                              LABELS[name] + " · " + stress))
    body.append("""</details>
    <h2>Validation and next decision</h2>
    <p>29 focused tests passed. Every one of the 1,080 original baseline source/stress
    outcomes was reproduced, along with all 1,650 prior mark_v1 variant/stress outcomes.
    This validates the expanded harness against previous calculations; it does not repair
    historical disagreements with the ledger. Raw evidence, frozen source, prior research,
    and configuration hashes were checked. All 16,200 source/view/variant/stress/trade
    combinations are retained, including censored attempts. The combined view adds no new
    independent market observations.</p>
    <p>The collector and monitoring coverage audits preserve missing rows, rejected timestamp
    groups, entry lags, and gaps. No peaks are seeded from recorded metadata. Cash settlement
    is reused only under the earlier near-close rule and is not independently broker-attested.
    Legacy entry commissions are uncertain; the extra $2.60 sensitivity is a P/L adjustment
    only, not a reconstruction of different fee-driven signal thresholds.</p>
    <p><strong>Recommendation:</strong> reject promotion of these settings. Keep the tighter
    trailer only as a hypothesis for further work, with the May winner loss and failed tail
    guardrail explicitly recorded. The full history does not validate the stop or confirmation
    rule either. Future research needs better full-session, post-signal, and historical-state
    evidence, followed by an untouched evaluation window with rules fixed in advance.</p>
    <p>All available history is examined development data. No fresh out-of-sample test,
    statistical significance claim, account return, annualized Sharpe, or marked-equity
    drawdown is produced. Live paper settings, risk limits and services were unchanged.</p>
    <h2>Reproduce and inspect</h2>
    <pre>.venv/bin/python docs/research/spx-exits-2026-09-12/all_history_trials/run_all_history.py
.venv/bin/python docs/research/spx-exits-2026-09-12/all_history_trials/render_report.py
uv run pytest docs/research/spx-exits-2026-09-12/all_history_trials/test_all_history.py \\
  docs/research/spx-exits-2026-09-12/exit_trials/test_exit_trials.py \\
  docs/research/spx-exits-2026-09-12/test_replay.py -q</pre>
    <footer><a href='PLAN.md'>Fixed scope</a> · <a href='README.md'>Reproduction notes</a> ·
    <a href='results/trade_results.csv'>All attempted outcomes</a> ·
    <a href='results/comparisons.json'>All paired metrics</a> ·
    <a href='results/breakdowns.json'>Monthly and directional metrics</a> ·
    <a href='results/baseline_parity.csv'>Ledger parity</a> ·
    <a href='results/focus_winners.csv'>Recorded-winner audit</a> ·
    <a href='results/coverage.csv'>Quote coverage</a> ·
    <a href='results/source_choices.csv'>Fixed source choices</a> ·
    <a href='configs.json'>Research settings</a> · <a href='manifest.json'>Provenance</a> ·
    <a href='verification.txt'>Verification record</a> ·
    <a href='../exit_trials/REPORT.html'>Earlier 33-trade study</a></footer>
    """)
    page = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>SPX exits · All 108 trades</title><style>" + styles
            + "</style></head><body><main>" + "\n".join(body) + "</main></body></html>")
    (HERE / "REPORT.html").write_text(page)
    print("Rendered", HERE / "REPORT.html")


if __name__ == "__main__":
    main()
