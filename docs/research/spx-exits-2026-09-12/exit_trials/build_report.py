"""Render the executed exit trials as an extension of the existing HTML report."""

import csv
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def money(value):
    return f"−${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"


def table(headers, rows, caption):
    head = "".join(f"<th scope='col'>{html.escape(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{html.escape(str(v))}</td>" for v in row)
                   + "</tr>" for row in rows)
    return (f"<div class='scroll'><table><caption>{html.escape(caption)}</caption>"
            f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>")


def main():
    comparisons = json.loads((HERE / "results/comparisons.json").read_text())
    index = {(r["variant"], r["stress"]): r for r in comparisons}
    trades = list(csv.DictReader((HERE / "results/trade_results.csv").open()))
    coverage = list(csv.DictReader((HERE / "results/coverage.csv").open()))
    # Editorial conclusions below refer to this exact executed experiment.
    assert index["trail_60", "mark"]["paired_candidate"]["net_pnl"] == 122
    assert index["stop_50", "mark"]["paired_candidate"]["net_pnl"] == -847
    assert index["confirm_5", "mark"]["paired_count"] == 1
    styles = """
    :root{color-scheme:light;--ink:#20313a;--muted:#596b72;--line:#d4dfe0;--accent:#176a67}
    *{box-sizing:border-box}body{margin:0;background:#edf2f2;color:var(--ink);
    font:17px/1.7 system-ui,sans-serif}main{max-width:1080px;margin:35px auto;
    padding:50px 64px;background:white;border-top:7px solid var(--accent)}
    h1{font:44px/1.15 Georgia,serif;margin:12px 0 20px;max-width:760px}
    h2{font-size:25px;line-height:1.3;margin:36px 0 15px}p{margin:0 0 20px}
    .eyebrow{font-size:12px;letter-spacing:.15em;text-transform:uppercase;color:var(--accent)}
    .muted,small{color:var(--muted)}.decision{background:#eaf4f1;padding:19px 24px;
    border-left:4px solid var(--accent);margin:25px 0}.scroll{overflow-x:auto;margin:25px 0}
    table{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}
    th,td{padding:10px 12px;border-bottom:1px solid var(--line);text-align:right}
    th:first-child,td:first-child{text-align:left}th{background:#edf4f3}
    caption{text-align:left;font-weight:700;font-size:16px;margin-bottom:10px}
    a{color:var(--accent);overflow-wrap:anywhere}details{margin:22px 0}summary{cursor:pointer;
    font-weight:700}li{margin-bottom:10px}pre{padding:18px;background:#f1f5f5;overflow:auto;
    font-size:12px}code{font-size:.9em}footer{border-top:1px solid var(--line);padding-top:22px;
    margin-top:35px;font-size:13px}@media(max-width:700px){main{margin:0;padding:26px 20px}
    h1{font-size:34px}body{font-size:16px}th,td{padding:9px 8px}}
    @media print{main{margin:0;padding:0;border:0}body{font-size:10pt;background:white}
    .scroll{overflow:visible}h1{font-size:27pt}table{font-size:9pt}tr{break-inside:avoid}}
    """
    body = ["""
    <p class='eyebrow'>Butterfly Guy / Executed research</p>
    <h1>A tighter late-morning trailer helps. Costs still decide.</h1>
    <p class='muted'>September 13, 2026 · 33 SPX paper entries · July 22–September 11
    <br>Three isolated primary experiments, six predeclared sensitivities, five fill scenarios.</p>
    <div class='decision'><strong>Decision: refine the late-morning trailer;
    promote nothing.</strong>
    The 60%/60%/75% candidate improves the historical comparison while preserving the dominant
    winner. Its positive mark result does not survive moderate costs. The 50% absolute stop
    worsens the mark result. Confirmation remains unmeasurable on 32 of 33 entries.</div>
    <p>This study changes only hypothetical exit decisions. Entries, strikes, direction,
    quantity, and embedded entry commissions remain fixed. No live configuration or service
    changed. All history is examined development data; there is no untouched holdout here.</p>
    """]
    rows = []
    for name, label in (("baseline", "Baseline 60/90/75"),
                        ("trail_60", "Trailer 60/60/75"), ("stop_50", "50% absolute stop")):
        row = [label]
        for stress in ("mark", "quarter_halfspread_005", "halfspread_005", "crossed_010"):
            comparison = index["trail_60" if name == "baseline" else name, stress]
            field = "paired_baseline" if name == "baseline" else "paired_candidate"
            row.append(money(comparison[field]["net_pnl"]))
        rows.append(row)
    body.append(table(["Exit policy", "Marks", "25% + .05", "50% + .05", "100% + .10"],
                      rows, "Net P/L · complete 33-entry comparisons"))
    body.append("""<p class='muted'>Stress columns deduct the stated fraction of positive
    mark-to-synthetic-bid concession plus option points. These are execution assumptions,
    not measured complex-order fills. Commissions follow the frozen paper model. Entry
    execution remains fixed. Full legwise crossing can imply negative fills and is a severe
    diagnostic, not an asserted executable price.</p>
    <h2>1. Keep the late-morning trailer at 60%</h2>
    <p>Moving from 60/90/75 to <strong>60/60/75</strong> changes six outcomes: five improve
    and one worsens. Net P/L improves by <strong>$655</strong> at marks and <strong>$649</strong>
    under the 25% concession stress. The $2,288 August 3 settlement winner survives.
    Realized drawdown falls from $2,053 to $1,770 at marks, and from $2,232 to $1,953
    under the 25% stress. Holding exposure falls from 60.18 to 50.84 hours.</p>
    <p>The candidate earns only $3.70 per entry at marks and loses $20.12 per entry under
    moderate stress. Adding the separate $5.20/entry fee sensitivity turns its +$122 into
    −$49.60 even at marks. Removing its largest winner leaves −$2,166. That is continued
    tail dependence, not a demonstrated robust edge. The same baseline top-five winner IDs
    retain 110.1% of their aggregate P/L at marks; improvements to other winners can make
    this ratio exceed 100%.</p>
    <p>Month-level mark deltas are +$227 in July, +$182 in August, and +$246 in September;
    the two partial months contain only eight and five trades. Both call and put groups
    improve. These small slices are descriptive, not independent replications.</p>""")
    b = {r["id"]: r for r in trades if r["variant"] == "baseline" and r["stress"] == "mark"}
    changed = [r for r in trades if r["variant"] == "trail_60" and r["stress"] == "mark"
               and r["pnl"] != b[r["id"]]["pnl"]]
    body.append(table(["Session / trade", "Baseline", "60/60/75", "Difference"],
                      [[r["date"] + " / " + r["id"], money(float(b[r["id"]]["pnl"])),
                        money(float(r["pnl"])),
                        money(float(r["pnl"]) - float(b[r["id"]]["pnl"]))]
                       for r in changed], "Every changed mark outcome · same entry IDs"))
    ci = index["trail_60", "quarter_halfspread_005"]["bootstrap_mean_delta"]
    body.append(f"""<p>A paired-day bootstrap gives a descriptive 95% percentile interval
    of ${ci['lower_025']:.2f} to ${ci['upper_975']:.2f} for mean improvement per entry under
    moderate stress. It uses 10,000 resamples of 33 observed days. This is conditional on
    the recorded sample, excludes unseen tails, and is not corrected for the wider research
    search. It does not establish positive candidate expectancy or statistical confirmation.</p>
    <h2>2. Enable the existing 50% absolute loss stop</h2>
    <p>The stop changes 14 mark outcomes: 11 improve, three worsen, and the total
    deteriorates by $314. July 31's +$248 becomes −$179; August 19's +$9 becomes −$123.
    The largest August 3 winner survives, but preserving that one winner is insufficient.</p>
    <p>Costs alter the relative result: the stop is $109 better than baseline under the
    25% stress and $535 better under the 50% stress, because its modeled exit concessions
    are lower. All totals remain negative. Thus the stop is not uniformly worse under every
    assumption, but it fails the proposed gate and does not warrant promotion.</p>
    <h2>3. Confirm trailing breaches for five seconds</h2>
    <p><strong>Unresolved: 32 of 33 entries.</strong> The recording ends at the baseline
    exit signal, exactly where confirmation requires later observations. Only the already
    settled August 3 trade resolves, at +$2,288. That single survivor must not be presented
    as the confirmed strategy's cohort profit or win rate.</p>
    <p>The rule requires the same drawdown reason on repeated observations for at least
    five seconds; recovery, a regime change, or a gap over ten seconds resets it. This does
    not establish uninterrupted prices between observations. Hard exits bypass the delay.
    Two- and ten-second sensitivities have the same 32 missing outcomes. All next-observation
    latency comparisons have only one paired resolved entry as well. Full-session and
    post-signal recording is necessary to evaluate these policies.</p>
    <h2>Predeclared neighboring settings</h2>
    <p>These are sensitivity checks, not newly selected recommendations. No combinations
    were tested. The 50% late-morning setting looks best at marks, but its moderate-stress
    profit is only $37 before the additional fee sensitivity. Its result becomes negative
    under the stronger spread stress. Do not pick it merely because it tops this table.</p>""")
    rows = []
    for name in ("trail_50", "trail_60", "trail_70", "stop_40", "stop_50", "stop_60"):
        row = [name]
        for stress in ("mark", "quarter_halfspread_005", "halfspread_005"):
            row.append(money(index[name, stress]["paired_candidate"]["net_pnl"]))
        rows.append(row)
    body.append(table(["Variant", "Marks", "25% + .05", "50% + .05"], rows,
                      "One-dimensional sensitivities · all 33 entries"))
    body.append("<details><summary>Full metrics for the two complete primary candidates</summary>")
    for name in ("trail_60", "stop_50"):
        for stress in ("mark", "quarter_halfspread_005", "halfspread_005", "crossed_010"):
            comp = index[name, stress]
            rows = []
            for field in ("net_pnl", "expectancy", "trades", "win_rate", "profit_factor",
                          "average_win", "average_loss", "closed_trade_drawdown",
                          "exposure_hours", "mean_hold_minutes", "pnl_sample_sd",
                          "trade_mean_over_sd", "largest_winner_share", "exit_drag_dollars",
                          "net_after_additional_520_fee"):
                vals = [comp[k][field] for k in ("paired_baseline", "paired_candidate")]
                rows.append([field.replace("_", " ")] + [
                    "Unavailable" if v is None else f"{v:,.4f}" for v in vals])
            body.append(table(["Metric", "Paired baseline", "Candidate"], rows,
                              name + " · " + stress))
    body.append("</details>")
    total_rows = sum(int(r["raw_rows"]) for r in coverage)
    max_gap = max(float(r["max_gap_seconds"]) for r in coverage)
    body.append(f"""<h2>What this evidence can support</h2>
    <p>All 33 mark baseline P/L values and reasons reproduce the ledger. All 165 baseline
    scenario statuses, and their resolved P/L, reasons and exit timestamps, match the prior
    frozen replay. Input hashes and all 99 frozen Python source hashes were verified.
    Reused monitoring contains {total_rows:,} held-leg rows; the largest valid-observation
    gap is {max_gap:.1f} seconds. Coverage is recorded per entry in the downloadable CSV.
    Simulations process chronological same-timestamp held legs; no collector substitution,
    peak seeding, quote interpolation, or fabricated last-quote liquidation is used.</p>
    <p>Recorded cash settlement is reused conditionally under the prior near-close coverage
    rule, not independently attested to broker settlement. A trigger is not a guaranteed fill.
    Missing trades are never assigned zero returns. Account capital and a verified no-trade
    calendar are unavailable: <strong>no account return or annualized Sharpe is claimed</strong>.
    Trade mean/standard deviation is a separate unannualized dollar diagnostic. Drawdown is
    closed-trade dollar drawdown, not intratrade marked equity drawdown.</p>
    <p><strong>Next decision:</strong> retain 60/60/75 for prospective research; reject promotion
    of the tested 50% stop; defer confirmation pending complete quote paths. Freeze the chosen
    rule before a future untouched evaluation window. The current one-lot limit and live
    settings remain unchanged.</p>
    <h2>Reproduce and inspect</h2>
    <pre>.venv/bin/python docs/research/spx-exits-2026-09-12/exit_trials/run_trials.py
.venv/bin/python docs/research/spx-exits-2026-09-12/exit_trials/build_report.py
uv run pytest docs/research/spx-exits-2026-09-12/exit_trials/test_exit_trials.py \\
  docs/research/spx-exits-2026-09-12/test_replay.py -q
uv run ruff check docs/research/spx-exits-2026-09-12/exit_trials</pre>
    <p>20 focused tests passed, including the historical parity regression. Targeted Ruff
    and whitespace checks passed. The graph update completed; its existing missing SQL
    parser warning limits SQL extraction and is unrelated to this Python-only change.
    No new raw data, live services, broker writes, runtime code, or configurations were changed.</p>
    <footer><a href='PLAN.md'>Fixed experiment plan</a> ·
    <a href='results/trade_results.csv'>Every attempted outcome</a> ·
    <a href='results/comparisons.json'>Paired comparisons and bootstrap</a> ·
    <a href='results/breakdowns.json'>Monthly and direction metrics</a> ·
    <a href='results/coverage.csv'>Quote coverage</a> ·
    <a href='configs.json'>All research settings</a> ·
    <a href='manifest.json'>Provenance</a> · <a href='../REPORT.html'>Original report</a>
    </footer>""")
    page = ("<!doctype html><html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width, initial-scale=1'>"
            "<title>SPX exit trials · September 13, 2026</title><style>" + styles
            + "</style></head><body><main>" + "\n".join(body) + "</main></body></html>")
    (HERE / "REPORT.html").write_text(page)
    print("Rendered", HERE / "REPORT.html")


if __name__ == "__main__":
    main()
