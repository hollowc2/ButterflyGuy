import json
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASHBOARDS = ROOT / "infra/grafana/dashboards"


def _dashboard(name: str) -> dict:
    return json.loads((DASHBOARDS / name).read_text())


def _panels(dashboard: dict) -> Iterator[dict]:
    def visit(panels: list[dict]) -> Iterator[dict]:
        for panel in panels:
            yield panel
            yield from visit(panel.get("panels", []))

    yield from visit(dashboard["panels"])


def _expressions(dashboard: dict) -> set[str]:
    return {
        target["expr"]
        for panel in _panels(dashboard)
        for target in panel.get("targets", [])
        if "expr" in target
    }


def test_only_primary_butterfly_dashboards_remain() -> None:
    assert {path.name for path in DASHBOARDS.glob("*.json")} == {
        "butterfly_trade_detail.json",
        "butterfly_trading.json",
        "performance.json",
    }


def test_candidate_review_metrics_are_folded_into_performance() -> None:
    dashboard = _dashboard("performance.json")
    rows = {panel["title"]: panel for panel in dashboard["panels"]}

    assert rows["SPX Candidate Comparison"]["collapsed"] is True
    assert {
        "candidate_evaluator_closed_trade_count",
        "candidate_evaluator_realized_pnl_dollars",
        "candidate_evaluator_average_pnl_dollars",
        "candidate_evaluator_win_rate",
        "candidate_evaluator_profit_factor",
        "candidate_evaluator_max_drawdown_dollars",
        "candidate_evaluator_largest_winner_share_ratio",
        "candidate_evaluator_pnl_without_largest_winner_dollars",
        "candidate_evaluator_parity_failures",
        "candidate_evaluator_data_quality_failures",
    } <= _expressions(dashboard)


def test_candidate_runtime_health_is_folded_into_trading() -> None:
    dashboard = _dashboard("butterfly_trading.json")
    rows = {panel["title"]: panel for panel in dashboard["panels"]}

    assert rows["SPX Candidate Fleet Health"]["collapsed"] is True
    assert {
        'up{job="spx_candidate_evaluator"}',
        "candidate_feed_sequence",
        "candidate_feed_snapshot_age_seconds",
        "candidate_evaluator_open_positions",
    } <= _expressions(dashboard)


def test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource() -> None:
    dashboard = _dashboard("butterfly_trade_detail.json")
    variables = {variable["name"]: variable for variable in dashboard["templating"]["list"]}
    strategy = variables["strategy_datasource"]

    assert strategy["type"] == "datasource"
    assert strategy["query"] == "grafana-postgresql-datasource"
    assert strategy["regex"] == "/^(TimescaleDB|Candidate .*)$/"
    assert strategy["current"] == {
        "selected": True,
        "text": "TimescaleDB",
        "value": "timescaledb",
    }
    assert variables["underlying"]["current"]["value"] == "SPX"
    assert variables["underlying"]["datasource"]["uid"] == "${strategy_datasource}"
    assert variables["trade_id"]["datasource"]["uid"] == "${strategy_datasource}"
    assert "${strategy_datasource:raw}" in variables["trade_id"]["query"]
    assert "metadata->>'paper_fill_model' = 'mark_v1'" in variables["trade_id"]["query"]

    sql_panels = [
        panel
        for panel in _panels(dashboard)
        if any("rawSql" in target for target in panel.get("targets", []))
    ]
    assert sql_panels
    assert all(
        panel["datasource"]
        == {
            "type": "grafana-postgresql-datasource",
            "uid": "${strategy_datasource}",
        }
        for panel in sql_panels
    )
    assert all(
        target["datasource"]["uid"] == "${strategy_datasource}"
        for panel in sql_panels
        for target in panel.get("targets", [])
        if "rawSql" in target
    )


def test_trade_detail_preserves_candidate_cohort_and_accounting_checks() -> None:
    dashboard = _dashboard("butterfly_trade_detail.json")
    review_row = next(
        panel
        for panel in dashboard["panels"]
        if panel["title"] == "Candidate Strategy Review"
    )
    queries = [
        target["rawSql"]
        for panel in _panels({"panels": review_row["panels"]})
        for target in panel.get("targets", [])
        if "rawSql" in target
    ]
    trade_queries = [query for query in queries if "butterfly_trades" in query]

    assert review_row["collapsed"] is True
    assert trade_queries
    assert all(
        "metadata->>'paper_fill_model' = 'mark_v1'" in query
        for query in trade_queries
    )
    assert any("largest_winner_share" in query for query in trade_queries)
    assert any("entry_execution_diagnostics" in query for query in trade_queries)
    assert any("exit_execution_diagnostics" in query for query in trade_queries)
    assert any("settlement_feed_blocked" in query for query in queries)


def test_trade_detail_uses_selected_trade_monitoring_as_candidate_spot_fallback() -> None:
    dashboard = _dashboard("butterfly_trade_detail.json")
    panels = {panel["title"]: panel for panel in _panels(dashboard)}
    spot_queries = [
        target["rawSql"]
        for target in panels["Spot Path vs Butterfly Tent"]["targets"]
    ]
    monitoring_queries = [
        target["rawSql"]
        for title in ("Selected Trade Monitoring Values", "Selected Trade Leg Marks")
        for target in panels[title]["targets"]
    ]

    assert any("monitoring_leg_quotes" in query for query in spot_queries)
    assert any("generate_series" in query for query in spot_queries)
    assert all("trade_id = $trade_id" in query for query in monitoring_queries)


def test_primary_trade_links_pin_the_main_strategy_datasource() -> None:
    for name in ("performance.json", "butterfly_trading.json"):
        serialized = json.dumps(_dashboard(name))
        assert "var-strategy_datasource=timescaledb" in serialized
