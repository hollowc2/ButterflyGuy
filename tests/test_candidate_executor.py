import datetime as dt

import pytest

from butterfly_guy.candidate_fleet.evaluator import (
    CandidateAuditContext,
    CandidatePaperExecutor,
    assert_candidate_safety,
)
from butterfly_guy.candidate_fleet.models import MarketSnapshot, SnapshotIdentity
from butterfly_guy.core.config import AppConfig
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote


class FakeProvider:
    def __init__(self, fail_pin: bool = False) -> None:
        self.fail_pin = fail_pin
        self.pinned: list[SnapshotIdentity] = []

    async def pin(self, identity: SnapshotIdentity) -> None:
        if self.fail_pin:
            raise RuntimeError("archive unavailable")
        self.pinned.append(identity)


def market() -> MarketSnapshot:
    expiration = dt.date.today()

    def q(symbol: str, strike: float, mark: float) -> OptionQuote:
        return OptionQuote(
            symbol=symbol,
            underlying="SPX",
            expiration=expiration,
            strike=strike,
            option_type="CALL",
            bid=mark - 0.1,
            ask=mark + 0.1,
            mark=mark,
        )

    return MarketSnapshot(
        identity=SnapshotIdentity("feed", 1),
        captured_at=dt.datetime.now(dt.timezone.utc),
        expiration=expiration,
        spot=6300,
        vix=18,
        session_open=6290,
        previous_close=6280,
        quotes=(q("L", 6280, 4.0), q("C", 6300, 2.0), q("U", 6320, 1.0)),
    )


def candidate() -> ButterflyCandidate:
    return ButterflyCandidate(
        direction="CALL",
        wing_width=20,
        center_strike=6300,
        lower_strike=6280,
        upper_strike=6320,
        cost=1,
        max_profit=19,
        reward_risk=19,
        lower_be=6281,
        upper_be=6319,
        distance_from_spot=0,
        spot_price=6300,
        lower_symbol="L",
        center_symbol="C",
        upper_symbol="U",
    )


@pytest.mark.asyncio
async def test_candidate_entry_pins_before_mark_fill() -> None:
    provider = FakeProvider()
    executor = CandidatePaperExecutor(
        provider,  # type: ignore[arg-type]
        CandidateAuditContext("best-rr", "config-hash", "git-sha"),
    )
    snapshot = market()

    fill = await executor.entry(candidate(), snapshot)

    assert provider.pinned == [snapshot.identity]
    assert fill["fill_price"] == 1.0
    assert fill["paper_fill_model"] == "shared_feed_mark_v1"
    assert not hasattr(executor, "place_order")
    assert not hasattr(executor, "cancel_order")
    assert not hasattr(executor, "get_order_status")


@pytest.mark.asyncio
async def test_candidate_entry_is_blocked_when_pin_fails() -> None:
    executor = CandidatePaperExecutor(
        FakeProvider(fail_pin=True),  # type: ignore[arg-type]
        CandidateAuditContext("best-rr", "config-hash", "git-sha"),
    )
    with pytest.raises(RuntimeError, match="archive unavailable"):
        await executor.entry(candidate(), market())


def test_candidate_safety_rejects_live_or_credentialed_runtime() -> None:
    assert_candidate_safety(AppConfig(), {})
    live = AppConfig(
        execution={
            "paper_trading": False,
            "allow_live_trading": True,
        }
    )
    with pytest.raises(RuntimeError, match="paper_trading"):
        assert_candidate_safety(live, {})
    with pytest.raises(RuntimeError, match="SCHWAB_API_KEY"):
        assert_candidate_safety(AppConfig(), {"SCHWAB_API_KEY": "secret"})
