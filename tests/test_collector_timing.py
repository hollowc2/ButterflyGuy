"""Collector timing metadata (migration 011): quote times, fetch timings, chain_snapshot_meta."""

from __future__ import annotations

import datetime as dt
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from butterfly_guy.core.config import AppConfig
from butterfly_guy.data import collector as collector_module
from butterfly_guy.data.collector import OptionChainCollector
from butterfly_guy.data.providers import (
    ChainObservation,
    ContractTiming,
    OmittedContract,
    SpotObservation,
)

EXPIRATION = dt.date(2026, 10, 5)
STAMP = dt.datetime(2026, 10, 5, 10, 0, 20, tzinfo=dt.UTC)
EVENT = dt.datetime(2026, 10, 5, 14, 0, 23, tzinfo=dt.UTC)


def _option(symbol: str) -> dict:
    return {"symbol": symbol, "bid": 1.0, "ask": 1.1, "mark": 1.05}


CHAIN = {
    "callExpDateMap": {f"{EXPIRATION}:0": {"6000": [_option("C6000")],
                                           "6300": [_option("C6300")]}},
    "putExpDateMap": {f"{EXPIRATION}:0": {"6000": [_option("P6000")]}},
}
OBSERVED = ChainObservation(
    source="schwab_rest", event_timestamp=EVENT, gateway_received_at=EVENT,
    age_seconds=0.4, stale=False, data_quality_flags=("stale_contracts_present",),
    contracts={"C6000": ContractTiming(EVENT, 0.5), "P6000": ContractTiming(EVENT, 2.0),
               "C6300": ContractTiming(None, 30.0)},
    contracts_delivered=4, contracts_kept=3,
    omitted=(OmittedContract("C6005", "CALL", 6005.0, True, 75.0, ("stale",)),),
)


def _provider() -> MagicMock:
    provider = MagicMock()
    provider.get_spot_observed = AsyncMock(side_effect=lambda symbol: SpotObservation(
        price=18.5 if symbol == "$VIX" else 6010.0, source="schwab_stream",
        event_timestamp=EVENT, age_seconds=0.1))
    provider.get_option_chain_observed = AsyncMock(return_value=(CHAIN, OBSERVED))
    provider.get_spot_price = AsyncMock(return_value=6010.0)
    provider.get_option_chain = AsyncMock(return_value=CHAIN)
    return provider


def _collector(provider, *, record_timing: bool = True, meta_error: Exception | None = None):
    config = AppConfig()
    config.collector.record_timing = record_timing
    chain_q = MagicMock()
    chain_q.bulk_insert_snapshot = AsyncMock(side_effect=lambda rows: len(rows))
    chain_q.insert_snapshot_meta = AsyncMock(side_effect=meta_error)
    spot_q = MagicMock()
    spot_q.insert = AsyncMock()
    return OptionChainCollector(config, provider, chain_q, spot_q), chain_q, spot_q


@pytest.fixture(autouse=True)
def _no_side_effects():
    with patch.object(collector_module, "now_eastern", return_value=STAMP), \
            patch.object(collector_module, "get_0dte_expiration", return_value=EXPIRATION), \
            patch.object(collector_module, "save_snapshot"), \
            patch.object(collector_module, "notify", AsyncMock()) as notify:
        yield SimpleNamespace(notify=notify)


@pytest.mark.asyncio
async def test_timed_snapshot_records_quote_times_and_meta() -> None:
    collector, chain_q, spot_q = _collector(_provider())

    assert await collector.collect_snapshot() == 3

    rows = chain_q.bulk_insert_snapshot.await_args.args[0]
    by_symbol = {r["symbol"]: r for r in rows}
    assert all(r["snapshot_time"] == STAMP for r in rows)  # stamp meaning unchanged
    assert (by_symbol["C6000"]["quote_event_ts"], by_symbol["C6000"]["quote_age_s"]) == (
        EVENT, 0.5)
    assert by_symbol["C6300"]["quote_event_ts"] is None
    assert spot_q.insert.await_args_list[0].kwargs == {"event_ts": EVENT, "age_s": 0.1}
    meta = chain_q.insert_snapshot_meta.await_args.args[0]
    assert (meta["snapshot_time"], meta["underlying"], meta["expiration"]) == (
        STAMP, "SPX", EXPIRATION)
    assert meta["scheduled_at"] is None
    for name in ("spot", "vix", "chain"):
        assert meta[f"{name}_fetch_started_at"] <= meta[f"{name}_fetch_completed_at"]
    assert meta["spot_fetch_completed_at"] <= meta["vix_fetch_started_at"]
    assert meta["vix_fetch_completed_at"] <= meta["chain_fetch_started_at"]
    assert (meta["chain_event_ts"], meta["chain_age_s"], meta["chain_source"]) == (
        EVENT, 0.4, "schwab_rest")
    assert meta["chain_flags"] == ["stale_contracts_present"]
    assert (meta["spot_event_ts"], meta["vix_age_s"]) == (EVENT, 0.1)
    assert (meta["contracts_delivered"], meta["contracts_stored"],
            meta["contracts_omitted"]) == (4, 3, 1)
    assert meta["omitted"] == [{"symbol": "C6005", "option_type": "CALL", "strike": 6005.0,
                                "stale": True, "age_s": 75.0, "flags": ["stale"]}]
    assert meta["strikes_within_spot_range"] == 1  # 6000 within 100 of 6010; 6300 is not


@pytest.mark.asyncio
async def test_meta_write_failure_does_not_block_the_chain_insert(_no_side_effects) -> None:
    collector, chain_q, _ = _collector(_provider(), meta_error=RuntimeError("db down"))

    assert await collector.collect_snapshot() == 3
    assert await collector.collect_snapshot() == 3

    assert chain_q.bulk_insert_snapshot.await_count == 2
    assert _no_side_effects.notify.await_count == 1  # alerted once, not every pass
    chain_q.insert_snapshot_meta.side_effect = None
    await collector.collect_snapshot()
    assert "recovered" in _no_side_effects.notify.await_args.args[0]


@pytest.mark.asyncio
async def test_default_config_keeps_the_untimed_path() -> None:
    provider = _provider()
    collector, chain_q, spot_q = _collector(provider, record_timing=False)

    assert await collector.collect_snapshot() == 3

    provider.get_spot_observed.assert_not_awaited()
    provider.get_option_chain_observed.assert_not_awaited()
    chain_q.insert_snapshot_meta.assert_not_awaited()
    rows = chain_q.bulk_insert_snapshot.await_args.args[0]
    assert all("quote_event_ts" not in r for r in rows)
    assert spot_q.insert.await_args_list[0].kwargs == {}


@pytest.mark.asyncio
async def test_provider_without_observations_records_unobserved_meta() -> None:
    provider = _provider()
    del provider.get_spot_observed
    del provider.get_option_chain_observed
    collector, chain_q, _ = _collector(provider)

    assert await collector.collect_snapshot() == 3

    meta = chain_q.insert_snapshot_meta.await_args.args[0]
    assert meta["chain_source"] == "unobserved" and meta["contracts_delivered"] is None
    rows = chain_q.bulk_insert_snapshot.await_args.args[0]
    assert all(r["quote_event_ts"] is None for r in rows)


def test_only_the_spx_config_records_timing() -> None:
    import yaml

    from butterfly_guy.core.config import CollectorSettings

    flags = {name: CollectorSettings(**yaml.safe_load(open(f"configs/{name}"))["collector"])
             .record_timing for name in ("config.yaml", "config_ndx.yaml", "config_xsp.yaml")}
    assert flags == {"config.yaml": True, "config_ndx.yaml": False, "config_xsp.yaml": False}
