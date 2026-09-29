"""Rebuild the committed mini dataset used by tests/test_research_parity.py.

    uv run python tests/fixtures/research/build_fixture.py

Reads the full research cache (see docs/research/research-core.md) and writes
`mini_spx/` plus `mini_expected.json`. Each chosen session keeps every quote the
entry search can see (snapshots 09:59-10:46 ET, strikes within the selection span of
spot, the traded option type) and, after that, only the traded legs of the frozen and
sweep E0 trades. IV, delta and everything else are NaN, so the files stay small while
E0 replays identically. 2026-06-12 has a full chain but no qualifying fly.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import structlog

from butterfly_guy.research.dataset import (
    Dataset,
    Manifest,
    SessionChain,
    chain_to_table,
    session_dir,
    write_table,
)
from butterfly_guy.research.entry import (
    PROFILES,
    RunContext,
    SessionLoader,
    load_spx_config,
    selection_span,
)
from butterfly_guy.research.market import et_us
from butterfly_guy.research.report import trade_record
from butterfly_guy.research.simulate import run_variants
from butterfly_guy.research.variants import resolve

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "frozen_ledger_b83c2a18.json"
DATES = [dt.date(2026, 3, 19), dt.date(2026, 3, 26), dt.date(2026, 4, 7),
         dt.date(2026, 4, 16), dt.date(2026, 6, 12), dt.date(2026, 7, 13)]


def main() -> None:
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    ds = Dataset.open()
    ctx = RunContext(load_spx_config())
    span = selection_span(ctx.config)
    trades = {}
    for profile in ("frozen_20260921", "sweep_20260925"):
        loader = SessionLoader(ds, PROFILES[profile])
        result = run_variants(loader, resolve(["E0"]), ctx, start=DATES[0], end=DATES[-1])
        trades[profile] = {t.date: t for t in result.runs["E0"].trades if t.date in DATES}

    out = HERE / "mini_spx"
    manifest = Manifest(dataset="mini_spx", underlying="SPX",
                        source={"kind": "fixture", "from_dataset_hash": ds.hash},
                        export=ds.manifest.export)
    sessions = ds.sessions()
    all_dates = list(sessions["date"])
    for d in DATES:
        chain, clock = ds.chain(d), ds.clock(d)
        window = (chain.ts >= et_us(d, 9, 59)) & (chain.ts <= et_us(d, 10, 46))
        near = (np.abs(chain.strikes[None, :] - chain.spot[:, None]) <= span)
        keep = window[:, None] & near
        day_trades = [t for t in (trades[p].get(d) for p in trades) if t is not None]
        types = {t.fly.direction[0] for t in day_trades} or {"C", "P"}
        legs = {k for t in day_trades for k in (t.fly.lower, t.fly.center, t.fly.upper)}
        leg_cols = np.isin(chain.strikes, sorted(legs))
        cols = keep.any(axis=0) | leg_cols
        fields = {}
        for name, a in chain.fields.items():
            if name[0] in types and name[2:] in ("bid", "ask", "mark"):
                b = np.where(keep | leg_cols[None, :], a, np.nan)
            else:
                b = np.full_like(a, np.nan)
            fields[name] = b[:, cols]
        mini = SessionChain(date=d, ts=chain.ts, strikes=chain.strikes[cols], spot=chain.spot,
                            fields=fields)
        rel = session_dir(d)
        manifest.files[f"{rel}/chain.parquet"] = write_table(
            chain_to_table(mini), out / rel / "chain.parquet")
        clock_df = pd.DataFrame({"ts_us": clock.ts, "spot": clock.spot,
                                 "spot_min": clock.spot, "spot_max": clock.spot})
        manifest.files[f"{rel}/clock.parquet"] = write_table(
            pa.Table.from_pandas(clock_df, preserve_index=False), out / rel / "clock.parquet")

    rows = sessions[sessions["date"].isin(DATES)].copy()
    rows["date"] = pd.to_datetime(rows["date"])
    manifest.files["sessions.parquet"] = write_table(
        pa.Table.from_pandas(rows, preserve_index=False), out / "sessions.parquet")
    bars = ds.daily_bars()
    bars = bars[bars["date"] <= DATES[-1]].copy()
    bars["date"] = pd.to_datetime(bars["date"])
    manifest.files["daily_bars.parquet"] = write_table(
        pa.Table.from_pandas(bars, preserve_index=False), out / "daily_bars.parquet")
    ticks = []
    for u in ("SPX", "$VIX"):
        ts, px = ds.spot_ticks(u)
        mask = np.zeros(len(ts), dtype=bool)
        for d in DATES:
            prior = max(x for x in all_dates if x < d)
            mask |= (ts >= et_us(prior, 15, 0)) & (ts <= et_us(d, 10, 50))
        ticks.append(pd.DataFrame({"ts_us": ts[mask], "underlying": u, "price": px[mask]}))
    manifest.files["spot_ticks.parquet"] = write_table(
        pa.Table.from_pandas(pd.concat(ticks, ignore_index=True), preserve_index=False),
        out / "spot_ticks.parquet")
    manifest.updated_at = "fixture"
    manifest.save(out / "manifest.json")

    ledger = {r["date"]: r for r in json.loads(LEDGER.read_text())}
    expected = {
        "dates": [d.isoformat() for d in DATES],
        "frozen_ledger": {d.isoformat(): ledger.get(d.isoformat()) for d in DATES},
        "sweep_e0": {d.isoformat(): trade_record(t) for d, t in trades["sweep_20260925"].items()},
    }
    (HERE / "mini_expected.json").write_text(json.dumps(expected, indent=1, sort_keys=True) + "\n")
    print(f"mini dataset {manifest.dataset_hash}")


if __name__ == "__main__":
    main()
