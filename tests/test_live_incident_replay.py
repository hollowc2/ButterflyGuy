"""End-to-end replays of live failure scenarios through the real execution code.

The 11-19 incident and its siblings run through the real OrderManager, entry_loop and
startup reconciliation. Only Schwab and the broker_order_intents table are stateful fakes;
Schwab's 11-19 payloads come from tests/fixtures. Timing runs on a fake clock.
"""

from __future__ import annotations

import asyncio
import copy
import datetime as dt
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from asyncpg.exceptions import UniqueViolationError

from butterfly_guy.core.metrics import readiness_snapshot, set_readiness
from butterfly_guy.data.schemas import TradeRecord
from butterfly_guy.execution.order_manager import (
    EntryOrderReplacedError,
    LiveSpread,
    OrderManager,
    PartialFillError,
)
from butterfly_guy.scripts.run_live import (
    LiveTradingHaltedError,
    _assert_broker_state_matches_db,
    entry_loop,
)
from tests.test_order_manager import (
    filled_order,
    live_1119_canceled_exit,
    live_1119_status,
    make_candidate,
    make_settings,
)

FINAL = {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}
# Found by these replays: the startup status sync (run_live.py, _assert_broker_state_matches_db)
# copies Schwab's REPLACED back over an intent the operator closed by the runbook, so every
# restart that session refuses again. Strict: these flip to failures once the sync is fixed.
SYNC_REOPENS_RESOLVED_INTENT = pytest.mark.xfail(
    strict=True, raises=RuntimeError,
    reason="startup sync reopens a runbook-resolved REPLACED intent",
)
LEGS = ("SPXW  261119C07435000", "SPXW  261119C07475000", "SPXW  261119C07515000")
SPREAD = LiveSpread(bid=1.85, mark=1.97, ask=2.10)  # live 100001's quote at its signal


class Broker:
    """Schwab as the bot sees it: scripted order reads, a cancel switches the script."""

    def __init__(self, positions: dict[str, int]):
        self.positions = dict(positions)
        self.scripts: dict[str, dict[str, list[dict]]] = {}
        self.orders: dict[str, dict] = {}  # latest payload per order, for today's orders
        self.events: list[tuple[str, str]] = []
        self.next_id = 1

    def script(self, order_id: str, working: list[dict], after_cancel: list[dict] = ()):
        self.scripts[order_id] = {"working": list(working), "after_cancel": list(after_cancel)}

    def payload(self, order_id: str, read: dict) -> dict:
        read = {**copy.deepcopy(read), "orderId": order_id}
        read.setdefault("orderLegCollection", [{"instrument": {"symbol": s}} for s in LEGS])
        return read

    def set_order(self, order_id: str, read: dict) -> None:
        self.orders[order_id] = self.payload(order_id, read)

    async def place_order(self, _spec) -> str:
        order_id = f"ORD{self.next_id}"
        self.next_id += 1
        self.events.append(("place", order_id))
        self.set_order(order_id, {"status": "WORKING"})
        return order_id

    async def cancel_order(self, order_id: str) -> None:
        self.events.append(("cancel", order_id))
        self.scripts[order_id]["working"] = self.scripts[order_id]["after_cancel"]

    async def get_order_status(self, order_id: str) -> dict:
        queue = self.scripts[order_id]["working"]
        read = queue.pop(0) if len(queue) > 1 else queue[0]
        self.set_order(order_id, read)
        self.events.append((f"status:{read.get('status')}", order_id))
        return self.orders[order_id]

    async def get_todays_orders(self) -> list[dict]:
        return [copy.deepcopy(order) for order in self.orders.values()]

    async def get_account_snapshot(self) -> dict:
        return {"securitiesAccount": {"positions": [
            {
                "instrument": {"assetType": "OPTION", "symbol": symbol},
                "longQuantity": max(quantity, 0), "shortQuantity": max(-quantity, 0),
            }
            for symbol, quantity in self.positions.items() if quantity
        ]}}


class IntentDB:
    """broker_order_intents with both active-intent unique indexes."""

    def __init__(self):
        self.rows: dict[int, dict] = {}
        self.history: list[tuple[int, str]] = []

    def active(self) -> list[dict]:
        return [row for row in self.rows.values() if row["status"] not in FINAL]

    async def create_intent(self, *, underlying, trade_date, side, candidate_snapshot,
                            trade_id=None, **_):
        for row in self.active():
            if row["side"] == side and (
                row["trade_id"] == trade_id if side == "EXIT"
                else (row["underlying"], row["trade_date"]) == (underlying, trade_date)
            ):
                raise UniqueViolationError("duplicate key value violates unique constraint")
        intent_id = len(self.rows) + 1
        self.rows[intent_id] = {
            "id": intent_id, "underlying": underlying, "trade_date": trade_date,
            "side": side, "trade_id": trade_id, "status": "SUBMITTING",
            "broker_order_id": None, "raw_broker_payload": None,
            "candidate_snapshot": copy.deepcopy(candidate_snapshot),
        }
        self.history.append((intent_id, "SUBMITTING"))
        return intent_id

    async def append_execution_observation(self, intent_id, observation):
        snapshot = self.rows[intent_id]["candidate_snapshot"]
        snapshot.setdefault("execution_observations", []).append(observation)

    async def mark_broker_order_id(self, intent_id, broker_order_id):
        self.rows[intent_id].update(broker_order_id=broker_order_id, status="SUBMITTED")
        self.history.append((intent_id, "SUBMITTED"))

    async def update_broker_status(self, intent_id, status, payload=None):
        self.rows[intent_id]["status"] = status
        if payload is not None:
            self.rows[intent_id]["raw_broker_payload"] = copy.deepcopy(payload)
        self.history.append((intent_id, status))

    async def mark_unknown(self, intent_id, error):
        self.rows[intent_id].update(status="UNKNOWN_ABORTED", raw_broker_payload={"error": error})
        self.history.append((intent_id, "UNKNOWN_ABORTED"))

    async def active_broker_order_ids(self, underlying, trade_date, *, exclude_intent_id=None):
        return {
            row["broker_order_id"] for row in self.active()
            if row["broker_order_id"] and row["id"] != exclude_intent_id
        }

    async def intents_for_day(self, underlying, trade_date):
        return [copy.deepcopy(row) for row in self.rows.values()
                if (row["underlying"], row["trade_date"]) == (underlying, trade_date)]

    async def active_exit_intents_for_trades(self, underlying, trade_ids):
        return [copy.deepcopy(row) for row in self.active()
                if row["side"] == "EXIT" and row["trade_id"] in trade_ids]


def _live_candidate():
    candidate = make_candidate(7435, 7475, 7515, 3.75, direction="CALL")
    candidate.lower_symbol, candidate.center_symbol, candidate.upper_symbol = LEGS
    return candidate


DAY = _live_candidate().lower_quote.expiration
FLY = dict(zip(LEGS, (1, -2, 1), strict=True))
OPEN_ROW = {"id": 100000, "trade_date": DAY, "quantity": 1,
            "lower_symbol": LEGS[0], "center_symbol": LEGS[1], "upper_symbol": LEGS[2]}


def _manager(broker: Broker, db: IntentDB, **settings) -> OrderManager:
    # Day-2 live settings: 20 s fill wait, 4 steps, recorded execution.
    om = OrderManager(
        make_settings(retry_interval_seconds=20, record_live_execution=True, **settings),
        broker, MagicMock(build_butterfly_open=Mock(return_value={}),
                          build_butterfly_close=Mock(return_value={})), "SPX",
    )
    om.intent_queries = db
    om._fetch_live_spread = AsyncMock(return_value=SPREAD)
    return om


class Clock:
    """Monotonic time advances only when someone sleeps; sleeping still yields."""

    def __init__(self):
        self.now = 0.0
        self._real_sleep = asyncio.sleep

    async def sleep(self, seconds):
        self.now += seconds
        await self._real_sleep(0)

    def patches(self):
        return (
            patch("butterfly_guy.execution.order_manager.monotonic", new=lambda: self.now),
            patch("asyncio.sleep", new=self.sleep),
        )


def _one_order_at_a_time(events):
    live = None
    for event, order_id in events:
        if event == "place":
            assert live is None, f"{order_id} placed while {live} was not final: {events}"
            live = order_id
        elif event in {"status:CANCELED", "status:FILLED"} and order_id == live:
            live = None


async def _restart(broker: Broker, db: IntentDB, open_rows):
    """The startup reconcile a restarted live bot runs before it does anything else."""
    await _assert_broker_state_matches_db(broker, "SPX", open_rows, db, trade_date=DAY)


@pytest.mark.asyncio
async def test_1119_exit_replayed_settles_the_pending_cancel_and_fills_the_next_step():
    # 11-19 07:19:56: exit 1 rested 20 s unfilled; the read 0.3 s after its cancel said
    # PENDING_CANCEL and 983ebc3 halted, leaving the fly unmanaged for six hours. Now the
    # wait settles to Schwab's real CANCELED payload and the ladder moves on.
    broker, db = Broker(FLY), IntentDB()
    broker.script(
        "ORD1",
        working=[live_1119_status("WORKING")],
        after_cancel=[live_1119_status("PENDING_CANCEL"), live_1119_canceled_exit()],
    )
    broker.script("ORD2", working=[live_1119_status("WORKING"), filled_order()])
    om = _manager(broker, db)
    clock = Clock()
    mono, sleep = clock.patches()

    with mono, sleep:
        fill = await om.execute_exit(
            _live_candidate(), current_value=1.97, exit_reason="drawdown_morning",
            trade_id=100000,
        )

    assert fill is not None and fill["order_id"] == "ORD2"
    assert [e for e in broker.events if e[0] in {"place", "cancel"}] == [
        ("place", "ORD1"), ("cancel", "ORD1"), ("place", "ORD2"),
    ]
    _one_order_at_a_time(broker.events)
    assert (1, "PENDING_CANCEL") in db.history  # the read that halted 11-19
    assert db.rows[1]["status"] == "CANCELED"
    assert db.rows[1]["raw_broker_payload"]["filledQuantity"] == 0
    assert db.rows[2]["status"] == "FILLED"
    assert db.active() == []
    phases = [o["phase"] for o in db.rows[2]["candidate_snapshot"]["execution_observations"]]
    assert phases[0] == "before_submit"


@pytest.mark.asyncio
async def test_cancel_that_never_settles_halts_restarts_and_resumes_only_once_final():
    # The cancel stays PENDING_CANCEL for the whole 15 s budget: no second exit is sent,
    # the live process halts (exit 1, Docker restarts it), and each restart's reconcile
    # refuses until Schwab shows the order final, then re-adopts the fly.
    broker, db = Broker(FLY), IntentDB()
    broker.script(
        "ORD1",
        working=[live_1119_status("WORKING")],
        after_cancel=[live_1119_status("PENDING_CANCEL")],
    )
    om = _manager(broker, db)
    candidate = _live_candidate()
    trade = TradeRecord(
        trade_id=100000, trade_date=DAY, direction="CALL", wing_width=40,
        center_strike=7475.0, lower_strike=7435.0, upper_strike=7515.0, entry_price=3.75,
        entry_time=dt.datetime(2026, 3, 21, 14, 37, tzinfo=dt.timezone.utc),
        lower_symbol=LEGS[0], center_symbol=LEGS[1], upper_symbol=LEGS[2],
    )

    async def monitor_loop(trade, candidate, recovered_peak=None):
        # The monitor's exit signal hands the fly to the real exit ladder.
        await om.execute_exit(candidate, 1.97, trade.quantity, "drawdown_morning",
                              trade.trade_id)

    position_service = Mock(monitor_loop=monitor_loop)
    position_service.config.execution.paper_trading = False
    critical_notifier = Mock(notify_critical=AsyncMock())
    clock = Clock()
    mono, sleep = clock.patches()
    set_readiness(None)

    with mono, sleep, patch("butterfly_guy.scripts.run_live.is_market_open", lambda: True), \
         pytest.raises(LiveTradingHaltedError, match="monitor stopped") as caught:
        await entry_loop(
            Mock(), position_service, recovered_trade=trade, recovered_candidate=candidate,
            critical_notifier=critical_notifier,
        )

    assert isinstance(caught.value.__cause__, PartialFillError)
    assert "still PENDING_CANCEL 15s after cancel" in str(caught.value)
    assert [e for e in broker.events if e[0] == "place"] == [("place", "ORD1")]
    critical_notifier.notify_critical.assert_awaited_once_with("broker_ambiguity")
    assert readiness_snapshot() == (False, "broker_order_state_unsafe")
    set_readiness(None)

    # Restart 1: the cancel is still pending at Schwab.
    with pytest.raises(RuntimeError, match="partial/cancel-pending/working bot-owned"):
        await _restart(broker, db, [OPEN_ROW])
    assert db.rows[1]["status"] == "PENDING_CANCEL"

    # Restart 2: Schwab closed it CANCELED, 0 filled; the fly is re-adopted.
    broker.set_order("ORD1", live_1119_canceled_exit())
    await _restart(broker, db, [OPEN_ROW])
    assert db.rows[1]["status"] == "CANCELED"
    assert db.active() == []


@pytest.mark.asyncio
@SYNC_REOPENS_RESOLVED_INTENT
async def test_entry_the_operator_replaced_halts_and_startup_waits_for_the_runbook():
    # An operator edits the bot's resting entry in ToS. The bot stops at once, cancels
    # nothing, and every restart refuses until the operator has resolved it.
    broker, db = Broker({}), IntentDB()
    broker.script("ORD1", working=[live_1119_status("WORKING"), live_1119_status("REPLACED")])
    om = _manager(broker, db)
    candidate = _live_candidate()

    async def attempt_entry():
        result = await om.execute_single_attempt(candidate, 3.75)
        broker.set_order("OP-1", {"status": "WORKING"})  # the operator's replacement
        return result

    trade_service = Mock(attempt_entry=attempt_entry, config=Mock(strategy=Mock(underlying="SPX")))
    position_service = Mock()
    position_service.config.execution.paper_trading = False
    clock = Clock()
    mono, sleep = clock.patches()
    set_readiness(None)

    with mono, sleep, patch("butterfly_guy.scripts.run_live.is_market_open", lambda: True), \
         pytest.raises(LiveTradingHaltedError, match="entry stopped") as caught:
        await entry_loop(trade_service, position_service, critical_notifier=None)
    set_readiness(None)

    assert isinstance(caught.value.__cause__, EntryOrderReplacedError)
    assert clock.now == pytest.approx(2.0)  # one poll, not the 20 s fill wait
    assert [e for e in broker.events if e[0] in {"place", "cancel"}] == [("place", "ORD1")]
    assert db.rows[1]["status"] == "REPLACED"
    broker.set_order("OP-1", {"status": "WORKING"})

    # Restart 1: the operator's replacement is still working.
    with pytest.raises(RuntimeError, match="unknown active SPX order"):
        await _restart(broker, db, [])
    # Restart 2: the operator cancelled it; the REPLACED intent still holds today's entries.
    broker.set_order("OP-1", {"status": "CANCELED"})
    with pytest.raises(RuntimeError, match=r"unresolved entry intent \(order REPLACED\)"):
        await _restart(broker, db, [])
    # The runbook's guarded UPDATE (by id and order id, after the ToS check).
    row = db.rows[1]
    assert row["broker_order_id"] == "ORD1" and row["status"] not in FINAL
    row.update(status="CANCELED", raw_broker_payload={
        "operator_resolved": "replaced in ToS, replacement canceled",
        "previous_status": "REPLACED",
    })
    # Restart 3: accepted, and the operator's resolution stays closed.
    await _restart(broker, db, [])
    assert db.rows[1]["status"] == "CANCELED"
    assert db.active() == []


@pytest.mark.asyncio
@SYNC_REOPENS_RESOLVED_INTENT
async def test_runbook_resolution_of_a_replaced_exit_intent_lets_the_next_startup_adopt():
    # docs/live-runbook.md: for REPLACED with a recorded order id, confirm in ToS that the
    # order and every replacement are final, then close the intent by id and order id.
    broker, db = Broker(FLY), IntentDB()
    intent_id = await db.create_intent(
        underlying="SPX", trade_date=DAY, side="EXIT", candidate_snapshot={}, trade_id=100000,
    )
    await db.mark_broker_order_id(intent_id, "ORD1")
    broker.set_order("ORD1", {"status": "REPLACED"})
    broker.set_order("OP-1", {"status": "CANCELED"})  # the operator's replacement, final

    with pytest.raises(RuntimeError, match=r"unresolved exit intent \(order REPLACED\)"):
        await _restart(broker, db, [OPEN_ROW])
    db.rows[intent_id].update(status="CANCELED", raw_broker_payload={
        "operator_resolved": "replaced in ToS, replacement canceled",
        "previous_status": "REPLACED",
    })

    await _restart(broker, db, [OPEN_ROW])
    assert db.rows[intent_id]["status"] == "CANCELED"
