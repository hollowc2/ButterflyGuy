"""Tests for Butterfly performance dashboard cohort safety."""

import json
from pathlib import Path


def test_closed_trade_queries_filter_paper_fill_model() -> None:
    dashboard = json.loads(
        Path("infra/grafana/dashboards/performance.json").read_text()
    )
    variables = {item["name"]: item for item in dashboard["templating"]["list"]}
    queries = [
        target["rawSql"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
        if "butterfly_trades" in target.get("rawSql", "")
        and "status='CLOSED'" in target["rawSql"]
    ]

    assert variables["fill_model"]["current"]["value"] == "mark_v1"
    assert queries
    assert all("metadata->>'paper_fill_model'" in query for query in queries)
