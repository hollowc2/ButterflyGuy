// Butterfly Guy SPX paper-performance page. Shipped as a same-origin file so
// the site CSP (script-src 'self') covers it without an inline-script hash.
// All per-run numbers arrive in the #page-data JSON block.
(() => {
const DATA = JSON.parse(document.getElementById('page-data').textContent);
const trades = DATA.trades;
const noTrade = DATA.noTrade;
const css = getComputedStyle(document.documentElement);
const C = (n) => css.getPropertyValue(n).trim();
const UP = C('--up-mark'), DOWN = C('--down-mark'), ACC = C('--accent'), MUTED = C('--muted');
const GRID = 'rgba(232,226,214,0.06)';

const EXIT = {
  cash_settled:          { label: 'Held to settlement', group: 'held', desc: 'Held to the close; SPX settled the fly. The big winners end this way.' },
  end_of_day:            { label: 'Sold at the close', group: 'held', desc: 'Sold in the last minutes of the session instead of settling.' },
  drawdown_morning:      { label: 'Trailing stop, morning', group: 'stop', desc: 'Before 11:30 ET the fly fell too far below its high of the day.' },
  drawdown_late_morning: { label: 'Trailing stop, midday', group: 'stop', desc: 'Between 11:30 and 1:30 ET the fly fell too far below its high.' },
  drawdown_afternoon:    { label: 'Trailing stop, afternoon', group: 'stop', desc: 'After 1:30 ET the fly fell too far below its high.' },
  absolute_loss_stop:    { label: 'Loss stop', group: 'stop', desc: 'Lost a set share of what it cost. No longer used.' },
};
const exitInfo = (r) => EXIT[r] || { label: r, group: 'other', desc: '' };

const fmt = (n) => Math.round(Math.abs(n)).toLocaleString('en-US');
const money = (n) => (Math.round(n) < 0 ? '−$' : Math.round(n) > 0 ? '+$' : '$') + fmt(n);
const plainMoney = (n) => '$' + fmt(n);
const cls = (n) => (n > 0 ? 'pos' : n < 0 ? 'neg' : '');
const D = (iso) => new Date(iso + 'T12:00:00Z');
const MON = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
const niceDate = (iso, year) => { const d = D(iso); return `${MON[d.getUTCMonth()]} ${d.getUTCDate()}${year ? ', ' + d.getUTCFullYear() : ''}`; };
const weekday = (iso) => ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][D(iso).getUTCDay()];
const strikes = (t) => t.strikes.split(' / ').map(Number);
const flyText = (t) => t.strikes.replace(/ \/ /g, ' / ');
const mult = (v, t) => (v == null || !t.entry_price ? null : v / t.entry_price);
const multText = (m) => (m == null ? '—' : (m >= 10 ? m.toFixed(0) : m.toFixed(1)) + '×');

// ----- summary numbers
const pnls = trades.map((t) => t.pnl);
const total = pnls.reduce((a, b) => a + b, 0);
const wins = trades.filter((t) => t.pnl > 0), losses = trades.filter((t) => t.pnl <= 0);
const sum = (arr) => arr.reduce((a, t) => a + t.pnl, 0);
const winSum = sum(wins), lossSum = sum(losses);
const peakEq = Math.max(...trades.map((t) => t.peak_equity));
const maxDd = trades.reduce((m, t) => (t.drawdown_dollars > m.drawdown_dollars ? t : m), trades[0]);
const first = trades[0], last = trades[trades.length - 1];

document.getElementById('meta').innerHTML =
  `<b>${trades.length} trades</b> · ${niceDate(first.date, true)} to ${niceDate(last.date, true)} · one contract per trade · refreshed after each session, last ${DATA.builtAt}`;
const net = document.getElementById('netPnl');
net.textContent = money(total); net.className = 'big ' + cls(total);
document.getElementById('netSub').textContent = `High-water mark ${money(peakEq)} · now ${plainMoney(last.drawdown_dollars)} below it`;

const kpis = [
  ['Win rate', `${Math.round(wins.length / trades.length * 100)}%`, `${wins.length} of ${trades.length} trades`],
  ['Average win', money(winSum / wins.length), 'per winning trade', 'pos'],
  ['Average loss', money(lossSum / losses.length), 'per losing trade', 'neg'],
  ['Profit factor', (winSum / -lossSum).toFixed(2), 'won $ ÷ lost $'],
  ['Biggest win', money(Math.max(...pnls)), niceDate(trades.find((t) => t.pnl === Math.max(...pnls)).date), 'pos'],
  ['Worst stretch', money(-maxDd.drawdown_dollars), `high to low, ${niceDate(maxDd.date)} trough`, 'neg'],
];
document.getElementById('kpis').innerHTML = kpis.map(([l, v, h, c]) =>
  `<div class="kpi"><div class="label">${l}</div><div class="value ${c || ''}">${v}</div><div class="hint">${h}</div></div>`).join('');

// ----- latest session
(() => {
  const t = last, [lo, mid, hi] = strikes(t), x = exitInfo(t.exit_reason);
  const scale = Math.max(t.peak_value || 0, t.entry_price, t.exit_price || 0) * 1.04;
  const pos = (v) => `${(v / scale) * 100}%`;
  const dir = t.direction === 'CALL' ? 'Call' : 'Put';
  const pk = mult(t.peak_value, t), ex = mult(t.exit_price, t);
  let note;
  if (x.group === 'held') note = `Held into the close and ${t.pnl > 0 ? 'paid off' : 'expired out of range'}.`;
  else if (pk && pk > 1.5) note = `It was worth ${multText(pk)} its cost at the high, then the trailing stop sold it at ${multText(ex)} after it fell ${t.dd_at_exit_pct != null ? Math.round(t.dd_at_exit_pct) + '%' : ''} from that high.`;
  else note = `It never got going; the trailing stop cut it at ${multText(ex)} of cost.`;
  document.getElementById('latest').innerHTML = `
    <div class="latest-head"><div class="label">Latest session · ${weekday(t.date)} ${niceDate(t.date)}</div>
      <div class="latest-pnl ${cls(t.pnl)}">${money(t.pnl)}</div></div>
    <div class="latest-title">${dir} butterfly ${lo.toLocaleString()} / ${mid.toLocaleString()} / ${hi.toLocaleString()}</div>
    <div class="latest-sub">${t.width}-point wings · SPX ${t.spot ? Math.round(t.spot).toLocaleString() : '—'} at entry · VIX ${t.vix ?? '—'} · ${t.entry_time} to ${t.exit_time} ET</div>
    <div class="path" aria-hidden="true">
      <div class="path-track">
        <div class="path-fill" style="width:${pos(t.peak_value || t.entry_price)}"></div>
        <div class="path-mark paid" style="left:${pos(t.entry_price)}"></div>
        ${t.peak_value != null ? `<div class="path-mark peak" style="left:${pos(t.peak_value)}"></div>` : ''}
        <div class="path-mark exit" style="left:${pos(t.exit_price || 0)}"></div>
      </div>
    </div>
    <div class="path-legend">
      <div><span><i style="background:var(--muted)"></i>Paid</span><b>${plainMoney(t.entry_price * 100)}</b></div>
      <div><span><i style="background:var(--accent)"></i>Peak value</span><b>${t.peak_value != null ? plainMoney(t.peak_value * 100) : '—'}</b></div>
      <div><span><i style="background:var(--text)"></i>Sold for</span><b>${plainMoney((t.exit_price || 0) * 100)}</b></div>
    </div>
    <p class="latest-note">${x.label}. ${note}</p>`;
})();

// ----- shape of returns
const pct = (a, b) => Math.round(a / b * 100);
const grossAbs = winSum - lossSum;
document.getElementById('shareCount').innerHTML =
  `<div class="w" style="flex:${wins.length}">${wins.length}</div><div class="l" style="flex:${losses.length}">${losses.length}</div>`;
document.getElementById('shareDollars').innerHTML =
  `<div class="w" style="flex:${winSum}">${money(winSum)}</div><div class="l" style="flex:${-lossSum}">${money(lossSum)}</div>`;
const sortedDesc = [...trades].sort((a, b) => b.pnl - a.pnl);
const top5 = sortedDesc.slice(0, 5), top5Sum = sum(top5);
document.getElementById('concentration').innerHTML =
  `The <b>5 best days</b> made <b class="pos">${money(top5Sum)}</b>. The other <b>${trades.length - 5} trades</b> together made <b class="${cls(total - top5Sum)}">${money(total - top5Sum)}</b>. ` +
  `The average win is <b>${((winSum / wins.length) / -(lossSum / losses.length)).toFixed(1)}×</b> the average loss, so one good day pays for about ${Math.round((winSum / wins.length) / -(lossSum / losses.length))} bad ones.`;
document.getElementById('shapeLede').textContent =
  `A ${Math.round(wins.length / trades.length * 100)}% hit rate sounds bad until you see the sizes. Here is every trade, worst to best.`;

const tip = document.getElementById('tip');
function showTip(html, x, y) {
  tip.innerHTML = html; tip.hidden = false;
  const r = tip.getBoundingClientRect();
  let left = x + 14, top = y + 14;
  if (left + r.width > innerWidth - 8) left = x - r.width - 14;
  if (top + r.height > innerHeight - 8) top = y - r.height - 14;
  tip.style.left = Math.max(8, left) + 'px'; tip.style.top = Math.max(8, top) + 'px';
}
const hideTip = () => { tip.hidden = true; };
function tradeTip(t) {
  const x = exitInfo(t.exit_reason);
  return `<b>${weekday(t.date)} ${niceDate(t.date, true)}</b><br>${t.direction === 'CALL' ? 'Call' : 'Put'} fly <span class="m">${flyText(t)}</span><br>` +
    `Paid <span class="m">${plainMoney(t.entry_price * 100)}</span> · peak <span class="m">${multText(mult(t.peak_value, t))}</span> · exit <span class="m">${multText(mult(t.exit_price, t))}</span><br>` +
    `${x.label}, ${t.exit_time} ET<br><b class="${cls(t.pnl)} m">${money(t.pnl)}</b>`;
}
function externalTip(getHtml) {
  return (ctx) => {
    const { chart, tooltip } = ctx;
    if (!tooltip.opacity || !tooltip.dataPoints?.length) { hideTip(); return; }
    const rect = chart.canvas.getBoundingClientRect();
    showTip(getHtml(tooltip.dataPoints[0].dataIndex), rect.left + tooltip.caretX, rect.top + tooltip.caretY);
  };
}
Chart.defaults.font.family = 'Inter, system-ui, sans-serif';
Chart.defaults.color = MUTED;
const moneyTick = (v) => (v < 0 ? '−$' : v > 0 ? '+$' : '$') + Math.abs(v).toLocaleString('en-US');

const ascending = [...trades].sort((a, b) => a.pnl - b.pnl);
new Chart(document.getElementById('sortedChart'), {
  type: 'bar',
  data: { labels: ascending.map((_, i) => i + 1), datasets: [{
    data: ascending.map((t) => t.pnl),
    backgroundColor: ascending.map((t) => (t.pnl > 0 ? UP : DOWN)),
    borderRadius: 2, barPercentage: 1, categoryPercentage: 0.82,
  }] },
  options: {
    responsive: true, maintainAspectRatio: false, animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { display: false }, tooltip: { enabled: false, external: externalTip((i) => tradeTip(ascending[i])) } },
    scales: {
      x: { display: false },
      y: { grid: { color: GRID }, border: { display: false }, ticks: { callback: moneyTick, maxTicksLimit: 6 } },
    },
  },
});
document.getElementById('sortedChart').setAttribute('aria-label',
  `Bar chart of all ${trades.length} trades sorted by P&L, from ${money(ascending[0].pnl)} to ${money(ascending.at(-1).pnl)}. ${losses.length} are losses and ${wins.length} are wins.`);

// ----- equity + drawdown
const firstOver = trades.find((t) => t.equity >= peakEq);
document.getElementById('equityLede').innerHTML =
  `Cumulative P&amp;L after each trade. It reached a high of <b>${money(peakEq)}</b> on ${niceDate(firstOver.date)} and is <b>${money(total)}</b> today. The jumps are the big settlement days; the slow drifts down are runs of small losses.`;
const labels = trades.map((t) => niceDate(t.date));
const bigWin = (t) => t.pnl >= 1000;
const xAxis = { grid: { display: false }, border: { color: GRID }, ticks: { maxRotation: 0, autoSkip: true, maxTicksLimit: innerWidth < 600 ? 4 : 9 } };
const eqChart = new Chart(document.getElementById('equityChart'), {
  type: 'line',
  data: { labels, datasets: [{
    data: trades.map((t) => t.equity), borderColor: ACC, borderWidth: 2, tension: 0,
    backgroundColor: 'rgba(200,146,42,0.08)', fill: 'origin',
    pointRadius: trades.map((t) => (bigWin(t) ? 4.5 : 0)), pointHoverRadius: 5,
    pointBackgroundColor: trades.map((t) => (bigWin(t) ? C('--up') : ACC)), pointBorderColor: C('--panel'), pointBorderWidth: 2,
  }] },
  options: {
    responsive: true, maintainAspectRatio: false, animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { display: false }, tooltip: { enabled: false, external: externalTip((i) => {
      const t = trades[i];
      return tradeTip(t) + `<br>Running total <span class="m">${money(t.equity)}</span>`;
    }) } },
    scales: { x: xAxis, y: { grid: { color: GRID }, border: { display: false }, ticks: { callback: moneyTick, maxTicksLimit: 6 } } },
  },
});
document.getElementById('equityChart').setAttribute('aria-label',
  `Line chart of cumulative P&L from ${niceDate(first.date, true)} to ${niceDate(last.date, true)}, peaking at ${money(peakEq)} and ending at ${money(total)}.`);

new Chart(document.getElementById('ddChart'), {
  type: 'line',
  data: { labels, datasets: [{
    data: trades.map((t) => -t.drawdown_dollars), borderColor: DOWN, borderWidth: 1.5, tension: 0,
    backgroundColor: 'rgba(204,85,85,0.22)', fill: 'origin', pointRadius: 0, pointHoverRadius: 4,
  }] },
  options: {
    responsive: true, maintainAspectRatio: false, animation: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { display: false }, tooltip: { enabled: false, external: externalTip((i) => {
      const t = trades[i];
      return `<b>${niceDate(t.date, true)}</b><br>Running total <span class="m">${money(t.equity)}</span><br>High so far <span class="m">${money(t.peak_equity)}</span><br>Below the high <span class="m neg">${money(-t.drawdown_dollars)}</span>`;
    }) } },
    scales: { x: xAxis, y: { max: 0, grid: { color: GRID }, border: { display: false }, ticks: { callback: moneyTick, maxTicksLimit: 4 } } },
  },
});
const ddStart = [...trades.slice(0, trades.indexOf(maxDd))].reverse().find((t) => t.drawdown_dollars === 0);
document.getElementById('ddCaption').innerHTML =
  `How far the running total sits below its best level so far. The deepest stretch gave back <b>${money(-maxDd.drawdown_dollars)}</b>, from a high of ${money(maxDd.peak_equity)}${ddStart ? ` on ${niceDate(ddStart.date)}` : ''} down to ${money(maxDd.equity)} on ${niceDate(maxDd.date)}.`;
document.getElementById('ddChart').setAttribute('aria-label', `Area chart of dollars below the running high. Deepest point ${money(-maxDd.drawdown_dollars)} on ${niceDate(maxDd.date, true)}.`);

// ----- breakdown
const VIX_BINS = [[0, 15, 'Under 15'], [15, 17, '15 to 17'], [17, 20, '17 to 20'], [20, 25, '20 to 25'], [25, 99, '25 and up']];
const GROUPS = {
  exit: { head: 'How it ended', key: (t) => exitInfo(t.exit_reason).label,
          sub: (k) => Object.values(EXIT).find((e) => e.label === k)?.desc || '',
          order: (a, b) => b.total - a.total },
  month: { head: 'Month', key: (t) => t.date.slice(0, 7), name: (k) => { const [y, m] = k.split('-'); return `${MON[+m - 1]} ${y}`; }, order: (a, b) => (a.k < b.k ? -1 : 1) },
  width: { head: 'Wing width', key: (t) => t.width, name: (k) => `${k} points`, order: (a, b) => a.k - b.k },
  dir: { head: 'Direction', key: (t) => t.direction, name: (k) => (k === 'CALL' ? 'Call flies (center above spot)' : 'Put flies (center below spot)'), order: (a, b) => (a.k < b.k ? -1 : 1) },
  vix: { head: 'VIX at entry', key: (t) => (t.vix == null ? 'none' : VIX_BINS.findIndex(([lo, hi]) => t.vix >= lo && t.vix < hi)),
         name: (k) => (k === 'none' ? 'Not recorded' : VIX_BINS[k][2]), sub: (k) => (k === 'none' ? 'Early trades, before VIX was logged' : ''),
         order: (a, b) => (a.k === 'none' ? 1 : b.k === 'none' ? -1 : a.k - b.k) },
};
function renderBreakdown(keyName) {
  const g = GROUPS[keyName], buckets = new Map();
  trades.forEach((t) => { const k = g.key(t); if (!buckets.has(k)) buckets.set(k, []); buckets.get(k).push(t); });
  const rows = [...buckets].map(([k, ts]) => ({ k, ts, total: sum(ts), n: ts.length, wins: ts.filter((t) => t.pnl > 0).length }));
  rows.sort(g.order);
  const maxPos = Math.max(0, ...rows.map((r) => r.total)), maxNeg = Math.max(0, ...rows.map((r) => -r.total));
  const span = maxPos + maxNeg || 1, zero = maxNeg / span * 100;
  document.getElementById('bdTable').innerHTML =
    `<thead><tr><th>${g.head}</th><th class="r">Trades</th><th class="r">Won</th><th></th><th class="r">Total</th><th class="r">Per trade</th></tr></thead><tbody>` +
    rows.map((r) => {
      const w = Math.abs(r.total) / span * 100;
      const bar = r.total >= 0 ? `<div class="p" style="left:${zero}%;width:${w}%"></div>` : `<div class="n" style="left:${zero - w}%;width:${w}%"></div>`;
      const name = g.name ? g.name(r.k) : r.k, sub = g.sub ? g.sub(r.k) : '';
      return `<tr><td class="what">${name}${sub ? `<small>${sub}</small>` : ''}</td><td class="r">${r.n}</td><td class="r">${Math.round(r.wins / r.n * 100)}%</td>` +
        `<td class="barcell"><div class="dbar" style="--zero:${zero}%">${bar}</div></td>` +
        `<td class="r ${cls(r.total)}">${money(r.total)}</td><td class="r ${cls(r.total)}">${money(r.total / r.n)}</td></tr>`;
    }).join('') + '</tbody>';
}
document.querySelectorAll('#bdControls button').forEach((b) => b.addEventListener('click', () => {
  document.querySelectorAll('#bdControls button').forEach((o) => o.setAttribute('aria-pressed', String(o === b)));
  renderBreakdown(b.dataset.key);
}));
renderBreakdown('exit');

// ----- calendar
const CAP = 1000;
const cellColor = (p) => {
  const a = 0.28 + 0.72 * Math.sqrt(Math.min(Math.abs(p), CAP) / CAP);
  return p > 0 ? `rgba(106,170,120,${a.toFixed(2)})` : `rgba(214,106,106,${a.toFixed(2)})`;
};
document.getElementById('rampNeg').innerHTML = [400, 150, 40].map((v) => `<i style="background:${cellColor(-v)}"></i>`).join('');
document.getElementById('rampPos').innerHTML = [40, 250, 1000].map((v) => `<i style="background:${cellColor(v)}"></i>`).join('');
(() => {
  const byDate = new Map(trades.map((t) => [t.date, t]));
  const ntByDate = new Map(noTrade.map((n) => [n.date, n]));
  const cal = document.getElementById('cal');
  const start = D(first.date); start.setUTCDate(start.getUTCDate() - (start.getUTCDay() - 1));
  const end = D(last.date);
  let html = '<span></span>' + ['Mon','','Wed','','Fri'].map((d) => `<span class="dow">${d}</span>`).join('');
  let lastMonth = -1;
  for (let wk = new Date(start); wk <= end; wk.setUTCDate(wk.getUTCDate() + 7)) {
    const m = wk.getUTCMonth();
    // Label the column whose Monday falls in a new month.
    html += `<span class="mon">${m !== lastMonth ? MON[m] : ''}</span>`;
    lastMonth = m;
    for (let d = 0; d < 5; d++) {
      const day = new Date(wk); day.setUTCDate(wk.getUTCDate() + d);
      const iso = day.toISOString().slice(0, 10);
      const t = byDate.get(iso), n = ntByDate.get(iso);
      if (day < D(first.date) || day > end) { html += '<span></span>'; continue; }
      if (t) html += `<button type="button" class="cell trade" data-date="${iso}" style="background:${cellColor(t.pnl)}" aria-label="${niceDate(iso, true)}: ${money(t.pnl)}"></button>`;
      else if (n) html += `<span class="cell ${n.status === 'Halted' ? 'halt' : ''}" data-nt="${iso}" tabindex="0" aria-label="${niceDate(iso, true)}: ${n.status}"></span>`;
      else html += `<span class="cell empty" data-nt="${iso}" tabindex="0" aria-label="${niceDate(iso, true)}: no session recorded"></span>`;
    }
  }
  cal.innerHTML = html;
  const reasonText = (n) => {
    if (!n) return 'No session recorded (market holiday or the bot was down)';
    if (n.status === 'Halted') return 'Halted: the daily loss limit was hit';
    const r = n.reason;
    if (r === 'Entry ladder exhausted') return 'No fill: every entry price was tried and none filled';
    if (r.startsWith('consecutive_losses')) return 'Paused after 10 losses in a row';
    if (r === 'session_open_unavailable') return 'Skipped: no opening price was available';
    return 'No trade';
  };
  cal.addEventListener('mouseover', (e) => {
    const el = e.target.closest('[data-date],[data-nt]'); if (!el) return;
    const r = el.getBoundingClientRect();
    if (el.dataset.date) showTip(tradeTip(byDate.get(el.dataset.date)), r.right, r.bottom);
    else showTip(`<b>${weekday(el.dataset.nt)} ${niceDate(el.dataset.nt, true)}</b><br>${reasonText(ntByDate.get(el.dataset.nt))}`, r.right, r.bottom);
  });
  cal.addEventListener('mouseout', hideTip);
  cal.addEventListener('click', (e) => {
    const el = e.target.closest('[data-date]'); if (el) jumpToTrade(el.dataset.date);
  });
})();

// ----- trade log
const PAGE = 25;
let filter = 'all', showAll = false;
const FILTERS = {
  all: () => true, win: (t) => t.pnl > 0, loss: (t) => t.pnl <= 0,
  held: (t) => exitInfo(t.exit_reason).group === 'held', stop: (t) => exitInfo(t.exit_reason).group === 'stop',
};
function renderLog() {
  const rows = [...trades].reverse().filter(FILTERS[filter]);
  const shown = showAll ? rows : rows.slice(0, PAGE);
  document.getElementById('logBody').innerHTML = shown.map((t) => {
    const pk = mult(t.peak_value, t), ex = mult(t.exit_price, t);
    return `<tr id="t-${t.date}">` +
      `<td>${weekday(t.date)} ${niceDate(t.date)} <span style="color:var(--faint)">${t.date.slice(0, 4)}</span></td>` +
      `<td class="fly"><span class="dir">${t.direction}</span>${flyText(t)}<small>${t.width}w</small></td>` +
      `<td class="r">${t.vix != null ? t.vix.toFixed(1) : '—'}</td>` +
      `<td>${t.entry_time}–${t.exit_time}</td>` +
      `<td class="r">${plainMoney(t.entry_price * 100)}</td>` +
      `<td class="r mult ${pk >= 3 ? 'hi' : ''}">${multText(pk)}</td>` +
      `<td class="r mult">${multText(ex)}</td>` +
      `<td class="how">${exitInfo(t.exit_reason).label}</td>` +
      `<td class="r ${cls(t.pnl)}">${money(t.pnl)}</td></tr>`;
  }).join('');
  document.getElementById('logCount').textContent = `${shown.length} of ${rows.length} trades · ${money(sum(rows))}`;
  const more = document.getElementById('logMore');
  more.hidden = rows.length <= PAGE;
  more.textContent = showAll ? 'Show fewer' : `Show all ${rows.length}`;
}
document.querySelectorAll('#logFilter button').forEach((b) => b.addEventListener('click', () => {
  document.querySelectorAll('#logFilter button').forEach((o) => o.setAttribute('aria-pressed', String(o === b)));
  filter = b.dataset.f; renderLog();
}));
document.getElementById('logMore').addEventListener('click', () => { showAll = !showAll; renderLog(); });
function jumpToTrade(date) {
  filter = 'all'; showAll = true;
  document.querySelectorAll('#logFilter button').forEach((o) => o.setAttribute('aria-pressed', String(o.dataset.f === 'all')));
  renderLog();
  const row = document.getElementById('t-' + date);
  if (!row) return;
  row.scrollIntoView({ behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'center' });
  row.classList.add('flash'); setTimeout(() => row.classList.remove('flash'), 1800);
}
renderLog();

})();
