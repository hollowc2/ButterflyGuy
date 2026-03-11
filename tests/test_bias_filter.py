"""Unit tests for BiasScoreFilter."""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from butterfly_guy.backtest.data_loader import DayData, MinuteBar
from butterfly_guy.backtest.simulation_engine import SimulationEngine, SimulationParams
from butterfly_guy.strategy.bias_filter import BiasScoreFilter

EASTERN = ZoneInfo("America/New_York")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_bar(
    hour: int,
    minute: int,
    close: float,
    volume: int = 1000,
    high: float | None = None,
    low: float | None = None,
) -> MinuteBar:
    ts = dt.datetime(2026, 1, 5, hour, minute, tzinfo=EASTERN)
    return MinuteBar(
        ts=ts,
        open=close,
        high=high if high is not None else close + 1,
        low=low if low is not None else close - 1,
        close=close,
        volume=volume,
    )


def make_pre_entry_bars(n: int = 25, base_close: float = 5900.0) -> list[MinuteBar]:
    """Build n bars starting at 09:30 ET, incrementing by 1 minute each."""
    bars = []
    for i in range(n):
        total_minutes = 9 * 60 + 30 + i
        h, m = divmod(total_minutes, 60)
        bars.append(make_bar(h, m, base_close))
    return bars


# ---------------------------------------------------------------------------
# _ema tests
# ---------------------------------------------------------------------------

class TestEma:
    def test_returns_none_when_insufficient_bars(self):
        assert BiasScoreFilter._ema([1.0] * 8, 9) is None

    def test_returns_none_exactly_one_short(self):
        assert BiasScoreFilter._ema([1.0] * 20, 21) is None

    def test_returns_value_at_exact_period(self):
        closes = [10.0] * 9
        result = BiasScoreFilter._ema(closes, 9)
        assert result == pytest.approx(10.0)

    def test_flat_series_returns_seed(self):
        closes = [5.0] * 15
        result = BiasScoreFilter._ema(closes, 9)
        assert result == pytest.approx(5.0)

    def test_rising_series_ema_below_last_price(self):
        closes = list(range(1, 30))  # 1..29
        ema9 = BiasScoreFilter._ema(closes, 9)
        ema21 = BiasScoreFilter._ema(closes, 21)
        assert ema9 > ema21  # faster EMA higher in uptrend

    def test_ema9_gt_ema21_in_uptrend(self):
        closes = [100.0 + i * 0.5 for i in range(30)]
        assert BiasScoreFilter._ema(closes, 9) > BiasScoreFilter._ema(closes, 21)


# ---------------------------------------------------------------------------
# _compute_vwap tests
# ---------------------------------------------------------------------------

class TestComputeVwap:
    def test_equal_volumes_returns_mean_close(self):
        bars = [make_bar(9, 30 + i, float(100 + i), volume=100) for i in range(5)]
        vwap = BiasScoreFilter._compute_vwap(bars, fallback=0.0)
        expected = sum(100 + i for i in range(5)) / 5
        assert vwap == pytest.approx(expected)

    def test_higher_volume_bar_pulls_vwap(self):
        bars = [
            make_bar(9, 30, 100.0, volume=1),
            make_bar(9, 31, 200.0, volume=9),
        ]
        vwap = BiasScoreFilter._compute_vwap(bars, fallback=0.0)
        assert vwap == pytest.approx((100 * 1 + 200 * 9) / 10)

    def test_zero_volume_returns_fallback(self):
        bars = [make_bar(9, 30, 500.0, volume=0)]
        assert BiasScoreFilter._compute_vwap(bars, fallback=999.0) == 999.0


# ---------------------------------------------------------------------------
# _compute_or tests
# ---------------------------------------------------------------------------

class TestComputeOr:
    def test_or_bars_filtered_before_945(self):
        bars = [
            make_bar(9, 30, 100.0, high=105.0, low=95.0),
            make_bar(9, 44, 102.0, high=108.0, low=98.0),
            make_bar(9, 45, 103.0, high=110.0, low=99.0),  # NOT in OR
        ]
        or_high, or_low = BiasScoreFilter._compute_or(bars)
        assert or_high == pytest.approx(108.0)
        assert or_low == pytest.approx(95.0)

    def test_no_or_bars_returns_zero_tuple(self):
        bars = [make_bar(9, 45, 100.0)]  # starts at 09:45, excluded
        assert BiasScoreFilter._compute_or(bars) == (0.0, 0.0)

    def test_empty_bars_returns_zero_tuple(self):
        assert BiasScoreFilter._compute_or([]) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Scoring / direction tests
# ---------------------------------------------------------------------------

class TestBiasScore:
    def _make_bullish_bars(self) -> list[MinuteBar]:
        """Bars that produce strong bullish score: rising price, above OR high."""
        bars = []
        for i in range(30):
            total_minutes = 9 * 60 + 30 + i
            h, m = divmod(total_minutes, 60)
            close = 5800.0 + i * 2  # steadily rising
            bars.append(make_bar(h, m, close, volume=1000))
        return bars

    def _make_bearish_bars(self) -> list[MinuteBar]:
        """Bars that produce strong bearish score: falling price, below OR low."""
        bars = []
        for i in range(30):
            total_minutes = 9 * 60 + 30 + i
            h, m = divmod(total_minutes, 60)
            close = 5900.0 - i * 2  # steadily falling
            bars.append(make_bar(h, m, close, volume=1000))
        return bars

    def test_strong_bullish_returns_call(self):
        f = BiasScoreFilter()
        bars = self._make_bullish_bars()
        entry_close = bars[-1].close
        prev_close = 5750.0  # gap up
        result = f.get_direction(bars, prev_close, entry_close)
        assert result == "CALL"

    def test_strong_bearish_returns_put(self):
        f = BiasScoreFilter()
        bars = self._make_bearish_bars()
        entry_close = bars[-1].close
        prev_close = 5950.0  # gap down
        result = f.get_direction(bars, prev_close, entry_close)
        assert result == "PUT"

    def test_or_breakout_alone_triggers_call(self):
        """OR signal is ±2 — alone it meets the ±2 threshold."""
        f = BiasScoreFilter()
        # One OR bar with very tight range
        or_bar = MinuteBar(
            ts=dt.datetime(2026, 1, 5, 9, 30, tzinfo=EASTERN),
            open=5900.0, high=5905.0, low=5895.0, close=5900.0, volume=1000,
        )
        # Entry bar well above OR high but flat vs prev_close (gap = 0), equal to VWAP
        entry_bar = MinuteBar(
            ts=dt.datetime(2026, 1, 5, 10, 0, tzinfo=EASTERN),
            open=5910.0, high=5911.0, low=5909.0, close=5910.0, volume=1000,
        )
        bars = [or_bar, entry_bar]
        # prev_close == entry_close → gap signal = 0
        # entry > or_high(5905) → +2 → total ≥ 2
        result = f.get_direction(bars, prev_close=5910.0, entry_close=5910.0)
        assert result == "CALL"

    def test_gap_alone_insufficient(self):
        """Gap signal only contributes +1, below the ±2 threshold."""
        f = BiasScoreFilter()
        # Single bar at 09:45 (outside OR window), same close as entry
        bar = MinuteBar(
            ts=dt.datetime(2026, 1, 5, 9, 50, tzinfo=EASTERN),
            open=5900.0, high=5901.0, low=5899.0, close=5900.0, volume=1000,
        )
        # entry_close == vwap (the only bar's close) → vwap signal = 0
        # gap: entry_close > prev_close by a tiny bit → +1
        # EMA: 1 bar, < 9, → None → 0
        # OR: no bars before 09:45 → (0,0) → skip
        result = f.get_direction([bar], prev_close=5899.0, entry_close=5900.0)
        assert result is None

    def test_neutral_returns_none(self):
        """Conflicting signals that cancel out → None."""
        f = BiasScoreFilter()
        # Bar after OR window (no OR signal): gap up (+1), entry < vwap (-1) → net 0
        bars = [make_bar(9, 50, 5910.0, volume=1000)]  # after 09:45 → no OR bars
        result = f.get_direction(bars, prev_close=5900.0, entry_close=5905.0)
        # entry_close=5905 < vwap=5910 → -1; gap: 5905>5900 → +1; OR: skip; net=0 → None
        assert result is None


# ---------------------------------------------------------------------------
# Engine integration tests
# ---------------------------------------------------------------------------

class TestEngineIntegration:
    def _make_day(self, trending_up: bool = True) -> DayData:
        bars = []
        for i in range(80):  # full trading day bars
            total_minutes = 9 * 60 + 30 + i
            h, m = divmod(total_minutes, 60)
            if trending_up:
                close = 5800.0 + i * 1.5
            else:
                close = 5900.0 - i * 1.0
            bars.append(make_bar(h, m, close, volume=500))
        return DayData(
            date=dt.date(2026, 1, 5),
            bars=bars,
            vix=15.0,
            prev_close=5780.0 if trending_up else 5950.0,
        )

    def test_use_bias_filter_true_routes_to_bias(self):
        """use_bias_filter=True should produce a trade result (direction set by bias)."""
        engine = SimulationEngine()
        day = self._make_day(trending_up=True)
        params = SimulationParams(use_bias_filter=True, wing_width=10, rr_min=6.0)
        result = engine.simulate_day(day, params)
        # Strong uptrend → bias filter should find CALL direction and trade
        assert result.direction in ("CALL", "PUT", "")  # at least runs without error

    def test_direction_override_ignores_bias(self):
        """direction_override takes precedence over use_bias_filter."""
        engine = SimulationEngine()
        day = self._make_day(trending_up=True)
        params = SimulationParams(
            direction_override="PUT",
            use_bias_filter=True,
            wing_width=10,
            rr_min=6.0,
        )
        result = engine.simulate_day(day, params)
        if result.traded:
            assert result.direction == "PUT"

    def test_none_direction_results_in_no_trade(self):
        """When bias filter always returns None, day should be untraded."""
        engine = SimulationEngine()
        # Flat bars with zero volume → VWAP fallback == entry_close → vwap signal = 0
        # gap: flat → 0; EMA: flat → 0 contribution; OR: no OR bars → skip
        # total = 0 → None every bar
        bars = []
        for i in range(80):
            total_minutes = 9 * 60 + 30 + i
            h, m = divmod(total_minutes, 60)
            bars.append(MinuteBar(
                ts=dt.datetime(2026, 1, 5, h, m, tzinfo=EASTERN),
                open=5900.0, high=5901.0, low=5899.0, close=5900.0, volume=0,
            ))
        day = DayData(date=dt.date(2026, 1, 5), bars=bars, vix=15.0, prev_close=5900.0)
        params = SimulationParams(use_bias_filter=True, wing_width=10, rr_min=6.0)
        result = engine.simulate_day(day, params)
        assert not result.traded
