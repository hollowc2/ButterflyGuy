"""Render the frozen quiet-fly results as a standalone offline HTML report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from tools.research_studies.xsp_independent.mean_reversion import digest

TEMPLATE = r'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>XSP quiet-day iron and OTM butterflies — November 12, 2026</title>
<style>
:root{color-scheme:light;--ink:#182522;--muted:#53635d;--accent:#17634a;--line:#cad3cc}
*{box-sizing:border-box}body{margin:0;background:#f4f5ef;color:var(--ink);font:16px/1.6 system-ui,sans-serif;overflow-wrap:anywhere}
main{max-width:1220px;margin:auto;padding:45px 30px}h1{font:clamp(30px,4vw,51px)/1.12 Georgia,serif;max-width:960px;margin:14px 0 24px}
h2{font:29px/1.2 Georgia,serif;margin-top:45px}h3{font-size:18px;margin:24px 0 10px}.eyebrow{font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:var(--accent)}
.lede{max-width:920px;font-size:19px}.note{border-left:3px solid var(--accent);padding:10px 22px;background:#e9eee5}
.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;padding:24px 0;border-bottom:1px solid var(--line)}
.stats strong{display:block;font:31px/1.3 Georgia,serif}.muted,small{color:var(--muted)}
.scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:right;padding:11px 10px;border-bottom:1px solid var(--line);white-space:nowrap}th:first-child,td:first-child{text-align:left}th{color:var(--muted);font-weight:500}
select,button{font:inherit;border:1px solid var(--line);padding:8px 12px;background:white;color:var(--ink);max-width:100%}label{display:block;margin:12px 0}.controls{display:flex;gap:22px;flex-wrap:wrap}.negative{color:#974036}.positive{color:var(--accent)}
svg{display:block;width:100%;height:auto;max-height:350px}.detail{display:grid;grid-template-columns:repeat(3,1fr);gap:20px;margin:20px 0}.detail strong{display:block;font-size:24px}
details{border-top:1px solid var(--line);padding:16px 0}summary{cursor:pointer;font-weight:600}code{font-size:13px;overflow-wrap:anywhere}a{color:var(--accent)}
@media(max-width:650px){main{padding:26px 17px}.stats,.detail{grid-template-columns:repeat(2,1fr);gap:15px}.lede{font-size:17px}h2{font-size:25px}table{font-size:12px}}
</style><main><div class="eyebrow">XSP · 0-DTE · Research only · November 12, 2026</div>
<h1>Quiet-day iron flies and OTM bodies: a fixed first test.</h1>
<p class="lede" id="verdict"></p>
<p id="lead"></p>
<div class="note">January 2–September 28, 2026 is previously inspected development data. These simulations establish no independent edge. All entries hold to native Cboe-published cash settlement; missing closing quotes cannot censor the result.<p id="source"></p></div>
<div class="stats" id="stats"></div>
<h2>The hypotheses</h2>
<p><b>ATM quiet:</b> sell an ATM straddle and buy equidistant protection. Compare its quoted economics with call and put debit flies at exactly the same center and wings.</p>
<p><b>Directional OTM:</b> move the body half an ATM straddle premium along the first-hour drift. <b>Neutral OTM pair:</b> put one body half a straddle above the forward proxy and one below. The pair is two flies, eight gross contracts, and twice the opening fees/stress. “OTM” describes the body; some wings can be ITM. Pair outcomes are not independent trades.</p>
<p id="gate"></p>
<h2>All 24 correlated comparisons</h2>
<p class="muted">USD net per one-fly or fixed two-fly session. Component bid/ask + $0.65 per gross opening contract + $5 adverse opening stress per fly. No closing transaction. Midpoint after fees is a diagnostic. Different admissions mean cell totals are not directly paired.</p>
<div class="scroll"><table><thead><tr><th>Arm / wings / form</th><th>Completed</th><th>Mid + fees</th><th>Component + fees</th><th>Stressed</th><th>$/trade</th><th>Top 3 removed</th><th>Decision</th></tr></thead><tbody id="cells"></tbody></table></div>
<h2>Inspect a complete terminal cohort</h2>
<div class="controls"><label>Comparison<br><select id="cell"></select></label><label>Accounting<br><select id="model"><option value="stressed">Component + fees + stress</option><option value="net">Component + fees</option><option value="midpoint">Midpoint + fees (diagnostic)</option></select></label></div>
<div class="detail" id="detail"></div><div id="chart"></div>
<p class="muted">Horizontal axis: trade/session date (ET). Vertical axis: cumulative terminal P&amp;L (USD). Trade outcomes only; intraday drawdown and account returns are not measured. Source: genuine ThetaData XSP minute quotes and published Cboe settlements, Jan 2–Sep 28, 2026.</p>
<div class="scroll"><table><thead><tr><th>Month</th><th>Completed</th><th>Stressed net</th><th>Win rate</th><th>Terminal drawdown</th></tr></thead><tbody id="months"></tbody></table></div>
<p id="coverage"></p><p id="paired"></p>
<h2>Does the iron construction improve entry economics?</h2>
<p>These comparisons require identical dates, centers, widths, and entry timestamps. Since the expiry shapes and fees match, the P&amp;L difference measures the modeled opening cost difference. A positive number favors IRON. These remain sampled component quotes, not demonstrated package executions.</p>
<div class="scroll"><table><thead><tr><th>Matched comparison</th><th>Same-snapshot pairs</th><th>IRON − debit net (USD)</th></tr></thead><tbody id="constructions"></tbody></table></div>
<h2>Limits and the next decision</h2>
<p>Neither signal source establishes native intraday XSP spot. Option parity is an approximate zero-carry forward; independent SPX observations divided by ten are a cross-index proxy. The straddle-to-normal-sigma conversion is a model approximation. Quote-event ages and complex-order fills are unavailable. The new transaction-needed size policy allows a purchased wing with no bid buyer, while requiring its ask size; short legs require positive bids and enough bid size. Pair shared-leg sizes are checked in aggregate without netting.</p>
<p>The event table covers named scheduled releases; it cannot certify a catalyst-free day. Settlement removes the closing-liquidity problem but retains full intraday risk. Fees are research assumptions; broker/exchange/exercise charges are not fully verified. The pair doubles exposure. These 24 cells are correlated, widths were fixed, and no outcome-based threshold tuning occurred. The complete campaign evaluated 72 correlated cells: parity/absolute, SPX/absolute, and SPX/relative calm. The first two produced no quiet-day trades and remain insufficient evidence for those strategies.</p>
<p>Refinement requires a complete terminal cohort, positive stressed net in both halves, positive net after removing the top three wins, and a positive paired daily difference against unconditional ATM on common valid days. Passing this retrospective screen would justify a new experiment, not activation.</p>
<details><summary>Frozen rules and provenance</summary><pre id="spec" style="white-space:pre-wrap;font-size:12px"></pre><p id="receipt"></p></details>
<p><button id="download">Download all journal records (CSV)</button> <a href="__RUN__/summary.json">Summary JSON</a> · <a href="__RUN__/cash-review.json">Independent cash audit</a></p>
<p class="muted">Contract mechanics: <a href="https://www.cboe.com/tradable_products/sp_500/mini_spx_options/specifications">Cboe XSP specifications</a>. Payoff comparison: <a href="https://www.optionseducation.org/news/august-webinar-key-takeaways-from-straddles-to-butterflies%2C-a-volatility-toolkit">Options Industry Council</a>. No runtime configuration or services were changed.</p>
<script>const D=__DATA__;
const $=id=>document.getElementById(id),money=n=>n==null?'Undefined':n.toLocaleString('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2});
const names={atm_all:'Unconditional ATM',atm_quiet:'Quiet ATM',otm_drift_quiet:'Quiet directional OTM',otm_pair_quiet:'Quiet neutral OTM pair'};
const label=k=>{const [arm,w,form]=k.split(/_w|_(?=CALL$|PUT$|IRON$)/);return `${names[arm]} / ${w}pt / ${form}`};
const keys=Object.keys(D.summary.cells),candidates=keys.filter(k=>!k.startsWith('atm_all_'));
const passing=candidates.filter(k=>D.summary.cells[k].decision==='refine');
$('verdict').textContent=passing.length?`${passing.length} of 18 candidate cells passed the retrospective screen; independent validation is still required.`:D.summary.features.quiet_days?'No candidate passed the frozen screen. Keep the construction findings; reject the completed exact entry/filter/geometry/settlement cells.':'The frozen classifier produced no quiet-day trades. The new ATM/OTM quiet-day hypotheses remain untested; this is insufficient evidence, not a profitability rejection.';
$('source').textContent=D.manifest.signal_source==='spx'?'Main experiment: independent recorded SPX last observation per completed minute, divided by ten. Supporting observations cover March 13–September 25; earlier or missing prefixes are exclusions. First parity-source experiment produced zero quiet signals; its evidence is retained separately. The same numerical rules were frozen before this new source was evaluated.':'Diagnostic first experiment: option-derived parity forward. No threshold changes followed this result.';
if(D.manifest.quiet_gate==='relative')$('source').textContent='Final experiment: recorded SPX last observations per completed minute, divided by ten. Signal coverage is March 13–September 25, with a further 20 covered-session warmup. Two earlier absolute realized/implied filter tests produced zero quiet-day trades. This final relative-calm hypothesis was frozen before its outcomes were examined; the campaign stops here.';
if(D.manifest.quiet_gate==='relative'){const lead=D.summary.cells.atm_quiet_w4_IRON;$('lead').textContent=`The strongest positive candidate is the quiet-day ATM iron fly with four-point wings: ${money(lead.stressed)} over ${lead.trades} trades after modeled costs/stress. It fails the prechosen checks: first half ${money(lead.halves.first.stressed)}, and ${money(lead.top3_removed)} after removing its three largest winners. This is a fragile lead, not a validated strategy.`;}
$('gate').textContent=D.manifest.quiet_gate==='relative'?'At 10:30 ET, compare normalized first-hour volatility with the lower tercile of the PRIOR 20 feature-covered first hours. Require directional efficiency at most 30% and no visible scheduled CPI, payrolls, PCE or FOMC date. Current/future observations never enter the training threshold. No implied-overpricing condition is imposed; the ratio remains diagnostic. Unconditional ATM on the same post-warmup, feature-covered sessions is the benchmark.':'At 10:30 ET, require the first-hour realized-variance forecast to be at most 75% of the remaining implied-move estimate, directional efficiency at most 30%, and no visible scheduled CPI, payrolls, PCE or FOMC date. This is a provisional quiet-day forecast, not an after-the-fact label. Unconditional ATM is the benchmark.';
$('stats').innerHTML=`<div><strong>${D.summary.sessions}</strong>archive sessions</div><div><strong>${D.summary.features.quiet_days}</strong>quiet signals</div><div><strong>${passing.length} / 18</strong>candidate cells passing</div><div><strong>${D.review.completed_cash_records}</strong>cash records reconciled</div>`;
$('cells').innerHTML=keys.map(k=>{const c=D.summary.cells[k];return `<tr><td>${label(k)}</td><td>${c.trades}</td><td>${money(c.midpoint)}</td><td>${money(c.net)}</td><td class="${c.stressed>0?'positive':'negative'}">${money(c.stressed)}</td><td>${money(c.expectancy)}</td><td>${money(c.top3_removed)}</td><td>${k.startsWith('atm_all_')?'Benchmark':c.decision}</td></tr>`}).join('');
const pricedKeys=keys.filter(k=>D.summary.cells[k].trades>0);$('cell').innerHTML=pricedKeys.map(k=>`<option value="${k}">${label(k)}</option>`).join('');$('cell').value=pricedKeys.includes('atm_quiet_w4_IRON')?'atm_quiet_w4_IRON':pricedKeys[0];
function render(){const key=$('cell').value,model=$('model').value,c=D.summary.cells[key];let total=0;const rows=D.rows.filter(r=>`${r.arm}_w${r.width}_${r.form}`===key&&r.status==='completed').sort((a,b)=>a.date.localeCompare(b.date));
const points=[0,...rows.map(r=>total+=r[model])],lo=Math.min(...points,0),hi=Math.max(...points,0),span=hi-lo||1;
const x=i=>70+i/(points.length-1||1)*950,y=v=>245-(v-lo)/span*210;
$('chart').innerHTML=rows.length?`<svg viewBox="0 0 1100 300" role="img" aria-label="Cumulative terminal P and L, USD by ET session date"><line x1="70" x2="1020" y1="${y(0)}" y2="${y(0)}" stroke="#89958c"/><polyline points="${points.map((v,i)=>`${x(i)},${y(v)}`).join(' ')}" fill="none" stroke="#17634a" stroke-width="2.5"/><text x="5" y="35" font-size="14">${money(hi)}</text><text x="5" y="245" font-size="14">${money(lo)}</text><text x="70" y="280" font-size="14">${rows[0].date}</text><text x="900" y="280" font-size="14">${rows.at(-1).date}</text><text x="450" y="298" font-size="13">Session date (ET)</text></svg>`:'';
$('detail').innerHTML=`<div><strong>${money(c[model])}</strong>total (${model})</div><div><strong>${money(c.mean_initial_risk)}</strong>mean stressed initial risk</div><div><strong>${c.mean_risk_units?.toFixed(3)??'Undefined'} R</strong>mean stressed net / initial risk</div><div><strong>${money(c.halves.first.stressed)}</strong>first half stressed</div><div><strong>${money(c.halves.second.stressed)}</strong>second half stressed</div><div><strong>${money(c.terminal_drawdown)}</strong>terminal-outcome drawdown</div>`;
$('months').innerHTML=Object.entries(c.monthly).filter(([m,v])=>v.trades).map(([m,v])=>`<tr><td>${m}</td><td>${v.trades}</td><td>${money(v.stressed)}</td><td>${(v.win_rate*100).toFixed(1)}%</td><td>${money(v.terminal_drawdown)}</td></tr>`).join('');
$('coverage').textContent=`Statuses: ${JSON.stringify(c.statuses)}. Chronological split: ${D.summary.split_date}; both halves are development. Missing inputs/entry quotes are exclusions, not zero P&L.`;
$('paired').textContent=`Common valid daily comparison: ${c.paired.days} days, candidate ${money(c.paired.candidate)}, ATM benchmark ${money(c.paired.benchmark)}, difference ${money(c.paired.difference)}. Valid no-signal days contribute zero. Conditional trade-only difference: ${money(c.conditional_paired.difference)} over ${c.conditional_paired.days} pairs. Pair exposure is twice ATM exposure.`;
}render();$('cell').onchange=render;$('model').onchange=render;
$('constructions').innerHTML=Object.entries(D.review.matched_construction_comparisons).filter(([k,c])=>c.matched_snapshots>0).map(([k,c])=>`<tr><td>${k}</td><td>${c.matched_snapshots}</td><td>${money(c.net_difference)}</td></tr>`).join('');
$('spec').textContent=JSON.stringify(D.spec,null,2);$('receipt').textContent=`Source rules SHA256: ${D.manifest.source_hashes['tools/research_studies/xsp_independent/quiet_flies.py']}. Native settlement SHA256: ${D.manifest.settlement_sha256}. Journal SHA256: ${D.review.journal_sha256}. ${D.review.result}`;
$('download').onclick=()=>{const blob=new Blob([D.csv],{type:'text/csv'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='xsp-quiet-flies-journal.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
</script></main></html>'''


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    data = {key: json.loads((args.run / name).read_text()) for key, name in (
        ("summary", "summary.json"), ("review", "cash-review.json"),
        ("manifest", "completed-manifest.json"), ("spec", "specification.json"))}
    data["rows"] = [json.loads(line) for line in (args.run / "journal.jsonl").read_text().splitlines()]
    data["csv"] = (args.run / "journal.csv").read_text()
    if data["review"]["journal_sha256"] != digest(args.run / "journal.jsonl"):
        raise ValueError("Journal changed since cash audit")
    # Escape script termination if an upstream descriptive field ever contains HTML.
    embedded = json.dumps(data, allow_nan=False).replace("</", "<\\/")
    with args.out.open("x") as handle:
        handle.write(TEMPLATE.replace("__DATA__", embedded).replace(
            "__RUN__", html.escape(str(args.run.relative_to(args.out.parent)))))
    print(html.escape(str(args.out)))


if __name__ == "__main__":
    main()
