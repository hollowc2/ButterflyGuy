"""Render the offline SPX end-of-day 1-DTE study from its frozen derived evidence."""
from __future__ import annotations

import argparse
import html
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'reports/research/spx-1dte-eod-20261112'
SCENARIOS = {'stressed_net': 'Component prices + fees + stress',
             'component_net': 'Component prices + fees',
             'midpoint_net': 'Midpoint + fees · diagnostic'}
DIRECTIONS = {'neutral': 'Neutral at forward proxy', 'day_continue': 'Day continuation',
              'day_fade': 'Day reversal', 'hour_continue': 'Last-hour continuation',
              'hour_fade': 'Last-hour reversal'}


def esc(value: object) -> str:
    return html.escape(str(value))


def money(value: float | None, signed: bool = True) -> str:
    if value is None or not math.isfinite(value):
        return 'Not resolved'
    sign = ('−' if value < 0 else '+' if signed else '')
    return sign + f'${abs(value):,.2f}'


def number(value: float | None, digits: int = 2) -> str:
    return 'Undefined' if value is None or not math.isfinite(value) else f'{value:,.{digits}f}'


def percent(value: float | None) -> str:
    return 'Undefined' if value is None else f'{100 * value:.1f}%'


def table(headers: list[str], rows: list[list[str]], css: str = '') -> str:
    return '<div class="table-wrap ' + css + '"><table><thead><tr>' + ''.join(
        '<th scope="col">' + x + '</th>' for x in headers
    ) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(
        ('<th scope="row">' + v + '</th>') if i == 0 else '<td>' + v + '</td>'
        for i, v in enumerate(row)) + '</tr>' for row in rows) + '</tbody></table></div>'


def metric_row(name: str, m: dict) -> list[str]:
    return [esc(name), str(m['count']), money(m.get('total')), money(m.get('expectancy')),
            percent(m.get('win_rate')), number(m.get('profit_factor')),
            money(m.get('drawdown'), False), str(m.get('unresolved', 0))]


def static_chart(series: list[dict], title: str) -> str:
    """Date-scaled SVG with missing outcomes explicitly omitted by normalization."""
    from datetime import date
    w, h, left, right, top, bottom = 1080, 360, 95, 24, 20, 62
    dates = sorted({p[0] for s in series for p in s['points']})
    if not dates:
        return '<p class="caption">A complete priced path is unavailable.</p>'
    start, end = date.fromisoformat(dates[0]).toordinal(), date.fromisoformat(dates[-1]).toordinal()
    values = [p[1] for s in series for p in s['points']] + [0]
    lo, hi = min(values), max(values)
    pad = max(100, (hi - lo) * .08)
    lo, hi = lo - pad, hi + pad
    def x(d):
        return left + (date.fromisoformat(d).toordinal() - start) / max(1, end - start) * (w - left - right)
    def y(v):
        return top + (hi - v) / (hi - lo) * (h - top - bottom)
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}"><title>{esc(title)}</title>']
    for i in range(5):
        v = lo + i * (hi - lo) / 4
        parts.append(f'<line class="gridline" x1="{left}" x2="{w-right}" y1="{y(v):.2f}" y2="{y(v):.2f}"/><text class="tick" text-anchor="end" x="{left-10}" y="{y(v)+4:.2f}">{money(v)}</text>')
    parts.append(f'<line class="zero" x1="{left}" x2="{w-right}" y1="{y(0):.2f}" y2="{y(0):.2f}"/>')
    for s in series:
        points = ' '.join(f'{x(d):.2f},{y(v):.2f}' for d, v in s['points'])
        parts.append(f'<polyline fill="none" stroke="{s["color"]}" stroke-width="2.5" points="{points}"/>')
    for i in range(5):
        d = dates[round((len(dates) - 1) * i / 4)]
        parts.append(f'<text class="tick" text-anchor="middle" x="{x(d):.2f}" y="{h-34}">{d}</text>')
    parts.append(f'<text class="axis-label" text-anchor="middle" x="{w/2}" y="{h-7}">Terminal date (ET)</text><text class="axis-label" transform="translate(17,{h/2}) rotate(-90)" text-anchor="middle">Cumulative net P&amp;L (USD)</text></svg>')
    return ''.join(parts)


CSS = r'''
:root{--paper:#f6f4ee;--white:#fffef9;--ink:#172f3e;--muted:#61717a;--line:#d6ded9;--teal:#256e6a;--red:#a55149;--wash:#e9efeb;--navy:#244c65}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}a{color:var(--teal);text-underline-offset:3px}header{border-bottom:1px solid var(--line)}.masthead{max-width:1240px;margin:auto;padding:20px 28px;display:flex;justify-content:space-between;gap:16px;font-size:11px;text-transform:uppercase;letter-spacing:.13em}main{max-width:1180px;margin:auto;padding:58px 30px 70px}.eyebrow,.kicker{font-size:11px;font-weight:750;letter-spacing:.15em;text-transform:uppercase;color:var(--teal)}h1,h2,h3{font-family:Georgia,"Times New Roman",serif;font-weight:400;letter-spacing:-.03em;line-height:1.14}h1{font-size:clamp(38px,6vw,72px);max-width:980px;margin:20px 0 26px}h2{font-size:clamp(28px,3.5vw,40px);margin:0 0 24px}h3{font-size:24px;margin:0 0 14px}p{margin:0 0 19px}.lead{font-size:21px;line-height:1.6;max-width:925px;color:#3b5360}.meta,.small,.caption{color:var(--muted);font-size:12px;line-height:1.65}.caption{margin:10px 0 22px}.verdict{margin:34px 0 28px;padding:22px 0;border-top:2px solid var(--ink);border-bottom:1px solid var(--line);display:grid;grid-template-columns:170px 1fr;gap:24px}.verdict b{font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--red)}.verdict p{margin:0}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;margin:30px 0 12px}.stat strong{font-weight:500;font-size:32px;line-height:1.2;display:block;font-variant-numeric:tabular-nums}.stat span{font-size:12px;color:var(--muted);display:block;margin-top:8px}.section{border-top:1px solid var(--line);margin-top:44px;padding-top:46px}.section-head{display:grid;grid-template-columns:45px 1fr;gap:12px}.section-number{font-size:12px;color:var(--muted);padding-top:10px}.section-body{margin-left:57px}.two{display:grid;grid-template-columns:1fr 1fr;gap:38px}.finding{border-top:1px solid var(--ink);padding-top:20px}.big{font-size:36px;font-weight:500;line-height:1.15;font-variant-numeric:tabular-nums;margin:12px 0 18px}.negative{color:var(--red)}.positive{color:var(--teal)}.callout{padding:22px 25px;background:var(--wash);border-left:3px solid var(--teal);margin:25px 0}.callout p:last-child{margin:0}.flow{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;margin:28px 0}.flow>div{padding-top:14px;border-top:2px solid var(--line)}.flow strong{font-size:12px}.flow p{font-size:13px;color:var(--muted);margin:8px 0}.table-wrap{overflow:auto;width:100%;margin:18px 0}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:12px;line-height:1.5}th,td{padding:12px 11px;text-align:right;white-space:nowrap;border-bottom:1px solid var(--line);vertical-align:top}th:first-child,td:first-child{text-align:left}thead th{background:#eeeee6;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:700}tbody th{font-weight:500;max-width:230px;white-space:normal;min-width:135px}.selected-row{background:#eaf0eb}.controls{display:flex;gap:12px;flex-wrap:wrap;align-items:end;margin:22px 0 14px}.controls label{font-size:11px;color:var(--muted);display:flex;flex-direction:column;gap:5px}select,button,.button{font:12px system-ui,sans-serif;padding:10px 12px;border:1px solid #a6b7b5;border-radius:3px;color:var(--ink);background:var(--white)}button,.button{cursor:pointer;text-decoration:none;display:inline-block}button:hover,.button:hover{background:var(--wash)}select:focus-visible,button:focus-visible,a:focus-visible,summary:focus-visible{outline:2px solid var(--teal);outline-offset:3px}.chart{border:1px solid var(--line);background:var(--white);padding:14px 8px}.chart svg{width:100%;height:auto;display:block}.gridline{stroke:#dfe5df;stroke-width:1}.zero{stroke:#acb9b7;stroke-dasharray:4 4}.tick,.axis-label{font:11px system-ui,sans-serif;fill:#61717a}.legend{display:flex;gap:12px 24px;flex-wrap:wrap;margin:15px 0;font-size:11px;color:var(--muted)}.legend span{display:flex;gap:8px;align-items:center}.legend i{display:inline-block;width:22px;height:3px}.scroll-table{max-height:650px;overflow:auto}.scroll-table thead{position:sticky;top:0}details{border-top:1px solid var(--line);padding:18px 0}summary{cursor:pointer;font-size:14px;font-weight:600}details>div,details>p{margin-top:18px}code,pre{font-family:ui-monospace,SFMono-Regular,Consolas,monospace;font-size:12px}pre{background:#eceee6;padding:20px;white-space:pre-wrap;overflow-wrap:anywhere}.source-list{font-size:13px;padding-left:20px}.source-list li{margin-bottom:11px}.toc{display:flex;gap:12px 25px;flex-wrap:wrap;font-size:12px;padding-top:22px}.badge{font-size:10px;text-transform:uppercase;letter-spacing:.05em;border:1px solid var(--line);padding:2px 5px;border-radius:2px}.bar-row{display:grid;grid-template-columns:175px 1fr 110px;gap:12px;align-items:center;font-size:12px;margin:13px 0}.track{height:12px;background:#e2e7df}.track i{height:100%;display:block;background:var(--teal)}.track i.loss{background:var(--red)}footer{border-top:1px solid var(--line);padding-top:22px;margin-top:40px;font-size:12px;color:var(--muted)}.noscript{padding:12px;background:var(--wash)}@media(max-width:740px){main{padding:32px 18px 45px}.masthead{padding:16px 18px;flex-direction:column;font-size:10px}.lead{font-size:18px}.stats{grid-template-columns:1fr 1fr;gap:25px 16px}.stat strong{font-size:27px}.verdict{grid-template-columns:1fr;gap:10px}.section-body{margin-left:0}.section-head{grid-template-columns:26px 1fr;gap:8px}.section{padding-top:32px;margin-top:34px}.two{grid-template-columns:1fr;gap:24px}.flow{grid-template-columns:1fr 1fr;gap:18px}.big{font-size:30px}.controls{gap:12px}.controls label{max-width:100%}select{max-width:100%}.bar-row{grid-template-columns:110px 1fr 92px;font-size:11px}.chart{padding:7px 0}.tick,.axis-label{font-size:13px}}@media print{body{background:white;font-size:11px}main{max-width:none;padding:12px}header,.no-print,.controls{display:none!important}h1{font-size:38px}.section{padding-top:24px;margin-top:26px}.section-body{margin-left:0}.table-wrap{overflow:visible}.scroll-table{max-height:none}th,td{padding:7px}.chart,table,.finding{break-inside:avoid}details>*{display:block}a{color:inherit}.stats{gap:15px}.stat strong{font-size:25px}}
'''


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light"><title>SPX 1-DTE — Buying Tomorrow's Butterfly at the Close</title><style>__CSS__</style></head>
<body><header><div class="masthead"><strong>Butterfly Guy · Research Notebook</strong><span>SPXW / End-of-day 1-DTE / 12 November 2026</span></div></header><main>
<div class="eyebrow">A new horizon · 18 entry rules · 3 exits · 54 policies</div>
<h1>Buy the fly today.<br>Where should tomorrow’s tent be?</h1>
<p class="lead">We tested buying a single SPX butterfly at 15:46 ET, with expiration in the next trading session. The question was whether the day’s move—or its final hour—helps choose the direction and body strike after paying for the trade.</p>
<p class="meta">Development: January 3, 2023–June 28, 2024 · Later temporal check: March 13–September 25, 2026 · Next-session SPXW PM expiry · One fly per eligible entry per policy · All clock times ET</p>
<div class="verdict"><b>__VERDICT_LABEL__</b><p>__VERDICT_TEXT__</p></div>
<div class="stats">__HERO_STATS__</div>
<nav class="toc no-print" aria-label="Report sections"><a href="#selection">Development choice → 2026</a><a href="#results">Explore all 54 policies</a><a href="#mechanics">Direction &amp; placement</a><a href="#coverage">Coverage &amp; gaps</a><a href="#evidence">Evidence &amp; reproduction</a></nav>
<noscript><p class="noscript">The key results, selected-policy chart and full 54-policy stressed table are readable below. Enable JavaScript to switch accounting scenarios, filter policies and inspect the derived ledger.</p></noscript>
<section class="section" id="selection"><div class="section-head"><span class="section-number">01</span><h2>The rule chosen before looking at 2026</h2></div><div class="section-body">
<p>Selection uses only the highest development-period stressed expectancy in initial-risk units among policies with complete outcomes. Ties follow the frozen rule. The later period then tests that same choice. Its most profitable rule is not promoted to the headline after seeing the answer.</p>
<div class="two"><div class="finding"><div class="kicker">Development-selected policy</div><h3>__SELECTED_NAME__</h3><p>__SELECTED_DESCRIPTION__</p><p class="big __SELECTED_COLOR__">__SELECTED_LATER_NET__</p><p class="small">Later-period stressed net · __SELECTED_LATER_COUNT__ completed outcomes</p></div><div class="finding"><div class="kicker">Fair comparison</div><h3>Same dates, same width, neutral body</h3><p>The cash/no-trade benchmark earns $0 with zero exposure. The neutral comparison uses only dates with priced outcomes for both the selected policy and its neutral counterpart. It changes placement while preserving width and exit policy.</p><p class="big">__MATCHED_DELTA__</p><p class="small">Selected minus matched neutral · later period · stressed net</p></div></div>
__SELECTED_TABLE__
<p class="caption">One contract lot per entry; different placements imply different debits and dollar risk. R divides net P&amp;L by initial debit plus opening fee and adverse entry stress. A one-lot dollar curve is not a funded-account return. “Unresolved” is retained as missing, never counted as zero.</p>
<h3>Cumulative net P&amp;L · the unchanged development choice</h3>
<div class="controls no-print"><label>Period<select id="curve-period"><option value="later">Later temporal check · 2026</option><option value="development">Development · 2023–24</option></select></label><label>Accounting scenario<select id="curve-scenario"><option value="stressed_net">Component prices + fees + stress</option><option value="component_net">Component prices + fees</option><option value="midpoint_net">Midpoint + fees · diagnostic</option></select></label></div>
<div class="chart" id="equity">__CHART__</div><div class="legend"><span><i style="background:#256e6a"></i>Development-selected policy</span><span><i style="background:#244c65"></i>Matched-date neutral baseline</span></div>
<p class="caption" id="curve-caption">Terminal-date cumulative US-dollar P&amp;L in the 2026 temporal check. Source: genuine ThetaData SPXW minute NBBO observations and attributed expiry-day SPX close inputs. Missing required outcome data remains unresolved; the chart includes only priced paired outcomes. Drawdown is sampled at terminal outcomes, excluding overnight and intraday marks.</p>
<div class="callout"><p>__READING__</p></div>
</div></section>
<section class="section" id="results"><div class="section-head"><span class="section-number">02</span><h2>Every direction, placement and exit</h2></div><div class="section-body">
<p>Two neutral baselines and sixteen directional constructions produce 18 entry cells. Each receives three exit policies: 09:45, noon, or settlement. These are alternatives on heavily overlapping dates, not 54 independent strategies or a combined portfolio.</p>
<div class="controls no-print"><label>Period<select id="period"><option value="later">Later temporal check · 2026</option><option value="development">Development · 2023–24</option></select></label><label>Exit<select id="exit"><option value="all">All three</option><option value="09:45">09:45</option><option value="12:00">12:00</option><option value="settlement">Settlement</option></select></label><label>Direction rule<select id="direction"><option value="all">All five</option>__DIRECTION_OPTIONS__</select></label><label>Accounting scenario<select id="scenario"><option value="stressed_net">Component prices + fees + stress</option><option value="component_net">Component prices + fees</option><option value="midpoint_net">Midpoint + fees · diagnostic</option></select></label><button type="button" id="download-metrics">Download displayed metrics</button></div>
<p class="small" id="table-note">54 policy cells · later temporal check · stressed accounting · highlighted row is the development choice</p>
<div id="all-results">__ALL_TABLE__</div>
<p class="caption">“Offset” is a multiple of the next-expiry ATM call-plus-put midpoint in SPX points, not standard deviations. Net includes declared costs; “Fallback” counts scheduled quote exits that irrevocably hold to settlement. Complete-cohort totals are not asserted where terminal outcomes remain unpriced. Midpoint results are diagnostics and do not represent demonstrated fills.</p>
<details><summary>Distribution, concentration and calendar-gap breakdown</summary><div id="detail-results">__DETAIL_TABLE__</div><p class="caption">Selected policy under stressed accounting. Top-three-removed net measures concentration, not an out-of-sample test. One calendar day means literal following-day expiry; longer gaps include weekends and holidays. These subsets are descriptive and were not used to select another rule.</p>__CALENDAR_TABLE__</details>
<details><summary>Monthly results for the unchanged development choice</summary>__MONTHLY_TABLE__</details>
<details><summary>Inspect the derived selected-policy ledger</summary><div class="controls no-print"><label>Period<select id="ledger-period"><option value="later">Later temporal check · 2026</option><option value="development">Development · 2023–24</option></select></label><button id="download-ledger" type="button">Download selected-policy records</button></div><div id="ledger" class="table-wrap scroll-table"></div><p class="caption">Only derived per-trade values are embedded. Original vendor quotes are not redistributed by this HTML. The linked journal preserves all policy outcomes and exclusions.</p></details>
</div></section>
<section class="section" id="mechanics"><div class="section-head"><span class="section-number">03</span><h2>Direction comes from the body strike</h2></div><div class="section-body">
<div class="flow"><div><strong>01 · Observe at 15:45</strong><p>Compare the day’s move or the last hour’s move using observations available by the decision time.</p></div><div><strong>02 · Place the tent</strong><p>Stay neutral, follow the move or fade it. Move the body 0.5× or 1.0× the observed ATM-straddle scale.</p></div><div><strong>03 · Buy at 15:46</strong><p>Buy one lower call, sell two body calls and buy one upper call. Use 20- or 40-point symmetric wings.</p></div><div><strong>04 · Resolve tomorrow</strong><p>Attempt the fixed 09:45 or noon exit, or hold to the expiration close. Missing scheduled exits follow the declared fallback.</p></div></div>
<p>Every cell uses calls. A body above today’s price seeks a higher terminal price; a body below it seeks a lower one. Choosing CALL versus PUT is not the direction signal. Equal-strike call and put butterflies share the same expiration payoff, while quoted trading costs can differ. <a href="https://www.optionseducation.org/strategies/all-strategies/long-call-butterfly">OIC butterfly construction</a>.</p>
__SIGNAL_DESCRIPTION__
<div class="callout"><p><strong>A direction forecast is not enough.</strong> A long fly needs price to finish near its body. Passing through that level or moving too far in the correct direction can still lose the debit. Overnight time decay also depends on where price is relative to the tent.</p></div>
<p>For body K, wing width W and settlement S, the terminal value is <code>100 × max(0, W − |S − K|)</code>. Subtract the actual modeled opening debit and declared opening costs. A settlement is a terminal contract outcome, not an invented closing-order fill.</p>
<h3>What a modeled dollar contains</h3>
__COST_TABLE__
<p class="caption">Component entry: lower ask − 2×body bid + upper ask. Component liquidation: lower bid − 2×body ask + upper bid, retaining signed negative values. Individual quote observations do not demonstrate a simultaneous executable complex-order fill. Unknown quote-update age, latency, rejections and partial fills are not modeled. Exchange/regulatory/exercise charges beyond the stated fee assumption require broker-specific verification.</p>
</div></section>
<section class="section" id="coverage"><div class="section-head"><span class="section-number">04</span><h2>What the archive can—and cannot—tell us</h2></div><div class="section-body">
__COVERAGE_INTRO__
__COVERAGE_TABLE__
<p>A raw late-day row is not enough. Scheduled early closes are excluded from a fixed 15:45 entry rule even when the archive continues emitting minute-grid observations. Entry admission must be independent of tomorrow’s exit availability. A missing timed exit triggers irrevocable settlement fallback, with counts reported above; missing settlement evidence remains unresolved.</p>
<div class="two"><div><h3>One night and one trading session differ</h3><p>Friday→Monday is one session to expiry but three calendar days. Holiday gaps are longer again. The report keeps these trades and also breaks out literal following-day expiry. No overnight option prices or protective stop fills are fabricated. Settlement positions overlap the next 15:46 entry by about 14 minutes on ordinary sessions. No capital, overlap-risk or funded-account-return model is supplied.</p></div><div><h3>History is already familiar</h3><p>The later window is a temporal stability check on dates exposed in prior research. The protected July 2024–March 2026 interval is not used. Neither the split nor this new strategy restores an untouched holdout.</p></div></div>
<details><summary>Every exclusion and unresolved case</summary>__EXCLUSIONS__<p class="caption">Reasons are not losses or no-trade days. Different geometry can have different entry eligibility; use the matched neutral comparison for placement attribution. No missing terminal value is substituted with zero.</p></details>
<p>NDX and XSP have only 0-DTE sets in the inspected archive, so this report makes no 1-DTE profitability claim for either. Earlier XSP research rejected its exact tested same-day policies; changing the holding horizon would require genuine new quotes and a separately attributable experiment.</p>
</div></section>
<section class="section" id="evidence"><div class="section-head"><span class="section-number">05</span><h2>The decision and its next test</h2></div><div class="section-body">
<p>__NEXT_DECISION__</p><p>The bounded first pass records all 54 policy cells. A favorable retrospective cell would justify freezing a specific rule and observing fresh next-session data and complex-order fills. It would not authorize activating a bot. No runtime strategy, trading limit, order route, paper/live setting, credential or service was changed.</p>
__VERIFICATION__
<details open><summary>Reproduce and inspect the evidence</summary><ul class="source-list">__ARTIFACT_LINKS__</ul><pre>__COMMANDS__</pre></details>
<details><summary>Official contract sources and prior research</summary><ul class="source-list"><li><a href="https://www.cboe.com/tradable-products/sp-500/spx-options/spx-specifications">Cboe SPX contract specifications</a>: $100 multiplier; expiring SPXW ordinarily stops trading at 16:00 ET, or 13:00 on half-days.</li><li><a href="https://www.cboe.com/tradable_products/sp_500/spx_weekly_options/specifications/">Cboe SPX Weeklys product comparison</a>: SPXW is PM-settled, cash-settled and European-style. Match the actual root; AM-settled SPX/SPXO contracts are a different horizon.</li><li><a href="https://cdn.cboe.com/resources/regulation/circulars/regulatory/RG17-054.pdf">Cboe SPXW settlement circular</a>: SPXW uses the official SPX closing price and has no separate settlement symbol. The <a href="https://cdn.cboe.com/resources/spx/spx-fact-sheet.pdf">SPX fact sheet</a> describes component closing-price settlement.</li><li><a href="https://www.cboe.com/about/hours/us-options/">Cboe trading hours and holidays</a>: actual session calendars govern entry and expiration. Exchange sessions do not establish broker access or archival coverage.</li><li><a href="https://datashop.cboe.com/faqs">Cboe DataShop FAQ</a>: Tuesday and Thursday SPX expirations began in April and May 2022. Older files do not imply all-weekday eligibility.</li><li><a href="https://www.optionseducation.org/strategies/all-strategies/long-call-butterfly">Options Industry Council long-call butterfly</a>: equal-wing construction and expiration payoff. Its generic American-style assignment discussion does not apply to European SPXW.</li><li><a href="../../../docs/research/thetadata-local-backtesting.md">Existing 1-DTE replay mechanics</a> and <a href="../../../docs/research/ernie-comparison-2026-10-01/PLAN.md">prior unrun Time Warp proposal</a>. A prior single-trade mechanics replay establishes lifecycle support, not an edge.</li><li><a href="../../../docs/research/xsp-independent-research-2026-11-12.md">Completed XSP research decision</a>. No synthetic SPX-scaled quote substitution is used here.</li></ul><p class="caption">Official pages checked November 12, 2026. Strategy conclusions come from this study’s evidence, not promotional returns or web anecdotes.</p></details>
</div></section><footer><p>Butterfly Guy · End-of-day SPXW 1-DTE research · November 12, 2026</p><p>This page is self-contained and works offline. Linked manifests, CSVs and source files require the accompanying repository. Charts and tables are derived research outcomes, not actual broker fills.</p></footer>
</main><script id="report-data" type="application/json">__DATA__</script><script>__JS__</script></body></html>'''


def policy_name(policy: str, short: bool = False) -> str:
    signal, offset, width, exit_rule = policy.split('|')
    direction = DIRECTIONS.get(signal, signal)
    placement = 'ATM body' if signal == 'neutral' else f'{float(offset):g}× straddle'
    return f'{direction} · {placement} · {width}-wide' + ('' if short else f' · {exit_rule}')


def aggregate(rows: list[dict], key: str) -> dict:
    complete = sorted((r for r in rows if r['status'] == 'completed' and r.get(key) is not None), key=lambda r: (r['exit_time'], r['date']))
    values = [r[key] for r in complete]
    accepted = sum(r.get('debit') is not None for r in rows)
    n = len(values)
    wins, losses = [v for v in values if v > 0], [v for v in values if v < 0]
    cumulative = peak = drawdown = 0.
    for v in values:
        cumulative += v
        peak = max(peak, cumulative)
        drawdown = max(drawdown, peak - cumulative)
    def average(a):
        return sum(a) / len(a) if a else None
    return {'count': n, 'entries': accepted, 'unresolved': accepted - n, 'attempts': len(rows),
            'excluded': len(rows) - accepted, 'total': sum(values) if n else None,
            'expectancy': average(values), 'win_rate': len(wins) / n if n else None,
            'profit_factor': sum(wins) / -sum(losses) if losses else None,
            'average_win': average(wins), 'average_loss': average(losses),
            'drawdown': drawdown if n else None, 'mean_r': average([r[key] / r['initial_risk'] for r in complete]),
            'worst': min(values) if n else None, 'best': max(values) if n else None,
            'top5_removed': sum(values) - sum(sorted(values, reverse=True)[:5]) if n else None,
            'median': sorted(values)[n // 2] if n % 2 else (sorted(values)[n // 2 - 1] + sorted(values)[n // 2]) / 2 if n else None,
            'next_day': sum(r.get('calendar_days') == 1 for r in complete),
            'long_gap': sum(r.get('calendar_days', 0) > 1 for r in complete)}


def load_evidence(base: Path, run_name: str) -> dict:
    import csv
    from collections import Counter
    run = base / run_name
    summary = json.loads((run / 'summary.json').read_text())
    specification = json.loads((run / 'specification.json').read_text())
    selection = summary['selection']['policy']
    if not selection:
        raise ValueError('No development policy was selected; report adapter needs explicit unavailable handling')
    _, _, width, exit_rule = selection.split('|')
    neutral = f'neutral|0|{width}|{exit_rule}'
    scalar = list(csv.DictReader((run / 'journal.csv').open()))
    rows = []
    for r in scalar:
        def f(k):
            value = r.get(k, '')
            return float(value) if value and math.isfinite(float(value)) else None
        rows.append({'period': 'later' if r['period'] == 'comparison' else r['period'],
                     'date': r['date'], 'expiration': r['expiration'], 'policy': r['policy'],
                     'signal': r['signal'], 'offset': f('offset'), 'width': f('width'), 'exit': r['exit'],
                     'status': r['status'], 'entry_time': r.get('entry_time'),
                     'exit_time': r.get('exit_time') or '', 'debit': f('debit'), 'center': f('center'),
                     'initial_risk': f('initial_risk'), 'calendar_days': f('calendar_days'),
                     'stressed_net': f('pnl'), 'component_net': f('pnl_component'), 'midpoint_net': f('pnl_mid')})
    policies = sorted({r['policy'] for r in rows})
    if len(policies) != 54:
        raise ValueError(f'Expected frozen54 policies, found{len(policies)}')
    metrics = {}
    for period in ('development', 'later'):
        metrics[period] = {}
        for policy in policies:
            selected = [r for r in rows if r['period'] == period and r['policy'] == policy]
            metrics[period][policy] = {key: aggregate(selected, key) for key in SCENARIOS}
            source = summary['comparison' if period == 'later' else period][policy]
            derived = metrics[period][policy]['stressed_net']
            assert derived['count'] == source['completed']
            assert derived['unresolved'] == source['unresolved']
            if derived['total'] is not None:
                assert abs(derived['total'] - source['total_pnl']) < 1e-6
    paired, curves, calendar = {}, {}, {}
    selected_rows = [r for r in rows if r['policy'] == selection]
    embedded_rows = [r for r in rows if r['policy'] in (selection, neutral)]
    for period in ('development', 'later'):
        paired[period], curves[period], calendar[period] = {}, {}, {}
        s = [r for r in selected_rows if r['period'] == period]
        b = {r['date']: r for r in rows if r['period'] == period and r['policy'] == neutral and r['status'] == 'completed'}
        pairs = [(r, b[r['date']]) for r in s if r['status'] == 'completed' and r['date'] in b]
        for key in SCENARIOS:
            candidate, benchmark = [p[0] for p in pairs], [p[1] for p in pairs]
            paired[period][key] = {'selected': aggregate(candidate, key), 'neutral': aggregate(benchmark, key),
                                   'delta': sum(a[key] - b[key] for a, b in pairs) if pairs else None}
            series = []
            for label, data, color in [('Development-selected policy', candidate, '#256e6a'), ('Matched-date neutral baseline', benchmark, '#244c65')]:
                c = 0.
                points = []
                for row in sorted(data, key=lambda r: (r['exit_time'], r['date'])):
                    c += row[key]
                    points.append([row['exit_time'][:10], c])
                series.append({'name': label, 'points': points, 'color': color})
            curves[period][key] = series
        for name, group in [('Literal next calendar day', [r for r in s if r['calendar_days'] == 1]),
                            ('Weekend / holiday gap', [r for r in s if r['calendar_days'] > 1])]:
            calendar[period][name] = aggregate(group, 'stressed_net')
    statuses = {period: dict(Counter(r['status'] for r in rows if r['period'] == period)) for period in ('development', 'later')}
    verification = json.loads((run / 'verification.json').read_text()) if (run / 'verification.json').exists() else None
    review = json.loads((run / 'independent-review.json').read_text()) if (run / 'independent-review.json').exists() else None
    return {'run_name': run_name, 'summary': summary, 'specification': specification,
            'selection': selection, 'neutral': neutral, 'policies': policies, 'metrics': metrics,
            'rows': embedded_rows, 'paired': paired, 'curves': curves, 'calendar': calendar,
            'statuses': statuses, 'verification': verification, 'review': review,
            'coverage': json.loads((base / 'coverage/summary.json').read_text())}


JS = r'''
'use strict';
const D=JSON.parse(document.getElementById('report-data').textContent);
const money=v=>v===null||v===undefined?'Not resolved':(v<0?'−':'+')+'$'+Math.abs(v).toLocaleString('en-US',{minimumFractionDigits:2,maximumFractionDigits:2});
const num=(v,d=2)=>v===null||v===undefined?'Undefined':v.toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});
const pct=v=>v===null||v===undefined?'Undefined':(v*100).toFixed(1)+'%';
const clean=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const name=p=>{const [s,o,w,e]=p.split('|');return D.directions[s]+' · '+(s==='neutral'?'ATM':o+'× straddle')+' · '+w+'w · '+e};
function current(){const period=document.getElementById('period').value,scenario=document.getElementById('scenario').value,e=document.getElementById('exit').value,d=document.getElementById('direction').value;return{period,scenario,policies:D.policies.filter(p=>{const a=p.split('|');return(e==='all'||a[3]===e)&&(d==='all'||a[0]===d)})}}
function drawTable(){const {period,scenario,policies}=current();document.getElementById('table-note').textContent=policies.length+' of54 policy cells · '+(period==='later'?'later temporal check':'development')+' · '+D.scenarios[scenario]+' · highlighted row is the development choice';let t='<div class="table-wrap scroll-table"><table><thead><tr><th>Direction / body offset</th><th>Wing width</th><th>Exit</th><th>Completed / admitted</th><th>Unresolved</th><th>Priced net¹</th><th>Expectancy¹</th><th>Win rate¹</th><th>Profit factor¹</th><th>Mean R¹</th><th>Paired neutral Δ / trade²</th></tr></thead><tbody>';for(const p of policies){const [s,o,w,e]=p.split('|'),m=D.metrics[period][p][scenario],b=D.paired_delta[period][p][scenario];t+='<tr'+(p===D.selection?' class="selected-row"':'')+'><th>'+clean(D.directions[s])+'<br><span class="small">'+(s==='neutral'?'ATM body':o+'× straddle')+(p===D.selection?' · DEV CHOICE':'')+'</span></th><td>'+w+' pts</td><td>'+e+'</td><td>'+m.count+' / '+m.entries+'</td><td>'+m.unresolved+'</td><td class="'+(m.total<0?'negative':'positive')+'">'+money(m.total)+(m.unresolved?'*':'')+'</td><td>'+money(m.expectancy)+'</td><td>'+pct(m.win_rate)+'</td><td>'+num(m.profit_factor)+'</td><td>'+num(m.mean_r,3)+'</td><td>'+money(b)+'</td></tr>'}document.getElementById('all-results').innerHTML=t+'</tbody></table></div>'}
function drawCurve(){const p=document.getElementById('curve-period').value,k=document.getElementById('curve-scenario').value,series=D.curves[p][k],dates=[...new Set(series.flatMap(s=>s.points.map(p=>p[0])))].sort();if(!dates.length){document.getElementById('equity').textContent='A complete priced path is unavailable.';return}const narrow=innerWidth<740,W=narrow?590:1080,H=narrow?340:360,L=95,R=24,T=20,B=62,start=Date.parse(dates[0]),end=Date.parse(dates.at(-1)),values=[0,...series.flatMap(s=>s.points.map(p=>p[1]))],low=Math.min(...values),high=Math.max(...values),pad=Math.max(100,(high-low)*.08),lo=low-pad,hi=high+pad,x=d=>L+(Date.parse(d)-start)/Math.max(1,end-start)*(W-L-R),y=v=>T+(hi-v)/(hi-lo)*(H-T-B);let s=`<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Cumulative net P and L, US dollars by terminal date"><title>${clean(D.scenarios[k])} cumulative net P and L by terminal date</title>`;for(let i=0;i<5;i++){const v=lo+(hi-lo)*i/4;s+=`<line class="gridline" x1="${L}" x2="${W-R}" y1="${y(v)}" y2="${y(v)}"/><text class="tick" text-anchor="end" x="${L-10}" y="${y(v)+4}">${money(v)}</text>`}s+=`<line class="zero" x1="${L}" x2="${W-R}" y1="${y(0)}" y2="${y(0)}"/>`;for(const q of series)s+=`<polyline fill="none" stroke="${q.color}" stroke-width="2.5" points="${q.points.map(p=>x(p[0])+','+y(p[1])).join(' ')}"/>`;for(let i=0;i<5;i++){const d=dates[Math.round((dates.length-1)*i/4)];s+=`<text class="tick" text-anchor="middle" x="${x(d)}" y="${H-34}">${d}</text>`}s+=`<text class="axis-label" text-anchor="middle" x="${W/2}" y="${H-7}">Terminal date (ET)</text><text class="axis-label" transform="translate(17,${H/2}) rotate(-90)" text-anchor="middle">Cumulative net P&amp;L (USD)</text></svg>`;document.getElementById('equity').innerHTML=s;document.getElementById('curve-caption').textContent=(p==='later'?'2026 later temporal check':'2023–24 development')+' · '+D.scenarios[k]+'. Source: genuine ThetaData SPXW minute NBBO observations and attributed expiry-day SPX close inputs. Only matched-date priced terminal outcomes are plotted; these are alternatives, not a portfolio. Drawdown excludes intraday and overnight marks.'}
function ledger(){const period=document.getElementById('ledger-period').value,rows=D.rows.filter(r=>r.period===period&&r.policy===D.selection).sort((a,b)=>a.date.localeCompare(b.date));let s='<table><thead><tr><th>Entry date</th><th>Expiry</th><th>Body</th><th>Debit pts</th><th>Status</th><th>Stressed net</th></tr></thead><tbody>';for(const r of rows)s+='<tr><th>'+r.date+'</th><td>'+r.expiration+'</td><td>'+num(r.center,0)+'</td><td>'+num(r.debit)+'</td><td>'+clean(r.status.replaceAll('_',' '))+'</td><td>'+money(r.stressed_net)+'</td></tr>';document.getElementById('ledger').innerHTML=s+'</tbody></table>'}
function download(rows,filename){if(!rows.length)return;const keys=Object.keys(rows[0]),q=v=>'"'+String(v??'').replaceAll('"','""')+'"',csv=[keys.map(q).join(','),...rows.map(r=>keys.map(k=>q(r[k])).join(','))].join('\r\n'),url=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
for(const id of ['period','scenario','exit','direction'])document.getElementById(id).addEventListener('change',drawTable);for(const id of ['curve-period','curve-scenario'])document.getElementById(id).addEventListener('change',drawCurve);document.getElementById('ledger-period').addEventListener('change',ledger);document.getElementById('download-metrics').addEventListener('click',()=>{const c=current();download(c.policies.map(p=>({period:c.period,policy:p,scenario:c.scenario,...D.metrics[c.period][p][c.scenario]})),'spx-1dte-displayed-metrics.csv')});document.getElementById('download-ledger').addEventListener('click',()=>download(D.rows.filter(r=>r.period===document.getElementById('ledger-period').value&&r.policy===D.selection),'spx-1dte-selected-policy.csv'));drawTable();drawCurve();ledger();window.addEventListener('resize',drawCurve);
'''


def render(base: Path, run_name: str = 'run-02') -> str:
    d = load_evidence(base, run_name)
    selected, metrics = d['selection'], d['metrics']
    dev, later = (metrics[p][selected]['stressed_net'] for p in ('development', 'later'))
    _, offset, width, exit_rule = selected.split('|')
    qualifying = [p for p in d['policies'] if metrics['development'][p]['stressed_net']['count'] >= 100 and
                  metrics['development'][p]['stressed_net']['count'] / max(1, metrics['development'][p]['stressed_net']['entries']) >= .95]
    positive_partial = sum(metrics['development'][p]['stressed_net']['expectancy'] is not None and metrics['development'][p]['stressed_net']['expectancy'] > 0 for p in d['policies'])
    qualifying_positive = sum(metrics['development'][p]['stressed_net']['expectancy'] > 0 for p in qualifying)
    settlement_negative = sum(metrics['development'][p]['stressed_net']['expectancy'] < 0 for p in d['policies'] if p.endswith('|settlement'))
    unresolved = sum(m['stressed_net']['unresolved'] for period in metrics.values() for m in period.values())
    decision = 'Reject as tested' if dev['expectancy'] <= 0 and dev['unresolved'] == 0 else 'Insufficient evidence'
    paired_delta = {}
    for period in ('development', 'later'):
        paired_delta[period] = {}
        source_rows = [r for r in d['rows'] if r['period'] == period]
        # Full-policy paired deltas use original summary for stressed case. Other
        # scenarios are derived from CSV, retaining common completed entry dates.
        import csv
        raw = list(csv.DictReader((base / run_name / 'journal.csv').open()))
        by_policy = {}
        for row in raw:
            source_period = 'later' if row['period'] == 'comparison' else row['period']
            if source_period == period and row['status'] == 'completed':
                by_policy.setdefault(row['policy'], {})[row['date']] = row
        for policy in d['policies']:
            _, _, w, ex = policy.split('|')
            a, b = by_policy.get(policy, {}), by_policy.get(f'neutral|0|{w}|{ex}', {})
            common = sorted(set(a) & set(b))
            paired_delta[period][policy] = {
                key: sum(float(a[t][col]) - float(b[t][col]) for t in common) / len(common) if common else None
                for key, col in [('stressed_net', 'pnl'), ('component_net', 'pnl_component'), ('midpoint_net', 'pnl_mid')]
            }
        assert len(source_rows) > 0
    all_rows = []
    for policy in d['policies']:
        signal, o, w, e = policy.split('|')
        m = metrics['later'][policy]['stressed_net']
        label = esc(DIRECTIONS[signal]) + '<br><span class="small">' + ('ATM body' if signal == 'neutral' else o + '× straddle') + (' · DEV CHOICE' if policy == selected else '') + '</span>'
        all_rows.append([label, w + ' pts', e, f'{m["count"]} / {m["entries"]}', str(m['unresolved']),
                         money(m['total']) + ('*' if m['unresolved'] else ''), money(m['expectancy']), percent(m['win_rate']), number(m['profit_factor']), number(m['mean_r'], 3), money(paired_delta['later'][policy]['stressed_net'])])
    headers = ['Direction / body offset', 'Wing width', 'Exit', 'Completed / admitted', 'Unresolved', 'Priced net¹', 'Expectancy¹', 'Win rate¹', 'Profit factor¹', 'Mean R¹', 'Paired neutral Δ / trade²']
    selected_rows = []
    for period, title in [('development', 'Development · 2023–24'), ('later', 'Later check · 2026')]:
        selected_rows.append(metric_row(title + ' · selected', metrics[period][selected]['stressed_net']))
        matched = d['paired'][period]['stressed_net']
        selected_rows.append(metric_row(title + ' · matched neutral', matched['neutral']))
    selected_table = table(['Cohort / policy', 'Priced trades', 'Net USD', 'Expectancy', 'Win rate', 'Profit factor', 'Terminal drawdown', 'Unresolved'], selected_rows)
    selected_table += '<p class="caption">Selected rows use their full accepted cohorts; neutral rows use the common priced dates. The matched selected/neutral counts are ' + str(d['paired']['development']['stressed_net']['selected']['count']) + ' in development and ' + str(d['paired']['later']['stressed_net']['selected']['count']) + ' later. Matched differences above and below use those common cohorts.</p>'
    details = []
    for p, title in [('development', 'Development'), ('later', 'Later 2026')]:
        m = metrics[p][selected]['stressed_net']
        source = d['summary']['development' if p == 'development' else 'comparison'][selected]
        details.append([title, money(m['average_win']), money(m['average_loss']), money(m['worst']), money(m['best']), money(m['top5_removed']), number(m['mean_r'], 3), number(source['avg_exposure_hours'], 1) + ' hours'])
    detail_table = table(['Period', 'Average win', 'Average loss', 'Worst trade', 'Best trade', 'Top 5 wins removed', 'Mean R', 'Average exposure'], details)
    detail_table += '<p class="caption">Average R and dollar expectancy can have different signs when each one-lot trade has a different debit. Selection used dollar expectancy; positive mean R does not overturn negative dollar results. Exposure includes weekends. Top-five removal is measured without replacing those trades.</p>'
    calendar_rows = []
    for p, title in [('development', 'Development'), ('later', 'Later 2026')]:
        for name, m in d['calendar'][p].items():
            calendar_rows.append([title + ' · ' + name, str(m['count']), money(m['total']), money(m['expectancy']), percent(m['win_rate'])])
    calendar_table = table(['Period / calendar gap', 'Trades', 'Stressed net', 'Expectancy', 'Win rate'], calendar_rows)
    monthly_rows = []
    for p in ('development', 'comparison'):
        for month, m in d['summary'][p][selected]['months'].items():
            monthly_rows.append([month, str(m['n']), money(m['pnl'])])
    monthly_table = table(['Entry month (ET)', 'Trades', 'Selected-policy stressed net USD'], monthly_rows)
    cost_rows = []
    for p, title in [('development', 'Development'), ('later', 'Later 2026')]:
        m = metrics[p][selected]
        # Explicit names avoid relying on dict iteration order for accounting.
        stress = m['stressed_net']['expectancy']
        component = m['component_net']['expectancy']
        midpoint = m['midpoint_net']['expectancy']
        heavy = stress - 15 * (1 if exit_rule == 'settlement' else 2)
        cost_rows.append([title, money(midpoint), money(component - midpoint), money(component), money(stress - component), money(stress), money(heavy)])
    cost_table = table(['Selected policy / period', 'Midpoint + fees', 'Component spread drag', 'Component + fees', 'Added $5 / transaction', 'Primary stressed', '$20 / transaction stress'], cost_rows)
    cost_table += '<p class="caption">All cells above are average US dollars per completed fly. Assumed commission is $0.65 × four contracts = $2.60 per transaction. Primary stress is 0.05 <strong>net fly point</strong> = $5 per transaction; the heavier sensitivity is 0.20 net fly point = $20 per transaction, equivalent to $0.05 adverse price per each of four contracts. Settlement pays opening assumptions only. Midpoint already includes fees; spread drag is its difference from component accounting.</p>'
    coverage_rows = []
    for key, count in d['summary']['session_counts'].items():
        p, status = key.split('|', 1)
        coverage_rows.append([('Development' if p == 'development' else 'Later 2026') + ' · ' + status.replace('_', ' '), str(count)])
    coverage_table = table(['Session-level audit', 'Distinct entry sessions'], coverage_rows)
    exclusions = table(['Policy-record status', 'Development records', 'Later 2026 records'],
                       [[esc(status.replace('_', ' ')), str(d['statuses']['development'].get(status, 0)), str(d['statuses']['later'].get(status, 0))]
                        for status in sorted(set(d['statuses']['development']) | set(d['statuses']['later']))])
    exclusions += '<p class="caption">A policy record is one date × one of 54 alternatives, so these counts repeat sessions. Session-level exclusions above occur before those policy records are generated. “Completed” means a modeled terminal price is available; it does not mean a broker order filled.</p>'
    positive_warning = f'{positive_partial} policies show positive development expectancy on their priced subsets, but none passes the frozen combination of at least 100 completed trades and 95% entry completion with a positive result. The incomplete timed-exit subsets cannot establish profitable complete strategies.'
    reading = f'<strong>The spread changes the development answer.</strong> The selected policy looks positive at midpoint ({money(metrics["development"][selected]["midpoint_net"]["expectancy"])}/fly after assumed fees), turns negative with component prices ({money(metrics["development"][selected]["component_net"]["expectancy"])}/fly), and averages {money(dev["expectancy"])}/fly with primary stress. In 2026 it is negative even at midpoint. {positive_warning}'
    verification = '<p><strong>Verification:</strong> The study’s focused tests and an independent raw-leg accounting reconciliation are linked below. See the verification record for exact commands, results and browser checks.</p>'
    links = [
        (f'{run_name}/specification.json', 'Frozen specification and 54-policy trial matrix'),
        (f'{run_name}/locked-selection.json', 'Development selection locked before later quote processing'),
        (f'{run_name}/manifest.json', 'Run manifest, source hashes, input hashes and environment'),
        (f'{run_name}/summary.json', 'All policy metrics'),
        (f'{run_name}/journal.csv', 'Full scalar journal · CSV'),
        (f'{run_name}/session-audit.jsonl', 'Session audit and exclusions'),
        (f'{run_name}/independent-review.json', 'Independent review and heavier cost sensitivity'),
        (f'{run_name}/independent-accounting-check.json', 'Independent per-leg accounting checks'),
        (f'{run_name}/verification.json', 'Tests, lint, graph and desktop/mobile verification'),
        ('coverage/audit.md', 'Coverage audit'), ('coverage/summary.json', 'Coverage source hashes and counts'),
        ('design.md', 'Research design and prior-work review'),
        ('../../../tools/research_studies/one_dte_eod.py', 'Research runner source'),
        ('../../../tools/research_studies/render_one_dte_report.py', 'HTML renderer source'),
        ('../../../tests/test_one_dte_eod.py', 'Focused mechanics tests')]
    if (base / run_name / 'verification.json').exists():
        verification += '<p class="caption">The linked verification record was available when this page was rendered. Full details remain in that record rather than an unstamped manual claim.</p>'
    embedded = {'selection': selected, 'policies': d['policies'], 'metrics': metrics, 'directions': DIRECTIONS,
                'scenarios': SCENARIOS, 'paired_delta': paired_delta, 'curves': d['curves'], 'rows': d['rows']}
    data = json.dumps(embedded, allow_nan=False, separators=(',', ':')).replace('</', '<\\/')
    replacements = {
        '__CSS__': CSS, '__JS__': JS, '__DATA__': data,
        '__VERDICT_LABEL__': decision,
        '__VERDICT_TEXT__': f'No qualifying policy passed the development criterion. The best eligible rule—day continuation, {float(offset):g}× straddle offset, {width}-point wings, held to settlement—returned <strong>{money(dev["total"])}</strong> on {dev["count"]} development entries, then <strong class="negative">{money(later["total"])}</strong> on {later["count"]} later entries. All {settlement_negative} settlement policies lost in development. Incomplete morning/noon policies remain insufficient evidence.',
        '__HERO_STATS__': ''.join('<div class="stat"><strong'+(' class="negative"' if i in (1, 2) else '')+'>'+v+'</strong><span>'+label+'</span></div>' for i, (v, label) in enumerate([
            (f'{qualifying_positive} / {len(qualifying)}', 'Positive policies passing the development coverage screen'),
            (money(dev['expectancy']), 'Selected rule · development stressed expectancy per fly'),
            (money(later['expectancy']), 'Same rule · 2026 stressed expectancy per fly'),
            (f'{unresolved:,}', 'Unpriced timed-exit records across overlapping policy trials') ])),
        '__SELECTED_NAME__': esc(policy_name(selected, short=True)),
        '__SELECTED_DESCRIPTION__': 'Follow the sign of the option-derived forward change from 09:35 to 15:45. Place the body half an ATM-straddle premium in that direction, round to the nearest 5-point strike, and hold the 40-point-wing fly to the next-session PM close.',
        '__SELECTED_COLOR__': 'negative' if later['total'] < 0 else 'positive',
        '__SELECTED_LATER_NET__': money(later['total']), '__SELECTED_LATER_COUNT__': str(later['count']),
        '__MATCHED_DELTA__': money(d['paired']['later']['stressed_net']['delta']),
        '__SELECTED_TABLE__': selected_table, '__CHART__': static_chart(d['curves']['later']['stressed_net'], 'Development-selected versus matched neutral cumulative stressed P&L, 2026'),
        '__READING__': reading, '__DIRECTION_OPTIONS__': ''.join(f'<option value="{k}">{esc(v)}</option>' for k, v in DIRECTIONS.items()),
        '__ALL_TABLE__': table(headers, all_rows, 'scroll-table'), '__DETAIL_TABLE__': detail_table,
        '__CALENDAR_TABLE__': calendar_table, '__MONTHLY_TABLE__': monthly_table,
        '__SIGNAL_DESCRIPTION__': '<p>“Day” compares 09:35 with 15:45; “last hour” compares 14:45 with 15:45. Continuation follows that change; reversal takes the opposite sign. Inputs use a <strong>zero-carry forward proxy</strong>: the median of <code>K + call mid − put mid</code> from three to five nearby low-cost straddles, with cross-pair dispersion capped at two SPX points. This is option-derived evidence, not observed official SPX spot. The placement scale is the nearest selected pair’s call-plus-put midpoint. Missing inputs and exact-zero direction signals exclude that cell; neither is invented as a neutral prediction.</p>',
        '__COST_TABLE__': cost_table,
        '__COVERAGE_INTRO__': f'<p>The independent audit found {d["coverage"]["files_inspected"]:,} unprotected genuine SPXW 1-DTE entry files with matching expiry-day 0-DTE files available. The experiment deliberately narrows that archive to the frozen periods below. The catalog contains no NDXP/XSP 1-DTE set. Raw option data has no underlying price, IV or Greeks, so signals use the explicitly labeled parity proxy.</p>',
        '__COVERAGE_TABLE__': coverage_table, '__EXCLUSIONS__': exclusions,
        '__NEXT_DECISION__': '<strong>Reject the tested complete settlement policies under these assumptions.</strong> None earned positive stressed development expectancy. The unchanged development choice then deteriorated in 2026 and underperformed its matched neutral baseline. Morning/noon policies with unresolved exits need complete terminal treatment before their economic results can be judged. If revisiting this horizon, freeze one materially new mechanism or execution hypothesis and obtain fresh evidence; another search over these inspected dates does not create validation.',
        '__VERIFICATION__': verification,
        '__ARTIFACT_LINKS__': ''.join(f'<li><a href="{path}">{label}</a></li>' for path, label in links),
        '__COMMANDS__': esc('uv run python -m tools.research_studies.one_dte_eod --out /tmp/spx-1dte-new-run --workers 4\nuv run pytest tests/test_one_dte_eod.py -q\nuv run python -m tools.research_studies.render_one_dte_report \\\n  --base reports/research/spx-1dte-eod-20261112 --run run-02\n\nThe runner requires the existing local licensed quote archive and attributed daily receipt.\nUse a new output directory; prior run evidence is immutable.')}
    page = PAGE
    for key, value in replacements.items():
        page = page.replace(key, value)
    if '__' in page:
        import re
        assert not re.search(r'__[A-Z_]+__', page), 'Unexpanded template token'
    # Final descriptions follow actual runner semantics: timed exits are exact
    # snapshots, missing terminal prices remain unresolved, no fallback exists.
    page = page.replace('highest development-period stressed expectancy in initial-risk units among policies with complete outcomes', 'highest development-period stressed dollar expectancy among policies with at least 100 completed outcomes and at least 95% completion of admitted entries')
    page = page.replace('“Fallback” counts scheduled quote exits that irrevocably hold to settlement.', '¹ Metrics describe priced outcomes; an asterisk marks a conditional total with unresolved accepted entries. ² Paired deltas use only common completed dates.')
    page = page.replace('Missing scheduled exits follow the declared fallback.', 'A missing exact-time exit remains explicitly unresolved.')
    page = page.replace('A missing timed exit triggers irrevocable settlement fallback, with counts reported above; missing settlement evidence remains unresolved.', 'A missing exact-time exit remains unresolved; there is no settlement fallback in these policies. Its priced-subset result must not be read as a full-cohort strategy result. Settlement-policy entries use attributed terminal close evidence.')
    page = page.replace('Top-three-removed net', 'Top-five-removed net')
    return page


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--run', default='run-02')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    out = args.out or args.base / 'index.html'
    out.write_text(render(args.base, args.run))
    print(out)


if __name__ == '__main__':
    main()
