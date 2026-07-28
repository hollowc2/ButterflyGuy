from __future__ import annotations

import asyncio
import datetime as dt
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from butterfly_guy.data.equity_market_data import (
    JsonlStreamRecorder,
    symbol_directory,
    write_candle_snapshot,
)
from butterfly_guy.scripts.record_equity_market_data import _subscribe


def test_symbol_directory_is_stable_and_sanitizes_path_characters(tmp_path):
    path = symbol_directory(tmp_path, "$ABC/DEF", dt.date(2026, 7, 23))

    assert path == tmp_path / "ABC_DEF" / "2026-07-23"


def test_symbol_directory_rejects_parent_directory_symbol(tmp_path):
    with pytest.raises(ValueError, match="letter or number"):
        symbol_directory(tmp_path, "..", dt.date(2026, 7, 23))


def test_write_candle_snapshot_sorts_candles(tmp_path):
    path = tmp_path / "candles_1m.json"
    write_candle_snapshot(
        path,
        symbol="bmnr",
        session_date=dt.date(2026, 7, 23),
        retrieved_at=dt.datetime(2026, 7, 24, tzinfo=dt.timezone.utc),
        candles=[
            {"datetime": 2000, "close": 17.20},
            {"datetime": 1000, "close": 17.10},
        ],
    )

    payload = json.loads(path.read_text())
    assert payload["symbol"] == "BMNR"
    assert payload["source"] == "schwab_price_history"
    assert [candle["datetime"] for candle in payload["candles"]] == [1000, 2000]


@pytest.mark.asyncio
async def test_jsonl_recorder_persists_raw_message(tmp_path):
    fixed_time = dt.datetime(2026, 7, 23, 14, 30, tzinfo=dt.timezone.utc)
    recorder = JsonlStreamRecorder(
        tmp_path,
        symbol="bmnr",
        clock=lambda: fixed_time,
    )
    recorder.handler("nyse_book")({"service": "NYSE_BOOK", "content": [{"key": "BMNR"}]})

    stop = asyncio.Event()
    stop.set()
    await recorder.write_until_stopped(stop)

    line = json.loads((tmp_path / "nyse_book.jsonl").read_text())
    assert line["kind"] == "nyse_book"
    assert line["symbol"] == "BMNR"
    assert line["received_at"] == fixed_time.isoformat()
    assert line["message"]["content"][0]["key"] == "BMNR"
    assert recorder.written == {"nyse_book": 1}


@pytest.mark.asyncio
async def test_subscribe_registers_handlers_before_nyse_services():
    stream = SimpleNamespace(
        add_chart_equity_handler=MagicMock(),
        add_level_one_equity_handler=MagicMock(),
        add_nyse_book_handler=MagicMock(),
        add_nasdaq_book_handler=MagicMock(),
        chart_equity_subs=AsyncMock(),
        level_one_equity_subs=AsyncMock(),
        nyse_book_subs=AsyncMock(),
        nasdaq_book_subs=AsyncMock(),
    )
    recorder = MagicMock()
    recorder.handler.side_effect = lambda kind: f"{kind}-handler"

    await _subscribe(
        stream,
        recorder,
        symbol="BMNR",
        venue="nyse",
        include_book=True,
    )

    stream.add_chart_equity_handler.assert_called_once_with("chart_equity-handler")
    stream.add_level_one_equity_handler.assert_called_once_with("level_one_equity-handler")
    stream.add_nyse_book_handler.assert_called_once_with("nyse_book-handler")
    stream.add_nasdaq_book_handler.assert_not_called()
    stream.chart_equity_subs.assert_awaited_once_with(["BMNR"])
    stream.level_one_equity_subs.assert_awaited_once_with(["BMNR"])
    stream.nyse_book_subs.assert_awaited_once_with(["BMNR"])
    stream.nasdaq_book_subs.assert_not_awaited()
