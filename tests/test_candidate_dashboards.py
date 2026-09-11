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


def test_experimental_candidate_fleet_is_absent_from_dashboards() -> None:
    dashboards = {
        name: _dashboard(name)
        for name in (
            "butterfly_trade_detail.json",
            "butterfly_trading.json",
            "performance.json",
        )
    }

    assert "SPX Candidate Comparison" not in {
        panel["title"] for panel in dashboards["performance.json"]["panels"]
    }
    assert "SPX Candidate Fleet Health" not in {
        panel["title"] for panel in dashboards["butterfly_trading.json"]["panels"]
    }
    assert "Candidate Strategy Review" not in {
        panel["title"]
        for panel in dashboards["butterfly_trade_detail.json"]["panels"]
    }
    assert "Trade Accounting Review" in {
        panel["title"]
        for panel in dashboards["butterfly_trade_detail.json"]["panels"]
    }
    assert all(
        not expression.startswith(("candidate_evaluator_", "candidate_feed_"))
        for dashboard in dashboards.values()
        for expression in _expressions(dashboard)
    )


def test_trading_dashboard_selects_one_strategy_source_without_metric_pollution() -> None:
    dashboard = _dashboard("butterfly_trading.json")
    variables = {variable["name"]: variable for variable in dashboard["templating"]["list"]}
    strategy = variables["strategy_datasource"]
    panels = {panel["title"]: panel for panel in _panels(dashboard)}

    assert strategy["label"] == "Source"
    assert strategy["type"] == "datasource"
    assert strategy["query"] == "grafana-postgresql-datasource"
    assert strategy["regex"] == "/^TimescaleDB$/"
    assert strategy["current"] == {
        "selected": True,
        "text": "TimescaleDB",
        "value": "timescaledb",
    }

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

    for title in (
        "Position Value",
        "Peak vs Current Value",
        "Daily Trade Count",
        "Active Trades",
    ):
        assert all("rawSql" in target for target in panels[title]["targets"])

    primary_runtime_titles = (
        "Chain Snapshots (1h rate)",
        "Butterfly Candidates Found",
        "Order Fill Duration (p95)",
        "Schwab API Errors",
        "Rows in Last Snapshot",
        "Snapshot Collect Duration",
    )
    assert all(
        'job=~"butterfly_(spx|ndx|xsp)"' in target["expr"]
        for title in primary_runtime_titles
        for target in panels[title]["targets"]
    )


def test_trading_breakeven_chart_uses_candidate_monitoring_spot_fallback() -> None:
    dashboard = _dashboard("butterfly_trading.json")
    panels = {panel["title"]: panel for panel in _panels(dashboard)}
    queries = [
        target["rawSql"]
        for target in panels["$underlying vs Breakevens"]["targets"]
    ]

    assert "monitoring_leg_quotes" in queries[0]
    assert "monitoring_leg_quotes" in queries[1]
    assert "metadata->>'entry_spot'" in queries[2]
    assert "q.spot_price" in queries[2]
    assert "COALESCE(sp.price, q.spot_price" in queries[3]


def test_trade_detail_defaults_to_primary_spx_and_selects_strategy_datasource() -> None:
    dashboard = _dashboard("butterfly_trade_detail.json")
    variables = {variable["name"]: variable for variable in dashboard["templating"]["list"]}
    strategy = variables["strategy_datasource"]

    assert strategy["type"] == "datasource"
    assert strategy["query"] == "grafana-postgresql-datasource"
    assert strategy["regex"] == "/^TimescaleDB$/"
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


def test_performance_trade_links_pin_the_main_strategy_datasource() -> None:
    serialized = json.dumps(_dashboard("performance.json"))
    assert "var-strategy_datasource=timescaledb" in serialized


def test_trading_trade_links_preserve_the_selected_strategy_datasource() -> None:
    serialized = json.dumps(_dashboard("butterfly_trading.json"))

    assert "var-strategy_datasource=${strategy_datasource:raw}" in serialized
    assert "var-strategy_datasource=timescaledb" not in serialized
