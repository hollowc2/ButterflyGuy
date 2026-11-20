"""Dated live pilot cannot open outside its session or lose audit evidence silently."""

import asyncio
import datetime as dt
import json
from unittest.mock import AsyncMock, patch

import pytest
from asyncpg.exceptions import (
    AdminShutdownError,
    CheckViolationError,
    ConnectionDoesNotExistError,
    InterfaceError,
    PostgresSyntaxError,
    QueryCanceledError,
    SerializationError,
    StatementCompletionUnknownError,
    UniqueViolationError,
)

from butterfly_guy.core.config import AppConfig, ExecutionSettings
from butterfly_guy.db.queries import OrderIntentQueries
from butterfly_guy.execution.order_manager import IntentPersistenceError, LiveSpread
from butterfly_guy.services.trade_service import TradeService
from tests.test_order_manager import (
    broker_fill,
    make_candidate,
    make_order_manager,
    make_settings,
)

DAY = dt.date(2026, 10, 29)


@pytest.mark.parametrize(
    "changes",
    [
        {"paper_trading": True},
        {"record_live_execution": False},
    ],
)
def test_pilot_config_requires_live_audit(changes):
    execution = dict(live_test_date=DAY, paper_trading=False, record_live_execution=True)
    execution.update(changes)
    with pytest.raises(ValueError, match="dated live test"):
        AppConfig(execution=ExecutionSettings(**execution))


@pytest.mark.asyncio
async def test_no_account_or_market_reads_outside_pilot_day():
    service = TradeService.__new__(TradeService)
    service.config = AppConfig(
        execution=ExecutionSettings(
            live_test_date=DAY,
            paper_trading=False,
            record_live_execution=True,
        )
    )
    with patch(
        "butterfly_guy.services.trade_service.session_date", return_value=DAY.replace(day=30)
    ):
        assert await service.attempt_entry() is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "quantity,limit,day", [(2, 3, DAY), (1, 4.05, DAY), (1, 3, DAY.replace(day=30))]
)
async def test_order_boundary_blocks_size_debit_and_wrong_day(quantity, limit, day):
    om, schwab = make_order_manager(make_settings(live_test_date=DAY))
    with patch("butterfly_guy.core.time_utils.session_date", return_value=day):
        assert (
            await om.execute_single_attempt(make_candidate(5900, 5950, 6000, 3), limit, quantity)
            is None
        )
    schwab.place_order.assert_not_called()


@pytest.mark.asyncio
async def test_pilot_blocks_untimed_or_stale_leg_quotes():
    om, _ = make_order_manager(make_settings(live_test_date=DAY))
    assert await om._fetch_live_spread(make_candidate(5900, 5950, 6000, 3)) is None
    assert om._spread_observation is None


@pytest.mark.asyncio
async def test_observation_persistence_failure_blocks_submit_but_preserves_fill():
    om, _ = make_order_manager(make_settings(record_live_execution=True))
    om.intent_queries = AsyncMock()
    om.intent_queries.append_execution_observation.side_effect = RuntimeError("DB down")
    candidate = make_candidate(5900, 5950, 6000, 3)
    with pytest.raises(RuntimeError, match="DB down"):
        await om._record_execution_quote(candidate, 1, "before_submit")
    await om._record_execution_quote(candidate, 1, "fill_detected")


@pytest.mark.asyncio
async def test_observation_contains_leg_quotes_and_local_timing():
    om, _ = make_order_manager(make_settings(record_live_execution=True))
    candidate = make_candidate(5900, 5950, 6000, 3)
    await om._fetch_live_spread(candidate)
    om.intent_queries = AsyncMock()
    await om._record_execution_quote(candidate, 42, "before_submit", limit_price=3)
    args = om.intent_queries.append_execution_observation.call_args.args
    assert args[0] == 42
    assert args[1]["limit_price"] == 3
    assert len(args[1]["quote"]["legs"]) == 3
    assert args[1]["quote"]["requested_at"] <= args[1]["quote"]["received_at"]


class _IntentStore:
    """broker_order_intents as the DB holds them, with both active-intent indexes.

    *fail_phases* are observation phases whose write fails. *lose_ack* commits the
    intent row and then raises, as a connection lost before the INSERT's reply would.
    """

    def __init__(self, fail_phases=(), lose_ack=False, create_error=None):
        self.rows: dict[int, dict] = {}
        self.fail_phases = set(fail_phases)
        self.lose_ack = lose_ack
        self.create_error = create_error
        self.read_back = AsyncMock(side_effect=ConnectionError("DB still unreachable"))
        self.snapshot_at_submit = None

    def active(self):
        final = {"FILLED", "CANCELED", "REJECTED", "EXPIRED"}
        return [row for row in self.rows.values() if row["status"] not in final]

    async def create_intent(self, *, side, candidate_snapshot, trade_id=None, **_):
        phases = {o["phase"] for o in candidate_snapshot.get("execution_observations", [])}
        if phases & self.fail_phases:
            raise CheckViolationError("before_submit rejected")  # definitive statement rollback
        if any(
            row["side"] == side and (side == "ENTRY" or row["trade_id"] == trade_id)
            for row in self.active()
        ):
            raise UniqueViolationError("duplicate key value violates unique constraint")
        if self.create_error is not None and not self.lose_ack:
            raise self.create_error
        intent_id = len(self.rows) + 1
        self.rows[intent_id] = {
            "side": side, "trade_id": trade_id, "status": "SUBMITTING",
            "snapshot": json.loads(json.dumps(candidate_snapshot)),
        }
        if self.lose_ack:
            raise self.create_error or ConnectionError("connection lost")
        return intent_id

    async def active_broker_order_ids(self, underlying, trade_date, *, exclude_intent_id=None):
        return {row["broker_order_id"] for row in self.active() if row.get("broker_order_id")}

    async def append_execution_observation(self, intent_id, observation):
        if observation["phase"] in self.fail_phases:
            raise ConnectionError("db unavailable")
        self.rows[intent_id]["snapshot"].setdefault("execution_observations", []).append(
            observation
        )

    async def mark_broker_order_id(self, intent_id, broker_order_id):
        self.rows[intent_id].update(status="SUBMITTED", broker_order_id=broker_order_id)

    async def update_broker_status(self, intent_id, status, payload=None):
        self.rows[intent_id]["status"] = status

    async def mark_unknown(self, intent_id, error):
        self.rows[intent_id]["status"] = "UNKNOWN_ABORTED"


SPREAD = LiveSpread(bid=1.85, mark=1.97, ask=2.10)


def _recording_manager(store):
    om, schwab = make_order_manager(make_settings(record_live_execution=True))
    om.intent_queries = store
    om._fetch_live_spread = AsyncMock(return_value=SPREAD)
    return om, schwab


async def _submit(om, side):
    candidate = make_candidate(5900, 5950, 6000, 2.50)
    if side == "entry":
        return await om.execute_single_attempt(candidate, limit_price=2.50)
    return await om.execute_exit(candidate, current_value=2.50, trade_id=7)


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
async def test_failed_before_submit_evidence_leaves_no_intent_and_sends_no_order(side):
    store = _IntentStore(fail_phases={"before_submit"})
    om, schwab = _recording_manager(store)

    for _ in range(2):  # the retry is a fresh attempt, not a conflict with an orphan
        with pytest.raises(CheckViolationError, match="before_submit rejected"):
            await _submit(om, side)

    schwab.place_order.assert_not_awaited()
    assert store.active() == []


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
async def test_before_submit_evidence_is_durable_before_the_order_is_sent(side):
    store = _IntentStore()
    om, schwab = _recording_manager(store)

    async def place(_spec):
        (row,) = store.rows.values()
        store.snapshot_at_submit = json.loads(json.dumps(row["snapshot"]))
        return "ORD1"

    schwab.place_order = AsyncMock(side_effect=place)
    with patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        assert await _submit(om, side) is not None

    build = om.builder.build_butterfly_open if side == "entry" else om.builder.build_butterfly_close
    (first, *_) = store.snapshot_at_submit["execution_observations"]
    assert first["phase"] == "before_submit"
    assert first["limit_price"] == build.call_args.args[1]
    assert [o["phase"] for o in store.rows[1]["snapshot"]["execution_observations"]] == [
        "before_submit", "broker_acknowledged", "fill_detected",
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
@pytest.mark.parametrize("committed", [True, False], ids=["committed", "no-row"])
@pytest.mark.parametrize("error_type", [
    ConnectionError, ConnectionDoesNotExistError, InterfaceError, TimeoutError,
    asyncio.CancelledError, StatementCompletionUnknownError, AdminShutdownError, RuntimeError,
])
async def test_uncertain_intent_create_halts_on_the_first_failure(side, committed, error_type):
    error = error_type("lost INSERT reply")
    store = _IntentStore(lose_ack=committed, create_error=error)
    om, schwab = _recording_manager(store)

    with pytest.raises(
        IntentPersistenceError, match=f"{side} intent creation outcome is unknown"
    ) as caught:
        await _submit(om, side)

    assert caught.value.__cause__ is error
    assert [row["status"] for row in store.active()] == (["SUBMITTING"] if committed else [])
    # Even an unreachable read-back cannot delay or suppress this halt. No adoption,
    # terminalization or broker request, including when the fake knows no row exists.
    store.read_back.assert_not_awaited()
    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
@pytest.mark.parametrize("error_type", [
    CheckViolationError, PostgresSyntaxError, QueryCanceledError, SerializationError,
])
async def test_definitive_intent_create_error_preserves_retry_and_exception(side, error_type):
    error = error_type("server rejected statement")
    store = _IntentStore(create_error=error)
    om, schwab = _recording_manager(store)
    for _ in range(2):
        with pytest.raises(error_type) as caught:
            await _submit(om, side)
        assert caught.value is error
    assert store.rows == {}
    schwab.place_order.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("side", ["entry", "exit"])
async def test_failed_evidence_after_submit_keeps_the_fill_without_resubmitting(side):
    store = _IntentStore(fail_phases={"broker_acknowledged", "fill_detected"})
    om, schwab = _recording_manager(store)

    with patch.object(om, "_wait_for_fill", new=AsyncMock(return_value=broker_fill())):
        result = await _submit(om, side)

    assert result["order_id"] == "ORD1"
    schwab.place_order.assert_awaited_once()
    assert len(store.rows) == 1


@pytest.mark.asyncio
async def test_missing_intent_is_an_audit_failure():
    db = AsyncMock()
    db.pool.execute.return_value = "UPDATE 0"
    with pytest.raises(RuntimeError, match="no durable order intent"):
        await OrderIntentQueries(db).append_execution_observation(1, {"phase": "before_submit"})


@pytest.mark.asyncio
@pytest.mark.parametrize("age,allowed", [(1, True), (15, False), (-5, False)])
async def test_pilot_requires_recent_quote_timestamps(age, allowed):
    om, schwab = make_order_manager(make_settings(live_test_date=DAY))
    candidate = make_candidate(5900, 5950, 6000, 3)
    original = schwab.get_option_chain.side_effect
    now = dt.datetime(2026, 3, 21, 14, 0, tzinfo=dt.timezone.utc)

    def chain(symbol, expiry):
        data = original(symbol, expiry)
        for expirations in (data.get("putExpDateMap", {}), data.get("callExpDateMap", {})):
            for strikes in expirations.values():
                for contracts in strikes.values():
                    for contract in contracts:
                        contract["quoteTimeInLong"] = (now.timestamp() - age) * 1000
        return data

    schwab.get_option_chain.side_effect = chain
    with patch("butterfly_guy.execution.order_manager.now_utc", return_value=now):
        spread = await om._fetch_live_spread(candidate)
    assert (spread is not None) == allowed


@pytest.mark.asyncio
async def test_live_test_exit_does_not_submit_with_missing_fresh_quotes():
    om, schwab = make_order_manager(make_settings(live_test_date=DAY))
    with pytest.raises(Exception, match="requires fresh leg quotes"):
        await om.execute_exit(make_candidate(5900, 5950, 6000, 3), 3)
    schwab.place_order.assert_not_called()


@pytest.mark.parametrize(
    "environment,yaml_value,expected",
    [
        ("false", True, False),
        ("true", False, True),
    ],
)
def test_deployment_paper_override_wins_over_yaml(
    tmp_path, monkeypatch, environment, yaml_value, expected
):
    from butterfly_guy.core.config import load_config

    path = tmp_path / "config.yaml"
    path.write_text(f"execution:\n  paper_trading: {str(yaml_value).lower()}\n")
    monkeypatch.setenv("EXECUTION__PAPER_TRADING", environment)
    assert (
        load_config(path, env_file=str(tmp_path / "absent.env")).execution.paper_trading is expected
    )


def test_invalid_deployment_mode_fails_closed(tmp_path, monkeypatch):
    from butterfly_guy.core.config import load_config

    monkeypatch.setenv("EXECUTION__PAPER_TRADING", "typo")
    with pytest.raises(ValueError):
        load_config(tmp_path / "absent.yaml", env_file=str(tmp_path / "absent.env"))


# --- Operator close in Schwab: bot exits run normally, but never fight a manual close ---

LOWER, CENTER, UPPER = (
    "SPXW  261030P05900000", "SPXW  261030P05950000", "SPXW  261030P06000000",
)
HELD = {"securitiesAccount": {"positions": [
    {"instrument": {"assetType": "OPTION", "symbol": LOWER}, "longQuantity": 1},
    {"instrument": {"assetType": "OPTION", "symbol": CENTER}, "shortQuantity": 2},
    {"instrument": {"assetType": "OPTION", "symbol": UPPER}, "longQuantity": 1},
]}}
FLAT = {"securitiesAccount": {"positions": []}}


def manual_close_order(status="FILLED", order_id="TOS1"):
    legs = [(1, LOWER, "SELL_TO_CLOSE", 1, 2.00), (2, CENTER, "BUY_TO_CLOSE", 2, 1.00),
            (3, UPPER, "SELL_TO_CLOSE", 1, 0.50)]
    return {
        "orderId": order_id, "status": status, "orderType": "NET_CREDIT",
        "quantity": 1, "filledQuantity": 1, "remainingQuantity": 0,
        "orderLegCollection": [
            {"legId": i, "instruction": ins, "quantity": q, "instrument": {"symbol": s}}
            for i, s, ins, q, _ in legs
        ],
        "orderActivityCollection": [{"executionLegs": [
            {"legId": i, "price": p, "quantity": q, "time": "2026-10-30T15:00:00Z"}
            for i, _, _, q, p in legs
        ]}],
    }


def live_service(snapshots, orders, execute_exit=None):
    from types import SimpleNamespace

    from tests.test_position_monitoring import _quotes, _service

    service = _service([_quotes()] * 40)
    service.config.strategy.underlying = "SPX"
    service.config.execution.paper_trading = False
    service.state_machine.evaluate.side_effect = lambda state: SimpleNamespace(
        reason="trailing_drawdown", urgency="NORMAL"
    )
    service.schwab.get_account_snapshot.side_effect = snapshots
    service.schwab.get_todays_orders.side_effect = orders
    service.trade_queries.close_trade = AsyncMock(return_value=True)
    service.risk_engine = AsyncMock()
    if execute_exit is not None:
        service.order_manager.execute_exit.side_effect = execute_exit
    return service


async def run_live_monitor(service, polls=12):
    import asyncio

    from butterfly_guy.data.schemas import TradeRecord
    from tests.test_position_monitoring import EXPIRATION, _candidate

    trade = TradeRecord(
        trade_id=500, trade_date=EXPIRATION, direction="PUT", entry_price=0.30,
        lower_symbol=LOWER, center_symbol=CENTER, upper_symbol=UPPER,
    )
    sleeps = AsyncMock(side_effect=[None] * polls + [asyncio.CancelledError])
    with patch(
        "butterfly_guy.services.position_service.is_market_open", return_value=True
    ), patch(
        "butterfly_guy.services.position_service.session_date", return_value=EXPIRATION
    ), patch(
        "butterfly_guy.services.position_service.get_0dte_expiration", return_value=EXPIRATION
    ), patch("butterfly_guy.services.position_service.asyncio.sleep", new=sleeps), patch(
        "butterfly_guy.services.position_service.notify_telegram",
        new=AsyncMock(return_value=True),
    ) as telegram:
        try:
            await service.monitor_loop(trade, _candidate())
        except asyncio.CancelledError:
            pass
    return telegram


def assert_manual_close_recorded(service):
    args = service.trade_queries.close_trade.await_args.args
    assert args[0] == 500 and args[3] == "manual_close"
    assert args[1] == pytest.approx(0.50)
    assert args[4] == pytest.approx(0.20)
    metadata = service.trade_queries.close_trade.await_args.kwargs["metadata"]
    assert metadata["suppressed_exit_signal"]["reason"] == "trailing_drawdown"
    service.risk_engine.record_pnl.assert_awaited_once()


@pytest.mark.asyncio
async def test_bot_exit_rules_still_run_when_operator_is_idle():
    service = live_service([HELD] * 10, [[]] * 10)
    await run_live_monitor(service, polls=3)
    assert service.order_manager.execute_exit.await_count == 4
    service.trade_queries.close_trade.assert_not_awaited()


@pytest.mark.asyncio
async def test_operator_working_order_hands_off_exit_then_fill_is_adopted():
    service = live_service(
        [HELD, FLAT], [[manual_close_order("WORKING")], [manual_close_order()]]
    )
    await run_live_monitor(service)

    service.order_manager.execute_exit.assert_not_awaited()
    events = [c.args[0] for c in service.decision_queries.log_event.await_args_list]
    assert events.count("exit_handed_to_operator") == 1
    assert events.count("manual_exit_signal_suppressed") == 1
    assert_manual_close_recorded(service)



@pytest.mark.asyncio
async def test_manual_close_discord_messages_say_it_was_manual():
    service = live_service(
        [HELD, FLAT], [[manual_close_order("WORKING")], [manual_close_order()]]
    )
    service.notifier = AsyncMock()
    await run_live_monitor(service)

    texts = [c.args[0] for c in service.notifier.notify_text.await_args_list]
    assert any("manual action in Schwab" in text for text in texts)
    exit_call = service.notifier.notify_exit.await_args.kwargs
    assert exit_call["exit_reason"] == "manual_close"
    assert exit_call["exit_price"] == pytest.approx(0.50)
    assert "Closed by you in Schwab (filled 11:00:00 ET)" in exit_call["manual_detail"]
    assert "`trailing_drawdown`" in exit_call["manual_detail"]


@pytest.mark.asyncio
async def test_bot_ladder_takeover_hands_off_and_adopts_operator_fill():
    from butterfly_guy.execution.order_manager import OperatorExitTakeoverError

    service = live_service(
        [HELD, FLAT], [[], [manual_close_order()]],
        execute_exit=OperatorExitTakeoverError("operator canceled bot exit order"),
    )
    await run_live_monitor(service)

    service.order_manager.execute_exit.assert_awaited_once()
    assert_manual_close_recorded(service)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "orders", [[], [manual_close_order(), manual_close_order("FILLED", "TOS2")]]
)
async def test_unresolved_manual_close_alerts_once_and_never_trades(orders):
    from butterfly_guy.core.metrics import readiness_snapshot, set_readiness

    set_readiness(None)
    service = live_service([FLAT] * 6, [orders] * 6)
    telegram = await run_live_monitor(service, polls=25)

    service.order_manager.execute_exit.assert_not_awaited()
    service.trade_queries.close_trade.assert_not_awaited()
    assert telegram.await_count == 1
    assert readiness_snapshot() == (False, "manual_close_unresolved")
    set_readiness(None)


def symbol_candidate():
    import dataclasses

    return dataclasses.replace(
        make_candidate(5900, 5950, 6000, 3),
        lower_symbol=LOWER, center_symbol=CENTER, upper_symbol=UPPER,
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "snapshot,orders",
    [(HELD, [manual_close_order("WORKING")]), (FLAT, [manual_close_order()])],
)
async def test_exit_ladder_never_submits_against_an_operator_close(snapshot, orders):
    from butterfly_guy.execution.order_manager import LiveSpread, OperatorExitTakeoverError

    om, schwab = make_order_manager(make_settings())
    schwab.get_account_snapshot.return_value = snapshot
    schwab.get_todays_orders.return_value = orders
    spread = LiveSpread(bid=0.4, mark=0.5, ask=0.6)
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)):
        with pytest.raises(OperatorExitTakeoverError):
            await om.execute_exit(symbol_candidate(), 0.5)
    schwab.place_order.assert_not_called()


@pytest.mark.asyncio
async def test_exit_ladder_ignores_its_own_unsettled_order():
    from butterfly_guy.execution.order_manager import LiveSpread

    om, schwab = make_order_manager(make_settings())
    schwab.get_account_snapshot.return_value = HELD
    schwab.get_todays_orders.return_value = [manual_close_order("WORKING", "ORD1")]
    spread = LiveSpread(bid=0.4, mark=0.5, ask=0.6)
    waits = AsyncMock(side_effect=[False, False])
    with patch.object(om, "_fetch_live_spread", new=AsyncMock(return_value=spread)), \
         patch.object(om, "_wait_for_fill", new=waits), \
         patch.object(om, "_check_post_cancel_fill", new=AsyncMock(return_value=None)):
        schwab.get_todays_orders.side_effect = [[], [manual_close_order("WORKING", "ORD1")],
                                                [manual_close_order("WORKING", "TOS9")]]
        from butterfly_guy.execution.order_manager import OperatorExitTakeoverError
        with pytest.raises(OperatorExitTakeoverError):
            await om.execute_exit(symbol_candidate(), 0.5)
    assert schwab.place_order.await_count == 2


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["CANCELED", "REPLACED"])
async def test_operator_cancel_or_edit_of_bot_exit_is_a_takeover(status):
    from butterfly_guy.execution.order_manager import OperatorExitTakeoverError

    om, schwab = make_order_manager(make_settings())
    schwab.get_order_status = AsyncMock(return_value={"status": status})
    with pytest.raises(OperatorExitTakeoverError):
        await om._wait_for_fill("ORD1", 5, operator_cancel_is_takeover=True)
    if status == "CANCELED":
        assert await om._wait_for_fill("ORD1", 5) is False


def _open_row():
    return {
        "id": 500, "quantity": 1, "lower_symbol": LOWER,
        "center_symbol": CENTER, "upper_symbol": UPPER,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize("monitored", [500, None])
async def test_reconciler_leaves_operator_close_to_the_monitor(monitored):
    from butterfly_guy.scripts.run_live import _assert_broker_state_matches_db

    intents = AsyncMock()
    intents.intents_for_day.return_value = []
    working = AsyncMock()
    working.get_account_snapshot.return_value = HELD
    working.get_todays_orders.return_value = [manual_close_order("WORKING")]
    filled = AsyncMock()
    filled.get_account_snapshot.return_value = FLAT
    filled.get_todays_orders.return_value = [manual_close_order()]
    replaced = AsyncMock()
    replaced.get_account_snapshot.return_value = HELD
    replaced.get_todays_orders.return_value = [manual_close_order("REPLACED")]

    for schwab, error in (
        (working, "unknown active"), (filled, "broker is flat"), (replaced, None),
    ):
        call = _assert_broker_state_matches_db(
            schwab, "SPX", [_open_row()], intents, allow_repair=False,
            monitored_trade_id=monitored,
        )
        if monitored or error is None:
            await call
        else:
            with pytest.raises(RuntimeError, match=error):
                await call


@pytest.mark.asyncio
async def test_reconciler_still_flags_orders_on_other_legs():
    from butterfly_guy.scripts.run_live import _assert_broker_state_matches_db

    intents = AsyncMock()
    intents.intents_for_day.return_value = []
    other = manual_close_order("WORKING")
    other["orderLegCollection"][0]["instrument"]["symbol"] = "SPXW  261030P05800000"
    schwab = AsyncMock()
    schwab.get_account_snapshot.return_value = HELD
    schwab.get_todays_orders.return_value = [other]
    with pytest.raises(RuntimeError, match="unknown active"):
        await _assert_broker_state_matches_db(
            schwab, "SPX", [_open_row()], intents, allow_repair=False,
            monitored_trade_id=500,
        )
