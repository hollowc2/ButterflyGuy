"""Self-contained HTML report with embedded journals, tables and payoff SVGs."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from tools.research_studies.xsp_independent.batman import payoff, read_rows
from tools.research_studies.xsp_independent.mean_reversion import write_new


def esc(value) -> str:
    return html.escape(str(value))


def money(value) -> str:
    return "—" if value is None else f"{'−' if value < 0 else ''}${abs(value):,.2f}"


def number(value, digits=2) -> str:
    return "—" if value is None else f"{value:,.{digits}f}"


def table(headers: list[str], records: list[list]) -> str:
    return ('<div class="scroll"><table><thead><tr>'
            + ''.join(f'<th scope="col">{esc(h)}</th>' for h in headers)
            + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{v}</td>' for v in r)
                                             + '</tr>' for r in records) + '</tbody></table></div>')


def payoff_svg(row: dict) -> str:
    centers = row["centers"]
    lo, hi = centers[0]-6, centers[1]+6
    cost = 100*row["entry_debit"]+15.20
    ymax = max(100*payoff(centers, c)-cost for c in centers)
    ymin = -cost
    ylo, yhi = min(-50, ymin)-20, max(50, ymax)+20
    x = lambda v: 65 + (v-lo)/(hi-lo)*660  # noqa: E731
    y = lambda v: 225-(v-ylo)/(yhi-ylo)*185  # noqa: E731
    points = ' '.join(f'{x(v):.2f},{y(100*payoff(centers,v)-cost):.2f}'
                      for v in sorted({lo, hi, *[v for c in centers for v in (c-4,c,c+4)]}))
    ticks = ''.join(f'<text x="{x(v):.1f}" y="246" text-anchor="middle">{v:g}</text>'
                    for v in (lo, centers[0], row["entry_proxy"], centers[1], hi))
    return f'''<svg viewBox="0 0 760 280" role="img" aria-label="Combined Batman expiry net payoff in dollars versus XSP settlement">
    <line x1="65" x2="725" y1="{y(0):.1f}" y2="{y(0):.1f}" class="axis"/>
    <line x1="65" x2="65" y1="40" y2="225" class="axis"/>
    <line x1="65" x2="725" y1="225" y2="225" class="axis"/>
    <polyline points="{points}" fill="none" stroke="var(--accent)" stroke-width="3"/>
    <text x="60" y="{y(ymax):.1f}" text-anchor="end">{ymax:.0f}</text>
    <text x="60" y="{y(ymin):.1f}" text-anchor="end">{ymin:.0f}</text>
    <text x="60" y="{y(0):.1f}" text-anchor="end">0</text>{ticks}
    <text x="395" y="274" text-anchor="middle">Native XSP settlement (index points)</text>
    <text transform="translate(17,140) rotate(-90)" text-anchor="middle">Net P&amp;L ($)</text>
    </svg>'''


def render(run: Path, output: Path) -> None:
    summary = json.loads((run / "summary.json").read_text())
    spec = json.loads((run / "specification.json").read_text())
    coverage = json.loads((run / "coverage.json").read_text())
    review = json.loads((run / "cash-review/review.json").read_text())
    manifest = json.loads((run / "completed-manifest.json").read_text())
    journal = read_rows(run / "journal.jsonl")
    cells = summary["cells"]
    matrix = []
    for key, m in cells.items():
        matrix.append([esc(key), m["trades"], money(m.get("stressed")), money(m.get("expectancy")),
                       number(100*m["win_rate"], 1)+'%' if m.get("trades") else '—',
                       number(m.get("profit_factor")), money(m.get("terminal_drawdown")),
                       money(m.get("mean_initial_risk")), number(m.get("mean_risk_units"), 4),
                       money(m.get("top3_removed")), money(m["halves"]["first"].get("stressed")),
                       money(m["halves"]["second"].get("stressed")), esc(m.get("decision", "prior reject"))])
    charts = []
    for geometry in ("body", "all_strikes"):
        example = next((r for r in journal if r["cell"] == geometry+'_unconditional_settlement'
                        and r["status"] == "completed"), None)
        if example:
            zones = '; '.join(f'({a:.3f}, {b:.3f})' for a,b in example["profit_zones"]) or 'none'
            charts.append(f'''<article><h3>{esc(geometry)} — first admitted example, {example['date']}</h3>
            {payoff_svg(example)}<p class="caption">Actual quote-priced geometry; settlement policy, opening fees and stress included.
            PUT body {example['centers'][0]:g}; CALL body {example['centers'][1]:g}; wings ±4;
            entry SPX/10 {example['entry_proxy']:.3f}. Both debits {money(100*example['entry_debit'])};
            initial maximum expiry loss {money(100*example['entry_debit']+15.20)}.
            Positive net zones: {esc(zones)}; boundaries break even. Excludes unverified extra broker charges.</p></article>''')
    signal_records = []
    for geometry in ("body", "all_strikes"):
        for signal in (False, True):
            selected = [r for r in journal if r["cell"] == geometry+'_unconditional_settlement'
                        and r["status"] == "completed" and r["movement_signal"] == signal]
            complete = [r for r in selected if r["reach_prefix_complete"]]
            hits = sum(r["zone_reach"] for r in complete)
            native_hits = sum(r["stressed"] > 0 for r in selected)
            signal_records.append([geometry, 'movement' if signal else 'other covered mornings', len(selected),
                                   len(complete), len(selected)-len(complete), hits,
                                   number(100*hits/len(complete),1)+'%' if complete else '—',
                                   sum(r["drift_side_zone_reach"] for r in complete), native_hits,
                                   money(sum(r["stressed"] for r in selected))])
    costs = []
    for key, m in cells.items():
        if m["trades"]:
            costs.append([esc(key), money(m["gross"]), money(m["fees"]), money(m["stress_cost"]),
                          money(m["midpoint"]-m["net"]), money(m["midpoint"]), money(m["stressed"]),
                          money(m.get("max_initial_risk"))])
    pair_rows = []
    for key, comparisons in summary["comparisons"].items():
        for benchmark, result in comparisons.items():
            dates = set(result["dates"])
            candidate_rows = [r for r in journal if r["cell"] == key
                              and r["date"] in dates and r["status"] == "completed"]
            reference_key = ("prior_atm_all_IRON_w4" if benchmark == "vs_single_iron"
                             else key.replace("_movement_", "_unconditional_"))
            reference_rows = [r for r in journal if r["cell"] == reference_key
                              and r["date"] in dates and r["status"] == "completed"]
            mean = lambda rs, field: sum(r[field] for r in rs)/len(rs) if rs else None  # noqa: E731
            pair_rows.append([esc(key), esc(benchmark), result["days"], money(result["candidate"]),
                              money(result["benchmark"]), money(result["difference"]),
                              money(mean(candidate_rows,"initial_risk")),
                              money(mean(reference_rows,"initial_risk")),
                              number(mean(candidate_rows,"risk_units"),4),
                              number(mean(reference_rows,"risk_units"),4)])
    native_possible = {k: f'{m.get("expiry_possible",0)}/{m["trades"]}' for k,m in cells.items()
                       if not k.startswith('prior_') and k.endswith('_settlement')}
    monthly_rows = []
    for key,m in cells.items():
        for month, result in m["monthly"].items():
            if result["trades"]:
                monthly_rows.append([esc(key), month, result["trades"], money(result["stressed"]),
                                     money(result["expectancy"]), number(result["mean_risk_units"],4)])
    records = read_rows(run / "cash-review/raw-quotes.jsonl")
    example_keys = []
    for geometry in ("body", "all_strikes"):
        group = [r for r in records if r["cell"].startswith(geometry)]
        if group:
            example_keys.append(group[0])
        closed = [r for r in group if r["terminal"] == "liquidation"]
        if closed:
            example_keys.append(closed[0])
    cash_examples = []
    for r in example_keys:
        raw_table = table(['Time ET','Action','Option','Qty','Bid / ask','Required / displayed','Signed cash $'],
                          [[esc(q['timestamp'][11:19]), esc(q['transaction']+' '+q['side']),
                            f"{q['right']} {q['strike']:g}",q['needed_size'],
                            f"{q['bid']:.2f} / {q['ask']:.2f}",f"{q['needed_size']} / {q['displayed_size']:g}",
                            money(q['signed_cash_dollars'])] for q in r['raw_quotes']])
        cash_examples.append(f'''<details><summary>{esc(r['cell'])} · {r['date']} · {r['terminal']} · {money(r['stressed'])}</summary>
        {raw_table}<p>Opening cash {money(r['opening_cash'])} + terminal cash {money(r['terminal_cash'])}
        − fees {money(r['fees'])} − stress {money(r['stress'])} = {money(r['stressed'])}.
        Native settlement: {esc(r['native_settlement'])}; final option inventory: 0.</p></details>''')
    decision = {"quiet": summary['quiet_decision'], "batman": summary['batman_decision'],
                "new_cells": 8, "reused_benchmarks": 2, "total_cells": 10,
                "no_runtime_changes": True, "promotion": "none",
                "native_profit_possible": native_possible,
                "completed_cash_records_reconciled": review['completed_records']}
    if not (run / "decision.json").exists():
        write_new(run / "decision.json", decision)
    data = {"summary": summary, "specification": spec, "coverage": coverage,
            "manifest": manifest, "review": review, "journal": journal, "decision": decision}
    encoded = json.dumps(data, allow_nan=False).replace('<', '\\u003c')
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1"><title>XSP quiet iron &amp; Batman research</title>
    <style>:root{{--ink:#172c36;--muted:#526572;--paper:#f7f6f1;--line:#cbd2d3;--accent:#007c78}}
    *{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}}
    main{{max-width:1280px;margin:auto;padding:36px 28px 70px}}h1{{font:600 clamp(30px,5vw,50px)/1.12 Georgia,serif;max-width:900px}}
    h2{{font:600 29px/1.2 Georgia,serif;margin-top:55px}}h3{{font-size:19px}}p{{max-width:1000px}}
    .eyebrow,.caption{{font-size:13px;color:var(--muted)}}.lead{{font-size:20px;max-width:970px}}
    .decisions{{display:grid;grid-template-columns:1fr 1fr;gap:28px;border-top:3px solid var(--accent);padding-top:18px}}
    .decisions strong{{display:block;font-size:21px}}a{{color:var(--accent)}}nav{{display:flex;gap:18px;flex-wrap:wrap;margin:24px 0}}
    section{{border-top:1px solid var(--line);margin-top:32px}}.scroll{{overflow:auto;max-width:100%;margin:18px 0}}
    table{{border-collapse:collapse;font-size:13px;width:100%;white-space:nowrap}}td,th{{padding:9px 12px;text-align:right;border-bottom:1px solid var(--line)}}
    td:first-child,th:first-child{{text-align:left}}th{{font-weight:600;background:#e9edeb}}code,pre{{font:13px/1.6 ui-monospace,monospace}}
    pre{{padding:18px;overflow:auto;background:#e9edeb}}details{{margin:14px 0;border-bottom:1px solid var(--line);padding:10px 0}}summary{{cursor:pointer}}
    .plots{{display:grid;grid-template-columns:1fr 1fr;gap:30px}}svg{{width:100%;height:auto}}svg text{{font:12px system-ui;fill:var(--muted)}}
    .axis{{stroke:var(--line);stroke-width:1}}button,select{{padding:9px;border:1px solid var(--line);background:var(--paper);color:var(--ink);font:inherit;margin:5px}}
    select{{max-width:100%}}.plots article{{min-width:0}}#equity{{min-height:200px}}.metric{{font-variant-numeric:tabular-nums}}@media(max-width:760px){{main{{padding:20px 16px 50px}}.decisions,.plots{{grid-template-columns:1fr}}}}
    @media print{{button,select,nav{{display:none}}details{{break-inside:avoid}}.scroll{{overflow:visible}}table{{font-size:9px;white-space:normal}}}}</style></head>
    <body><main><p class="eyebrow">BOUNDED RESEARCH · XSP 0-DTE · FROZEN 12 NOVEMBER 2026 (PACIFIC) · RETROSPECTIVE DEVELOPMENT</p>
    <h1>Can two finite payoff zones pay for both butterflies?</h1>
    <p class="lead">Eight mixed PUT-below / CALL-above Batman cells test actual XSP component quotes.
    Two unchanged iron benchmarks preserve the quiet-day observation. This is one frozen matrix, with no outcome-led expansion.</p>
    <div class="decisions"><div><strong>Quiet ATM iron: insufficient evidence</strong><p>No new joint quote/signal cohort or demonstrated complex fills.
    Preserve +$405 on 30 dates, with −$171.20 after the top three wins and −$44.40 in the first fixed half. The completed policy retains its prior rejection.</p></div>
    <div><strong>Batman: {esc(summary['batman_decision'])}</strong><p>Decision applies to these provisional geometries, signal and exits under modeled component execution.
    No strategy is promoted or activated. Settlement and intraday monetization are separate tests.</p></div></div>
    <nav><a href="#coverage">Coverage</a><a href="#rules">Frozen rules</a><a href="#payoff">Payoffs</a><a href="#results">Results</a>
    <a href="#signals">Signal evidence</a><a href="#costs">Costs</a><a href="#verification">Verification</a><a href="#reproduce">Reproduce</a></nav>
    <section id="coverage"><h2>Coverage and prior inspection</h2>
    <p>Local genuine XSP minute quote partitions: {coverage['inventories']['quote_1m']['count']:,},
    {coverage['inventories']['quote_1m']['first']}–{coverage['inventories']['quote_1m']['last']}.
    Only the 185 dates in 2026 have the audited joint evidence used here: native published settlements cover all 185;
    independent recorded SPX/10 prefixes cover 122; 63 dates are excluded. SPX signal coverage is March 13–September 25.
    The canonical support contains SPX and VIX, with no native intraday XSP. No newer quote dates are available locally.</p>
    <p>January–September has been inspected in earlier research. The quiet 30 dates and the prior CALL/CALL, PUT/PUT and IRON/IRON
    neutral-pair results informed this task. Those constructions were never exact Batman tests. Older quote files have not been
    admitted as a fresh holdout: their joint settlement/signal and liquidity quality is not established by file counts.
    No new download, broker query, runtime change, deployment or order was performed.</p>
    <p>Exchange-calendar inputs are hashed and use only previously published schedules. This cohort contains no scheduled half-day;
    raw rows at or after the session close are removed. Minute observation timestamps do not establish individual leg update age.
    The absence of a named event is not an absence of catalysts.</p></section>
    <section id="rules"><h2>The frozen experiment</h2>
    <p>All Batman cells enter at the first usable simultaneous snapshot strictly after 10:30 and no later than 10:32 ET.
    The completed [09:31,10:30) SPX/10 prefix must have at least 54 of 59 minutes, gaps no larger than 120 seconds, and the 10:29 observation.
    An ATM XSP straddle midpoint at 10:29 supplies the offset scale. Signals are proxies; execution uses genuine XSP contracts.</p>
    <p><b>Movement gate:</b> absolute first-hour drift is at least half the straddle, and drift divided by total absolute increments
    is at least 0.30. This provisional persistence hypothesis uses only information available at 10:30. It does not inherit the quiet filter.
    Unconditional entry uses identical data requirements and geometry, with no movement gate. There are {len(summary['movement_dates'])} signal dates before entry-quality admission.</p>
    <p><b>Two geometries:</b> four-point wings throughout. Body-only targets are proxy ± half the straddle;
    all-strikes targets are proxy ± (4 + half the straddle). Choose the nearest listed body on the required side (lower tie),
    with listed wings. No alternative geometry search. At entry the last completed SPX minute must still satisfy the chosen OTM definition.
    OTM status is relative to SPX/10; native XSP status remains unobserved. Body-only wings may cross the reference price and overlap.</p>
    <p><b>One combined position:</b> lower PUT +1/−2/+1 and upper CALL +1/−2/+1; six distinct contracts and eight gross units,
    same expiry. Each fly must have a positive component debit below four points. Both open together and both remain tracked until
    flat or settled. This study has no winning-fly-only exit, strike netting, re-entry, stop or partial-fill simulation.</p>
    <p><b>Settlement:</b> hold both flies to native Cboe-published XSP settlement. Missing terminal data remains unresolved.
    <b>Zone exit:</b> freeze the combined positive expiry-net intervals at entry. The first later completed SPX/10 minute inside either
    interval triggers a combined close at a strictly later usable quote within two minutes, capped at close minus 15 minutes.
    A body touch or an inferred crossing is not a fill. The realized quote can lose money even after the zone signal.</p>
    <p>On the first SPX prefix failure beyond 120 seconds or the first failed exit window, irrevocably hold both to settlement.
    No recovery search. A missing start-labeled minute becomes knowable only after completion; gap failure is last observation availability +3 minutes.
    With no trigger, try the exact scheduled cutoff quote, then settle if it is unavailable. Never require future exits to admit entries,
    interpolate a missing quote, discard an open loser, or assign zero to a missing outcome.</p>
    <details><summary>Complete frozen specification and timing contract</summary><pre>{esc(json.dumps(spec,indent=2))}</pre></details></section>
    <section id="payoff"><h2>Payoff geometry: movement has a finite destination</h2>
    <p>Per fly: <code>T(S,c)=max(4−|S−c|,0)</code> points. Combined settlement net:
    <code>100×[T(S,c_put)+T(S,c_call)−D_put−D_call]−5.20−10.00</code>.
    Maximum expiry loss is both debits plus $15.20 opening costs. Peak combined payoff depends on overlap;
    for separated bodies at least four points apart it is at most four points, despite paying for two flies.
    If all-in entry cost reaches that peak, there is no positive expiry zone. No such admission filter was added after inspection.</p>
    <p>For disjoint tents and all-in cost C in points below four, the two positive intervals are
    <code>(c_put−4+C,c_put+4−C)</code> and <code>(c_call−4+C,c_call+4−C)</code>.
    Overlapping tents require the exact sum; they may create a connected plateau. Staying in a central gap, overshooting the outside wings,
    or reversing before the later exit fill can lose both debits. A payable component close plus closing costs can exceed the stated expiry maximum loss.</p>
    <div class="plots">{''.join(charts)}</div>
    <p>Trades with a mathematically possible positive expiry net at their observed entry cost:
    {esc(json.dumps(native_possible))}. These counts establish payoff feasibility, not a profitable forecast or an executable exit.</p></section>
    <section id="results"><h2>All trials, without winner selection</h2>
    <p><b>The only positive Batman cell is fragile:</b> all-strikes-OTM movement entry held to settlement earns $414 on 10 trades,
    with $41.40 expectancy, 60% wins, 1.85 profit factor and $285.40 terminal drawdown. Its mean initial risk is $120.60
    and mean trade return is +0.4614 R. Both fixed halves are positive (+$344.60 / +$69.40), but removing the three largest
    winners leaves −$202.40. The positive total fails the frozen robustness gate; it is not a paper-trade candidate.</p>
    <p>Unconditional all-strikes settlement loses $2,313.20 on 121 trades, and its zone-exit version loses $4,820.
    The movement zone-exit cell loses $169.80 on the same 10 entries: four combined liquidations and six settlement fallbacks.
    For body-only geometry, settlement loses $5,042.80 on 119 entries; zone exits lose $11,383.20.
    Movement-filtered body-only results are −$776.60 (settlement) and −$656.20 (zone exit), eight entries each.</p>
    <p>Primary P&amp;L crosses component bids/asks, pays gross-contract fees, and applies additional adverse stress.
    Each Batman episode contains two flies; iron benchmarks contain one. Entries across cells reuse dates, so the rows are correlated alternatives,
    not independent trades or a combined portfolio. R is each trade's stressed initial maximum expiry risk. No funded-account return is defined.</p>
    {table(['Cell','Trades','Net stressed','Expectancy','Win rate','PF','Terminal DD','Mean initial risk','Mean R','Top3 removed','Before May15','May15 onward','Decision'],matrix)}
    <p class="caption">Drawdown values use cumulative terminal episode P&amp;L once per traded session, starting at zero. They are not intraday or mark-to-market drawdowns.
    Fixed chronological split: May 15, inherited from the archive, not a median-trade split. Top-three removal subtracts the three largest positive wins.</p>
    <label for="cell">Inspect a complete cell:</label><select id="cell"></select><div id="detail"></div><div id="equity"></div>
    <details><summary>Monthly net performance and risk units — every cell</summary>
    {table(['Cell','Month','Trades','Stressed net','Expectancy','Mean R'],monthly_rows)}</details>
    <details><summary>Matched-date comparisons, including valid no-signal participation</summary>
    <p>Traded comparisons require both episodes completed. Participation comparisons allow zero only for a valid ex-ante no-signal;
    exclusions and unresolved outcomes never become zero. On admitted movement dates the unconditional construction is identical;
    gate improvement comes from participation. Single-iron comparisons have unequal gross exposure and unequal initial risk.</p>
    {table(['Batman cell','Comparison','Matched days','Candidate','Benchmark','Difference','Candidate mean risk','Benchmark mean risk','Candidate mean R','Benchmark mean R'],pair_rows)}
    <p class="caption">Risk and R means use actual completed positions on those matched dates; valid no-signal days have no position or initial risk.
    Daily participation P&amp;L includes those known no-signals at zero. These R means are conditional trade means, not daily portfolio returns.</p></details></section>
    <section id="signals"><h2>Does the entry signal reach a payoff zone?</h2>
    <p>These diagnostics use unconditional entries, split by the already-known movement signal. A reach means an actual sampled SPX/10
    observation lies in the entry-specific combined expiry-profit interval by the cutoff. No interpolation or assumption that a crossing
    touched an executable price. Complete paths require gaps ≤120 seconds; incomplete paths remain unknown even when some hits were observed.</p>
    {table(['Geometry','Ex-ante group','Accepted','Complete paths','Unknown paths','Zone hits','Reach rate','Drift-side hits','Native expiry wins','Settlement net'],signal_records)}
    <p>For all-strikes geometry the movement gate reaches a profitable interval on 7/10 complete paths (70%),
    versus 72/105 other complete paths (68.6%). Four of those ten signal dates reach a zone on the original drift side.
    This tiny retrospective difference does not establish useful forecast skill. The signal's settlement gains are concentrated in three winners.</p>
    <p>The body-only tents often overlap around entry, so 112/113 complete unconditional paths reach the entry-specific expiry-profit region.
    This is usually immediate location inside an overlapping intrinsic-payoff region, not evidence of a later moderate move.
    All eight movement-filtered body zone exits lose after costs. One unconditional body-only entry has no positive expiry zone at all;
    it remains in the cohort with its actual loss rather than being removed after inspection.</p>
    <p>Reach is a necessary hypothesis check, not proof of realizable option value. The intervals describe expiry intrinsic cash;
    the intraday option market has time value and component spreads. Compare the zone-exit realized results and fallback counts above.
    Groups are observational, potentially confounded by volatility, timing and liquidity; this archive cannot establish a causal market effect.
    Initial signal timing itself is causal and independently tested.</p></section>
    <section id="costs"><h2>Costs and execution uncertainty</h2>
    <p>At each transaction, long legs buy at ask or sell at bid; short legs sell at bid or buy at ask. Displayed sizes must cover actual needed
    quantities (two at debit bodies). A purchased wing may have no bid, but selling it later requires a positive bid with sufficient size.
    Both Batman flies are priced together. Estimated full-pair fills are assumed atomic; six displayed component quotes do not demonstrate
    an eight-unit complex order, its fill probability, latency or partial-fill handling.</p>
    <p>Assumed fees: $0.65 per gross contract per side. Batman pays $5.20 at entry and again if closed; additional adverse stress is $10 per pair
    per transaction. Iron pays half. Settlement has opening charges only. Exchange, broker-specific and exercise charges are unverified,
    so all-in real costs may be greater. Midpoint results are diagnostic, using exactly the same entries and exit decisions.</p>
    {table(['Cell','Component gross','Fees','Extra stress','Spread drag vs mid','Mid net diagnostic','Stressed net','Max initial expiry risk'],costs)}
    <p>Spread drag is midpoint net minus unstressed component net, on identical lifecycle choices. Fees and stress are shown separately.
    Equal lots do not mean equal dollar risk; the results provide mean initial risk and mean per-trade R, not return on a funded account.</p></section>
    <section id="verification"><h2>Independent cash-flow reconciliation</h2>
    <p>{review['completed_records']:,} completed records reconcile to raw option-side prices, transaction-needed sizes,
    gross fees, stress and individual native-settlement option cash flows, with {len(review['errors'])} discrepancies.
    Terminal counts: {esc(json.dumps(review['terminal_counts']))}. Counts reuse entries across policies and are not independent observations.
    Every reconciled raw side and the full separate cash ledger are preserved. Examples below are the first admitted and first liquidated records per geometry,
    selected by date rather than P&amp;L.</p>{''.join(cash_examples)}
    <p>Focused tests cover mixed option rights, overlapping and disjoint payoff zones, impossible profit zones, initial risk,
    both transaction fees, signed payable closes, transaction-needed sizes, strictly later fills, future-independent signals,
    complete entry cohorts, first-failure fallback, gap timing and the hard cutoff. Final test/lint/graphify receipts accompany the report.</p></section>
    <section id="reproduce"><h2>Evidence and reproduction</h2>
    <p>All inputs are read-only local evidence. The report embeds the full specification, coverage, source/input hashes, manifest,
    all cell summaries, comparisons and complete date/cell journal. Raw vendor data remains private and must be available at the recorded paths.
    Fresh output paths are mandatory. The original sources and input receipts are preserved under the run directory.</p>
    <button id="download">Download full evidence JSON</button><button id="download-journal">Download complete journal JSONL</button>
    <pre>uv run python -m tools.research_studies.xsp_independent.batman --out /tmp/xsp-batman-coverage-new --audit
uv run python -m tools.research_studies.xsp_independent.batman --out /tmp/xsp-batman-new --coverage /tmp/xsp-batman-coverage-new/coverage.json --freeze
uv run python -m tools.research_studies.xsp_independent.batman --out /tmp/xsp-batman-new --run
uv run python -m tools.research_studies.xsp_independent.review_batman --run /tmp/xsp-batman-new
uv run python -m tools.research_studies.xsp_independent.render_batman_report --run /tmp/xsp-batman-new --out /tmp/xsp-batman-new/report.html
uv run pytest tests/test_xsp_batman.py tests/test_xsp_quiet_flies.py -q
uv run ruff check .
graphify update .</pre>
    <p>Payoff calculations use the $100 multiplier and cash settlement described by
    <a href="https://www.cboe.com/tradable_products/sp_500/mini_spx_options/specifications">Cboe XSP specifications</a>.
    Native values come from the preserved raw responses and receipt associated with
    <a href="https://www.cboe.com/index_settlement_values">Cboe Index Settlement Values</a>;
    no SPX-close rounding or option-derived forward substitutes for published settlement.</p>
    <p>Next evidence for quiet iron: genuinely new joint XSP quotes/native settlements and independently timed signal prices,
    or observed complex-order fills with complete charges, using the exact retained policy. Next evidence for any redesigned Batman:
    a separately frozen economic hypothesis and fresh cohort, with combined position executions. No retrospective positive alone authorizes promotion.</p>
    <details><summary>Manifest and source hashes</summary><pre>{esc(json.dumps(manifest,indent=2))}</pre></details>
    </section></main><script type="application/json" id="evidence">{encoded}</script><script>
    const evidence=JSON.parse(document.getElementById('evidence').textContent);
    const select=document.getElementById('cell');
    const fmt=v=>v===undefined||v===null?'—':new Intl.NumberFormat('en-US',{{style:'currency',currency:'USD'}}).format(v);
    Object.keys(evidence.summary.cells).forEach(k=>{{const o=document.createElement('option');o.value=k;o.textContent=k;select.append(o)}});
    function update(){{const key=select.value,m=evidence.summary.cells[key];
    document.getElementById('detail').textContent='Lifecycle/status counts: '+JSON.stringify(m.statuses)+' · Terminal reasons: '+JSON.stringify(m.terminal_reasons)+' · Average win '+fmt(m.average_win)+' · Average loss '+fmt(m.average_loss)+' · Exposure '+(m.exposure_minutes||0).toFixed(0)+' position-minutes.';
    const rows=evidence.journal.filter(r=>r.cell===key&&r.status==='completed').sort((a,b)=>a.date.localeCompare(b.date));
    if(!rows.length){{document.getElementById('equity').innerHTML='';return;}}
    let sum=0;const values=[0,...rows.map(r=>sum+=r.stressed)],low=Math.min(0,...values),high=Math.max(0,...values),span=high-low||1;
    const pts=values.map((v,i)=>`${{65+i/(values.length-1)*1000}},${{250-(v-low)/span*200}}`).join(' ');
    document.getElementById('equity').innerHTML=`<h3>Cumulative terminal net P&amp;L — ${{key}}</h3><svg viewBox="0 0 1100 300" role="img" aria-label="Cumulative terminal P and L in dollars by chronological episode"><line x1="65" x2="1065" y1="250" y2="250" class="axis"/><polyline points="${{pts}}" fill="none" stroke="var(--accent)" stroke-width="2"/><text x="60" y="55" text-anchor="end">${{high.toFixed(0)}}</text><text x="60" y="250" text-anchor="end">${{low.toFixed(0)}}</text><text x="65" y="275">${{rows[0].date}}</text><text x="1065" y="275" text-anchor="end">${{rows.at(-1).date}}</text><text x="560" y="296" text-anchor="middle">Chronological terminal episodes (traded sessions; unequal calendar spacing)</text><text transform="translate(18,150) rotate(-90)" text-anchor="middle">Cumulative net ($)</text></svg><p class="caption">Source: frozen genuine XSP quote replay; fees and adverse stress included; ${{rows.length}} episodes. One observation per terminal outcome, no intraday valuation.</p>`;}}
    select.addEventListener('change',update);update();
    function download(name,value,type){{const blob=new Blob([value],{{type}}),u=URL.createObjectURL(blob),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);}}
    document.getElementById('download').onclick=()=>download('xsp-batman-evidence.json',JSON.stringify(evidence,null,2),'application/json');
    document.getElementById('download-journal').onclick=()=>download('xsp-batman-journal.jsonl',evidence.journal.map(r=>JSON.stringify(r)).join('\n')+'\n','application/x-ndjson');
    </script></body></html>'''
    # JS requires literal backslash-n, not a newline within a quoted string.
    body = body.replace(".join('\n')+'\n'", ".join('\\n')+'\\n'")
    with output.open('x') as handle:
        handle.write(body)
    print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    render(args.run,args.out)


if __name__ == '__main__':
    main()
