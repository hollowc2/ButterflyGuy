"""Render an offline, self-contained HTML report from immutable XSP audit outputs."""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'reports/research/xsp-fallback-2026-11-12'
NAMES = {'baseline_60m': 'Timed exit + fallback', 'center_cross': 'Center crossing + fallback',
         'net_profit_25pct': '25% target + fallback', 'settlement': 'Always hold to settlement'}
COLORS = {'baseline_60m': '#8c847c', 'center_cross': '#1f6079',
          'net_profit_25pct': '#a45c35', 'settlement': '#3d7767'}


def money(value: float | None) -> str:
    if value is None:
        return 'Undefined'
    return ('−' if value < 0 else '+') + f'${abs(value):,.2f}'


def svg_chart(rows: list[dict], model: str = 'stressed_net') -> str:
    width, height, left, right, top, bottom = 1060, 360, 82, 28, 24, 52
    series = {}
    for policy in NAMES:
        selected = sorted((r for r in rows if r['policy'] == policy), key=lambda r: r['date'])
        cumulative = 0.
        points = [0.]
        for row in selected:
            cumulative += row[model]
            points.append(cumulative)
        series[policy] = points
    lower = min(min(v) for v in series.values())
    upper = max(0., max(max(v) for v in series.values()))
    pad = max(100., (upper - lower) * .08)
    lower, upper = lower - pad, upper + pad
    def x(i):
        return left + i / 105 * (width - left - right)

    def y(value):
        return top + (upper - value) / (upper - lower) * (height - top - bottom)
    parts = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Cumulative net P and L in US dollars by accepted entry sequence">']
    for i in range(5):
        value = lower + (upper - lower) * i / 4
        parts.append(f'<line class="gridline" x1="{left}" x2="{width-right}" y1="{y(value):.2f}" y2="{y(value):.2f}"/><text class="tick" text-anchor="end" x="{left-12}" y="{y(value)+4:.2f}">{money(value)}</text>')
    parts.append(f'<line class="zero" x1="{left}" x2="{width-right}" y1="{y(0):.2f}" y2="{y(0):.2f}"/>')
    for policy, points in series.items():
        path = ' '.join(f'{x(i):.2f},{y(value):.2f}' for i, value in enumerate(points))
        parts.append(f'<polyline fill="none" stroke="{COLORS[policy]}" stroke-width="2.4" points="{path}"/>')
    for i, label in [(0, 'Entry 0'), (35, 'Entry 35'), (70, 'Entry 70'), (105, 'Entry 105')]:
        parts.append(f'<text class="tick" text-anchor="middle" x="{x(i):.2f}" y="{height-25}">{label}</text>')
    parts.append(f'<text class="axis-label" text-anchor="middle" x="{width/2}" y="{height-4}">Accepted entry sequence · chronological ET session dates, Jan 2–Sep 28, 2026</text></svg>')
    return ''.join(parts)


def render(base: Path) -> str:
    replay = base / 'replay/run-01'
    summary = json.loads((replay / 'summary.json').read_text())
    audit = json.loads((base / 'quote-audit/summary.json').read_text())
    rows = [json.loads(line) for line in (replay / 'journal.jsonl').read_text().splitlines()]
    assert len(rows) == 420 and summary['accepted_entries'] == 105
    assert all(v['count'] == 105 for v in summary['policies'].values())
    table, monthly = [], []
    for policy, label in NAMES.items():
        m = summary['policies'][policy]
        s = m['stressed_net']
        priced = m['terminal_modes'].get('original_priced_exit', 0)
        settled = 105 - priced
        table.append(f'<tr><th scope="row">{label}</th><td>{priced} / {settled}</td><td>{money(m["marketable_net"]["total"])}</td><td class="negative">{money(s["total"])}</td><td>{100*s["win_rate"]:.1f}%</td><td>{s["profit_factor"]:.2f}</td><td>${s["drawdown_trade_close"]:,.2f}</td><td>{money(s["expectancy"])}</td></tr>')
    for month in summary['policies']['settlement']['stressed_net']['monthly']:
        monthly.append('<tr><th scope="row">' + month + '</th>' + ''.join(f'<td>{money(summary["policies"][p]["stressed_net"]["monthly"][month])}</td>' for p in NAMES) + '</tr>')
    extra = []
    for policy, label in NAMES.items():
        m = summary['policies'][policy]
        s = m['stressed_net']
        extra.append(f'<tr><th scope="row">{label}</th><td>{money(s["average_win"])}</td><td>{money(s["average_loss"])}</td><td>{money(s["worst_trade"])}</td><td>{s["expectancy_r"]:.3f} R</td><td>{money(s["top3_removed"])}</td><td>{money(s["halves"]["first"])}</td><td>{money(s["halves"]["second"])}</td></tr>')
    embedded = json.dumps({'summary': summary, 'rows': [{k: r.get(k) for k in ('date', 'policy', 'terminal_mode', 'entry_time', 'exit_time', 'entry_ask', 'center', 'right', 'marketable_net', 'stressed_net', 'midpoint_net', 'fallback_reason', 'fallback_known_at')} for r in rows], 'names': NAMES, 'colors': COLORS}, allow_nan=False, separators=(',', ':')).replace('</', '<\\/')
    chart = svg_chart(rows)
    legend = ''.join(f'<span><i style="background:{color}"></i>{NAMES[p]}</span>' for p, color in COLORS.items())
    page = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>XSP Butterfly Research — Completing the Missing Exits</title>
<style>
:root{--paper:#f7f5ef;--ink:#182b3a;--muted:#60707a;--line:#d9dedb;--blue:#1f6079;--red:#9e4234;--light:#eef2f1;--white:#fffefa}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.65 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--blue);text-underline-offset:3px}header{border-bottom:1px solid var(--line)}.masthead{max-width:1200px;margin:auto;padding:18px 28px;display:flex;justify-content:space-between;gap:12px;font-size:12px;letter-spacing:.1em;text-transform:uppercase}.masthead strong{letter-spacing:.15em}main{max-width:1140px;margin:auto;padding:50px 28px 70px}.eyebrow{font-size:11px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:var(--blue)}h1,h2,h3{font-family:Georgia,"Times New Roman",serif;font-weight:400;line-height:1.12;letter-spacing:-.025em}h1{max-width:880px;font-size:clamp(36px,5.7vw,65px);margin:18px 0 24px}h2{font-size:clamp(28px,3.5vw,39px);margin:0 0 20px}h3{font-size:24px;margin:0 0 12px}p{margin:0 0 18px}.lead{font-size:20px;line-height:1.6;max-width:850px;color:#3f535f}.meta{font-size:12px;color:var(--muted)}.verdict{display:flex;gap:20px;align-items:flex-start;padding:22px 0;border-top:2px solid var(--ink);border-bottom:1px solid var(--line);margin:34px 0 26px}.verdict .tag{flex:none;font-size:11px;letter-spacing:.13em;font-weight:800;color:var(--red);padding-top:4px}.verdict p{margin:0;max-width:850px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin:28px 0 12px}.stat strong{font-size:30px;line-height:1.2;font-weight:500;font-variant-numeric:tabular-nums;display:block}.stat span{font-size:12px;line-height:1.45;display:block;color:var(--muted);margin-top:8px}.negative{color:var(--red)}.section{padding:46px 0;border-top:1px solid var(--line);margin-top:38px}.section-head{display:grid;grid-template-columns:45px 1fr;gap:10px}.section-number{font-size:12px;color:var(--muted);padding-top:10px}.section-body{margin-left:55px}.two{display:grid;grid-template-columns:1fr 1fr;gap:40px}.finding{padding:22px 0;border-top:1px solid var(--ink)}.big{font-size:35px;font-weight:500;letter-spacing:-.04em;line-height:1.2}.small{font-size:13px;color:var(--muted)}.callout{background:var(--light);padding:22px 25px;margin:24px 0;border-left:3px solid var(--blue)}.callout p:last-child{margin-bottom:0}.table-wrap{width:100%;overflow-x:auto;margin:18px 0}table{border-collapse:collapse;width:100%;font-size:13px;font-variant-numeric:tabular-nums}th,td{padding:13px 12px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top;white-space:nowrap}thead th{font-size:10px;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);font-weight:700;background:#efefe8}th:first-child,td:first-child{text-align:left}tbody th{font-weight:500;white-space:normal;min-width:180px}.caption{font-size:12px;line-height:1.6;color:var(--muted);margin:10px 0 18px}.chart{width:100%;background:var(--white);border:1px solid var(--line);padding:16px 8px}.chart svg{width:100%;height:auto;display:block}.gridline{stroke:#e1e5e2;stroke-width:1}.zero{stroke:#a7b3b5;stroke-width:1;stroke-dasharray:4 4}.tick,.axis-label{font:11px system-ui,sans-serif;fill:#62717a}.legend{display:flex;flex-wrap:wrap;gap:8px 20px;font-size:11px;color:var(--muted);margin:14px 0}.legend span{display:flex;gap:7px;align-items:center}.legend i{width:18px;height:3px;display:inline-block}.controls{display:flex;gap:14px;flex-wrap:wrap;align-items:center;justify-content:space-between;margin:20px 0 12px}select,button,.button{font:13px system-ui,sans-serif;color:var(--ink);border:1px solid #a9b6bb;background:var(--white);padding:10px 14px;border-radius:3px}button,.button{cursor:pointer;text-decoration:none;display:inline-block}button:hover,.button:hover{background:#e9eeeb}select:focus-visible,button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--blue);outline-offset:3px}.reason-row{display:grid;grid-template-columns:minmax(155px,1fr) 2fr 45px;gap:14px;align-items:center;margin:14px 0;font-size:13px}.track{height:12px;background:#e5e8e3}.track b{display:block;height:100%;background:var(--blue)}.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin:25px 0}.flow div{border-top:2px solid var(--line);padding-top:12px}.flow b{font-size:12px;letter-spacing:.04em}.flow p{font-size:13px;color:var(--muted);margin:7px 0}.sources{font-size:13px;line-height:1.8;padding-left:20px}.sources li{margin-bottom:8px}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#eeeee7;padding:18px}details{border-top:1px solid var(--line);padding:18px 0}summary{cursor:pointer;font-size:14px;font-weight:600}.ledger{max-height:440px;overflow:auto}footer{border-top:1px solid var(--line);padding-top:20px;font-size:12px;color:var(--muted)}.no-print{display:block}@media(max-width:700px){main{padding:30px 18px 45px}.masthead{padding:15px 18px;flex-direction:column;font-size:10px;gap:4px}.stats{grid-template-columns:1fr 1fr;gap:24px 18px}.stat strong{font-size:27px}.lead{font-size:17px}.verdict{display:block}.verdict .tag{display:block;margin-bottom:10px}.two{grid-template-columns:1fr;gap:22px}.section-body{margin-left:0}.section-head{grid-template-columns:28px 1fr;gap:8px}.section{padding-top:32px;margin-top:30px}.flow{grid-template-columns:1fr 1fr}.reason-row{grid-template-columns:minmax(125px,1fr) 1fr 28px;gap:8px}.controls{align-items:flex-start;flex-direction:column}.big{font-size:30px}.chart{padding:8px 0}.tick,.axis-label{font-size:14px}}@media print{body{background:white;font-size:11px}main{padding:15px;max-width:none}header{display:none}h1{font-size:36px}.section{break-inside:avoid;padding-top:22px;margin-top:24px}.no-print{display:none!important}.chart,table{break-inside:avoid}details{display:block}details>*{display:block}th,td{padding:7px}.table-wrap{overflow:visible}.ledger{max-height:none}a{color:inherit}.stats{margin:18px 0}}
</style></head><body>
<header><div class="masthead"><strong>Butterfly Guy · Research Notebook</strong><span>XSP / Independent strategy development / 12 November 2026</span></div></header>
<main>
<div class="eyebrow">Study 03 · Missing-quote completion audit</div>
<h1>The missing exits remove the apparent butterfly edge.</h1>
<p class="lead">Earlier exits looked profitable on the trades we could price. Giving every accepted entry a defined terminal outcome reverses that result. These exact 4-point excursion-reversal policies remain unprofitable under the stated research assumptions.</p>
<p class="meta">Historical window: January 2–September 28, 2026 · 185 sessions examined · 105 accepted MR2 / 4-point-wing entries · One butterfly per entry · All times ET</p>
<div class="verdict"><span class="tag">Decision: reject as tested</span><p>Center crossing with a settlement fallback loses <strong class="negative">$2,978.40</strong>. The 25% profit target with the same fallback loses <strong class="negative">$2,343.00</strong>. Both do better than the completed timed-exit baseline, but worse than always holding these same entries to settlement. This rejects the specified policies, not every XSP butterfly strategy.</p></div>
<div class="stats"><div class="stat"><strong>105 / 105</strong><span>Entries resolved for every policy</span></div><div class="stat"><strong>420</strong><span>Policy outcomes across the same 105 entries</span></div><div class="stat"><strong>57 / 57</strong><span>Missing late center exits with a required wing showing zero bid and bid size</span></div><div class="stat"><strong>0</strong><span>Profitable complete-cohort policies under modeled costs</span></div></div>
<section class="section" id="reversal"><div class="section-head"><span class="section-number">01</span><h2>What changed when the ledger became complete</h2></div><div class="section-body">
<div class="two"><div class="finding"><div class="eyebrow">Center-cross policy</div><p class="big">+$493.20 <span class="small">→</span> <span class="negative">−$2,978.40</span></p><p>The original 39 priced exits are unchanged. The other 66 entries now receive their published cash-settlement outcome after an explicit, irrevocable fallback decision.</p></div><div class="finding"><div class="eyebrow">25% profit-target policy</div><p class="big">+$501.00 <span class="small">→</span> <span class="negative">−$2,343.00</span></p><p>The original 20 priced exits are unchanged. The 85 unresolved cases remain in the cohort and settle when their required quote path first becomes unusable.</p></div></div>
<p class="caption">All figures above include the same modeled adverse-price stress and fee assumptions. The positive values describe partial subsets; the negative values describe all 105 entries under a newly specified fallback. The earlier reports remain preserved.</p>
<div class="callout"><p><strong>The apparent winners were selected by observability.</strong> A path that reached a priced profit exit before quotes failed stayed in the earlier result. A path that never reached that exit often disappeared from the priced cohort. Missing cases were never recorded as zero; this pass makes their treatment explicit and causal.</p></div>
<p>This is a retrospective completion audit. The previous missingness analysis had already exposed the excluded cohorts’ settlement totals. It is not a fresh holdout, independent discovery, or a new search for favorable parameters.</p>
</div></section>
<section class="section" id="results"><div class="section-head"><span class="section-number">02</span><h2>Four policies, identical entries, complete outcomes</h2></div><div class="section-body">
<p>Every row below evaluates the same 105 accepted entries at their original opening prices. “Priced / settled” counts actual modeled closing transactions versus terminal cash settlements; it is not a count of live broker fills.</p>
<div class="table-wrap"><table><thead><tr><th>Exit policy</th><th>Priced / settled</th><th>Component net</th><th>Stressed net</th><th>Win rate¹</th><th>Profit factor¹</th><th>Drawdown¹</th><th>Expectancy¹</th></tr></thead><tbody>__RESULT_TABLE__</tbody></table></div>
<p class="caption">¹ Stressed case. Net amounts are US dollars for one butterfly per entry. Drawdown is measured at terminal trade outcomes, not intraday. Fees are research assumptions; component NBBO calculations are not observed complex-order fills.</p>
<div class="controls"><div><h3 style="margin-bottom:4px">Cumulative net P&amp;L</h3><span class="small" id="chart-subtitle">Component prices + fees + adverse-price stress · complete cohort</span></div><label class="no-print small">Accounting scenario <select id="model"><option value="stressed_net">Component prices + fees + stress</option><option value="marketable_net">Component prices + fees</option><option value="midpoint_net">Midpoint + fees · diagnostic</option></select></label></div>
<div class="chart" id="equity">__CHART__</div><div class="legend">__LEGEND__</div>
<p class="caption">Horizontal axis: accepted entry sequence in chronological ET session order, 0–105. Vertical axis: cumulative US-dollar P&amp;L. Source: frozen XSP entries, minute NBBO observations and native Cboe XSP settlements, Jan 2–Sep 28, 2026. The four lines are alternative policies; they must not be summed as a portfolio.</p>
<p>With the added fallback, early exits still improve on the completed timed policy. They also cut trades whose eventual settlement outcomes were better: center crossing finishes $1,228.40 below the always-settle benchmark, while the target finishes $593.00 below it. Always settling loses money too.</p>
</div></section>
<section class="section" id="quotes"><div class="section-head"><span class="section-number">03</span><h2>What the “missing quotes” actually contained</h2></div><div class="section-body">
<p>The raw audit covers all 105 scheduled 15:45 exit snapshots and all 151 unresolved center/target events. It retains 1,192 timestamped snapshots with the three held legs’ prices and displayed sizes.</p>
<h3>Scheduled 15:45 liquidation: primary rejection reason</h3>
<div class="reason-row"><span>Required zero bid / zero bid size</span><span class="track"><b style="width:90.476%"></b></span><strong>95</strong></div>
<div class="reason-row"><span>Other required-size failure</span><span class="track"><b style="width:2.857%"></b></span><strong>3</strong></div>
<div class="reason-row"><span>Only an unused-side size failure</span><span class="track"><b style="width:.952%"></b></span><strong>1</strong></div>
<div class="reason-row"><span>Passes the original filter</span><span class="track"><b style="width:5.714%"></b></span><strong>6</strong></div>
<p class="caption">Counts are primary classifications among the same 105 cutoff snapshots; categories sum to 105. Source: quote-audit/summary.json. A seventh snapshot has the necessary closing-side sizes but fails an inherited requirement on an unused side.</p>
<div class="two"><div><h3>Center-policy failures</h3><p>All <strong>57</strong> no-trigger cutoff failures had at least one required wing bid of zero with zero displayed bid size and a positive ask. Checking only the transaction-needed sides rescues none of these 57 cutoff exits.</p><p class="small">That is an absence of a displayed buyer in the recorded leg market. It does not prove that the butterfly is worthless, or that no complex-order execution could be obtained.</p></div><div><h3>Profit-policy gaps</h3><p>Of the <strong>85</strong> unresolved target events, the first missing snapshot fails solely on an unused side in <strong>32</strong> cases. Another 28 fail a required-size condition, and 25 show a required zero bid with zero bid size.</p><p class="small">This exposes genuine censoring from the inherited filter. No filter was relaxed and no alternative fill was assumed in the current performance results.</p></div></div>
<details><summary>Concrete raw-quote examples</summary><div class="table-wrap"><table><thead><tr><th>ET observation</th><th>Held-leg evidence</th><th>Interpretation</th></tr></thead><tbody><tr><th>Jan 2 · 15:45<br>CALL center 688</th><td>Upper wing: bid 0 / ask 0.01<br>Bid size 0</td><td>No displayed wing buyer on the required selling side</td></tr><tr><th>Jan 15 · 15:45<br>PUT center 696</th><td>Body: bid 1.84 / ask 2.00<br>Bid / ask sizes 1 / 1</td><td>Closing needs two body contracts at the ask; displayed ask size is insufficient</td></tr><tr><th>Feb 13 · 15:45<br>PUT center 682</th><td>Body: bid 0.55 / ask 0.60<br>Bid / ask sizes 1 / 25</td><td>Ask size is sufficient for the close; the unused body bid-size requirement causes rejection</td></tr></tbody></table></div><p class="caption">Examples are the first chronological occurrence of their cause, not selected by P&amp;L. Prices are option points; sizes are contracts. Raw snapshots and source-file hashes are preserved.</p></details>
<p>Across the 76 nonterminal profit-prefix gap events, 48 contain at least one snapshot with sufficient transaction-needed closing sizes, and 25 have sufficient needed sizes throughout the missing interval. These observations motivate a separate side-specific quote-quality study; they do not establish executable package prices.</p>
</div></section>
<section class="section" id="rules"><div class="section-head"><span class="section-number">04</span><h2>The missing-quote fallback is a rule, not an imputed price</h2></div><div class="section-body">
<div class="flow"><div><b>01 · Enter</b><p>Keep the frozen MR2 signal, 4-point symmetric geometry, side and opening quote.</p></div><div><b>02 · Monitor</b><p>Evaluate the first center crossing or nominal 25% net-profit trigger on known observations.</p></div><div><b>03 · Resolve</b><p>Use the original later priced exit. On the first required data or fill failure, lock settlement.</p></div><div><b>04 · Settle</b><p>Use the published expiry value only at the terminal event. Never resume the earlier exit search.</p></div></div>
<p>An input gap becomes known on the scheduled minute at the last usable observation plus three minutes, the first poll beyond the two-minute tolerance. It is not backdated to an eventual recovery quote. Missing an exact entry proxy is known at entry. A failed fill is known after its first two-minute attempt window expires, capped at the scheduled cutoff.</p>
<p>The original signal uses an opening-range excursion and a subsequent reversal toward its midpoint. It uses an option-derived approximate forward, not an observed official intraday XSP feed. A butterfly center crossing is a sampled equality or sign change; it is not an exact intrabar-touch claim.</p>
<div class="callout"><p><strong>Costs remain unchanged.</strong> One 1:−2:1 butterfly has four contracts per side. Fees assume $0.65 per contract per side: $2.60 to open and $2.60 for an actual modeled liquidation. Additional adverse stress is $5 per transaction. Cash settlement incurs the opening assumptions only, with no closing order, fee or slippage.</p></div>
<p>A long symmetric fly’s expiry value is <code>100 × max(0, width − |settlement − center|)</code>. Published Cboe XSP values are used unchanged; no final-minute proxy, zero-price substitution, or guessed rounding rule supplies the terminal payoff.</p>
</div></section>
<section class="section" id="robustness"><div class="section-head"><span class="section-number">05</span><h2>The losses persist beyond the headline total</h2></div><div class="section-body">
<div class="table-wrap"><table><thead><tr><th>Policy</th><th>Avg. win</th><th>Avg. loss</th><th>Worst outcome</th><th>Expectancy / risk</th><th>Top 3 wins removed</th><th>First half</th><th>Second half</th></tr></thead><tbody>__EXTRA_TABLE__</tbody></table></div>
<p class="caption">All figures use the stressed case. R divides net P&amp;L by the entry debit plus opening fee and entry stress. It is not a funded-account return. Chronological halves use the previously fixed May 15 split in the 185-session archive calendar.</p>
<details><summary>Monthly stressed P&amp;L</summary><div class="table-wrap"><table><thead><tr><th>Month</th><th>Timed + fallback</th><th>Center + fallback</th><th>Target + fallback</th><th>Always settle</th></tr></thead><tbody>__MONTHLY__</tbody></table></div></details>
<details><summary class="no-print">Inspect or download the complete policy ledger</summary><div class="controls no-print"><label class="small">View policy <select id="ledger-policy">__POLICY_OPTIONS__</select></label><button id="download" type="button">Download all 420 policy records · CSV</button></div><div class="table-wrap ledger"><table><thead><tr><th>Entry date</th><th>Terminal mode</th><th>Entry debit</th><th>Exit time ET</th><th>Stressed net</th><th>Fallback reason</th></tr></thead><tbody id="ledger-body"></tbody></table></div><p class="caption">Each policy has 105 rows. Records repeat the same entries for alternative exit rules; 420 records do not represent 420 independent trades.</p></details>
</div></section>
<section class="section" id="review"><div class="section-head"><span class="section-number">06</span><h2>Verification, boundaries and next decision</h2></div><div class="section-body">
<p>The original 101 timed, 39 center-cross and 20 target exits are preserved exactly. Every policy now contains the same 105 entry identities and exactly one terminal result for each. Independent review reconciled all 420 cash ledgers and the causal fallback clocks; 25 focused tests passed. The native settlement CSV is checked against its attributed receipt, and all source and output hashes are recorded.</p>
<p><strong>Reject the completed center-cross and 25% target policies under this fallback.</strong> The appropriate next experiment is a narrowly specified audit of transaction-needed quote checks and execution evidence, with explicit treatment of failed orders. Additional target or timing optimization on the previously observable winners would not address the problem.</p>
<p class="small">This result depends on the fallback choice. Other data-recovery or execution responses have not been tested. Unknown leg-update age, asynchronous NBBO observations, complex-order price improvement, order rejection, latency, partial fills and broker exercise charges remain unmodeled. Reported drawdown excludes intraday marks. The study uses previously inspected dates and a signal/width chosen after earlier results, so it cannot establish an independent edge. No runtime strategy, account guard, paper/live mode, risk limit, routing or service was changed.</p>
<details><summary>Sources and reproduction</summary><ul class="sources"><li><a href="replay/run-01/summary.json">Completed-cohort statistics</a>, <a href="replay/run-01/journal.csv">CSV ledger</a>, <a href="replay/run-01/manifest.json">run manifest</a>, and <a href="protocol.json">completion-audit protocol</a>.</li><li><a href="quote-audit/summary.json">Raw quote audit summary</a> and <a href="quote-audit/manifest.json">105-file input manifest</a>.</li><li>Previous study: <a href="../xsp-realization-2026-11-11/root-review-02/decision.json">coverage review and conditional results</a>. All prior artifacts remain unchanged.</li><li>Cboe published settlements: <a href="https://www.cboe.com/index_settlement_values/get_sv_data/W/2026/">weekly</a>, <a href="https://www.cboe.com/index_settlement_values/get_sv_data/S/2026/">standard</a>, and <a href="https://www.cboe.com/index_settlement_values/get_sv_data/M/2026/">end of month</a>. Exact XSP trading/settlement symbols are required. Current snapshot; historical publication/correction times are unknown.</li><li>Genuine ThetaData XSP minute quote archive, locally preserved under the owner’s research licence. NBBO observation timestamps do not establish the individual legs’ update age.</li></ul><pre>uv run python -m tools.research_studies.xsp_independent.fallback \
  --out /tmp/xsp-fallback-unique --freeze --run
uv run python -m tools.research_studies.xsp_independent.quote_evidence \
  --out /tmp/xsp-quote-audit-unique
uv run python -m tools.research_studies.xsp_independent.render_fallback_report \
  --out /tmp/xsp-fallback-report.html</pre></details>
</div></section>
<footer><p>XSP independent butterfly research · Retrospective evidence · Prepared November 12, 2026</p><p>This HTML is self-contained. Charts, scenario controls and the embedded CSV download run locally without external scripts, fonts, data requests or services. Linked evidence files require the accompanying research directory.</p></footer>
</main>
<script id="report-data" type="application/json">__DATA__</script>
<script>
'use strict';
const D=JSON.parse(document.getElementById('report-data').textContent);
const money=n=>n===null||n===undefined?'Undefined':(n<0?'−':'+')+'$'+Math.abs(n).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
function chart(model){const narrow=innerWidth<700,W=narrow?540:1060,H=narrow?330:360,L=82,R=28,T=24,B=52,series={};Object.keys(D.names).forEach(p=>{let c=0;series[p]=[0,...D.rows.filter(r=>r.policy===p).sort((a,b)=>a.date.localeCompare(b.date)).map(r=>c+=r[model])]});const all=Object.values(series).flat(),lo=Math.min(0,...all),hi=Math.max(0,...all),pad=Math.max(100,(hi-lo)*.08),lower=lo-pad,upper=hi+pad,x=i=>L+i/105*(W-L-R),y=v=>T+(upper-v)/(upper-lower)*(H-T-B);let out=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Complete-cohort cumulative net P and L in US dollars">`;for(let i=0;i<5;i++){const v=lower+(upper-lower)*i/4;out+=`<line class="gridline" x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}"/><text class="tick" text-anchor="end" x="${L-12}" y="${y(v)+4}">${money(v)}</text>`}out+=`<line class="zero" x1="${L}" x2="${W-R}" y1="${y(0)}" y2="${y(0)}"/>`;Object.keys(series).forEach(p=>{out+=`<polyline fill="none" stroke="${D.colors[p]}" stroke-width="2.4" points="${series[p].map((v,i)=>`${x(i)},${y(v)}`).join(' ')}"/>`});[0,35,70,105].forEach(i=>out+=`<text class="tick" text-anchor="middle" x="${x(i)}" y="${H-25}">Entry ${i}</text>`);return out+`<text class="axis-label" text-anchor="middle" x="${W/2}" y="${H-4}">${narrow?'Accepted entry sequence (ET)':'Accepted entry sequence · chronological ET session dates, Jan 2–Sep 28, 2026'}</text></svg>`}
function ledger(){const p=document.getElementById('ledger-policy').value,body=document.getElementById('ledger-body');body.replaceChildren();D.rows.filter(r=>r.policy===p).sort((a,b)=>a.date.localeCompare(b.date)).forEach(r=>{const tr=document.createElement('tr');[r.date,r.terminal_mode.replaceAll('_',' '),'$'+r.entry_ask.toFixed(2),r.exit_time,money(r.stressed_net),(r.fallback_reason||'—').replaceAll('_',' ')].forEach(v=>{const td=document.createElement('td');td.textContent=v;tr.appendChild(td)});body.appendChild(tr)})}
document.getElementById('model').addEventListener('change',e=>{document.getElementById('equity').innerHTML=chart(e.target.value);const labels={stressed_net:'Component prices + fees + adverse-price stress · complete cohort',marketable_net:'Component prices + fees · complete cohort',midpoint_net:'Midpoint + fees · diagnostic only; not a fill model'};document.getElementById('chart-subtitle').textContent=labels[e.target.value]});
document.getElementById('ledger-policy').addEventListener('change',ledger);
document.getElementById('download').addEventListener('click',()=>{const cols=Object.keys(D.rows[0]),quote=v=>'"'+String(v??'').replaceAll('"','""')+'"',csv=[cols.map(quote).join(','),...D.rows.map(r=>cols.map(k=>quote(r[k])).join(','))].join('\r\n');const url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='xsp-fallback-complete-420-policy-records.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});ledger();document.getElementById('equity').innerHTML=chart(document.getElementById('model').value);window.addEventListener('resize',()=>{document.getElementById('equity').innerHTML=chart(document.getElementById('model').value)});
</script></body></html>'''
    replacements = {'__RESULT_TABLE__': ''.join(table), '__EXTRA_TABLE__': ''.join(extra),
                    '__MONTHLY__': ''.join(monthly), '__CHART__': chart, '__LEGEND__': legend,
                    '__DATA__': embedded, '__POLICY_OPTIONS__': ''.join(f'<option value="{p}"'+(' selected' if p == 'center_cross' else '')+f'>{html.escape(label)}</option>' for p, label in NAMES.items())}
    assert audit['cutoffs']['snapshots'] == 105
    assert audit['cutoffs']['primary_reasons']['required_side_zero_bid_no_size'] == 95
    assert audit['unresolved_policies']['center_cross']['by_original_status']['excluded_fallback_exit_quote']['events'] == 57
    for key, value in replacements.items():
        page = page.replace(key, value)
    return page


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    out = args.out or args.base / 'index.html'
    with out.open('x') as handle:
        handle.write(render(args.base))
    print(out)


if __name__ == '__main__':
    main()
