"""Fidelity validation of a vendor dataset against the Helios export.

Steps 1-4 of the validation plan in `docs/research/history-vendor-readiness.md`. The pass
criteria were fixed there before any vendor data was seen and are copied here verbatim
(`CRITERIA`); they must not be relaxed after seeing results. The validation uses
sessions already seen (2026-03-13 onward), so it says nothing about any rule.

Where the plan leaves a detail open, this module fixes it (and `report.md` repeats it):

- **σ (step 1)** is the session's chain-implied remaining move, 1.25 x the Helios ATM
  straddle at the snapshot at or before 10:00 ET, as in the 2026-09-25 journal. The OTM
  region is 1.0-2.5 σ from the Helios spot at each snapshot: calls above spot, puts below.
- **A bid/ask pair agrees** when both sources quote it and both the bid and the ask differ
  by at most $0.05. The 95% share is taken at offset 0 (the vendor quote as of the Helios
  timestamp); the offset scan (-180..+180 s in 15 s steps, scored on the same region)
  reports the offset that maximises agreement, the smaller |offset| winning a tie.
- **Step 2** replays E0 on a derived dataset: vendor quotes sampled at the Helios chain
  timestamps, with the Helios clock, spot, VIX and daily bars. A disagreement is a session
  where the fly, entry time or exit reason differs, one side did not trade, or a P&L
  differs by more than half a cent. It is *explained* when a vendor and Helios quote differ
  at a decision snapshot on or before it: for an entry, any quote of the gap direction's
  type within the selection span of spot at a clock time in the entry window up to the
  later entry; for an exit or P&L, a leg of the fly between the entry and the later exit.
- **Step 3** runs the vendor dataset under `vendor_1m` against each step-2 Helios profile
  on the sessions both replay. It passes when the vendor stressed total lies inside the
  Helios replay's $0.10 tie-set draw band (5th-95th percentile of the draw totals) for
  every profile.
- **Step 4** requires every official SPX close the vendor supplies on a compared session
  to equal (to the cent) the Helios `daily_bars` close and Cboe's published SPX close.
  Spot differences are reported, with no threshold, as the plan says.
"""

from __future__ import annotations

import datetime as dt
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa

from butterfly_guy.research.accounting import MODELS
from butterfly_guy.research.dataset import (
    OPTION_TYPES,
    Dataset,
    Manifest,
    SessionChain,
    chain_to_table,
    default_cache_root,
    session_dir,
    write_table,
)
from butterfly_guy.research.entry import (
    PROFILES,
    RunContext,
    Session,
    SessionLoader,
    gap_direction,
    selection_span,
)
from butterfly_guy.research.evaluate import common_dates
from butterfly_guy.research.market import TYPE_CODE, et_us
from butterfly_guy.research.simulate import RunResult, Trade, run_variants
from butterfly_guy.research.tieset import TiesetScorer
from butterfly_guy.research.variants import resolve

SOURCE_DOC = "docs/research/history-vendor-readiness.md"
CRITERIA = {
    1: "at least 95% of bid/ask pairs within $0.05 in the 1.0–2.5σ OTM region where the "
       "strategy trades. The best offset is within one minute.",
    2: "the same fly on at least 90% of entries. Stressed total within the larger of ±5% "
       "and ±$750. Each disagreement explained by a quote difference at a decision snapshot.",
    3: "the stressed total's difference from the Helios replay is inside the $0.10 tie-set "
       "draw band of the Helios replay.",
    4: "Official closes against our `daily_bars` and Cboe settlement values: they must be "
       "identical, since settlement-dependent P&L relies on them.",
}
QUOTE_TOL = 0.05
QUOTE_SHARE = 0.95
OTM_REGION = (1.0, 2.5)
QUOTE_BAND = 200.0
MAX_OFFSET_S = 60
OFFSETS_S = tuple(range(-180, 181, 15))
SAME_FLY = 0.90
STRESSED_REL, STRESSED_ABS = 0.05, 750.0
PNL_TOL = 0.005
TIE = 0.10
HELIOS_PROFILES = ("frozen_20260921", "sweep_20260925")
VENDOR_PROFILE = "vendor_1m"
SIGMA_AT = (10, 0)
STRADDLE_MULTIPLE = 1.25


def _dates(helios: Dataset, vendor: Dataset, start: dt.date, end: dt.date) -> list[dt.date]:
    a = {d for d in helios.sessions()["date"] if start <= d <= end}
    b = {d for d in vendor.sessions()["date"] if start <= d <= end}
    return sorted(a & b)


def _vendor_index(v: SessionChain, ts: np.ndarray) -> np.ndarray:
    return np.searchsorted(v.ts, ts, side="right") - 1


def _take(a: np.ndarray, rows: np.ndarray) -> np.ndarray:
    out = np.full((len(rows), a.shape[1]), np.nan)
    ok = rows >= 0
    out[ok] = a[rows[ok]]
    return out


def session_sigma(h: SessionChain) -> float | None:
    i = int(np.searchsorted(h.ts, et_us(h.date, *SIGMA_AT), side="right")) - 1
    if i < 0:
        return None
    j = int(np.argmin(np.abs(h.strikes - h.spot[i])))
    c, p = h.fields["C_mark"][i, j], h.fields["P_mark"][i, j]
    if not (np.isfinite(c) and np.isfinite(p)) or c + p <= 0:
        return None
    return STRADDLE_MULTIPLE * float(c + p)


# ---------------------------------------------------------------------------
# Step 1: quote level
# ---------------------------------------------------------------------------


@dataclass
class QuoteTally:
    both: int = 0
    within: int = 0
    only_helios: int = 0
    only_vendor: int = 0
    region_both: int = 0
    region_within: int = 0
    diff_counts: np.ndarray = field(default_factory=lambda: np.zeros(50_001, dtype=np.int64))

    def median_abs_diff(self) -> float | None:
        n = int(self.diff_counts.sum())
        if n == 0:
            return None
        k = int(np.searchsorted(np.cumsum(self.diff_counts), (n + 1) // 2))
        return k / 1000


def _compare(h: SessionChain, v: SessionChain, sigma: float | None, offset_s: int,
             tally: QuoteTally, *, full: bool) -> None:
    ks, hk, vk = np.intersect1d(h.strikes, v.strikes, return_indices=True)
    if len(ks) == 0:
        return
    rows = _vendor_index(v, h.ts + offset_s * 1_000_000)
    band = np.abs(ks[None, :] - h.spot[:, None]) <= QUOTE_BAND
    for t in OPTION_TYPES:
        hb, ha, hm = (h.fields[f"{t}_{f}"][:, hk] for f in ("bid", "ask", "mark"))
        vb, va, vm = (_take(v.fields[f"{t}_{f}"][:, vk], rows) for f in ("bid", "ask", "mark"))
        hq = np.isfinite(hb) & np.isfinite(ha) & np.isfinite(hm)
        vq = np.isfinite(vb) & np.isfinite(va) & np.isfinite(vm)
        both = band & hq & vq
        with np.errstate(invalid="ignore"):
            db, da = np.abs(hb - vb), np.abs(ha - va)
            within = both & (db <= QUOTE_TOL + 1e-9) & (da <= QUOTE_TOL + 1e-9)
        if sigma is not None:
            dist = ((ks[None, :] - h.spot[:, None]) if t == "C"
                    else (h.spot[:, None] - ks[None, :])) / sigma
            region = both & (dist >= OTM_REGION[0]) & (dist <= OTM_REGION[1])
            tally.region_both += int(region.sum())
            tally.region_within += int((region & within).sum())
        if full:
            tally.both += int(both.sum())
            tally.within += int(within.sum())
            tally.only_helios += int((band & hq & ~vq).sum())
            tally.only_vendor += int((band & vq & ~hq).sum())
            diffs = np.concatenate([db[both], da[both]])
            np.add.at(tally.diff_counts,
                      np.minimum(np.rint(diffs * 1000).astype(np.int64), 50_000), 1)


def step1(helios: Dataset, vendor: Dataset, dates: list[dt.date]) -> dict:
    at_zero = QuoteTally()
    scan = {o: QuoteTally() for o in OFFSETS_S if o != 0}
    no_sigma = []
    for d in dates:
        h, v = helios.chain(d), vendor.chain(d)
        sigma = session_sigma(h)
        if sigma is None:
            no_sigma.append(d.isoformat())
        _compare(h, v, sigma, 0, at_zero, full=True)
        for o, tally in scan.items():
            _compare(h, v, sigma, o, tally, full=False)
    share = {0: _share(at_zero)} | {o: _share(t) for o, t in scan.items()}
    scored = {o: s for o, s in share.items() if s is not None}
    best = (min(scored, key=lambda o: (-scored[o], abs(o))) if scored else None)
    region_share = share[0]
    passed = (region_share is not None and region_share >= QUOTE_SHARE and best is not None
              and abs(best) <= MAX_OFFSET_S)
    pairs = at_zero.both + at_zero.only_helios + at_zero.only_vendor
    return {
        "pass": passed,
        "region_pairs": at_zero.region_both,
        "region_share_within": region_share,
        "band_pairs_both": at_zero.both,
        "band_share_within": None if not at_zero.both else round(at_zero.within / at_zero.both, 6),
        "median_abs_diff": at_zero.median_abs_diff(),
        "presence": {"both": at_zero.both, "only_helios": at_zero.only_helios,
                     "only_vendor": at_zero.only_vendor,
                     "agreement": None if not pairs else round(at_zero.both / pairs, 6)},
        "offset_scan": {str(o): share[o] for o in sorted(share)},
        "best_offset_s": best,
        "sessions_without_sigma": no_sigma,
    }


def _share(t: QuoteTally) -> float | None:
    return None if not t.region_both else round(t.region_within / t.region_both, 6)


# ---------------------------------------------------------------------------
# Step 2: replay on the Helios clock
# ---------------------------------------------------------------------------


def build_helios_clock_dataset(helios: Dataset, vendor: Dataset, dates: list[dt.date],
                               root: Path) -> Dataset:
    """Vendor quotes sampled at Helios chain timestamps, with the Helios clock, spot,
    VIX and daily bars (so only quotes differ)."""
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    files = {}
    for rel in ("daily_bars.parquet", "spot_ticks.parquet"):
        shutil.copyfile(helios.root / rel, root / rel)
        files[rel] = dict(helios.manifest.files[rel])
    sessions = helios.sessions()
    sessions = sessions[sessions["date"].isin(dates)].assign(
        date=lambda x: pd.to_datetime(x["date"]))
    files["sessions.parquet"] = write_table(pa.Table.from_pandas(sessions, preserve_index=False),
                                            root / "sessions.parquet")
    for d in dates:
        h, v = helios.chain(d), vendor.chain(d)
        rows = _vendor_index(v, h.ts)
        fields = {k: _take(a, rows).astype(a.dtype) for k, a in v.fields.items()}
        chain = SessionChain(date=d, ts=h.ts.copy(), strikes=v.strikes.copy(), spot=h.spot.copy(),
                             fields=fields)
        rel = session_dir(d)
        files[f"{rel}/chain.parquet"] = write_table(chain_to_table(chain),
                                                    root / rel / "chain.parquet")
        (root / rel).mkdir(parents=True, exist_ok=True)
        shutil.copyfile(helios.root / rel / "clock.parquet", root / rel / "clock.parquet")
        files[f"{rel}/clock.parquet"] = dict(helios.manifest.files[f"{rel}/clock.parquet"])
    Manifest(dataset=root.name, underlying="SPX",
             source={"kind": "derived_helios_clock", "helios": helios.hash, "vendor": vendor.hash},
             export={"kind": "derived_helios_clock"}, files=files).save(root / "manifest.json")
    return Dataset(root)


def _pnl(t: Trade) -> dict[str, float | None]:
    return {m: t.pnl(m) for m in MODELS}


def _first_difference(a: SessionChain, b: SessionChain, snapshots: list[int], t: str,
                      strikes: np.ndarray) -> dict | None:
    """The first (snapshot, strike) among `strikes` where the two chains' quotes differ."""
    for i in snapshots:
        for k in strikes:
            qa, qb = _quote(a, i, t, k), _quote(b, i, t, k)
            if not all((np.isnan(x) and np.isnan(y)) or abs(x - y) < 1e-9
                       for x, y in zip(qa, qb, strict=True)):
                return {"ts": _iso(int(a.ts[i])), "type": t, "strike": float(k),
                        "helios": _q(qa), "vendor": _q(qb)}
    return None


def _quote(c: SessionChain, i: int, t: str, k: float) -> tuple[float, float, float]:
    j = c.column(float(k))
    if j is None or i < 0 or i >= len(c.ts):
        return (np.nan, np.nan, np.nan)
    return tuple(float(c.fields[f"{t}_{f}"][i, j]) for f in ("bid", "ask", "mark"))


def _q(q: tuple[float, float, float]) -> list[float | None]:
    return [None if np.isnan(x) else round(x, 4) for x in q]


def _iso(ts_us: int | None) -> str | None:
    if ts_us is None:
        return None
    return dt.datetime.fromtimestamp(ts_us / 1e6, tz=dt.UTC).isoformat()


def explain(hs: Session, vs: Session, ctx: RunContext, a: Trade | None, b: Trade | None
            ) -> dict | None:
    """A quote difference at a decision snapshot that explains a disagreement, or None."""
    h, v = hs.market.chain, vs.market.chain
    same_entry = (a is not None and b is not None and a.fly == b.fly
                  and a.entry_ts_us == b.entry_ts_us)
    if not same_entry:
        lo, hi = ctx.window(hs.date)
        later = max([t.entry_ts_us for t in (a, b) if t is not None], default=hi)
        direction = gap_direction(hs)
        span = selection_span(ctx.config)
        for ts in hs.clock_ts[(hs.clock_ts >= lo) & (hs.clock_ts <= later)]:
            i = hs.market.at_or_before(int(ts))
            spot = float(hs.clock_spot[hs.clock_index(int(ts))])
            strikes = np.union1d(h.strikes, v.strikes)
            strikes = strikes[np.abs(strikes - spot) <= span]
            found = _first_difference(h, v, [i], TYPE_CODE[direction], strikes)
            if found:
                return {"at": "entry decision", **found}
        return None
    fly = a.fly
    last = max(x if x is not None else len(h.ts) - 1 for x in (a.exit_index, b.exit_index))
    legs = np.array([fly.lower, fly.center, fly.upper])
    found = _first_difference(h, v, list(range(a.entry_index, last + 1)),
                              TYPE_CODE[fly.direction], legs)
    return None if found is None else {"at": "position", **found}


def compare_replays(helios_run: RunResult, other_run: RunResult, helios_loader: SessionLoader,
                    other_loader: SessionLoader, ctx: RunContext) -> dict:
    ha = {t.date: t for t in helios_run.runs["E0"].trades}
    ob = {t.date: t for t in other_run.runs["E0"].trades}
    dates = sorted(set(ha) | set(ob))
    rows, same_fly = [], 0
    for d in dates:
        a, b = ha.get(d), ob.get(d)
        issues = []
        if a is None or b is None:
            issues.append("only in " + ("vendor" if a is None else "helios"))
        else:
            if a.fly != b.fly:
                fa, fb = a.fly, b.fly
                issues.append(f"fly {fa.direction} {fa.lower:g}/{fa.center:g}/{fa.upper:g} "
                              f"vs {fb.direction} {fb.lower:g}/{fb.center:g}/{fb.upper:g}")
            else:
                same_fly += 1
            if a.entry_ts_us != b.entry_ts_us:
                issues.append(f"entry {_iso(a.entry_ts_us)} vs {_iso(b.entry_ts_us)}")
            if a.exit_reason != b.exit_reason:
                issues.append(f"exit {a.exit_reason} vs {b.exit_reason}")
            pa_, pb_ = _pnl(a), _pnl(b)
            for m in MODELS:
                x, y = pa_[m], pb_[m]
                if (x is None) != (y is None) or (x is not None and abs(x - y) > PNL_TOL):
                    issues.append(f"{m} {x} vs {y}")
        if issues:
            hs, vs = helios_loader.load(d), other_loader.load(d)
            why = explain(hs, vs, ctx, a, b) if hs is not None and vs is not None else None
            rows.append({"date": d.isoformat(), "issues": issues, "explained_by": why})
    totals = {m: {"helios": round(sum((t.pnl(m) or 0.0) for t in ha.values()), 2),
                  "vendor": round(sum((t.pnl(m) or 0.0) for t in ob.values()), 2)}
              for m in MODELS}
    return {"sessions_with_trades": len(dates), "same_fly": same_fly,
            "same_fly_share": None if not dates else round(same_fly / len(dates), 6),
            "totals": totals, "disagreements": rows}


def step2(helios: Dataset, hybrid: Dataset, dates: list[dt.date], ctx: RunContext) -> dict:
    out: dict = {"profiles": {}}
    passed = True
    for name in HELIOS_PROFILES:
        prof = PROFILES[name]
        hl, vl = SessionLoader(helios, prof), SessionLoader(hybrid, prof)
        hr = run_variants(hl, resolve(["E0"]), ctx, start=dates[0], end=dates[-1])
        vr = run_variants(vl, resolve(["E0"]), ctx, start=dates[0], end=dates[-1])
        cmp = compare_replays(hr, vr, SessionLoader(helios, prof), SessionLoader(hybrid, prof),
                              ctx)
        h_tot, v_tot = cmp["totals"]["stressed"]["helios"], cmp["totals"]["stressed"]["vendor"]
        tol = max(STRESSED_REL * abs(h_tot), STRESSED_ABS)
        unexplained = [r["date"] for r in cmp["disagreements"] if r["explained_by"] is None]
        checks = {
            "same_fly": cmp["same_fly_share"] is None or cmp["same_fly_share"] >= SAME_FLY,
            "stressed_total": abs(v_tot - h_tot) <= tol,
            "disagreements_explained": not unexplained,
        }
        cmp.update({"stressed_tolerance": round(tol, 2),
                    "stressed_difference": round(v_tot - h_tot, 2),
                    "unexplained": unexplained, "checks": checks, "pass": all(checks.values())})
        out["profiles"][name] = cmp
        passed &= cmp["pass"]
    out["pass"] = passed
    return out


# ---------------------------------------------------------------------------
# Step 3: replay on the vendor clock
# ---------------------------------------------------------------------------


def _distribution(result: RunResult, dates: list[dt.date], scorer: TiesetScorer) -> dict:
    keep = set(dates)
    trades = [t for t in result.runs["E0"].trades if t.date in keep]
    stressed = [t.pnl("stressed") or 0.0 for t in trades]
    ties = scorer.summary(["E0"], dates)["E0"]
    return {
        "sessions": len(dates), "trades": len(trades),
        "stressed_total": round(float(sum(stressed)), 2),
        "per_trade_median": None if not stressed else round(float(np.median(stressed)), 2),
        "settled": sum(t.exit_reason == "cash_settled" for t in trades),
        "tieset": {k: ties[k]["stressed"] for k in ("0.10", "0.25") if k in ties},
    }


def step3(helios: Dataset, vendor: Dataset, dates: list[dt.date], ctx: RunContext) -> dict:
    vs = TiesetScorer()
    vr = run_variants(SessionLoader(vendor, PROFILES[VENDOR_PROFILE]), resolve(["E0"]), ctx,
                      start=dates[0], end=dates[-1], tieset=vs)
    out: dict = {"profiles": {}}
    passed = True
    for name in HELIOS_PROFILES:
        hs = TiesetScorer()
        hr = run_variants(SessionLoader(helios, PROFILES[name]), resolve(["E0"]), ctx,
                          start=dates[0], end=dates[-1], tieset=hs)
        common = sorted(set(common_dates(hr, ["E0"])[0]) & set(common_dates(vr, ["E0"])[0]))
        h, v = _distribution(hr, common, hs), _distribution(vr, common, vs)
        band = h["tieset"].get(f"{TIE:.2f}", {})
        lo, hi = band.get("draw_p05"), band.get("draw_p95")
        ok = lo is not None and hi is not None and lo <= v["stressed_total"] <= hi
        out["profiles"][name] = {"helios": h, "vendor": v, "band": [lo, hi],
                                 "difference": round(v["stressed_total"] - h["stressed_total"], 2),
                                 "pass": ok}
        passed &= ok
    out["pass"] = passed
    return out


# ---------------------------------------------------------------------------
# Step 4: spot and settlement
# ---------------------------------------------------------------------------


def step4(helios: Dataset, vendor: Dataset, dates: list[dt.date], cboe_spx: pd.DataFrame) -> dict:
    diffs, sources = [], {}
    for d in dates:
        hc, v = helios.clock(d), vendor.chain(d)
        rows = _vendor_index(v, hc.ts)
        ok = rows >= 0
        vs = np.where(ok, v.spot[np.maximum(rows, 0)], np.nan)
        dd = np.abs(vs - hc.spot)
        diffs.append(dd[np.isfinite(dd)])
        s = vendor.sessions().set_index("date")
        src = str(s.loc[d, "spot_source"]) if "spot_source" in s.columns else "unknown"
        sources[src] = sources.get(src, 0) + 1
    alld = np.concatenate(diffs) if diffs else np.array([])

    def closes(ds_bars: pd.DataFrame) -> dict[dt.date, float]:
        b = ds_bars[ds_bars["underlying"] == "SPX"]
        return {d: float(c) for d, c in zip(b["date"], b["close"], strict=True) if np.isfinite(c)}

    vc, hc_ = closes(vendor.daily_bars()), closes(helios.daily_bars())
    cboe = {d: float(c) for d, c in zip(cboe_spx["date"], cboe_spx["close"], strict=True)}
    mismatches, missing = [], []
    for d in dates:
        if d not in vc:
            missing.append(d.isoformat())
            continue
        for label, ref in (("helios_daily_bars", hc_), ("cboe", cboe)):
            if d not in ref:
                missing.append(f"{d.isoformat()} ({label})")
            elif round(vc[d], 2) != round(ref[d], 2):
                mismatches.append({"date": d.isoformat(), "vendor": vc[d], label: ref[d]})
    return {
        "spot": {"points": int(len(alld)),
                 "median_abs": None if not len(alld) else round(float(np.median(alld)), 4),
                 "p99_abs": None if not len(alld) else round(float(np.percentile(alld, 99)), 4),
                 "spot_sources": sources},
        "closes": {"compared": len(dates) - len([m for m in missing if "(" not in m]),
                   "mismatches": mismatches, "missing": missing},
        "pass": not mismatches and not missing,
    }


def parse_cboe_spx(data: bytes) -> pd.DataFrame:
    """Cboe's public `SPX_History.csv` (columns DATE, SPX)."""
    import io

    df = pd.read_csv(io.BytesIO(data))
    df.columns = [c.strip().upper() for c in df.columns]
    if list(df.columns) != ["DATE", "SPX"]:
        raise ValueError(f"unexpected Cboe SPX columns {list(df.columns)}")
    return pd.DataFrame({"date": pd.to_datetime(df["DATE"], format="%m/%d/%Y").dt.date,
                         "close": pd.to_numeric(df["SPX"], errors="coerce")})


# ---------------------------------------------------------------------------
# Whole validation
# ---------------------------------------------------------------------------


def validate(helios: Dataset, vendor: Dataset, start: dt.date, end: dt.date, ctx: RunContext,
             cboe_spx: pd.DataFrame, work_root: Path | None = None) -> dict:
    dates = _dates(helios, vendor, start, end)
    if not dates:
        raise ValueError("no sessions in both datasets")
    work = (work_root or default_cache_root() / "_validation") / f"{vendor.name}__helios_clock"
    hybrid = build_helios_clock_dataset(helios, vendor, dates, work)
    steps = {
        "1": step1(helios, vendor, dates),
        "2": step2(helios, hybrid, dates, ctx),
        "3": step3(helios, vendor, dates, ctx),
        "4": step4(helios, vendor, dates, cboe_spx),
    }
    return {
        "meta": {"helios": {"dataset": helios.name, "dataset_hash": helios.hash},
                 "vendor": {"dataset": vendor.name, "dataset_hash": vendor.hash,
                            "source": vendor.manifest.source},
                 "range": [start.isoformat(), end.isoformat()], "sessions": len(dates),
                 "criteria_source": SOURCE_DOC,
                 "criteria": {str(k): v for k, v in CRITERIA.items()}},
        "steps": steps,
        "pass": all(s["pass"] for s in steps.values()),
    }


def _pf(ok: bool) -> str:
    return "PASS" if ok else "FAIL"


def markdown(results: dict, provenance: dict) -> str:
    m, s = results["meta"], results["steps"]
    s1, s4 = s["1"], s["4"]
    lines = [
        f"# Vendor fidelity validation ({provenance['run_id']})",
        "",
        f"- Vendor: `{m['vendor']['dataset']}` @ `{m['vendor']['dataset_hash'][:12]}`; "
        f"Helios: `{m['helios']['dataset']}` @ `{m['helios']['dataset_hash'][:12]}`",
        f"- Sessions: {m['sessions']} ({m['range'][0]} → {m['range'][1]}); seen data, so this "
        "says nothing about any rule.",
        f"- Criteria: verbatim from `{m['criteria_source']}`, fixed before any vendor data.",
        f"- **Overall: {_pf(results['pass'])}.** A failed step blocks the development download.",
        "",
        "| Step | Criterion | Measured | Threshold | Result |",
        "|---|---|---|---|---|",
        f"| 1 quote level | {CRITERIA[1]} | {s1['region_share_within']} of "
        f"{s1['region_pairs']} region pairs within $0.05; best offset {s1['best_offset_s']} s "
        f"| ≥ {QUOTE_SHARE}; \\|offset\\| ≤ {MAX_OFFSET_S} s | {_pf(s1['pass'])} |",
    ]
    for name, p in s["2"]["profiles"].items():
        lines.append(
            f"| 2 Helios clock, `{name}` | {CRITERIA[2]} | same fly {p['same_fly_share']}; "
            f"stressed Δ {p['stressed_difference']}; unexplained {len(p['unexplained'])} | "
            f"≥ {SAME_FLY}; \\|Δ\\| ≤ {p['stressed_tolerance']}; 0 | {_pf(p['pass'])} |")
    for name, p in s["3"]["profiles"].items():
        lines.append(
            f"| 3 vendor clock vs `{name}` | {CRITERIA[3]} | vendor stressed "
            f"{p['vendor']['stressed_total']} (Helios {p['helios']['stressed_total']}) | "
            f"band {p['band']} | {_pf(p['pass'])} |")
    lines.append(
        f"| 4 settlement | {CRITERIA[4]} | {len(s4['closes']['mismatches'])} mismatches, "
        f"{len(s4['closes']['missing'])} missing | 0 and 0 | {_pf(s4['pass'])} |")
    lines += [
        "",
        "## Step 1 detail",
        "",
        f"- Band pairs quoted in both: {s1['band_pairs_both']}, share within $0.05: "
        f"{s1['band_share_within']}; median |Δ| ${s1['median_abs_diff']}.",
        f"- Presence: {s1['presence']}.",
        f"- Offset scan (region share by offset, s): {s1['offset_scan']}.",
        f"- Sessions without a 10:00 σ: {s1['sessions_without_sigma'] or 'none'}.",
        "",
        "## Step 2 disagreements",
        "",
    ]
    for name, p in s["2"]["profiles"].items():
        lines.append(f"### `{name}`: totals {p['totals']['stressed']}")
        lines.append("")
        for r in p["disagreements"]:
            why = r["explained_by"]
            lines.append(f"- {r['date']}: {'; '.join(r['issues'])} — "
                         + ("**unexplained**" if why is None else
                            f"{why['at']} {why['ts']} {why['type']} {why['strike']:g}: "
                            f"Helios {why['helios']} vs vendor {why['vendor']}"))
        if not p["disagreements"]:
            lines.append("- none")
        lines.append("")
    lines += ["## Step 3 distributions", ""]
    for name, p in s["3"]["profiles"].items():
        lines.append(f"- `{name}`: Helios {p['helios']}; vendor {p['vendor']}")
    lines += ["", "## Step 4", "", f"- Spot: {s4['spot']}.",
              f"- Closes: {s4['closes']}.", ""]
    return "\n".join(lines)
