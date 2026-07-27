"""Persistence helpers for recorded equity candles and Schwab stream events."""

from __future__ import annotations

import asyncio
import datetime as dt
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any, Callable

UTC = dt.timezone.utc
SCHEMA_VERSION = 1
STREAM_KINDS = frozenset({"chart_equity", "level_one_equity", "nyse_book", "nasdaq_book"})


def utc_now() -> dt.datetime:
    return dt.datetime.now(UTC)


def symbol_directory(output_dir: Path, symbol: str, session_date: dt.date) -> Path:
    """Return the stable output directory for one symbol and session."""
    safe_symbol = re.sub(r"[^A-Z0-9._-]", "_", symbol.upper()).strip("._")
    if not safe_symbol:
        raise ValueError("Symbol must contain at least one letter or number")
    return output_dir / safe_symbol / session_date.isoformat()


def write_candle_snapshot(
    path: Path,
    *,
    symbol: str,
    session_date: dt.date,
    candles: list[dict[str, Any]],
    retrieved_at: dt.datetime | None = None,
) -> None:
    """Write a deterministic JSON candle snapshot."""
    payload = {
        "schema_version": SCHEMA_VERSION,
        "source": "schwab_price_history",
        "symbol": symbol.upper(),
        "session_date": session_date.isoformat(),
        "retrieved_at": (retrieved_at or utc_now()).isoformat(),
        "interval": "1m",
        "candles": sorted(candles, key=lambda candle: int(candle.get("datetime", 0))),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class JsonlStreamRecorder:
    """Non-blocking stream handlers backed by one JSONL file per Schwab service."""

    def __init__(
        self,
        output_dir: Path,
        *,
        symbol: str,
        max_queue_size: int = 100_000,
        clock: Callable[[], dt.datetime] = utc_now,
    ) -> None:
        self.output_dir = output_dir
        self.symbol = symbol.upper()
        self.clock = clock
        self.queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self.received: Counter[str] = Counter()
        self.written: Counter[str] = Counter()
        self.dropped: Counter[str] = Counter()

    def handler(self, kind: str) -> Callable[[dict[str, Any]], None]:
        """Build a synchronous schwab-py handler that never blocks the stream."""
        if kind not in STREAM_KINDS:
            raise ValueError(f"Unsupported stream kind: {kind}")

        def record(message: dict[str, Any]) -> None:
            self.received[kind] += 1
            envelope = {
                "schema_version": SCHEMA_VERSION,
                "source": "schwab_stream",
                "kind": kind,
                "symbol": self.symbol,
                "received_at": self.clock().isoformat(),
                "message": message,
            }
            try:
                self.queue.put_nowait((kind, envelope))
            except asyncio.QueueFull:
                self.dropped[kind] += 1

        return record

    async def write_until_stopped(self, stop: asyncio.Event) -> None:
        """Drain queued events until the stop flag is set and the queue is empty."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        handles: dict[str, Any] = {}
        writes_since_flush = 0
        try:
            while not stop.is_set() or not self.queue.empty():
                try:
                    kind, envelope = await asyncio.wait_for(self.queue.get(), timeout=0.5)
                except TimeoutError:
                    continue
                handle = handles.get(kind)
                if handle is None:
                    handle = (self.output_dir / f"{kind}.jsonl").open(
                        "a", encoding="utf-8"
                    )
                    handles[kind] = handle
                handle.write(json.dumps(envelope, separators=(",", ":"), default=str) + "\n")
                self.written[kind] += 1
                self.queue.task_done()
                writes_since_flush += 1
                if writes_since_flush >= 100:
                    for open_handle in handles.values():
                        open_handle.flush()
                    writes_since_flush = 0
        finally:
            for handle in handles.values():
                handle.flush()
                handle.close()

    def write_manifest(
        self,
        *,
        started_at: dt.datetime,
        ended_at: dt.datetime,
        venue: str,
    ) -> Path:
        """Write a run summary without exposing credentials or account identifiers."""
        path = self.output_dir / f"run-{started_at.strftime('%H%M%S')}.json"
        payload = {
            "schema_version": SCHEMA_VERSION,
            "source": "schwab_stream",
            "symbol": self.symbol,
            "venue": venue,
            "started_at": started_at.isoformat(),
            "ended_at": ended_at.isoformat(),
            "received": dict(self.received),
            "written": dict(self.written),
            "dropped": dict(self.dropped),
        }
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return path
