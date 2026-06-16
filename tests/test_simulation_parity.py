"""Tests for backtest/live parity fields on SimulationParams."""

import pytest

from butterfly_guy.backtest.simulation_engine import SimulationParams


def test_paper_entry_commission_matches_live_formula():
    params = SimulationParams(paper_commission_per_contract=0.65, quantity=1)
    assert params.paper_entry_commission() == pytest.approx(0.026)


def test_exit_before_close_defaults_to_disabled_like_live_config():
    params = SimulationParams()
    assert params.exit_before_close_minutes == 0
