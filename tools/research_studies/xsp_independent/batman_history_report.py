"""Independent raw cash reconciliation and standalone expanded-history HTML."""

from __future__ import annotations

import argparse
import html
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

from tools.research_studies.xsp_independent.batman import read_rows
from tools.research_studies.xsp_independent.batman_history import ORIGINAL, ROOT, SPLIT
from tools.research_studies.xsp_independent.mean_reversion import digest, write_new
from tools.research_studies.xsp_independent.render_batman_report import (
    money,
    number,
    payoff_svg,
    table,
)


def review(run: Path) -> None:
    spec = json.loads((run / "specification.json").read_text())
    prepared = ROOT / spec["prepared"]
    native = pd.read_csv(prepared / "settlements-native.csv").set_index("date").settlement.to_dict()
    coverage = json.loads((prepared / "coverage.json").read_text())
    for name, expected in coverage["input_hashes"].items():
        if digest(ROOT / name) != expected:
            raise ValueError("Source input changed")
    rows = read_rows(run / "journal.jsonl")
    out = run / "cash-review"
    out.mkdir(exist_ok=False)
    errors, ledger = [], []
    admitted = ("completed", "unresolved_settlement")
    dates = sorted({r["date"] for r in rows if r["status"] in admitted})
    with (out / "raw-quotes.jsonl").open("x") as raw_file:
        for i, day in enumerate(dates):
            path = ROOT / f"data/thetadata/xsp_0dte/quote_1m/{day[:4]}/{day}.parquet"
            q = pd.read_parquet(path)
            if set(q.symbol) != {"XSP"} or set(pd.to_datetime(q.expiration).dt.strftime("%Y-%m-%d")) != {day}:
                raise ValueError("Raw identity mismatch")
            q["timestamp"] = q.timestamp.dt.tz_convert("America/New_York")
            q = q.set_index(["timestamp", "right", "strike"])
            for r in (r for r in rows if r["date"] == day and r["status"] in admitted):
                a, b = r["centers"]
                # Independently enumerate actual PUT/CALL options, not simulator tents.
                legs = [("PUT", a-4, 1), ("PUT", a, -2), ("PUT", a+4, 1),
                        ("CALL", b-4, 1), ("CALL", b, -2), ("CALL", b+4, 1)]
                transactions = [("open", pd.Timestamp(r["entry_time"]))]
                closing = r["terminal"] == "liquidation"
                if closing:
                    transactions.append(("close", pd.Timestamp(r["exit_time"])))
                amounts, marks, records = {}, {}, []
                for label, stamp in transactions:
                    amounts[label], marks[label] = 0., 0.
                    for right, strike, quantity in legs:
                        quote = q.loc[(stamp, right, strike)]
                        buy = (quantity > 0) == (label == "open")
                        price = float(quote["ask" if buy else "bid"])
                        size = float(quote["ask_size" if buy else "bid_size"])
                        if not (np.isfinite([quote.bid, quote.ask, size]).all()
                                and 0 <= quote.bid <= quote.ask and price > 0 and size >= abs(quantity)):
                            errors.append([day, r["cell"], label, right, strike, "side/size"])
                        amounts[label] += quantity*price
                        marks[label] += quantity*(quote.ask+quote.bid)/2
                        records.append({"time": stamp.isoformat(), "transaction": label,
                                        "right": right, "strike": strike, "position_qty": quantity,
                                        "side": "buy" if buy else "sell", "price": price,
                                        "needed": abs(quantity), "displayed": size,
                                        "bid": float(quote.bid), "ask": float(quote.ask),
                                        "bid_size": float(quote.bid_size), "ask_size": float(quote.ask_size)})
                unresolved = r["status"] == "unresolved_settlement"
                terminal = None if unresolved else 0.
                if closing:
                    terminal = 100*amounts["close"]
                elif not unresolved:
                    for right, strike, quantity in legs:
                        terminal += 100*quantity*(max(native[day]-strike, 0) if right == "CALL"
                                                  else max(strike-native[day], 0))
                fees, stress = 8*.65*len(transactions), 10*len(transactions)
                net = None if unresolved else terminal - 100*amounts["open"] - fees - stress
                risk = 100*amounts["open"]+15.20
                midpoint = None if unresolved else (100*marks["close"] if closing else terminal)-100*marks["open"]-fees
                expected = {"entry_debit": amounts["open"]}
                if unresolved:
                    expected["known_initial_risk"] = risk
                else:
                    expected.update(stressed=net, initial_risk=risk, fee=fees,
                                    stress_cost=stress, midpoint=midpoint, risk_units=net/risk)
                for key, value in expected.items():
                    if abs(r[key]-value) > 1e-7:
                        errors.append([day, r["cell"], key, r[key], value])
                receipt = {"date": day, "cell": r["cell"], "opening_cash": -100*amounts["open"],
                           "terminal_cash": terminal, "fees": fees, "stress": stress, "net": net,
                           "terminal": r["terminal"], "status": r["status"],
                           "terminal_cash_observed": not unresolved, "final_option_inventory": 0}
                ledger.append(receipt)
                raw_file.write(json.dumps({**receipt, "raw_quotes": records})+"\n")
            if i % 100 == 0:
                print(f"Cash review {i+1}/{len(dates)} {day}", flush=True)
    with (out / "ledger.jsonl").open("x") as handle:
        for row in ledger:
            handle.write(json.dumps(row)+"\n")
    result = {"method": "Direct raw quote sides and quantities, individual option intrinsic, gross fees and stress; no simulator pricing/payoff/account functions. Every completed record; all raw sides retained.",
              "accepted_records": len(ledger),
              "completed_records": sum(r["status"] == "completed" for r in ledger),
              "unresolved_openings_reconciled": sum(r["status"] == "unresolved_settlement" for r in ledger),
              "errors": errors,
              "terminal_counts": dict(Counter(r["terminal"] for r in ledger)),
              "source_sha256": digest(Path(__file__)), "journal_sha256": digest(run / "journal.jsonl"),
              "files": {p.name: digest(p) for p in out.iterdir() if p.is_file()}}
    write_new(out / "review.json", result)
    if errors:
        raise AssertionError(errors[:5])
    print(json.dumps({k: result[k] for k in ("completed_records", "errors", "terminal_counts")}))


def render(run: Path, out: Path) -> None:
    summary = json.loads((run / "summary.json").read_text())
    spec = json.loads((run / "specification.json").read_text())
    prepared = ROOT / spec["prepared"]
    coverage = json.loads((prepared / "coverage.json").read_text())
    cash = json.loads((run / "cash-review/review.json").read_text())
    rows = read_rows(run / "journal.jsonl")
    previous = json.loads((ORIGINAL / "summary.json").read_text())
    esc = lambda x: html.escape(str(x))  # noqa: E731
    primary, costs, years, months, sources, parent_rows, matches, reach_rows = [], [], [], [], [], [], [], []
    for cell, m in summary["cells"].items():
        primary.append([cell, m["accepted_entries"], m["trades"], m["unresolved_entries"],
                        money(m.get("stressed")), money(m.get("expectancy")),
                        number(100*m["win_rate"], 1)+'%' if m["trades"] else '—',
                        number(m.get("profit_factor")), money(m.get("terminal_drawdown")),
                        money(m.get("mean_initial_risk")), number(m.get("mean_risk_units"),4),
                        money(m.get("top3_removed")), money(m["halves"]["first"].get("stressed")),
                        money(m["halves"]["second"].get("stressed")),
                        f'{money(m["full_cohort_pnl_bounds"][0])} to {money(m["full_cohort_pnl_bounds"][1])}',
                        m["decision"]])
        if m["trades"]:
            costs.append([cell, money(m["gross"]), money(m["fees"]), money(m["stress_cost"]),
                          money(m["spread_drag"]), money(m["midpoint"]), money(m["stressed"]), money(m["max_initial_risk"])])
        for name, target in (("yearly",years),("monthly",months),("source_cohorts",sources)):
            for key, sub in m[name].items():
                target.append([cell, key, sub["trades"], money(sub.get("stressed")),
                               money(sub.get("expectancy")), number(sub.get("profit_factor")),
                               money(sub.get("top3_removed")), number(sub.get("mean_risk_units"),4)])
        parent_rows.append([cell, previous["cells"][cell]["trades"],money(previous["cells"][cell]["stressed"]),
                            m["yearly"]["2026"]["trades"],money(m["yearly"]["2026"].get("stressed"))])
        paired = m["vs_unconditional_participation"]
        matches.append([cell, paired["days"],money(paired["candidate"]),money(paired["benchmark"]),money(paired["difference"])])
    for geometry in ("body", "all_strikes"):
        for source in sorted({r["source"] for r in rows}):
            for movement in (False,True):
                rs = [r for r in rows if r["cell"] == geometry+"_unconditional_settlement"
                      and r["source"] == source and r["status"] in ("completed", "unresolved_settlement")
                      and r["movement_signal"] == movement]
                complete = [r for r in rs if r["reach_prefix_complete"]]
                hits = sum(r["zone_reach"] for r in complete)
                reach_rows.append([geometry,source,'movement' if movement else 'other',len(rs),len(complete),len(rs)-len(complete),hits,
                                   number(100*hits/len(complete),1)+'%' if complete else '—',
                                   sum(r["drift_side_zone_reach"] for r in complete),
                                   sum(r["status"] == "completed" for r in rs),
                                   sum(r["stressed"]>0 for r in rs if r["status"] == "completed")])
    plots = []
    for geometry in ("body", "all_strikes"):
        first = next((r for r in rows if r["cell"] == geometry+"_unconditional_settlement"
                      and r["status"] in ("completed", "unresolved_settlement")),None)
        if first:
            plots.append(f'<article><h3>{geometry}, first admitted date {first["date"]}</h3>{payoff_svg(first)}'
                         f'<p class="caption">Actual native XSP quotes; SPX/10 reference. Bodies {esc(first["centers"])}; wing width4. '
                         f'Both debits {money(100*first["entry_debit"])}; opening fees+stress $15.20. Positive expiry intervals {esc(first["profit_zones"])}.</p></article>')
    data = {"summary":summary,"specification":spec,"coverage":coverage,"cash_review":cash,
            "manifest":json.loads((run/"completed-manifest.json").read_text()),"journal":rows}
    encoded = json.dumps(data,allow_nan=False).replace('<','\\u003c')
    headers = ['Cell','Period / source','Priced trades','Priced net','Priced expectancy','Priced PF','Priced top3 removed','Priced mean R']
    first_date, last_date = coverage["sessions"][0]["date"],coverage["sessions"][-1]["date"]
    all_bounds_negative = all(m["full_cohort_pnl_bounds"][1] < 0 for m in summary["cells"].values())
    negative_summary = (
        "Every cell has a negative full-cohort upper bound under the frozen component-cost model. "
        "Even granting each unresolved settlement its maximum theoretical payoff cannot make a cell profitable. "
        "Missing terminals prevent exact full-cohort statistics; the frozen completeness rule therefore labels those cells "
        "insufficient evidence. This arithmetic bound still rules out a positive total under these modeled prices and costs."
        if all_bounds_negative else
        "Read full-cohort bounds alongside the completeness labels; missing terminal values prevent exact cohort statistics.")
    lead = summary["cells"]["all_strikes_movement_settlement"]
    body = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Batman XSP — expanded 2022–2026 history</title><style>
    :root{{--ink:#182e37;--paper:#f7f6f1;--muted:#526571;--accent:#087c77;--line:#c9d1d2}}*{{box-sizing:border-box}}
    body{{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}}
    main{{max-width:1280px;margin:auto;padding:35px 26px 70px}}h1{{font:600 clamp(32px,5vw,49px)/1.15 Georgia,serif;max-width:990px}}
    h2{{font:600 28px/1.2 Georgia,serif;margin-top:42px}}h3{{font-size:19px}}p{{max-width:1050px}}
    section{{border-top:1px solid var(--line);margin-top:28px;padding-top:8px}}.caption,.eyebrow{{font-size:13px;color:var(--muted)}}
    a{{color:var(--accent)}}nav{{display:flex;gap:18px;flex-wrap:wrap;margin:24px 0}}.decision{{border-top:3px solid var(--accent);padding-top:15px;font-size:20px}}
    .scroll{{overflow:auto;max-width:100%;margin:20px 0}}table{{border-collapse:collapse;font-size:13px;white-space:nowrap;width:100%}}
    td,th{{padding:9px 12px;border-bottom:1px solid var(--line);text-align:right}}td:first-child,th:first-child{{text-align:left}}th{{background:#e9edeb}}
    details{{padding:10px 0;border-bottom:1px solid var(--line)}}summary{{cursor:pointer}}pre{{overflow:auto;background:#e9edeb;padding:15px;font:13px/1.6 ui-monospace,monospace}}
    .plots{{display:grid;grid-template-columns:1fr 1fr;gap:28px}}article{{min-width:0}}svg{{width:100%;height:auto}}svg text{{font:12px system-ui;fill:var(--muted)}}.axis{{stroke:var(--line)}}
    select,button{{font:inherit;padding:9px;margin:5px;border:1px solid var(--line);max-width:100%;background:var(--paper);color:var(--ink)}}
    @media(max-width:760px){{main{{padding:20px 16px 45px}}.plots{{grid-template-columns:1fr}}}}</style></head><body><main>
    <p class="eyebrow">XSP 0-DTE · DATE EXTENSION · FROZEN 13 NOVEMBER 2026 · RESEARCH ONLY</p>
    <h1>Batman over a larger historical range</h1>
    <p class="decision"><b>Profitability screen: {'all eight cells fail even at their upper bounds' if all_bounds_negative else esc(summary['decision'])}.</b>
    Same eight Batman cells; no tuned width, threshold, sizing, cost or exit.
    This is retrospective, source-qualified historical evidence, not an untouched holdout or authorization to activate a bot.</p>
    <p>{esc(negative_summary)}</p>
    <p>The previously positive all-strikes movement/settlement cell now has {lead['accepted_entries']} accepted entries:
    {lead['trades']} priced outcomes totaling {money(lead.get('stressed'))}, and {lead['unresolved_entries']} unresolved settlements.
    Its full-cohort net lies between {money(lead['full_cohort_pnl_bounds'][0])} and {money(lead['full_cohort_pnl_bounds'][1])}.
    The original2026 +$414 result is reproduced, not erased; the older years offset it.</p>
    <p>Requested window: January3,2022–September28,2026. Available option partitions: {len(coverage['sessions']):,},
    {first_date}–{last_date}. By year: {esc(coverage['by_year'])}. Feature coverage: {esc(coverage['feature_statuses'])}.
    Missing native settlement dates: {esc(coverage['missing_settlements'])}.</p>
    <nav><a href="#coverage">Sources</a><a href="#rules">Rules</a><a href="#results">Results</a><a href="#signals">Movement</a>
    <a href="#costs">Costs</a><a href="#verify">Verification</a><a href="#reproduce">Reproduce</a></nav>
    <section id="coverage"><h2>More history, with an explicit source boundary</h2>
    <p>2022–2025 uses the owner-supplied SPX minute file, whose original third-party provider is unknown. These are SPX observations divided by ten,
    not native XSP and not Schwab observations. The established America/Chicago bar-end mapping becomes a minute-start label at end minus one minute,
    available at the original bar end. All2026 dates use the unchanged recorded SPX tick source; missing dates are not filled from the owner file.
    Results below distinguish those sources rather than treating them as one uniform feed.</p>
    <p>Actual XSP option quotes and displayed sizes remain the execution evidence. Additional native Cboe settlement history is preserved from the
    weekly, standard and month-end endpoints for2022–2025; only trading_symbol=XSP and settlement_symbol=XSP is accepted. Published values are never
    replaced by SPX/10, a rounded close or an option-implied forward. Current public source snapshots may contain later corrections with unknown publication times.</p>
    <p>Dates from2022–2025 have been inspected for other SPX research, including the spent2024–2026 SPX holdout. The prior2026 Batman results are known.
    No date here is claimed to be an untouched independent holdout. Archived expirations were not daily before October2022; absent non-expiry days are not zero-P&amp;L sessions.
    2020–2021 option files remain outside scope because their joint source quality and the calendar mapping are not established to this study's standard.</p>
    <p><b>Stale data:</b> the owner file has documented repeated, forward-filled OHLC stretches. The existing30-comparison stale threshold is enforced causally:
    detection removes observations from that availability time through the day, without retroactively discarding earlier entries. Earlier undetected repeats may affect signals.
    A post-entry failure therefore invokes the original irreversible settlement fallback. Invalid OHLC triggers the same quarantine. No missing values are interpolated.
    This differs from canonical whole-day stale exclusions, which would condition admission on later data quality. Detection receipts are preserved.</p></section>
    <section id="rules"><h2>Unchanged Batman economics</h2>
    <p>One lower PUT debit fly plus one upper CALL debit fly, each+1/−2/+1, four-point wings, same XSP0-DTE expiration: eight gross units, two flies together.
    Body-only offsets are half the10:29 XSP ATM straddle; all-strikes OTM offsets add four points. Nearest listed body on the required side, lower tie,
    no strike search. OTM is relative to the independent SPX/10 proxy and is rechecked at entry.</p>
    <p>Signal at10:30 ET from completed [09:31,10:30) minutes, >=54/59 observations, gaps<=120s, exact10:29 final observation.
    Entry is strictly after10:30 through10:32 at simultaneous transaction-needed component sides/sizes, each fly debit in(0,4).
    Movement requires efficiency>=0.30 and absolute first-hour drift>=half the straddle; unconditional is its benchmark. No quiet filter.</p>
    <p>Settlement holds both flies to published XSP settlement. Zone exit uses the entry-fixed combined expiry-profit interval, waits for a later completed SPX/10 observation inside it,
    then closes both flies at a strictly later usable quote within two minutes and by close minus15minutes. A touch is not a fill.
    First failed window or signal gap irreversibly settles both; no trigger attempts the exact cutoff quote, then settles if absent.
    Missing terminal data remains unresolved; no future exit availability admits entries.</p>
    <p>Expiry net =100×[max(4−|S−put_body|,0)+max(4−|S−call_body|,0)−both debits]−$5.20 opening fees−$10 stress.
    Maximum expiry loss is both debits plus$15.20. Positive zones are finite; remaining between disjoint tents, overshooting or reversing before the exit can lose.
    Overlap can create a central plateau and immediate zone signals without a later move. A payable component close and closing charges can lose more than expiry risk.</p>
    <div class="plots">{''.join(plots)}</div>
    <details><summary>Full frozen specification</summary><pre>{esc(json.dumps(spec,indent=2))}</pre></details></section>
    <section id="results"><h2>Every cell and every period</h2>
    <p><b>Missing terminal values remain missing.</b> Some admitted settlement positions lack a native published terminal input.
    Priced net, expectancy, win rate, PF, DD and R below describe only completed outcomes, and cannot be presented as full-cohort performance.
    Every accepted opening is retained. The full-cohort net interval adds contract-payoff lower/upper bounds for unresolved positions;
    it does not impute a settlement or assign zero. Any unresolved cell is classified insufficient evidence under the frozen decision rule.</p>
    <p>Primary results cross every component bid/ask, include gross-contract fees and additional adverse stress. These are component estimates,
    not demonstrated eight-unit complex-order fills. The eight rows are correlated alternatives, not an aggregate portfolio.</p>
    {table(['Cell','Accepted','Priced','Unresolved','Priced net stressed','Priced expectancy','Priced win rate','Priced PF','Priced terminal DD','Priced mean risk','Priced mean R','Priced top3 removed','Priced before Jul2024','Priced Jul2024 onward','Full-cohort net bounds','Decision'],primary)}
    <p class="caption">Fixed chronological split: {SPLIT}, the existing archive boundary, not the median accepted trade. DD uses terminal outcomes once per traded session,
    including initial equity0; no intraday or continuously marked DD. R divides each net trade by its stressed initial maximum expiry loss. No funded capital return is defined.</p>
    <label for="cell">Inspect a cell:</label><select id="cell"></select><div id="detail"></div><div id="equity"></div>
    <h3>Year by year</h3>{table(headers,years)}
    <details><summary>Monthly results</summary>{table(headers,months)}</details>
    <details><summary>Source-separated results</summary>{table(headers,sources)}</details>
    <details><summary>Matched participation comparisons</summary><p>Movement and unconditional use identical constructions on admitted signal dates.
    Differences reflect participation. Valid no-signal days may contribute zero; excluded or unresolved days never become zero.</p>
    {table(['Cell','Matched days','Candidate net','Unconditional net','Difference'],matches)}</details>
    <h3>Exact2026 reproduction</h3><p>{summary['original_2026_rows_reproduced_exactly']:,} original date/cell rows reproduce exactly before the source label is added,
    including exclusions, entries, prices, decisions and outcomes. The original report remains unchanged.</p>
    {table(['Cell','Prior trades','Prior net','New2026 trades','New2026 net'],parent_rows)}</section>
    <section id="signals"><h2>Movement forecast and realization are separate</h2>
    <p>Diagnostics include every admitted unconditional entry, including positions with unresolved settlements, split by the ex-ante movement signal and feed source.
    They are not selected by future terminal availability. A sampled reach requires an observation inside the
    combined entry-specific positive expiry-net interval; no crossing interpolation. An incomplete path is unknown, not a failed reach or a zero trade.
    Reaching an expiry intrinsic interval does not establish available intraday component liquidation value. See lifecycle counts for the selected cell.</p>
    {table(['Geometry','Source','Signal group','Accepted','Complete paths','Unknown paths','Zone hits','Reach rate','Drift-side hits','Native priced','Expiry winners'],reach_rows)}
    <p>Intraday realization must cover both entry debits, spreads and opening/closing charges. All exits close both flies; no remaining losing fly is dropped.
    Source/regime differences and prior inspection prevent a causal market-effect or deployable-edge claim.</p></section>
    <section id="costs"><h2>Spread, fees, stress and initial risk</h2>
    <p>Opening buys use asks; opening shorts use bids. Closing reverses those sides and retains signed negative liquidation values.
    Displayed sizes cover one wing or two body contracts on the transaction-needed side. Zero-bid purchased wings can later prevent a close.
    Fees are assumed$0.65 per gross contract per transaction: $5.20 entry and$5.20 if closed. Additional adverse stress is$10 per pair per transaction.
    Settlement has opening charges only. Extra broker/exchange/exercise charges, quote update ages, latency and partial fills remain unverified.
    Simultaneous full-pair component fills are assumed atomic, not demonstrated. Midpoints are diagnostic on the same lifecycle choices.</p>
    {table(['Cell','Component gross','Fees','Stress','Spread drag vs midpoint','Mid net diagnostic','Stressed net','Max initial expiry risk'],costs)}</section>
    <section id="verify"><h2>Independent accounting and verification</h2>
    <p>Direct raw option-side cash sums and individual-option intrinsic reconcile {cash['completed_records']:,} completed episodes and
    {cash['unresolved_openings_reconciled']:,} unresolved openings, with {len(cash['errors'])} discrepancies.
    Terminal counts: {esc(cash['terminal_counts'])}. All raw sides and a separate full cash ledger are preserved.
    Tests cover source bar-end availability/DST, causal stale quarantine without future admission filtering, invalid OHLC, duplicate timestamps,
    exact native settlement identity/conflict/missing behavior and unchanged economic rules, alongside the original mechanics tests.
    Verification logs, browser screenshots and AST graph-update receipts accompany this standalone file.</p></section>
    <section id="reproduce"><h2>Preserved evidence and reproduction</h2>
    <button id="download">Download full evidence JSON</button><button id="download-journal">Download full journal JSONL</button>
    <p>Embedded evidence includes every trial and date/cell row, frozen rules, coverage, source/input hashes and accounting receipt. Raw vendor data remains private.
    New output directories are required; partial and original evidence are preserved.</p>
    <pre>uv run python -m tools.research_studies.xsp_independent.batman_history acquire --out /tmp/batman-history-acquisition-new
uv run python -m tools.research_studies.xsp_independent.batman_history prepare --out /tmp/batman-history-inputs-new --acquisition /tmp/batman-history-acquisition-new
uv run python -m tools.research_studies.xsp_independent.batman_history freeze --out /tmp/batman-history-run-new --prepared /tmp/batman-history-inputs-new
uv run python -m tools.research_studies.xsp_independent.batman_history run --out /tmp/batman-history-run-new
uv run python -m tools.research_studies.xsp_independent.batman_history_report review --run /tmp/batman-history-run-new
uv run python -m tools.research_studies.xsp_independent.batman_history_report render --run /tmp/batman-history-run-new --out /tmp/batman-history-run-new/index.html</pre>
    <p class="caption">The source receipts use repository-relative paths for canonical data and absolute paths for external output roots.</p>
    <p>Contract multiplier/cash settlement: <a href="https://www.cboe.com/tradable_products/sp_500/mini_spx_options/specifications">Cboe XSP specifications</a>.
    Native terminal history: <a href="https://www.cboe.com/index_settlement_values">Cboe settlement values</a>.
    Research decision applies only to this fixed matrix. No runtime settings, deployments, services, tokens or orders were changed.</p></section>
    </main><script id="evidence" type="application/json">{encoded}</script><script>
    const e=JSON.parse(document.getElementById('evidence').textContent),s=document.getElementById('cell');
    Object.keys(e.summary.cells).forEach(k=>{{let o=document.createElement('option');o.value=k;o.textContent=k;s.append(o)}});
    function update(){{const k=s.value,m=e.summary.cells[k],rs=e.journal.filter(r=>r.cell===k&&r.status==='completed').sort((a,b)=>a.date.localeCompare(b.date));
    document.getElementById('detail').textContent='Statuses: '+JSON.stringify(m.statuses)+' · Priced terminal lifecycle: '+JSON.stringify(m.terminal_reasons)+' · Priced subset with profitable expiry geometry at entry: '+m.expiry_possible+'/'+m.trades;
    if(!rs.length){{document.getElementById('equity').innerHTML='';return}}let total=0;const vs=[0,...rs.map(r=>total+=r.stressed)],lo=Math.min(0,...vs),hi=Math.max(0,...vs),range=hi-lo||1;
    const p=vs.map((v,i)=>`${{65+i/(vs.length-1)*1000}},${{250-(v-lo)/range*200}}`).join(' ');
    document.getElementById('equity').innerHTML=`<h3>Cumulative terminal net P&amp;L — ${{k}}</h3><svg viewBox="0 0 1100 305" role="img" aria-label="Cumulative terminal net dollars by chronological episode"><line x1="65" x2="1065" y1="250" y2="250" class="axis"/><polyline points="${{p}}" fill="none" stroke="var(--accent)" stroke-width="2"/><text x="60" y="55" text-anchor="end">${{hi.toFixed(0)}}</text><text x="60" y="250" text-anchor="end">${{lo.toFixed(0)}}</text><text x="65" y="275">${{rs[0].date}}</text><text x="1065" y="275" text-anchor="end">${{rs.at(-1).date}}</text><text x="560" y="300" text-anchor="middle">Chronological traded sessions (unequal calendar spacing)</text><text transform="translate(18,150) rotate(-90)" text-anchor="middle">Cumulative net ($)</text></svg><p class="caption">Frozen genuine XSP quote replay, ${{rs.length}} completed episodes. Fees/stress included; one terminal valuation per episode, not intraday DD.</p>`;}}
    s.onchange=update;update();function save(name,text,type){{const u=URL.createObjectURL(new Blob([text],{{type}})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}}
    document.getElementById('download').onclick=()=>save('batman-history-evidence.json',JSON.stringify(e,null,2),'application/json');
    document.getElementById('download-journal').onclick=()=>save('batman-history-journal.jsonl',e.journal.map(r=>JSON.stringify(r)).join('\\n')+'\\n','application/x-ndjson');
    </script></body></html>'''
    with out.open("x") as handle:
        handle.write(body)
    print(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("review", "render"))
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    if args.action == "review":
        review(args.run.resolve())
    else:
        if args.out is None:
            parser.error("render requires --out")
        render(args.run.resolve(),args.out.resolve())


if __name__ == "__main__":
    main()
