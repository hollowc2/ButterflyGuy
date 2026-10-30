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


def test_panels_do_not_overlap() -> None:
    dashboard = json.loads(
        Path("infra/grafana/dashboards/performance.json").read_text()
    )
    occupied: dict[tuple[int, int], str] = {}
    for panel in dashboard["panels"]:
        grid = panel["gridPos"]
        assert grid["x"] + grid["w"] <= 24, panel["title"]
        for x in range(grid["x"], grid["x"] + grid["w"]):
            for y in range(grid["y"], grid["y"] + grid["h"]):
                assert (x, y) not in occupied, (panel["title"], occupied[(x, y)])
                occupied[(x, y)] = panel["title"]


def test_today_panels_use_the_pacific_date_not_utc_current_date() -> None:
    text = Path("infra/grafana/dashboards/performance.json").read_text()

    # The database runs in UTC, so CURRENT_DATE rolls to tomorrow at 17:00 PT.
    assert "CURRENT_DATE" not in text
    assert "(NOW() AT TIME ZONE 'America/Los_Angeles')::date" in text
