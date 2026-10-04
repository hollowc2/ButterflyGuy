"""Schwab-vs-ThetaData fidelity report on synthetic, arbitrage-free sessions."""

from __future__ import annotations

import datetime as dt
import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pyarrow as pa

from butterfly_guy.research import fidelity
from butterfly_guy.research.dataset import (
    Dataset,
    Manifest,
    SessionChain,
    chain_to_table,
    session_dir,
    write_table,
)
from butterfly_guy.research.market import et_us

D = dt.date(2026, 6, 3)
STRIKES = np.arange(5800.0, 6201.0, 5.0)
CONFIG = SimpleNamespace(strategy=SimpleNamespace(
    wing_widths=[10, 20], vix_width_buckets=[SimpleNamespace(widths=[20, 30])], spot_range=100))


def _spot(n: int) -> np.ndarray:
    steps = np.random.default_rng(7).normal(0.0, 2.0, n)
    return 6000.0 + np.cumsum(steps)


def _value(s: np.ndarray, t: str) -> np.ndarray:
    x = (s[:, None] - STRIKES[None, :]) / 5.0
    return 5.0 * np.logaddexp(0.0, x if t == "C" else -x) + 1.0


def _chain(ts: np.ndarray, spot: np.ndarray, strikes=STRIKES) -> SessionChain:
    keep = np.isin(STRIKES, strikes)
    fields = {}
    for t in ("C", "P"):
        mid = np.round(_value(spot, t) * 20) / 20
        fields[f"{t}_bid"] = (mid - 0.05)[:, keep]
        fields[f"{t}_ask"] = (mid + 0.05)[:, keep]
        fields[f"{t}_mark"] = mid[:, keep]
        fields[f"{t}_iv"] = np.full(mid.shape, 0.2, dtype=np.float32)[:, keep]
        fields[f"{t}_delta"] = np.full(mid.shape, 0.5, dtype=np.float32)[:, keep]
    return SessionChain(date=D, ts=ts, strikes=STRIKES[keep], spot=spot, fields=fields)


def _write(root, name: str, chain: SessionChain, event_us: np.ndarray | None = None,
           vix: bool = False) -> Dataset:
    root = root / name
    m = Manifest(dataset=name, underlying="SPX", source={"kind": "test"}, export={})
    rel = session_dir(D)
    m.files[f"{rel}/chain.parquet"] = write_table(chain_to_table(chain),
                                                  root / rel / "chain.parquet")
    clock = {"ts_us": chain.ts, "spot": chain.spot}
    if event_us is not None:
        clock[fidelity.EVENT_COLUMN] = event_us
    m.files[f"{rel}/clock.parquet"] = write_table(pa.table(clock), root / rel / "clock.parquet")
    m.files["sessions.parquet"] = write_table(
        pa.Table.from_pandas(pd.DataFrame({"date": [pd.Timestamp(D)]})),
        root / "sessions.parquet")
    ticks = chain.ts if vix else np.array([], dtype=np.int64)
    m.files["spot_ticks.parquet"] = write_table(pa.table({
        "ts_us": ticks, "underlying": ["$VIX"] * len(ticks),
        "price": np.full(len(ticks), 15.0)}), root / "spot_ticks.parquet")
    m.save(root / "manifest.json")
    return Dataset(root)


GRID = et_us(D, 9, 31) + np.arange(390, dtype=np.int64) * 60_000_000
SPOT = _spot(390)


def _pair(tmp_path, *, offset_s: float = 20.0, shift: int = 0, strikes=STRIKES,
          event_us: bool = False):
    vendor = _write(tmp_path, "vendor", _chain(GRID, SPOT))
    # Helios quotes are the state at minute i - shift, stamped `offset_s` after minute i.
    src = np.clip(np.arange(390) - shift, 0, None)
    ts = GRID + int(offset_s * 1e6)
    helios_chain = _chain(ts, SPOT[src], strikes)
    events = (GRID + 2_000_000) if event_us else None
    helios = _write(tmp_path, "helios", helios_chain, events, vix=True)
    return helios, vendor


def test_exact_quotes_agree_everywhere(tmp_path):
    helios, vendor = _pair(tmp_path)
    summary, rows = fidelity.run(helios, vendor, D, D, CONFIG)
    assert summary["timing_basis"] == "snapshot_time"
    assert summary["thresholds"] is None and "TODO" in summary["thresholds_todo"]
    assert summary["matching"]["matched"] == 390
    assert summary["matching"]["matched_by_lateness_s"]["15-30"] == 390
    p = summary["prices"]["overall"]
    assert p["cells"] > 0 and p["agree_within_tol"] == 1.0
    assert p["abs_mid"]["p95"] == 0.0 and p["spread"]["p95"] == 0.0
    f = summary["flies"]["overall"]
    assert f["flies"] > 0 and f["abs_mid"]["p95"] == 0.0 and f["share_abs_over_0.05"] == 0.0
    assert summary["meta"]["fly_widths"] == [10, 20, 30]
    assert summary["coverage"]["missing_in_helios"] == 0
    assert summary["coverage"]["minutes_without_snapshot"] == 0
    assert summary["quality"]["helios"]["crossed"] == 0
    assert summary["quality"]["vendor"]["arb_violations"] == 0
    assert rows[0]["vix"]["observations"] == 389  # the 16:00:20 tick is after the close
    # Parity spot on exact mids sits within a rounding step of the true level.
    assert summary["spot"]["abs"]["p95"] <= 0.1


def test_one_minute_shift_is_detected(tmp_path):
    helios, vendor = _pair(tmp_path, shift=1)
    summary, _ = fidelity.run(helios, vendor, D, D, CONFIG)
    p, f = summary["prices"]["overall"], summary["flies"]["overall"]
    assert p["agree_within_tol"] < 0.9
    assert p["abs_mid"]["p95"] > 0.5
    assert f["share_abs_over_0.05"] > 0.0


def test_missing_strikes_are_counted(tmp_path):
    keep = STRIKES[(STRIKES < 5990) | (STRIKES > 6010)]
    helios, vendor = _pair(tmp_path, strikes=keep)
    summary, _ = fidelity.run(helios, vendor, D, D, CONFIG)
    c = summary["coverage"]
    assert c["missing_in_helios"] > 0 and 0 < c["missing_share"] < 0.2
    assert summary["prices"]["overall"]["agree_within_tol"] == 1.0


def test_quote_event_time_is_the_basis_when_recorded(tmp_path):
    helios, vendor = _pair(tmp_path, offset_s=40.0, event_us=True)
    summary, _ = fidelity.run(helios, vendor, D, D, CONFIG)
    assert summary["timing_basis"] == "quote_event_ts"
    assert summary["matching"]["matched_by_lateness_s"]["0-5"] == 390


def test_missing_snapshots_and_lateness(tmp_path):
    vendor = _write(tmp_path, "vendor", _chain(GRID, SPOT))
    keep = np.ones(390, dtype=bool)
    keep[100:110] = False
    helios = _write(tmp_path, "helios", _chain(GRID[keep] + 45_000_000, SPOT[keep]))
    summary, rows = fidelity.run(helios, vendor, D, D, CONFIG)
    assert rows[0]["coverage"]["minutes_without_snapshot"] == 10
    assert rows[0]["coverage"]["longest_gap_minutes"] == 10
    assert summary["matching"]["matched_by_lateness_s"]["30-60"] == 380
    assert rows[0]["vix"] == {"observations": 0, "max_gap_s": None}


def test_rerun_is_byte_identical(tmp_path):
    helios, vendor = _pair(tmp_path, shift=1)
    inputs = {"helios": helios.hash, "vendor": vendor.hash}
    out = tmp_path / "out"
    first = fidelity.publish(out, *fidelity.run(helios, vendor, D, D, CONFIG), inputs, D)
    files = {p.name: p.read_bytes() for p in first.iterdir()}
    second = fidelity.publish(out, *fidelity.run(helios, vendor, D, D, CONFIG), inputs, D)
    assert first == second
    assert files == {p.name: p.read_bytes() for p in second.iterdir()}
    other = fidelity.publish(tmp_path / "other", *fidelity.run(helios, vendor, D, D, CONFIG),
                             inputs, D)
    assert other.name == first.name
    for name in ("summary.json", "sessions.jsonl"):
        assert (other / name).read_bytes() == files[name]
    prov = json.loads(files["provenance.json"])
    assert prov["input_sha256"] == inputs
    fidelity.verify_artifact(first)


def test_histogram_quantiles_are_nearest_rank():
    h = fidelity.Hist()
    h.add(np.array([0.0, 0.05, 0.10, 0.15, np.nan]))
    assert h.n == 4
    assert h.quantile(0.5) == 0.05 and h.quantile(0.95) == 0.15
    assert h.share_above(0.05) == 0.5
