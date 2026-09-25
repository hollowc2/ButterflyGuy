"""Convert the exported chain CSV into per-day dense arrays (ts x strike) per option type."""
import os
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

D = Path(os.environ.get("SWEEP_DATA", Path(__file__).resolve().parent / "data"))
df = pd.read_csv(D / "chain.csv.gz", dtype={"ts": "int64", "k": "int32", "t": "category",
                 "bid": "float32", "ask": "float32", "mark": "float32", "iv": "float32",
                 "delta": "float32", "s": "float32"})
df["dt"] = pd.to_datetime(df.ts, unit="s", utc=True).dt.tz_convert("America/New_York")
df["d"] = df.dt.dt.date
print("rows", len(df), "days", df.d.nunique(), file=sys.stderr)
days = {}
for d, g in df.groupby("d", sort=True):
    ts = np.sort(g.ts.unique())
    ks = np.sort(g.k.unique())
    ti = {v: i for i, v in enumerate(ts)}
    ki = {v: i for i, v in enumerate(ks)}
    r = g.ts.map(ti).to_numpy(); c = g.k.map(ki).to_numpy()
    out = {"ts": ts, "k": ks}
    spot = g.groupby("ts").s.first().reindex(ts).to_numpy()
    out["spot"] = spot
    for t in ("C", "P"):
        m = (g.t == t).to_numpy()
        for f in ("bid", "ask", "mark", "iv", "delta"):
            a = np.full((len(ts), len(ks)), np.nan, dtype=np.float32)
            a[r[m], c[m]] = g[f].to_numpy()[m]
            out[f"{t}_{f}"] = a
    days[d] = out
pickle.dump(days, open(D / "chain_days.pkl", "wb"), protocol=5)
print("saved", len(days), file=sys.stderr)
