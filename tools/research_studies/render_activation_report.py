"""Render the frozen activation study as a self-contained offline HTML report."""

from __future__ import annotations

import argparse
import base64
import io
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from activation_study import DEFAULT_OUT, RULES, skip_mask

LABELS = {
    "low_vix": "Skip VIX < 17", "high_vix": "Skip VIX ≥ 24.5",
    "chaos_vix": "Skip VIX ≥ 32", "backwardation": "Skip prior VIX/VIX3M ≥ 1",
    "one_day_premium": "Skip prior VIX1D/VIX ≥ 1",
    "small_gap": "Skip |opening gap| < 0.25%", "large_gap": "Skip |opening gap| ≥ 1%",
    "opening_reversal": "Skip opening move against gap", "quiet_open": "Skip quiet opening range",
    "fast_open": "Skip fast opening range", "vix_chain_mismatch": "Skip VIX/chain move ≥ 1.25",
    "wide_spread": "Skip entry ask–mid / mid ≥ 20%", "early_release": "Skip CPI/NFP/PCE release",
    "fomc": "Skip FOMC statement day", "losing_20": "Pause after losing prior 20 sessions",
    "underwater_5000": "Pause at $5,000 shadow drawdown",
}


def money(value: float) -> str:
    return f"−${abs(value):,.0f}" if value < 0 else f"${value:,.0f}"


def chart_image(fig, out: Path, name: str) -> str:
    fig.savefig(out / f"{name}.png", dpi=180, bbox_inches="tight", facecolor="white")
    stream = io.BytesIO()
    fig.savefig(stream, format="svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return "data:image/svg+xml;base64," + base64.b64encode(stream.getvalue()).decode()


def render(out: Path = DEFAULT_OUT) -> None:
    m = json.loads((out / "summary.json").read_text())
    f = pd.read_json(out / "sessions.jsonl", lines=True, convert_dates=False)
    dates = pd.to_datetime(f.date)
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.labelcolor": "#40464d", "axes.edgecolor": "#bac0c7"})
    fig, ax = plt.subplots(figsize=(11.4, 4.4))
    for key, label, color, style in (("midpoint", "Midpoint + fees", "#597784", "-"),
                                     ("marketable", "Bid/ask + fees", "#777777", "-"),
                                     ("stressed", "Bid/ask + fees + stress", "#b24b42", "-"),
                                     ("stressed_floor", "Stress with $0 net exit floor", "#b24b42", "--")):
        ax.plot(dates, f[key].cumsum(), label=label, color=color, linestyle=style, lw=1.8)
    ax.axhline(0, color="#777777", lw=.7)
    ax.axvspan(pd.Timestamp("2025-12-10"), pd.Timestamp("2026-03-16"), color="#eeeeee")
    ax.text(pd.Timestamp("2026-01-15"), 28000, "No inputs", rotation=90, ha="center", fontsize=8)
    ax.set(title="Execution assumptions change the sign of cumulative E0 P&L",
           ylabel="Cumulative realized P&L ($ / one fly per opportunity)", xlabel="Observed session date")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    ax.grid(axis="y", alpha=.15)
    cost_chart = chart_image(fig, out, "execution-costs")
    fig, axes = plt.subplots(2, 1, figsize=(11.4, 6.4), sharex=True, gridspec_kw={"height_ratios": [2, 1]})
    for name, color, style in (("E0", "#444444", "-"), ("wide_spread", "#216479", "-"),
                                ("backwardation", "#919191", "-"), ("underwater_5000", "#216479", "--")):
        rule = next((r for r in RULES if r[0] == name), None)
        keep = ~skip_mask(f, rule) if rule else np.ones(len(f), bool)
        equity = np.cumsum(np.where(keep, f.stressed, 0))
        label = LABELS.get(name, "E0 baseline")
        axes[0].plot(dates, equity, label=label, color=color, linestyle=style, lw=1.7)
        axes[1].plot(dates, equity - np.maximum.accumulate(np.r_[0, equity])[1:],
                     color=color, linestyle=style, lw=1.4)
    axes[0].set(title="Lower drawdown alone does not establish a selective activation edge",
                ylabel="Cumulative realized P&L ($)")
    axes[1].set(ylabel="Realized drawdown ($)", xlabel="Observed session date")
    for ax in axes:
        ax.axhline(0, color="#777777", lw=.7)
        ax.grid(axis="y", alpha=.15)
        ax.axvspan(pd.Timestamp("2025-12-10"), pd.Timestamp("2026-03-16"), color="#eeeeee")
    axes[0].legend(loc="lower left", frameon=False, fontsize=8)
    axes[1].xaxis.set_major_locator(mdates.YearLocator())
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    filter_chart = chart_image(fig, out, "activation-drawdowns")
    rows = []
    for name in ("wide_spread", "backwardation", "one_day_premium", "fomc", "underwater_5000", "low_vix"):
        r = next(x for x in m["rules"] if x["name"] == name)
        v = r["periods"]["all"]
        rows.append(f"<tr><th>{LABELS[name]}</th><td>{v['skipped_trades']}</td>"
                    f"<td>{money(v['losses_avoided'])}</td><td>{money(v['winning_dollars_missed'])}</td>"
                    f"<td>{v['gross_wins_retained_pct']}%</td><td>{v['top10_retained']}/10</td>"
                    f"<td>{money(v['net'])}</td></tr>")
    evidence_rows = "".join(rows)
    year_rows = "".join(f"<tr><th>{year}</th><td>{m['baseline'][year]['kept_trades']}</td>"
                        f"<td>{money(m['baseline'][year]['net'])}</td>"
                        f"<td>{money(m['baseline'][year]['max_drawdown'])}</td>"
                        f"<td>{money(m['x1'][year]['net'])}</td></tr>"
                        for year in ("2022", "2023", "2024", "2025", "2026"))
    payload = json.dumps({"summary": m, "labels": LABELS}, allow_nan=False).replace("</", "<\\/")
    html = r'''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>SPX activation research · 18 October 2026</title>
<style>
:root{font-family:system-ui,sans-serif;color:#25303a;background:#f4f5f6;line-height:1.55}*{box-sizing:border-box}
body{margin:0}main{max-width:1220px;margin:auto;padding:44px 30px 64px}h1{font:600 clamp(28px,4vw,43px)/1.15 system-ui;letter-spacing:-1.1px;max-width:900px;margin:12px 0 22px}h2{font-size:22px;line-height:1.3;margin:42px 0 16px}h3{font-size:17px;margin:26px 0 10px}p{max-width:950px}.kicker{font-size:12px;letter-spacing:1.7px;text-transform:uppercase;color:#536975}.lead{font-size:19px;max-width:960px}.decision{padding:18px 22px;background:#e7edf0;border-left:4px solid #216479;margin:24px 0}.stats{display:flex;gap:32px;flex-wrap:wrap;border-block:1px solid #cdd4d9;padding:23px 0;margin:28px 0}.stat{flex:1;min-width:160px}.stat strong{display:block;font-size:28px;letter-spacing:-.7px}.stat small{color:#5b6670}.negative{color:#a74439}figure{margin:24px 0;background:white;padding:18px}figure img{width:100%;display:block}figcaption,.small{font-size:12px;color:#5e6c77}table{width:100%;border-collapse:collapse;font-size:13px;font-variant-numeric:tabular-nums}th,td{padding:11px 12px;border-bottom:1px solid #dce1e5;text-align:right;white-space:nowrap}th:first-child,td:first-child{text-align:left}thead th{background:#e8ecef;font-size:12px}tbody th{font-weight:500}tbody tr:hover{background:#eaf0f3}.scroll{overflow:auto;margin:16px 0}.controls{display:flex;gap:16px;align-items:end;flex-wrap:wrap;margin:20px 0}label{font-size:13px;display:grid;gap:6px}select{font:inherit;padding:9px 14px;border:1px solid #bdc8d0;border-radius:4px;background:white;color:#25303a}a{color:#216479}li{margin-bottom:8px}details{margin:22px 0}summary{cursor:pointer;font-weight:600}.cols{display:grid;grid-template-columns:1fr 1fr;gap:30px}.cols p{font-size:15px}footer{border-top:1px solid #cdd4d9;margin-top:40px;padding-top:20px}.note{font-size:14px;color:#52636e}code{font-size:12px;background:#e8ecef;padding:2px 4px}pre{white-space:pre-wrap;word-break:break-word;background:#e8ecef;padding:16px;font-size:12px}@media(max-width:700px){main{padding:25px 16px}.cols{grid-template-columns:1fr;gap:0}.stats{gap:15px}.stat strong{font-size:24px}figure{padding:4px;margin-inline:-8px}}
</style><main>
<div class="kicker">Butterfly Guy / SPXW 0-DTE / retrospective research / 18 October 2026</div>
<h1>Can we avoid the drawdowns without missing the big winners?</h1>
<p class="lead">Some observable conditions identify costly trades while preserving nearly all winning dollars. This study does <strong>not</strong> establish an activation rule that makes the current strategy profitable under the primary execution stress.</p>
<div class="decision"><strong>Decision: refine; insufficient evidence for an activation change.</strong> None of 16 fixed filters passed the development-period criteria. The simplest promising research directions are entry execution quality and prior-day volatility structure. Runtime strategy and services were unchanged.</div>
<div class="stats"><div class="stat"><strong>1,070 / 823</strong><small>eligible sessions / E0 trades</small></div><div class="stat"><strong class="negative">−$39,319</strong><small>stressed P&L, independent one-fly trades</small></div><div class="stat"><strong class="negative">$53,430</strong><small>maximum observed realized drawdown</small></div><div class="stat"><strong>13.1%</strong><small>win rate · average win $1,333 / loss $256</small></div></div>
<p class="note">Coverage: Jan 2022–Jun 2024, Jul 2024–Dec 9 2025, Mar 17–Sep 25 2026. No observations are filled into the intervening gap. The cumulative curve concatenates observed independent opportunities; it is not a continuous account simulation.</p>
<h2>The first issue is execution cost</h2>
<p>The same midpoint-driven entry and exit decisions earn <strong>$31,011 at midpoint with fees</strong>, lose <strong>$10,279 crossing observed leg bid/ask with fees</strong>, and lose <strong>$39,319 after an additional $0.05 adverse fill per contract on each executed side</strong>. A one-minute delayed exit gives −$34,112. These are alternative modeled cash flows, not measured complex-order fills.</p>
<figure><img src="COST_CHART" alt="Cumulative realized E0 profit under four execution assumptions"><figcaption>Source: fresh canonical research-core replays, Jan 3 2022–Sep 25 2026, available sessions only. Four cash-flow models over unchanged decisions. Gray shading: missing input interval. Maximum drawdown uses daily realized trade results, not intraday mark-to-market.</figcaption></figure>
<p>The unfloored stress model sometimes pays to close a long butterfly. Setting net stressed exit proceeds to zero removes $5,337 of losses across 18 trades, but the total remains <strong>−$33,982</strong>. This sensitivity does not establish that a complex order can fill at zero. Some crossed-leg entries also cost much more than their selection midpoint; their costs do not feed back into selection or exit triggers.</p>
<h2>What the most informative filters actually remove</h2>
<p>Each filter vetoes a baseline opportunity using information available at its entry. It does not replace that trade with a later entry. All figures below use the primary stressed model. <strong>Winning-dollar retention</strong> is the share of all positive baseline P&L retained, which is more informative here than keeping only the ten largest winners.</p>
<div class="scroll"><table><thead><tr><th>Condition to skip</th><th>Trades skipped</th><th>Losses avoided</th><th>Winning $ missed</th><th>Winning $ retained</th><th>Top 10 retained</th><th>Remaining net</th></tr></thead><tbody>EVIDENCE_ROWS</tbody></table></div>
<div class="cols"><div><h3>Wide spreads: primarily an execution signal</h3><p>The 20% ask-minus-mid rule skips 43 of 823 trades. It improves stressed P&L by $19,338 while retaining 97.6% of winning dollars and all ten largest winners. Improvement is positive in each sampled year; 15% and 25% neighboring thresholds also improve the stressed total. At midpoint its benefit is only $90. This is mostly avoiding modeled transaction costs, not evidence of better directional forecasting.</p><h3>Volatility structure: a narrow, plausible veto</h3><p>Prior VIX/VIX3M ≥ 1 skips 29 trades, avoids $13,710 of losses and misses $554 of wins. There are no skipped baseline trades in the 2022–mid-2024 development window, so that interval cannot validate its effect. Prior VIX1D/VIX ≥ 1 skips 84 trades, retains 94.7% of winning dollars and improves each sampled year; 27 traded sessions lack this feature and keep their baseline trade.</p></div><div><h3>FOMC: promising, but only 16 observations</h3><p>All 16 baseline trades on visibly scheduled FOMC statement days lose in this sample; skipping them saves $6,701. Those are 16 traded event days, not all scheduled meetings. The sample is too small and already inspected to support a reliable standalone rule. Skipping all early CPI/NFP/PCE releases is less selective and misses more winners.</p><h3>Blanket “trade less” rules lose too much upside</h3><p>VIX &lt;17 removes 55.9% of trades and 44.7% of winning dollars; its improvement is ordinary versus random skipping of the same trade count. Requiring the first half-hour to follow the opening gap loses six of the ten largest winners. Skipping fast openings makes total P&L worse. The apparent $5,000 drawdown-pause profit comes with 62.9% of winning dollars missed and almost no trading throughout 2024–25.</p></div></div>
<figure><img src="FILTER_CHART" alt="Cumulative stressed P&L and drawdown for E0, spread veto, backwardation veto, and drawdown pause"><figcaption>Source: same fresh replays and causal session features. Jan 2022–Sep 2026 observed sessions. Each comparison starts at $0 and uses one fly per retained baseline opportunity. Drawdown pause tracks a virtual, always-running E0 and resets after missing-history gaps longer than seven calendar days. This reset is a research assumption.</figcaption></figure>
<h2>Periods matter, but knowing the calendar afterward is not a trading signal</h2>
<div class="scroll"><table><thead><tr><th>Observed year</th><th>Trades</th><th>E0 stressed net</th><th>Within-year realized DD</th><th>Same entries held to settlement</th></tr></thead><tbody>YEAR_ROWS</tbody></table></div>
<p>2022 has only 75 qualifying E0 trades; 2025 stops on December 9; 2026 starts on March 17 and stops on September 25. The worst concatenated observed drawdown runs from December 12 2022 to March 25 2026, spanning 748 eligible observations after the peak. It is not proof of a continuously observed account drawdown throughout that calendar period.</p>
<p>Holding the same flies to settlement (<code>X1</code>) improves the aggregate from −$39,319 to <strong>+$1,575</strong>, but still loses <strong>$17,588 in July 2024–December 2025</strong>. This is a diagnostic about exit/cost interaction, not a successful replacement: a three-year total near zero and a large losing period do not establish a viable edge.</p>
<h2>Explore every prespecified filter</h2>
<p class="note">The selector changes only the displayed evidence. It does not tune thresholds or alter a bot. “Later” means July 2024 onward, already inspected historically. Full-data ranking is descriptive and is not the frozen selection procedure.</p>
<div class="controls"><label>Observed period<select id="period"><option value="all">All available sessions</option><option value="development">Development: 2022–June 2024</option><option value="later">Later: July 2024 onward</option><option>2022</option><option>2023</option><option>2024</option><option value="2024H2">2024 H2</option><option>2025</option><option value="2025H1">2025 H1</option><option value="2025H2">2025 H2</option><option>2026</option></select></label><label>Rank by<select id="rank"><option value="net">Highest remaining net</option><option value="max_drawdown">Lowest realized drawdown</option><option value="gross_wins_retained_pct">Most winning dollars retained</option></select></label></div>
<div class="scroll"><table><thead><tr><th>Filter</th><th>Trades kept</th><th>Net $</th><th>Δ vs E0 $</th><th>Realized DD $</th><th>Winning $ retained</th><th>Top winners retained</th></tr></thead><tbody id="rules"></tbody></table></div>
<h3>How much uncertainty remains?</h3>
<p>The all-session, paired 10-session moving-block bootstrap gives these exploratory 90% intervals for the improvement over E0: spread veto <strong>+$9,997 to +$29,467</strong>; backwardation <strong>+$4,983 to +$23,362</strong>; FOMC <strong>+$3,017 to +$11,884</strong>. These intervals are not adjusted for the 26 filter/threshold comparisons, are conditional on observed coverage and execution assumptions, and do not show that remaining P&L is positive. Matched-count random skipping provides another descriptive benchmark: broad low-VIX and small-gap skips look much less distinctive than their dollar improvements suggest.</p>
<details><summary>Show fixed threshold-neighborhood sensitivities</summary><div class="scroll"><table><thead><tr><th>Secondary threshold</th><th>Net $</th><th>Δ vs E0 $</th><th>Winning $ retained</th><th>Realized DD $</th></tr></thead><tbody id="neighbors"></tbody></table></div></details>
<h2>What would justify the next experiment?</h2>
<p><strong>Refine execution-aware eligibility first</strong>: the spread veto is interpretable, preserves almost all upside, and behaves similarly at neighboring thresholds. A separate, frozen follow-up could compare spread-only and volatility-structure-only vetoes under midpoint, bid/ask and adverse execution models. It should validate actual limit-fill behavior and use future observations for a promotion decision. This study does not search conjunctions of the promising filters.</p>
<p>The prewritten development selection required positive stressed net, at least 20% less realized drawdown, retention of at least 80% of winning dollars and eight of ten top winners, and improvement in both development halves. <strong>No primary filter qualified.</strong> An expanding-history half-year selector, trained only on earlier data, therefore mostly stayed with E0; it briefly selected the spread filter in 2023 H2, when no baseline trades met its skip condition. It produced no aggregate improvement. Falling back to E0 is an experimental comparison convention, not a recommendation to activate it.</p>
<details><summary>Methods, evidence limits and reproduction</summary>
<ul><li>Three hash-verified immutable local SPXW datasets: 585 development, 357 spent-holdout, 128 recent-validation sessions. 247 eligible no-trade days stay in session vectors at zero; unavailable sessions are excluded, not invented.</li><li>Canonical <code>vendor_1m</code> profile; current checked-in SPX config; unchanged E0 entry/exit logic. All 823 E0 and 823 X1 trades priced and resolved. Fresh E0 development replay exactly reproduces the earlier frozen baseline trade records.</li><li>Commission $0.65 per contract, four contracts per executed side; free cash settlement. One-fly independent opportunities, no compounding, capital-based return, buying-power simulation, or daily-account loss overlay. Average holding exposure is about 181 minutes per E0 trade; net expectancy is −$47.78 per trade, −0.1241 stressed-debit units. Nominal E0 commissions total $3,775.</li><li>Signals use actual entry quotes and VIX; opening features stop at 10:00 ET; gap is official open/prior close. Daily volatility ratios use the preceding SPX session. Event schedules must have been public before the date. Realized closing moves are descriptive only, never activation inputs.</li><li>Each skip vetoes the selected E0 opportunity; it does not retry at a better spread. A deployable retry policy would be a distinct experiment. Missing feature values keep E0 and are counted. The cooldown uses prior virtual-baseline P&L and resets after gaps &gt;7 calendar days.</li><li>All historical windows were previously inspected, including the spent holdout. Chronological checks here are retrospective stability checks, not fresh out-of-sample evidence. The study froze 16 primary conditions and ten secondary neighbor thresholds; no conjunction search. The original plan's “12 neighbors” was a count typo; its listed bounds specify ten.</li><li>Minute leg NBBO cannot demonstrate complex-order fills, intraminute trigger ordering or queue priority. Cash-flow repricing does not resimulate decisions using executable costs. The historical SPX/VIX minute CSV provider remains unknown. Prior quality approval covers this mapping; recent-session Q5 timing comparison remains unevaluable on irregular recorded index ticks.</li><li>The input gap Dec 10 2025–Mar 16 2026 is not a no-trade strategy outcome. 2022 also predates regular Tuesday/Thursday expiration availability. Historical session eligibility and supporting-input exclusions remain as recorded by existing import quality ledgers.</li></ul>
<p><a href="https://www.cboe.com/tradable-products/volatility-trading/">Cboe: VIX measures 30-day expected volatility.</a> A VIX-based daily move and a same-day ATM-straddle proxy describe different horizons; the ratio tested here is a heuristic, not a directly observed mispricing.</p>
<pre>uv run --no-sync python tools/research_studies/activation_study.py
uv run --no-sync python tools/research_studies/render_activation_report.py
uv run --no-sync pytest -q tests/test_activation_study.py tests/test_research_accounting.py tests/test_research_features.py tests/test_research_evaluate.py</pre>
<p class="note">The three required canonical replay commands are preserved in each replay's <code>provenance.json</code> and in the accompanying research note. <code>plan.json</code>, <code>sessions.jsonl</code>, <code>summary.json</code>, <code>dataset-verification.json</code> and source/output hashes accompany this report. All work is local research; no order API, deployment or service mutation was performed.</p>
</details><footer><span class="small">Butterfly Guy · Research decision: REFINE / INSUFFICIENT EVIDENCE · 18 October 2026 · One-fly simulated dollar results, not account returns.</span></footer>
</main><script id="data" type="application/json">PAYLOAD</script><script>
const D=JSON.parse(document.getElementById('data').textContent), S=D.summary;
const fmt=x=>x==null?'—':Math.round(x).toLocaleString('en-US');
function row(label,v){return `<tr><th>${label}</th><td>${v.kept_trades}</td><td>${fmt(v.net)}</td><td>${fmt(v.net_diff)}</td><td>${fmt(v.max_drawdown)}</td><td>${v.gross_wins_retained_pct??'—'}%</td><td>${v.top10_retained}/${v.top10_available}</td></tr>`}
function render(){const p=document.getElementById('period').value,k=document.getElementById('rank').value;let R=S.rules.filter(r=>r.primary).slice();R.sort((a,b)=>k==='max_drawdown'?(a.periods[p][k]??0)-(b.periods[p][k]??0):(b.periods[p][k]??0)-(a.periods[p][k]??0));document.getElementById('rules').innerHTML=row('E0 baseline',S.baseline[p])+R.map(r=>row(D.labels[r.name],r.periods[p])).join('');}
document.getElementById('period').addEventListener('change',render);document.getElementById('rank').addEventListener('change',render);render();
document.getElementById('neighbors').innerHTML=S.rules.filter(r=>!r.primary).map(r=>{let v=r.periods.all;return `<tr><th>${r.name}</th><td>${fmt(v.net)}</td><td>${fmt(v.net_diff)}</td><td>${v.gross_wins_retained_pct}%</td><td>${fmt(v.max_drawdown)}</td></tr>`}).join('');
</script></html>'''
    for key, value in (("COST_CHART", cost_chart), ("FILTER_CHART", filter_chart),
                       ("EVIDENCE_ROWS", evidence_rows), ("YEAR_ROWS", year_rows), ("PAYLOAD", payload)):
        html = html.replace(key, value)
    (out / "report.html").write_text(html)
    print(out / "report.html")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    render(parser.parse_args().out)
