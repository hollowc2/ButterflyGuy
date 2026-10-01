"""Local archive regression fixtures contain invented prices, never vendor data."""
import datetime as dt
import io
from dataclasses import replace

import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import pytest

from butterfly_guy.research.cli import main
from butterfly_guy.research.dataset import Dataset, chain_to_table, table_to_chain
from butterfly_guy.research.entry import PROFILES, Entry, RunContext, SessionLoader, load_spx_config
from butterfly_guy.research.exits import PeakTrailer, TimeExit
from butterfly_guy.research.history import HistoryPlan, QualityNotPassedError, write_history
from butterfly_guy.research.holdout import HoldoutSealedError
from butterfly_guy.research.lifecycle import capability_check, replay_position
from butterfly_guy.research.local import LocalThetaDataSource, audit, import_local
from butterfly_guy.research.market import Fly, et_us
from tests.research_synth import FakeSource, synthetic_day

FRIDAY = dt.date(2026, 5, 22)
TUESDAY = dt.date(2026, 5, 26)  # Memorial Day gap
PROFILE = replace(PROFILES["vendor_1m"], integer_strikes=False)


def support(tmp_path, dates=(FRIDAY, TUESDAY)):
    days = {d: synthetic_day(d) for d in dates}
    prior = synthetic_day(dates[0] - dt.timedelta(days=1))["bars"]
    write_history(FakeSource(days, extra_bars=prior),
                  HistoryPlan(min(dates), max(dates), "spx_0dte_fake", require_quality=False,
                              log=io.StringIO()), tmp_path)
    return Dataset.open("spx_0dte_fake", tmp_path)


def raw(tmp_path, d=FRIDAY, expiration=None, set_name="spxw_0dte", root="SPXW"):
    day = synthetic_day(d)
    df = day["quotes"].rename(columns={"t": "right"})
    df["right"] = df.right.map({"C": "CALL", "P": "PUT"})
    df["timestamp"] = pd.to_datetime(df.ts_us, unit="us", utc=True).dt.tz_convert(
        "America/New_York")
    df["symbol"], df["expiration"] = root, expiration or d
    df["bid_size"], df["ask_size"] = 2, 3
    path = tmp_path / "raw" / set_name / "quote_1m" / str(d.year) / f"{d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    return path


def source(tmp_path, set_name="spxw_0dte", dataset="spx_0dte_local_test", dates=None):
    return LocalThetaDataSource(tmp_path / "raw", set_name, dataset,
                                support(tmp_path, dates=dates or (FRIDAY, TUESDAY)))


def normalize(src, tmp_path, d=FRIDAY):
    return import_local(src, HistoryPlan(d, d, src.dataset, log=io.StringIO()), tmp_path)


def test_guard_before_any_raw_io_and_cli_construction(tmp_path, monkeypatch):
    src = source(tmp_path)
    def fail(*args, **kwargs):
        pytest.fail("raw parquet opened before guard")
    monkeypatch.setattr(pq, "ParquetFile", fail)
    protected = dt.date(2025, 1, 2)
    for f in (lambda: src.quotes(protected, (0, 99999)),
              lambda: src.sessions(protected, protected),
              lambda: src.path(protected),
              lambda: audit(src, protected, protected),
              lambda: import_local(src, HistoryPlan(protected, protected, src.dataset), tmp_path)):
        with pytest.raises(HoldoutSealedError):
            f()
    assert main(["--dataset", src.dataset, "import-local", "--archive", "/missing",
                 "--set", "spxw_0dte", "--support", "missing", "--start", "2025-01-02",
                 "--end", "2025-01-02"]) == 2


def test_no_quote_missing_greeks_sizes_and_identity(tmp_path):
    src = source(tmp_path)
    p = raw(tmp_path)
    df = pd.read_parquet(p)
    df.loc[0, ["bid", "ask"]] = [0, 0]
    df.loc[1, ["bid", "ask"]] = [0, .2]
    df.loc[2, ["bid", "ask"]] = [3, 2]
    df.to_parquet(p)
    q = src.quotes(FRIDAY, (0, 99999))
    assert pd.isna(q.iloc[0].bid)
    assert q.iloc[1].bid == 0 and q.iloc[1].ask == .2
    assert q.iloc[2].bid > q.iloc[2].ask
    m = normalize(src, tmp_path)
    ds = Dataset.open(m.dataset, tmp_path)
    c = ds.chain(FRIDAY)
    assert c.expiration == FRIDAY and c.underlying == "SPX" and c.option_root == "SPXW"
    assert np.isnan(c.fields["C_iv"]).all()
    assert np.isnan(c.fields["C_delta"]).all()
    assert np.isnan(c.fields["C_quote_age_s"]).all()
    assert np.isfinite(c.fields["C_observation_age_s"]).any()
    assert "C_bid_size" in c.fields
    assert np.isnan(c.fields["C_mark"][3]).all()  # five-minute quote gap is too old
    assert ds.verify() == []


@pytest.mark.parametrize("bad", ["root", "right", "strike", "duplicate", "timezone", "date"])
def test_invalid_contract_and_timestamp_rejected(tmp_path, bad):
    src = source(tmp_path)
    p = raw(tmp_path)
    df = pd.read_parquet(p)
    if bad == "root":
        df.loc[0, "symbol"] = "NDXP"
    elif bad == "right":
        df.loc[0, "right"] = "BAD"
    elif bad == "strike":
        df.loc[0, "strike"] = 5980.2
    elif bad == "duplicate":
        df = pd.concat([df, df.iloc[:1]])
    elif bad == "timezone":
        df["timestamp"] = df.timestamp.dt.tz_localize(None)
    elif bad == "date":
        df["timestamp"] += pd.Timedelta(days=1)
    df.to_parquet(p)
    with pytest.raises(ValueError):
        src.quotes(FRIDAY, (0, 99999))


def test_repeat_export_and_changed_input_detection(tmp_path):
    src = source(tmp_path)
    p = raw(tmp_path)
    m = normalize(src, tmp_path)
    manifest = (tmp_path / m.dataset / "manifest.json").read_bytes()
    assert normalize(src, tmp_path).dataset_hash == m.dataset_hash
    assert (tmp_path / m.dataset / "manifest.json").read_bytes() == manifest
    df = pd.read_parquet(p)
    df.loc[0, "ask"] += .05
    df.to_parquet(p)
    with pytest.raises(ValueError, match="changed raw"):
        normalize(src, tmp_path)


def test_incomplete_parquet_and_partial_export_are_not_published(tmp_path, monkeypatch):
    src = source(tmp_path)
    p = raw(tmp_path)
    original = p.read_bytes()
    p.write_bytes(original[:100])
    with pytest.raises(Exception):
        normalize(src, tmp_path)
    assert not (tmp_path / src.dataset / "manifest.json").exists()
    p.write_bytes(original)
    import butterfly_guy.research.local as local
    actual = local.write_table
    def broken(*a, **kw):
        raise OSError("interrupted writer")
    monkeypatch.setattr(local, "write_table", broken)
    with pytest.raises(OSError, match="interrupted"):
        normalize(src, tmp_path)
    assert not (tmp_path / src.dataset).exists()
    monkeypatch.setattr(local, "write_table", actual)
    assert normalize(src, tmp_path).files


def test_quality_gate_cannot_inherit_other_vendor_approval(tmp_path):
    d = dt.date(2023, 11, 22)
    src = source(tmp_path, dates=(d,))
    raw(tmp_path, d)
    with pytest.raises(QualityNotPassedError):
        normalize(src, tmp_path, d)


class OneFly:
    def entries(self, s, ctx):
        i = s.market.at_or_before(et_us(s.date, 10, 1))
        fly = Fly("CALL", 5990, 6000, 6010)
        return [Entry(fly, int(s.market.ts[i]), i,
                      float(s.market.fly_path(fly).mark[i]), "CALL")]


def test_one_dte_intraday_and_carry_holiday_gap(tmp_path):
    s1 = source(tmp_path, "spxw_1dte", "spx_1dte_local_test")
    raw(tmp_path, FRIDAY, TUESDAY, "spxw_1dte")
    normalize(s1, tmp_path)
    ds1 = Dataset.open(s1.dataset, tmp_path)
    with pytest.raises(ValueError, match="explicit lifecycle"):
        SessionLoader(ds1, PROFILE).load(FRIDAY)
    loader = SessionLoader(ds1, PROFILE, lifecycle="carry")
    s0 = LocalThetaDataSource(tmp_path / "raw", "spxw_0dte", "spx_0dte_local_expiry", s1.support)
    raw(tmp_path, TUESDAY)
    normalize(s0, tmp_path, TUESDAY)
    expiry = SessionLoader(Dataset.open(s0.dataset, tmp_path), PROFILE)
    ctx = RunContext(load_spx_config())
    intraday = replay_position(loader, FRIDAY, ctx, lifecycle="intraday",
                              entry_rule=OneFly(), rules=(TimeExit(11, 0),))
    assert intraday["status"] == "resolved"
    assert intraday["settlement"] is None
    assert intraday["expiration"] == str(TUESDAY)
    carry = replay_position(loader, FRIDAY, ctx, lifecycle="carry", expiry_loader=expiry,
                            end=TUESDAY, entry_rule=OneFly(), rules=())
    assert carry["status"] == "resolved" and carry["exit_reason"] == "cash_settled"
    assert carry["fills"]["marketable"]["exit"] == 8.0
    assert carry["observations"][0]["ts_us"] < et_us(TUESDAY, 9, 30)
    assert carry["observations"][-1]["ts_us"] >= et_us(TUESDAY, 15, 0)
    unresolved = replay_position(loader, FRIDAY, ctx, lifecycle="carry", end=FRIDAY,
                                 entry_rule=OneFly(), rules=())
    assert unresolved["status"] == "unresolved"
    assert unresolved["reason"] == "range_ends_before_expiration"
    missing = replay_position(loader, FRIDAY, ctx, lifecycle="carry", end=TUESDAY,
                              entry_rule=OneFly(), rules=())
    assert missing["reason"] == "missing_expiration_dataset"


def test_overnight_peak_state_and_expiry_exit(tmp_path):
    # A peak made on Friday arms a trailer that must still trigger on Monday.
    friday, monday = dt.date(2026, 5, 15), dt.date(2026, 5, 18)
    src = source(tmp_path, "spxw_1dte", "spx_1dte_local_state", dates=(friday, monday))
    p = raw(tmp_path, friday, monday, "spxw_1dte")
    df = pd.read_parquet(p)
    late = df.timestamp.dt.hour >= 11
    df.loc[late & (df.strike == 5990), ["bid", "ask"]] += 20
    df.to_parquet(p)
    normalize(src, tmp_path, friday)
    src0 = LocalThetaDataSource(tmp_path / "raw", "spxw_0dte", "spx_0dte_local_state", src.support)
    raw(tmp_path, monday)
    normalize(src0, tmp_path, monday)
    out = replay_position(SessionLoader(Dataset.open(src.dataset, tmp_path), PROFILE,
                                        lifecycle="carry"), friday, RunContext(load_spx_config()),
                          lifecycle="carry", end=monday,
                          expiry_loader=SessionLoader(
                              Dataset.open(src0.dataset, tmp_path), PROFILE),
                          entry_rule=OneFly(), rules=(PeakTrailer(morning=.5),))
    assert out["status"] == "resolved"
    assert out["exit_time_us"] >= et_us(monday, 9, 30)
    assert out["peak"] > 20


@pytest.mark.parametrize("asset,root,set_name,grid", [("NDX", "NDXP", "ndxp_0dte", 5),
                                                      ("XSP", "XSP", "xsp_0dte", .5)])
def test_alternate_instrument_identity_and_fractional_grid(tmp_path, asset, root, set_name, grid):
    sup = support(tmp_path)
    src = LocalThetaDataSource(tmp_path / "raw", set_name, f"{asset.lower()}_0dte_local_test", sup)
    p = raw(tmp_path, set_name=set_name, root=root)
    df = pd.read_parquet(p)
    if grid == .5:
        df["strike"] = df.strike / 10 + .5
        df.to_parquet(p)
    q = src.quotes(FRIDAY, (0, 99999))
    assert not q.empty
    c = sup.chain(FRIDAY)
    c.underlying, c.option_root, c.expiration = asset, root, FRIDAY
    if grid == .5:
        c.strikes = c.strikes / 10 + .5
    back = table_to_chain(chain_to_table(c), FRIDAY)
    assert back.underlying == asset and back.option_root == root
    from butterfly_guy.research.market import DayMarket
    quote = DayMarket(back).quotes_at(0, "CALL")[0]
    assert quote.underlying == asset and quote.expiration == FRIDAY
    reasons = audit(src, FRIDAY, FRIDAY)[0]["reasons"]
    assert "missing_index_observations" in reasons and "missing_settlement" in reasons


def test_missing_capabilities_are_explicit():
    capability_check(())
    with pytest.raises(ValueError, match="lacks required capabilities: delta, iv"):
        capability_check(("iv", "delta"))


@pytest.mark.parametrize("asset,root,set_name", [("NDX", "NDXP", "ndxp_0dte"),
                                                ("XSP", "XSP", "xsp_0dte")])
def test_alternate_instrument_replay_with_attributable_inputs(tmp_path, asset, root, set_name):
    from butterfly_guy.research.dataset import Manifest, write_table
    from butterfly_guy.research.history import _table
    src_spx = support(tmp_path)
    # Independent invented index observations for fixture mechanics, never scaled real data.
    factor = 10 if asset == "NDX" else .1
    sup_root = tmp_path / f"{asset.lower()}_support"
    m = Manifest(sup_root.name, asset, {"settlement": {asset: {
        "symbol": "XQC" if asset == "NDX" else "XSP", "source_url": "fixture://official"}}}, {})
    bars = src_spx.daily_bars().copy()
    mask = bars.underlying == "SPX"
    bars.loc[mask, "underlying"] = asset
    bars.loc[mask, ["open", "high", "low", "close"]] *= factor
    frames = []
    for sym in ("SPX", "$VIX"):
        ts, px = src_spx.spot_ticks(sym)
        frames.append(pd.DataFrame({"ts_us": ts, "price": px * factor if sym == "SPX" else px,
                                    "underlying": asset if sym == "SPX" else sym}))
    m.files["daily_bars.parquet"] = write_table(_table(bars), sup_root / "daily_bars.parquet")
    m.files["spot_ticks.parquet"] = write_table(_table(pd.concat(frames)),
                                              sup_root / "spot_ticks.parquet")
    m.save(sup_root / "manifest.json")
    src = LocalThetaDataSource(tmp_path / "raw", set_name, f"{asset.lower()}_0dte_local_replay",
                                Dataset(sup_root))
    path = raw(tmp_path, root=root, set_name=set_name)
    df = pd.read_parquet(path)
    df.strike *= factor
    df[["bid", "ask"]] *= factor
    df.to_parquet(path)
    normalize(src, tmp_path)
    ds = Dataset.open(src.dataset, tmp_path)
    class AssetFly:
        def entries(self, s, ctx):
            i = s.market.at_or_before(et_us(FRIDAY, 10, 1))
            fly = Fly("CALL", 5990 * factor, 6000 * factor, 6010 * factor)
            return [Entry(fly, int(s.market.ts[i]), i,
                          float(s.market.fly_path(fly).mark[i]), "CALL")]
    config = load_spx_config().model_copy(deep=True)
    config.strategy.underlying = asset
    out = replay_position(SessionLoader(ds, PROFILE), FRIDAY, RunContext(config, asset),
                          lifecycle="0dte", rules=(), entry_rule=AssetFly())
    assert out["status"] == "resolved"
    fill = out["fills"]["marketable"]
    assert fill["exit"] == pytest.approx(8 * factor)
    assert fill["pnl_dollars"] == pytest.approx(100 * (fill["exit"] - fill["entry"]))
    assert {r["underlying"] for r in out["entry_legs"]} == {asset}


def test_one_dte_guard_checks_protected_expiry_before_parquet_open(tmp_path, monkeypatch):
    import json
    friday = dt.date(2024, 6, 28)
    src = source(tmp_path, "spxw_1dte", "spx_1dte_local_guard", dates=(friday,))
    raw(tmp_path, friday, dt.date(2024, 7, 1), "spxw_1dte")
    (tmp_path / "raw" / "catalog.jsonl").write_text(json.dumps({
        "set": "spxw_1dte", "kind": "quote_1m", "date": str(friday),
        "expiration": "2024-07-01", "status": "ok"}) + "\n")
    def fail(*args, **kwargs):
        pytest.fail("protected expiry opened")
    monkeypatch.setattr(pq, "ParquetFile", fail)
    with pytest.raises(HoldoutSealedError):
        src.path(friday)


def test_cached_daily_inputs_supply_development_closes_without_network(tmp_path, monkeypatch):
    import hashlib
    import json
    src = source(tmp_path)
    def forbidden(*a, **kw):
        pytest.fail("network attempted during cached replay")
    import butterfly_guy.research.thetadata as theta
    monkeypatch.setattr(theta, "fetch_cboe", forbidden)
    records = {}
    for index, text in {
        "SPX": "DATE,SPX\n11/21/2023,5995\n11/22/2023,6002\n",
        "VIX": "DATE,OPEN,HIGH,LOW,CLOSE\n11/21/2023,17,19,16,18\n"
               "11/22/2023,18,19,17,18.5\n",
    }.items():
        path = tmp_path / f"{index}.csv"
        path.write_text(text)
        records[index] = {"path": str(path), "sha256": hashlib.sha256(text.encode()).hexdigest(),
                          "source_url": f"fixture://{index}", "retrieved_at": "fixture"}
    meta = tmp_path / "daily.json"
    meta.write_text(json.dumps(records))
    cached = LocalThetaDataSource(tmp_path / "raw", "spxw_0dte", "spx_0dte_local_cached",
                                   src.support, daily_cache=meta)
    bars = cached.daily_bars(dt.date(2023, 11, 21), dt.date(2023, 11, 22))
    spx = bars[bars.underlying == "SPX"]
    assert list(spx.close) == [5995, 6002]
    assert spx.open.isna().all()  # official close never masquerades as an opening observation
    assert cached.describe()["daily_cache"]["SPX"]["source_url"] == "fixture://SPX"
    (tmp_path / "SPX.csv").write_text("changed")
    with pytest.raises(ValueError, match="changed cached SPX"):
        cached.describe()


def test_support_input_changes_are_detected_on_resume(tmp_path):
    src = source(tmp_path)
    raw(tmp_path)
    normalize(src, tmp_path)
    p = src.support.root / "daily_bars.parquet"
    df = pd.read_parquet(p)
    df.loc[0, "close"] += 1
    df.to_parquet(p)
    with pytest.raises(ValueError, match="changed supporting input"):
        normalize(src, tmp_path)


def test_local_normalized_schema_is_distinct_and_unsupported_readers_fail(tmp_path):
    src = source(tmp_path)
    raw(tmp_path)
    m = normalize(src, tmp_path)
    assert m.schema_version == 3
    assert m.export["schema"] == 3


def test_scheduled_early_close_does_not_monitor_after_cutoff(tmp_path):
    from butterfly_guy.research.exits import MonitorState, monitor
    d = dt.date(2023, 11, 24)
    src = support(tmp_path, dates=(d,))
    market = SessionLoader(src, PROFILE).load(d).market
    path = market.fly_path(Fly("CALL", 5990, 6000, 6010))
    state = MonitorState()
    result = monitor(date=d, clock_ts=market.ts, snapshot_ts=market.ts, path=path,
                     entry_ts_us=et_us(d, 10, 0), entry_price=10, rules=(TimeExit(14, 0),),
                     session_close=dt.time(13, 0), state=state)
    assert result.reason == "cash_settled"
    assert state.observations[-1]["ts_us"] == et_us(d, 13, 0)
