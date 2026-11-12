// Butterfly Guy strategy lab. Served as a same-origin file so the site CSP
// (script-src 'self' + hashes) needs no new entry. Parameters come from the
// application/json block the generator writes from the live config.
(() => {
  const P = JSON.parse(document.getElementById('strategy-params').textContent);
  const STEP = 5;                 // SPX strike grid
  const VOL_SCALE = 0.62;         // 0-DTE IV sits well under the 30-day VIX
  const DAY_MIN = Math.round(P.hoursLeft * 60);   // minutes from entry to the 4:00 close
  // Snapshot curves, in minutes left: spaced tighter toward the close, where the tent forms.
  const SNAPSHOTS = [DAY_MIN, 180, 90, 45, 15].filter((m, i) => i === 0 || m < DAY_MIN);
  const PLAY_MS = 6500;
  const yearsLeft = (minLeft) => minLeft / 60 / 6.5 / 252;
  const T = yearsLeft(DAY_MIN);
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const SVG_NS = 'http://www.w3.org/2000/svg';

  const $ = (id) => document.getElementById(id);
  const fmt = (n, d = 2) => n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
  const money = (n) => `${n < 0 ? '−' : '+'}$${Math.abs(Math.round(n)).toLocaleString('en-US')}`;

  // left = minutes to the close on the payoff clock; 0 is the expiry tent.
  const state = { dir: 'CALL', vix: 16, pinned: null, settle: null, left: 0 };

  // ---------- pricing ----------
  function ncdf(x) {
    const t = 1 / (1 + 0.2316419 * Math.abs(x));
    const d = 0.3989423 * Math.exp(-x * x / 2);
    const p = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274))));
    return x > 0 ? 1 - p : p;
  }
  function bs(S, K, vol, call, years = T) {
    const sd = vol * Math.sqrt(years);
    const d1 = (Math.log(S / K) + 0.5 * sd * sd) / sd;
    const d2 = d1 - sd;
    return call ? S * ncdf(d1) - K * ncdf(d2) : K * ncdf(-d2) - S * ncdf(-d1);
  }
  const round05 = (x) => Math.round(x * 20) / 20;
  function quote(K) {
    const mid = Math.max(0.05, round05(bs(P.spot, K, state.vix / 100 * VOL_SCALE, state.dir === 'CALL')));
    const half = mid < 1 ? 0.05 : mid < 10 ? 0.1 : 0.2;
    return { strike: K, mid, bid: Math.max(0, mid - half), ask: mid + half };
  }

  // ---------- the bot's selection rules ----------
  function bucketFor(vix) {
    return P.buckets.find((b) => vix < b.vixMax) || P.buckets[P.buckets.length - 1];
  }
  const expectedMove = (vix) => P.spot * (vix / 100) / Math.sqrt(252);
  function fly(center, width) {
    const lo = quote(center - width), c = quote(center), hi = quote(center + width);
    const cost = Math.round((lo.mid - 2 * c.mid + hi.mid) * 100) / 100;
    return { width, center, lower: center - width, upper: center + width, cost, rr: cost > 0 ? (width - cost) / cost : 0 };
  }
  function failReason(f) {
    const cap = P.maxCostPerWidth[String(f.width)];
    if (f.cost < P.minDebit) return 'too far out — worthless';
    if (cap != null && f.cost > cap) return `costs more than $${fmt(cap)} cap`;
    if (f.rr < P.rrMin) return `R:R under ${P.rrMin}:1`;
    return null;
  }
  // Mirrors ButterflySelector.select_best: prefer R:R ≤ max, closest to target, wider on tie.
  function pickBest(pool) {
    if (!pool.length) return null;
    const capped = pool.filter((f) => f.rr <= P.rrMax);
    const use = capped.length ? capped : pool;
    return use.reduce((best, f) => {
      const a = Math.abs(f.rr - P.rrTarget), b = Math.abs(best.rr - P.rrTarget);
      return a < b || (a === b && f.width > best.width) ? f : best;
    });
  }
  function scan() {
    const bucket = bucketFor(state.vix);
    const em = expectedMove(state.vix);
    const sign = state.dir === 'CALL' ? 1 : -1;
    const rows = bucket.widths.map((width, i) => {
      const sigma = bucket.sigmas[i];
      const target = Math.round((P.spot + sign * sigma * em) / STEP) * STEP;
      const pool = [];
      for (let c = target - P.centerTolerance; c <= target + P.centerTolerance; c += STEP) pool.push(fly(c, width));
      const passing = pool.filter((f) => !failReason(f));
      const best = pickBest(passing);
      const shown = best || pool.find((f) => f.center === target);
      return { width, sigma, target, best, shown, reason: best ? null : failReason(shown) };
    });
    const chosen = pickBest(rows.filter((r) => r.best).map((r) => r.best));
    return { bucket, em, rows, chosen };
  }

  // ---------- rendering ----------
  function renderControls(result) {
    $('vixOut').textContent = state.vix.toFixed(1);
    $('regimeName').textContent = result.bucket.name;
    document.querySelectorAll('.regime').forEach((el) => {
      el.classList.toggle('active', Number(el.dataset.vixMax) === result.bucket.vixMax);
    });
    document.querySelectorAll('.seg').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.dir === state.dir)));
  }

  function renderWidths(result, active) {
    const wrap = $('widths');
    wrap.replaceChildren(...result.rows.map((row) => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'width-card';
      btn.setAttribute('aria-pressed', String(active && active.width === row.width));
      const f = row.shown;
      const isPick = result.chosen && result.chosen.width === row.width;
      const status = row.best
        ? (isPick ? '<span class="wc-status pick">★ the bot buys this one</span>' : '<span class="wc-status ok">✓ qualifies</span>')
        : `<span class="wc-status fail">✗ ${row.reason}</span>`;
      btn.innerHTML = `
        <span class="wc-top"><span class="wc-width">${row.width}-wide</span><span class="wc-sigma">center ${row.sigma}σ out</span></span>
        <span class="wc-nums">${fmt(f.lower, 0)} / ${fmt(f.center, 0)} / ${fmt(f.upper, 0)} · $${fmt(f.cost)} · ${f.rr.toFixed(1)}:1</span>
        ${status}`;
      btn.addEventListener('click', () => {
        state.pinned = state.pinned === row.width ? null : row.width;
        state.settle = null;
        render();
      });
      return btn;
    }));
  }

  function renderChain(f) {
    const side = state.dir === 'CALL' ? 'calls' : 'puts';
    $('chainTitle').textContent = `${P.underlying} 0-DTE ${side} · ${P.entryEt} ET`;
    const want = new Set();
    for (const k of [f.lower - 10, f.lower - 5, f.lower, f.lower + 5, f.center - 5, f.center, f.center + 5,
      f.upper - 5, f.upper, f.upper + 5, f.upper + 10]) want.add(k);
    const spotLo = Math.floor(P.spot / STEP) * STEP;
    want.add(spotLo); want.add(spotLo + STEP);
    // High strikes on top, like a price ladder; spot sorts below a strike it sits on.
    const entries = [...want].map((k) => ({ k })).concat([{ k: P.spot, spot: true }])
      .sort((a, b) => b.k - a.k || (a.spot ? 1 : -1));
    const tbody = $('chain').tBodies[0];
    const out = [];
    let prev = null;
    for (const e of entries) {
      if (e.spot) {
        out.push(`<tr class="spot"><td>${P.underlying} ${fmt(P.spot)}</td><td colspan="4">◂ spot · ${Math.abs(f.center - P.spot).toFixed(0)} pts to the center</td></tr>`);
        continue;
      }
      if (prev !== null && prev - e.k > STEP) {
        const skipped = (prev - e.k) / STEP - 1;
        out.push(`<tr class="gap"><td colspan="5">⋮ ${skipped} strike${skipped === 1 ? '' : 's'}</td></tr>`);
      }
      const q = quote(e.k);
      let cls = '', leg = '';
      if (e.k === f.lower || e.k === f.upper) { cls = 'leg'; leg = '<span class="leg-tag buy">BUY 1</span>'; }
      else if (e.k === f.center) { cls = 'leg leg-sell'; leg = '<span class="leg-tag sell">SELL 2</span>'; }
      else if (e.k > f.lower && e.k < f.upper) cls = 'in-tent';
      out.push(`<tr class="${cls}"><td>${fmt(e.k, 0)}</td><td>${fmt(q.bid)}</td><td>${fmt(q.mid)}</td><td>${fmt(q.ask)}</td><td>${leg}</td></tr>`);
      prev = e.k;
    }
    tbody.innerHTML = out.join('');
  }

  // Model value of the fly with minLeft to the close; 0 is the expiry payoff. Call and put
  // flies on the same strikes share both (put-call parity, no rates), so calls price either.
  function flyValue(f, S, minLeft) {
    if (minLeft <= 0) return Math.max(0, f.width - Math.abs(S - f.center));
    const vol = state.vix / 100 * VOL_SCALE, years = yearsLeft(minLeft);
    return bs(S, f.lower, vol, true, years) - 2 * bs(S, f.center, vol, true, years) + bs(S, f.upper, vol, true, years);
  }
  // Mark-to-model P&L per contract.
  const pnlAt = (f, S, minLeft = state.left) => (flyValue(f, S, minLeft) - f.cost) * 100;
  const clockAt = (minLeft) => {
    const total = 16 * 60 - minLeft;
    return `${Math.floor(total / 60) % 12 || 12}:${String(total % 60).padStart(2, '0')}`;
  };
  // Expiry is piecewise linear, so its kinks are exact; earlier curves are sampled.
  function curvePoints(f, minLeft, x0, x1, n) {
    const xs = minLeft <= 0 ? [x0, f.lower, f.center, f.upper, x1]
      : Array.from({ length: n + 1 }, (_, i) => x0 + (x1 - x0) * i / n).concat([f.center]).sort((a, b) => a - b);
    return xs.map((s) => [s, pnlAt(f, s, minLeft)]);
  }

  function renderPayoff(result, f) {
    const svg = $('payoff');
    // Size the viewBox to the rendered width so labels stay at their CSS size on phones.
    const W = Math.max(300, Math.round(svg.clientWidth || 640));
    const H = Math.round(Math.min(300, Math.max(210, W * 0.47)));
    const L = 52, R = 16, Tp = 22, B = 34;
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    const pad = Math.max(f.width * 0.7, 20);
    const x0 = Math.min(P.spot, f.lower) - pad;
    const x1 = Math.max(P.spot, f.upper) + pad;
    const yMax = (f.width - f.cost) * 100, yMin = -f.cost * 100;
    const yLo = yMin - (yMax - yMin) * 0.1, yHi = yMax + (yMax - yMin) * 0.14;
    const sx = (s) => L + (s - x0) / (x1 - x0) * (W - L - R);
    const sy = (v) => Tp + (yHi - v) / (yHi - yLo) * (H - Tp - B);
    const el = (tag, attrs, text) => {
      const node = document.createElementNS(SVG_NS, tag);
      for (const [k, v] of Object.entries(attrs)) node.setAttribute(k, v);
      if (text != null) node.textContent = text;
      return node;
    };
    const kids = [];
    // 1σ expected-move band around spot
    const emLo = Math.max(x0, P.spot - result.em), emHi = Math.min(x1, P.spot + result.em);
    kids.push(el('rect', { class: 'em-band', x: sx(emLo), y: Tp, width: sx(emHi) - sx(emLo), height: H - Tp - B }));
    const n = Math.round((W - L - R) / 3);
    const path = (pts) => pts.map(([s, v]) => `${sx(s).toFixed(1)},${sy(v).toFixed(1)}`).join(' ');
    // profit / loss fills under the curve at the current clock, split at $0
    const now = curvePoints(f, state.left, x0, x1, n);
    const area = `${sx(x0)},${sy(0)} ${path(now)} ${sx(x1)},${sy(0)}`;
    const defs = el('defs', {});
    const clip = (id, y, h) => {
      const c = el('clipPath', { id });
      c.appendChild(el('rect', { x: 0, y, width: W, height: Math.max(0, h) }));
      defs.appendChild(c);
    };
    clip('pz-up', 0, sy(0));
    clip('pz-dn', sy(0), H - sy(0));
    kids.push(defs);
    kids.push(el('polygon', { class: 'profit', points: area, 'clip-path': 'url(#pz-up)' }));
    kids.push(el('polygon', { class: 'loss', points: area, 'clip-path': 'url(#pz-dn)' }));
    kids.push(el('line', { class: 'zero', x1: L, x2: W - R, y1: sy(0), y2: sy(0) }));
    kids.push(el('line', { class: 'axis', x1: L, x2: W - R, y1: H - B, y2: H - B }));
    // the day's snapshots, faint to firmer toward the close; labels at each peak, skipped if crowded
    let lastLabelY = -Infinity;
    const labelX = sx(f.center) + 8;
    const snaps = SNAPSHOTS.filter((m) => m !== state.left);
    snaps.forEach((m, i) => {
      kids.push(el('polyline', { class: 'ghost', 'stroke-opacity': (0.18 + 0.32 * i / Math.max(1, snaps.length - 1)).toFixed(2), points: path(curvePoints(f, m, x0, x1, n)) }));
    });
    if (state.left > 0) kids.push(el('polyline', { class: 'tent-ghost', points: path(curvePoints(f, 0, x0, x1, n)) }));
    [0, ...snaps.slice().reverse()].forEach((m) => {
      if (m === 0 && state.left === 0) return;
      const y = sy(pnlAt(f, f.center, m));
      if (y - lastLabelY < 13 || y > sy(0) - 4) return;
      kids.push(el('text', { x: labelX, y: y + 4, class: m === 0 ? 't-accent t-faint' : 't-faint' }, m === 0 ? '4:00' : clockAt(m)));
      lastLabelY = y;
    });
    kids.push(el('polyline', { class: 'curve', points: path(now) }));
    const peakNow = pnlAt(f, f.center, state.left);
    // spot + strike ticks
    kids.push(el('line', { class: 'spot-line', x1: sx(P.spot), x2: sx(P.spot), y1: Tp, y2: H - B }));
    kids.push(el('text', { x: sx(P.spot), y: Tp - 6, 'text-anchor': 'middle', class: 't-strong' }, 'spot'));
    [[f.lower, ''], [f.center, 't-accent'], [f.upper, '']].forEach(([k, cls]) => {
      kids.push(el('text', { x: sx(k), y: H - B + 16, 'text-anchor': 'middle', class: cls }, fmt(k, 0)));
    });
    kids.push(state.dir === 'CALL'
      ? el('text', { x: sx(emHi) - 4, y: H - 4, 'text-anchor': 'end' }, '← 1σ day move')
      : el('text', { x: sx(emLo) + 4, y: H - 4 }, '1σ day move →'));
    kids.push(el('text', { x: L - 8, y: sy(yMax) + 4, 'text-anchor': 'end', class: 't-accent' }, money(yMax)));
    if (sy(yMin) - sy(0) > 14) kids.push(el('text', { x: L - 8, y: sy(0) + 4, 'text-anchor': 'end' }, '$0'));
    kids.push(el('text', { x: L - 8, y: sy(yMin) + 4, 'text-anchor': 'end' }, money(yMin)));
    // crosshair
    const S = state.settle;
    const v = pnlAt(f, S);
    const color = v >= 0 ? '#6aaa78' : '#cc5555';
    kids.push(el('line', { class: 'cross', x1: sx(S), x2: sx(S), y1: Tp, y2: H - B }));
    kids.push(el('circle', { class: 'cross-dot', cx: sx(S), cy: sy(v), r: 6, fill: color }));
    const right = sx(S) > W * 0.62;
    kids.push(el('text', { x: sx(S) + (right ? -10 : 10), y: Math.max(Tp + 12, sy(v) - 12), 'text-anchor': right ? 'end' : 'start', class: 't-strong' }, money(v)));
    svg.replaceChildren(...kids);

    const range = $('settle');
    range.min = x0; range.max = x1; range.value = S;
    $('settleOut').textContent = `${fmt(S)} → ${money(v)}`;
    $('settleOut').style.color = color;
    $('settleWhen').textContent = state.left > 0 ? `at ${clockAt(state.left)} ET` : 'at the 4:00 close';
    svg._scale = { x0, x1, L, R, W };
    renderClock(f, yMax, peakNow);
  }

  function renderClock(f, yMax, peakNow) {
    const clock = $('clock');
    clock.max = DAY_MIN;
    clock.value = DAY_MIN - state.left;
    const left = state.left;
    $('clockOut').textContent = left > 0
      ? `${clockAt(left)} ET · ${left >= 60 ? `${Math.floor(left / 60)}h ` : ''}${left % 60 ? `${left % 60}m ` : ''}left`
      : '4:00 · expired';
    const center = fmt(f.center, 0);
    $('decayNote').innerHTML = left > 0
      ? `If ${P.underlying} were on ${center} at ${clockAt(left)}, the fly would be up <b>${money(peakNow)}</b> — ${Math.max(0, Math.round(peakNow / yMax * 100))}% of the
        <b>${money(yMax)}</b> it pays if ${P.underlying} is still there at 4:00. Time left keeps the curve low and wide; it sharpens fastest in the last hour.`
      : `At 4:00 the curve becomes the tent: the full <b>${money(yMax)}</b> only if ${P.underlying} settles on ${center}, nothing past the wings.
        The faint lines are the same fly earlier in the day.`;
  }

  function renderTicket(f, result) {
    const qualifies = !failReason(f);
    const picked = result.chosen && result.chosen.width === f.width && result.chosen.center === f.center;
    const side = state.dir === 'CALL' ? 'call' : 'put';
    const verdict = $('verdict');
    if (picked) {
      verdict.innerHTML = `<span class="v-main">The bot buys the ${f.width}-wide ${side} fly for $${fmt(f.cost)}</span><span class="v-sub">${result.bucket.name} · risk $${Math.round(f.cost * 100)} to make up to $${Math.round((f.width - f.cost) * 100).toLocaleString('en-US')}</span>`;
    } else if (!result.chosen) {
      verdict.innerHTML = `<span class="v-main no">No qualifying fly — the bot sits out today</span><span class="v-sub">showing the ${f.width}-wide anyway: ${failReason(f)}</span>`;
    } else {
      verdict.innerHTML = `<span class="v-main">Exploring the ${f.width}-wide</span><span class="v-sub">${qualifies ? 'qualifies, but another width is closer to the target' : failReason(f)}</span>`;
    }
    const cells = [
      ['Debit (max loss)', `$${Math.round(f.cost * 100)}`],
      ['Max profit', `$${Math.round((f.width - f.cost) * 100).toLocaleString('en-US')}`],
      ['Reward : risk', `${f.rr.toFixed(1)} : 1`],
      ['Breakevens', `${fmt(f.lower + f.cost, 0)}–${fmt(f.upper - f.cost, 0)}`],
    ];
    $('ticket').innerHTML = cells.map(([k, v]) => `<div><dt>${k}</dt><dd>${v}</dd></div>`).join('');
  }

  let current = null;   // last scan + displayed fly, reused while only the settle point moves

  function render() {
    const result = scan();
    const pinnedRow = result.rows.find((r) => r.width === state.pinned);
    const active = pinnedRow ? (pinnedRow.best || pinnedRow.shown)
      : result.chosen || result.rows[result.rows.length - 1].shown;
    if (state.settle == null) state.settle = active.center;
    renderControls(result);
    renderWidths(result, active);
    renderChain(active);
    renderPayoff(result, active);
    renderTicket(active, result);
    current = { result, active };
  }

  function renderSettle(value) {
    state.settle = value;
    renderPayoff(current.result, current.active);
  }

  // ---------- events ----------
  document.querySelectorAll('.seg').forEach((b) => b.addEventListener('click', () => {
    state.dir = b.dataset.dir; state.pinned = null; state.settle = null; render();
  }));
  $('vix').addEventListener('input', (e) => {
    state.vix = Number(e.target.value); state.pinned = null; state.settle = null; render();
  });
  $('settle').addEventListener('input', (e) => renderSettle(Number(e.target.value)));

  // ---------- the clock ----------
  let anim = null;
  function setPlaying(on) {
    $('play').setAttribute('aria-pressed', String(on));
    $('play').textContent = on ? '❚❚ pause' : '▶ play the day';
  }
  function stop() {
    if (anim) cancelAnimationFrame(anim.raf);
    anim = null;
    setPlaying(false);
  }
  function setClock(minLeft) {
    state.left = Math.max(0, Math.min(DAY_MIN, Math.round(minLeft)));
    if (current) renderPayoff(current.result, current.active);
  }
  function play() {
    if (anim) { stop(); return; }
    const startLeft = state.left > 0 ? state.left : DAY_MIN;
    // Ease the clock so the last hour, where the tent forms, gets screen time.
    const from = 1 - Math.pow(startLeft / DAY_MIN, 1 / 1.6);
    const t0 = performance.now() - from * PLAY_MS;
    const step = (now) => {
      const p = Math.min(1, (now - t0) / PLAY_MS);
      setClock(DAY_MIN * Math.pow(1 - p, 1.6));
      if (p < 1) anim.raf = requestAnimationFrame(step);
      else stop();
    };
    anim = { raf: requestAnimationFrame(step) };
    setPlaying(true);
  }
  $('play').addEventListener('click', play);
  $('clock').addEventListener('input', (e) => { stop(); setClock(DAY_MIN - Number(e.target.value)); });
  // Play the day once, the first time the chart scrolls into view.
  if (!reduceMotion && 'IntersectionObserver' in window) {
    const seen = new IntersectionObserver((entries) => {
      if (!entries.some((e) => e.isIntersecting)) return;
      seen.disconnect();
      if (!anim && state.left === 0) { state.left = DAY_MIN; play(); }
    }, { threshold: 0.6 });
    seen.observe($('payoff'));
  }
  const svg = $('payoff');
  const track = (e) => {
    const s = svg._scale;
    if (!s) return;
    const box = svg.getBoundingClientRect();
    const px = (e.clientX - box.left) / box.width * s.W;
    const frac = Math.min(1, Math.max(0, (px - s.L) / (s.W - s.L - s.R)));
    renderSettle(Math.round((s.x0 + frac * (s.x1 - s.x0)) * 4) / 4);
  };
  svg.addEventListener('pointermove', track);
  svg.addEventListener('pointerdown', track);
  window.addEventListener('resize', () => current && renderPayoff(current.result, current.active));

  $('tolOut').textContent = P.centerTolerance;
  $('vix').min = P.vixScale[0];
  $('vix').max = P.vixScale[1];
  render();
})();
