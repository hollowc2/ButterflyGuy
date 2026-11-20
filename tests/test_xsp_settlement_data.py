"""Native settlement identity, conflict detection, and independent expiry cash ledger."""
import json
from decimal import Decimal

import pytest

from tools.research_studies.xsp_independent.settlement_data import (
    ENDPOINTS,
    SOURCE_TYPE,
    cash_settlement_pnl,
    native_rows,
    scaled_close_diagnostic,
    tent_value,
)


def native(value, *, trading_symbol="XSP", settlement_symbol="XSP", date="2026-09-25"):
    return {"expiration_date": date, "trading_symbol": trading_symbol,
            "settlement_symbol": settlement_symbol, "settlement_value": value}


def raw_files(root, weekly=(), standard=(), eom=()):
    for category, values in zip(ENDPOINTS, (weekly, standard, eom), strict=True):
        (root / ENDPOINTS[category][0]).write_text(json.dumps({"data": list(values)}))


def test_exact_native_identity_excludes_binary_nanos_and_spx(tmp_path):
    raw_files(tmp_path, weekly=[
        native(774.34), native(900, trading_symbol="XSPBW", settlement_symbol="XSPBX"),
        native(800, trading_symbol="NANOS"),
        native(700, trading_symbol="SPXW", settlement_symbol="SPX")])
    row = native_rows(tmp_path, ["2026-09-25"], {"2026-09-25": "7743.410000"})[0]
    assert row["settlement"] == "774.34"
    assert row["source_type"] == SOURCE_TYPE
    assert row["scaled_close_exact_diagnostic"] == "774.341"
    assert row["published_minus_scaled_diagnostic"] == "-0.001"


def test_conflicting_native_sources_fail_and_identical_overlap_is_attributed(tmp_path):
    raw_files(tmp_path, weekly=[native(774.34)], standard=[native(774.35)])
    with pytest.raises(ValueError, match="conflicting"):
        native_rows(tmp_path, ["2026-09-25"], {})
    raw_files(tmp_path, weekly=[native(774.34)], standard=[native(774.34)])
    row = native_rows(tmp_path, ["2026-09-25"], {})[0]
    assert row["source_categories"] == "weekly|standard"
    assert "W/2026" in row["source_url"] and "S/2026" in row["source_url"]


def test_missing_native_value_stays_missing_even_when_official_spx_close_exists(tmp_path):
    raw_files(tmp_path)
    row = native_rows(tmp_path, ["2026-09-25"], {"2026-09-25": "7743.41"})[0]
    assert row["settlement"] == ""
    assert row["source_type"] == "missing_native_settlement"
    assert row["scaled_close_exact_diagnostic"] == "774.341"


def test_duplicate_source_date_refused(tmp_path):
    raw_files(tmp_path, weekly=[native(774.34), native(774.34)])
    with pytest.raises(ValueError, match="duplicate"):
        native_rows(tmp_path, ["2026-09-25"], {})


@pytest.mark.parametrize("settlement, expected", [
    (597, 0), (598, 0), (599, 1), (600, 2), (600.37, 1.63), (602, 0), (603, 0)])
def test_tent_intrinsic_matches_independent_three_leg_call_and_put_exercise(settlement, expected):
    call = max(settlement - 598, 0) - 2 * max(settlement - 600, 0) + max(settlement - 602, 0)
    put = max(598 - settlement, 0) - 2 * max(600 - settlement, 0) + max(602 - settlement, 0)
    assert call == pytest.approx(expected)
    assert put == pytest.approx(expected)
    assert tent_value(600, 2, settlement) == pytest.approx(expected)


def test_expiry_cash_ledger_has_only_opening_fee_and_opening_stress():
    # $163 intrinsic cash - $50 entry - $2.60 opening fee; no closing order.
    assert cash_settlement_pnl(.50, 600, 2, 600.37) == pytest.approx(110.40)
    assert cash_settlement_pnl(.50, 600, 2, 600.37, entry_stress=.05) == pytest.approx(105.40)
    assert cash_settlement_pnl(.50, 600, 2, 603) == pytest.approx(-52.60)


def test_exact_scaling_is_labeled_diagnostic_and_has_no_effective_date_assumption():
    assert scaled_close_diagnostic("5160.19") == Decimal("516.019")
    with pytest.raises(ValueError):
        scaled_close_diagnostic("5160.191")


@pytest.mark.parametrize("entry, stress, fee", [
    (float("nan"), 0, 2.6), (.5, float("inf"), 2.6), (.5, 0, -1)])
def test_invalid_cash_inputs_refused(entry, stress, fee):
    with pytest.raises(ValueError):
        cash_settlement_pnl(entry, 600, 2, 600.37, entry_stress=stress, opening_fee=fee)
