"""Unit tests for GapRegimeFilter.apply()."""

from butterfly_guy.strategy.gap_regime_filter import GapRegimeFilter
from butterfly_guy.strategy.regime_classifier import Regime

# Helpers
SPOT = 5500.0
PREV_CLOSE_GAP_DOWN = 5520.0   # spot < prev_close → gap down ~0.36%
PREV_CLOSE_GAP_UP = 5480.0     # spot > prev_close → gap up ~0.36%
PREV_CLOSE_TINY = 5501.0       # abs gap = 0.018% — below any reasonable min_gap_pct


class TestMinGapPct:
    def test_gap_below_min_returns_skip(self):
        f = GapRegimeFilter(min_gap_pct=0.0025)
        direction, reason = f.apply(SPOT, PREV_CLOSE_TINY, Regime.BULL)
        assert direction is None
        assert reason == "gap_below_min"

    def test_gap_above_min_passes_through(self):
        f = GapRegimeFilter(min_gap_pct=0.0025)
        direction, reason = f.apply(SPOT, PREV_CLOSE_GAP_DOWN, Regime.BULL)
        # No bull_call_bias set, so no override either
        assert direction is None
        assert reason is None

    def test_min_gap_applies_symmetrically_to_gap_up(self):
        f = GapRegimeFilter(min_gap_pct=0.0025)
        direction, reason = f.apply(SPOT, PREV_CLOSE_TINY, Regime.BEAR)
        assert direction is None
        assert reason == "gap_below_min"


class TestBullCallBias:
    def test_bull_regime_gap_down_returns_call_override(self):
        f = GapRegimeFilter(bull_call_bias=True)
        direction, reason = f.apply(SPOT, PREV_CLOSE_GAP_DOWN, Regime.BULL)
        assert direction == "CALL"
        assert reason is None

    def test_bull_regime_gap_up_is_noop(self):
        f = GapRegimeFilter(bull_call_bias=True)
        direction, reason = f.apply(SPOT, PREV_CLOSE_GAP_UP, Regime.BULL)
        assert direction is None
        assert reason is None

    def test_bear_regime_gap_down_is_noop(self):
        f = GapRegimeFilter(bull_call_bias=True)
        direction, reason = f.apply(SPOT, PREV_CLOSE_GAP_DOWN, Regime.BEAR)
        assert direction is None
        assert reason is None

    def test_chop_regime_gap_down_is_noop(self):
        f = GapRegimeFilter(bull_call_bias=True)
        direction, reason = f.apply(SPOT, PREV_CLOSE_GAP_DOWN, Regime.CHOP)
        assert direction is None
        assert reason is None


class TestSkipBeforeOverride:
    def test_tiny_gap_down_in_bull_is_skipped_not_overridden(self):
        """min_gap_pct check runs before bull_call_bias, so tiny gap-down is skipped."""
        f = GapRegimeFilter(bull_call_bias=True, min_gap_pct=0.0025)
        direction, reason = f.apply(SPOT, PREV_CLOSE_TINY, Regime.BULL)
        assert direction is None
        assert reason == "gap_below_min"


class TestDefaultsAreNoop:
    def test_default_filter_is_noop(self):
        f = GapRegimeFilter()
        direction, reason = f.apply(SPOT, PREV_CLOSE_GAP_DOWN, Regime.BULL)
        assert direction is None
        assert reason is None
