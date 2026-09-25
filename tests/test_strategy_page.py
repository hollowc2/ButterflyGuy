"""Tests for the static "strategy explained" page."""

from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

from butterfly_guy.core.config import load_config
from butterfly_guy.reports.live_performance import TradePoint
from butterfly_guy.reports.strategy_page import (
    DEFAULT_REFERENCE_SPOT,
    STRATEGY_SCRIPT_NAME,
    best_trade,
    reference_spot,
    render_strategy_html,
    strategy_params,
    strategy_script,
)
from butterfly_guy.scripts import generate_live_performance

SPX_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "config.yaml"
SCRIPT_TAG = re.compile(r"<script(?P<attrs>(?:\s[^>]*)?)>(?P<body>.*?)</script\s*>", re.DOTALL)


def _trade(day: int, pnl: float, *, center: float = 7630.0) -> TradePoint:
    return TradePoint(
        trade_date=dt.date(2026, 9, day),
        direction="PUT",
        wing_width=25,
        center_strike=center,
        lower_strike=center - 25,
        upper_strike=center + 25,
        entry_price=2.0,
        entry_time=None,
        exit_price=2.0 + pnl / 100,
        exit_time=None,
        exit_reason="cash_settled",
        pnl_dollars=pnl,
        peak_value=None,
        vix=None,
        entry_spot=None,
        dd_at_exit_pct=None,
    )


def _params(doc: str) -> dict:
    match = re.search(r'id="strategy-params">(.*?)</script>', doc, re.DOTALL)
    assert match
    return json.loads(match.group(1))


def test_params_follow_the_spx_config() -> None:
    config = load_config(SPX_CONFIG)
    params = strategy_params(config, spot=7650.0)

    buckets = sorted(config.strategy.vix_width_buckets or [], key=lambda b: b.vix_max)
    assert [b["widths"] for b in params["buckets"]] == [b.widths for b in buckets]
    assert [b["vixMax"] for b in params["buckets"]] == [b.vix_max for b in buckets]
    assert all(b["sigmas"] == [0.25, 0.5, 0.75] for b in params["buckets"])
    assert params["rrMin"] == config.strategy.rr_min
    assert params["centerTolerance"] == config.entry.center_tolerance
    # 07:00 PT entry start → 10:00 ET → six hours to the close.
    assert params["entryEt"] == "10:00"
    assert params["hoursLeft"] == 6.0


def test_page_renders_config_values_and_no_leftover_tokens() -> None:
    doc = render_strategy_html(load_config(SPX_CONFIG), spot=7650.0, best=_trade(23, 944.0))

    assert "__" not in re.sub(r"<script.*?</script>", "", doc, flags=re.DOTALL)
    assert "10:00–10:45 ET" in doc
    assert "Zombieland" in doc and "Chaos" in doc
    assert "60%" in doc and "90%" in doc and "75%" in doc
    assert "Best paper hit so far" in doc
    assert "+$944" in doc
    assert 'href="../"' in doc
    assert _params(doc)["spot"] == 7650.0


def test_page_has_no_inline_executable_script() -> None:
    """The site CSP allows inline scripts only by hash; this page must need none."""
    doc = render_strategy_html(load_config(SPX_CONFIG), spot=7650.0, best=None)
    for match in SCRIPT_TAG.finditer(doc):
        attrs = match.group("attrs")
        assert "application/json" in attrs or f'src="{STRATEGY_SCRIPT_NAME}?v=' in attrs
    for origin in ("fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net"):
        assert origin not in doc
    assert "Best paper hit so far" not in doc


def test_reference_spot_and_best_trade() -> None:
    assert reference_spot([]) == DEFAULT_REFERENCE_SPOT
    assert reference_spot([_trade(1, -100.0, center=7612.0)]) == 7600.0
    assert best_trade([_trade(1, -100.0)]) is None
    assert best_trade([_trade(1, 50.0), _trade(2, 944.0), _trade(3, -10.0)]).pnl_dollars == 944.0


def test_generate_writes_strategy_page_beside_report(tmp_path, monkeypatch) -> None:
    class FakeConn:
        async def close(self) -> None:
            return None

    async def fake_connect(_dsn):
        return FakeConn()

    async def fake_build_report(_conn, _underlying):
        return [_trade(23, 944.0)], []

    monkeypatch.setattr(generate_live_performance.asyncpg, "connect", fake_connect)
    monkeypatch.setattr(generate_live_performance, "build_report", fake_build_report)

    output = tmp_path / "butterfly-spx" / "index.html"
    generate_live_performance.main(
        ["--output", str(output), "--strategy-config", str(SPX_CONFIG)]
    )

    assert 'href="strategy/"' in output.read_text()
    page = (output.parent / "strategy" / "index.html").read_text()
    assert _params(page)["spot"] == 7650.0
    assert (output.parent / "strategy" / STRATEGY_SCRIPT_NAME).read_text() == strategy_script()


def test_generate_refuses_missing_strategy_config(tmp_path, monkeypatch, capsys) -> None:
    class FakeConn:
        async def close(self) -> None:
            return None

    async def fake_connect(_dsn):
        return FakeConn()

    async def fake_build_report(_conn, _underlying):
        return [], []

    monkeypatch.setattr(generate_live_performance.asyncpg, "connect", fake_connect)
    monkeypatch.setattr(generate_live_performance, "build_report", fake_build_report)

    output = tmp_path / "index.html"
    code = generate_live_performance.main(
        ["--output", str(output), "--strategy-config", str(tmp_path / "missing.yaml")]
    )

    assert code == 1
    # The performance page is still published; only the explainer is skipped.
    assert output.exists()
    assert not (tmp_path / "strategy" / "index.html").exists()
    assert "strategy config not found" in capsys.readouterr().err

