import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_candidate_fleet_dashboard_exposes_full_review_gate() -> None:
    dashboard = json.loads(
        (ROOT / "infra/grafana/dashboards/spx-candidate-fleet.json").read_text()
    )
    expressions = {
        target["expr"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
    }

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
    } <= expressions


def test_candidate_detail_dashboard_never_mixes_fill_models() -> None:
    dashboard = json.loads(
        (ROOT / "infra/grafana/dashboards/spx-candidate-detail.json").read_text()
    )
    queries = [
        target["rawSql"]
        for panel in dashboard["panels"]
        for target in panel.get("targets", [])
        if "rawSql" in target
    ]
    trade_queries = [query for query in queries if "butterfly_trades" in query]

    assert trade_queries
    assert all(
        "metadata->>'paper_fill_model' = 'mark_v1'" in query
        for query in trade_queries
    )
    assert any("largest_winner_share" in query for query in trade_queries)
    assert any("entry_execution_diagnostics" in query for query in trade_queries)
    assert any("exit_execution_diagnostics" in query for query in trade_queries)
    assert any("settlement_feed_blocked" in query for query in queries)


def test_candidate_detail_dashboard_uses_grafana_postgres_datasources() -> None:
    dashboard = json.loads(
        (ROOT / "infra/grafana/dashboards/spx-candidate-detail.json").read_text()
    )
    candidate_variable = next(
        variable
        for variable in dashboard["templating"]["list"]
        if variable["name"] == "candidate_datasource"
    )

    assert candidate_variable["type"] == "datasource"
    assert candidate_variable["query"] == "grafana-postgresql-datasource"
    assert candidate_variable["refresh"] == 1
    assert candidate_variable["current"] == {
        "selected": True,
        "text": "Candidate vix-center",
        "value": "candidate-vix-center",
    }
    assert all(
        panel["datasource"] == {
            "type": "grafana-postgresql-datasource",
            "uid": "${candidate_datasource}",
        }
        for panel in dashboard["panels"]
    )
