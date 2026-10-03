"""Build harness inputs (chain_days.pkl, spot.csv, daily.csv) from the local ThetaData archive.

Usage (needs pandas + pyarrow):
  python thetadata_prep.py START END OUT_DIR [--helios-spot data/spot.csv]

Sources
  options    : data/thetadata/spxw_0dte/quote_1m (minute NBBO, America/New_York).
               mark = (bid + ask) / 2; a row with bid 0 and ask 0 is "no quote" (NaN).
  index/VIX  : owner minute CSVs data/spx_1min.csv and data/vix_1min.csv (America/Chicago,
               bar END, price = bar close) through 2025-12-09; Helios spot_prices export for
               2026-03-13 onward (--helios-spot).
  settlement : FRED SP500 official close (OUT_DIR/fred_sp500.csv must exist).
Guards: refuses dates in the sealed holdout (2024-07-01 .. 2026-03-12); skips the owner's
development exclusion 2022-06-02. The output is ThetaData-derived and must not be committed.
"""
import argparse
import datetime as dt
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[3]
ARCHIVE = REPO.parent / "Butterflyguy" / "data" / "thetadata" / "spxw_0dte" / "quote_1m"
OWNER = REPO.parent / "Butterflyguy" / "data"
SEALED = (dt.date(2024, 7, 1), dt.date(2026, 3, 12))
EXCLUDE = {dt.date(2022, 6, 2)}
OWNER_LAST = dt.date(2025, 12, 9)
STRIKE_RANGE = 200


def owner_minutes(path, lo, hi):
    df = pd.read_csv(path, usecols=["ts", "open", "close"])
    t = pd.to_datetime(df.ts).dt.tz_localize("America/Chicago").dt.tz_convert("America/New_York")
    df = df.assign(et=t)
    df = df[(df.et.dt.date >= lo) & (df.et.dt.date <= hi)]
    tod = df.et.dt.hour * 60 + df.et.dt.minute
    df = df[(tod >= 9 * 60 + 31) & (tod <= 16 * 60)]  # RTH bar ends; drop the 16:01-16:15 filler
    rows = [(int(r.et.timestamp()), float(r.close)) for r in df.itertuples()]
    firsts = df.groupby(df.et.dt.date).head(1)  # 09:30 point = first bar's open
    rows += [(int(r.et.timestamp()) - 60, float(r.open)) for r in firsts.itertuples()]
    return sorted(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("start", type=dt.date.fromisoformat)
    ap.add_argument("end", type=dt.date.fromisoformat)
    ap.add_argument("out", type=Path)
    ap.add_argument("--helios-spot", type=Path)
    a = ap.parse_args()
    if not (a.end < SEALED[0] or a.start > SEALED[1]):
        sys.exit(f"refusing: range overlaps the sealed holdout {SEALED[0]}..{SEALED[1]}")
    a.out.mkdir(parents=True, exist_ok=True)

    files = sorted(p for y in range(a.start.year, a.end.year + 1)
                   for p in (ARCHIVE / str(y)).glob("*.parquet")
                   if a.start <= dt.date.fromisoformat(p.stem) <= a.end
                   and dt.date.fromisoformat(p.stem) not in EXCLUDE)

    spot_rows = []  # (ts, u, price)
    if a.start <= OWNER_LAST:
        hi = min(a.end, OWNER_LAST)
        spot_rows += [(t, "SPX", p) for t, p in owner_minutes(OWNER / "spx_1min.csv", a.start, hi)]
        spot_rows += [(t, "$VIX", p) for t, p in owner_minutes(OWNER / "vix_1min.csv", a.start, hi)]
    if a.end > OWNER_LAST:
        if not a.helios_spot:
            sys.exit("dates after 2025-12-09 need --helios-spot")
        h = pd.read_csv(a.helios_spot)
        hd = pd.to_datetime(h.ts, unit="s", utc=True).dt.tz_convert("America/New_York").dt.date
        h = h[(hd >= max(a.start, OWNER_LAST + dt.timedelta(days=1))) & (hd <= a.end)]
        spot_rows += list(h[["ts", "u", "price"]].itertuples(index=False, name=None))
    spot = pd.DataFrame(spot_rows, columns=["ts", "u", "price"]).sort_values("ts")
    spot.to_csv(a.out / "spot.csv", index=False)
    spx = spot[spot.u == "SPX"]
    sts, spx_px = spx.ts.to_numpy(), spx.price.to_numpy()

    fred = pd.read_csv(a.out / "fred_sp500.csv")
    fred = fred[pd.to_numeric(fred.SP500, errors="coerce").notna()]
    days, daily = {}, []
    for p in files:
        d = dt.date.fromisoformat(p.stem)
        q = pd.read_parquet(p, columns=["strike", "right", "timestamp", "bid", "ask"])
        tod = q.timestamp.dt.hour * 60 + q.timestamp.dt.minute
        q = q[(tod >= 9 * 60 + 30) & (tod <= 16 * 60) & (q.strike == q.strike.round())]
        if q.empty:
            continue
        q = q.assign(ts=(q.timestamp.astype("int64") // 10**6).astype("int64"), k=q.strike.astype(int),
                     t=q.right.str[0])
        ts = np.sort(q.ts.unique())
        idx = np.searchsorted(sts, ts, side="right") - 1
        ok = (idx >= 0) & (sts[np.clip(idx, 0, None)] >= ts - 300)
        if ok.sum() < len(ts) * 0.9:
            print(f"skip {d}: index minutes missing", file=sys.stderr)
            continue
        spot_ts = np.where(ok, spx_px[np.clip(idx, 0, None)], np.nan).astype(np.float32)
        mid = float(np.nanmedian(spot_ts))
        q = q[(q.k - mid).abs() <= STRIKE_RANGE]
        ks = np.sort(q.k.unique())
        ti = {v: i for i, v in enumerate(ts)}
        ki = {v: i for i, v in enumerate(ks)}
        r, c = q.ts.map(ti).to_numpy(), q.k.map(ki).to_numpy()
        noq = ((q.bid == 0) & (q.ask == 0)).to_numpy()
        bid = np.where(noq, np.nan, q.bid.to_numpy())
        ask = np.where(noq, np.nan, q.ask.to_numpy())
        out = {"ts": ts, "k": ks, "spot": spot_ts}
        for typ in ("C", "P"):
            m = (q.t == typ).to_numpy()
            for f, v in (("bid", bid), ("ask", ask), ("mark", (bid + ask) / 2)):
                arr = np.full((len(ts), len(ks)), np.nan, dtype=np.float32)
                arr[r[m], c[m]] = v[m]
                out[f"{typ}_{f}"] = arr
            for f in ("iv", "delta"):
                out[f"{typ}_{f}"] = np.full((len(ts), len(ks)), np.nan, dtype=np.float32)
        days[d] = out
        fr = fred[fred.observation_date == d.isoformat()]
        if not fr.empty:
            daily.append((d.isoformat(), "SPX", float(spot_ts[0]), np.nan, np.nan, float(fr.SP500.iloc[0])))
    # prior-session closes for the first day(s) and any day whose prior session had no file
    for r in fred.itertuples():
        dd = dt.date.fromisoformat(r.observation_date)
        if dd not in days and a.start - dt.timedelta(days=10) <= dd <= a.end:
            daily.append((r.observation_date, "SPX", np.nan, np.nan, np.nan, float(r.SP500)))
    pd.DataFrame(daily, columns=["date", "u", "open", "high", "low", "close"]).sort_values("date") \
        .to_csv(a.out / "daily.csv", index=False)
    pickle.dump(days, open(a.out / "chain_days.pkl", "wb"), protocol=5)
    print(f"days {len(days)} of {len(files)} files; spot rows {len(spot)}", file=sys.stderr)


if __name__ == "__main__":
    main()
