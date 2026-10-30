"""Refresh the Trading chart's exit level from the bots' profit-management configs.

For a deployed dashboard, supply the configs actually used by each running bot.
They can differ from configs/: on Helios, `docker inspect butterfly_xsp_app` shows XSP
mounting a release snapshot (e.g. .releases/<release>/config_xsp.yaml). The panel
filters on the hidden $session_date variable, never the UTC database's CURRENT_DATE.
This edits dashboard JSON only; it does not change trading settings or services.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from butterfly_guy.core.config import ProfitManagementSettings

ROOT = Path(__file__).resolve().parents[1]


def regime_annotation(policies: dict[str, ProfitManagementSettings]) -> dict:
    rows = ",\n    ".join(
        f"('{asset}', {regime.start_minutes_after_open}, "
        f"'{name.replace('_', ' ').capitalize()}', {regime.drawdown_threshold * 100:g})"
        for asset, policy in policies.items()
        if asset in {"SPX", "NDX", "XSP"}
        for name, regime in policy.regimes.items()
    )
    sql = """WITH regimes(underlying, start_minutes, regime_name, drawdown_pct) AS (
  VALUES
    """ + rows + """
), boundaries AS (
  SELECT ('$session_date'::date + TIME '09:30'
    + start_minutes * INTERVAL '1 minute') AT TIME ZONE 'America/New_York' AS time,
    regime_name || ' - ' || drawdown_pct::text || '% drawdown' AS text,
    'drawdown-regime' AS tags
  FROM regimes WHERE underlying = '$underlying'
)
SELECT time, text, tags FROM boundaries WHERE $__timeFilter(time) ORDER BY time"""
    return {
        "name": "Drawdown regimes",
        "datasource": {"type": "grafana-postgresql-datasource", "uid": "${strategy_datasource}"},
        "enable": True,
        "hide": False,
        "iconColor": "#B877D9",
        "filter": {"exclude": False, "ids": [3]},
        "target": {"refId": "DrawdownRegimes", "rawQuery": True,
                   "rawSql": sql, "format": "table"},
    }


def exit_trigger_sql(policies: dict[str, ProfitManagementSettings]) -> str:
    fields = {"strategy", "regimes", "max_loss_from_cost", "use_absolute_loss_stop",
              "profitprotector"}
    rows = ",\n    ".join(
        "('" + asset + "', '"
        + json.dumps(policy.model_dump(include=fields)).replace("'", "''") + "'::jsonb)"
        for asset, policy in policies.items()
        if asset in {"SPX", "NDX", "XSP"}
    )
    return """WITH policies(underlying, settings) AS (
  VALUES
    """ + rows + """
), observations AS (
  SELECT q.ts AS time, t.id AS trade_id, t.entry_price, t.entry_time, t.quantity,
    MAX(q.peak_value) AS peak, MAX(q.fly_mark) AS current
  FROM monitoring_leg_quotes q
  JOIN butterfly_trades t ON t.id = q.trade_id AND t.underlying = q.underlying
  WHERE q.underlying = '$underlying' AND t.trade_date = '$session_date'::date
    AND t.status != 'CANCELLED' AND q.ts >= '$session_date'::date
  GROUP BY q.ts, t.id, t.entry_price, t.entry_time, t.quantity
), history AS (
  SELECT *, BOOL_OR(current >= entry_price) OVER (
    PARTITION BY trade_id ORDER BY time ROWS UNBOUNDED PRECEDING
  ) OR peak > entry_price AS ever_in_profit,
    GREATEST(0, EXTRACT(EPOCH FROM (
      (time AT TIME ZONE 'America/New_York')::time - TIME '09:30'
    )) / 60) AS minutes_after_open,
    EXTRACT(EPOCH FROM (time - entry_time)) / 60 AS age_minutes
  FROM observations
), regimes AS (
  SELECT h.*, p.settings, p.settings->'regimes'->(CASE
    WHEN minutes_after_open < (p.settings #>> '{regimes,morning,end_minutes_after_open}')::float
      THEN 'morning'
    WHEN minutes_after_open < (p.settings #>> '{regimes,late_morning,end_minutes_after_open}')::float
      THEN 'late_morning'
    ELSE 'afternoon' END) AS regime
  FROM history h CROSS JOIN policies p WHERE p.underlying = '$underlying'
), levels AS (
  SELECT *, ever_in_profit
    AND peak >= entry_price * (regime->>'min_peak_profit_ratio')::float
    AND age_minutes >= (regime->>'min_hold_minutes')::float AS armed,
    peak * (1 - CASE WHEN settings->>'strategy' = 'profitprotector'
      AND entry_price > 0
      AND peak >= entry_price * (settings #>> '{profitprotector,large_peak_profit_ratio}')::float
      THEN LEAST((regime->>'drawdown_threshold')::float,
        (settings #>> '{profitprotector,large_peak_drawdown_threshold}')::float)
      ELSE (regime->>'drawdown_threshold')::float END) AS trailing_level
  FROM regimes
)
SELECT time, (peak * 100 * quantity)::float AS "Peak",
  (current * 100 * quantity)::float AS "Current",
  (GREATEST(
    CASE WHEN (settings->>'use_absolute_loss_stop')::boolean AND entry_price > 0
      THEN entry_price * (1 - (settings->>'max_loss_from_cost')::float) END,
    CASE WHEN armed THEN trailing_level END,
    CASE WHEN armed AND settings->>'strategy' = 'profitprotector' AND entry_price > 0
      AND peak >= entry_price + (settings #>> '{profitprotector,breakeven_activation_profit}')::float
      THEN entry_price + (settings #>> '{profitprotector,breakeven_floor_profit}')::float END,
    CASE WHEN armed AND settings->>'strategy' = 'profitprotector' AND entry_price > 0
      AND peak >= entry_price + (settings #>> '{profitprotector,profit_lock_activation_profit}')::float
      THEN entry_price + (settings #>> '{profitprotector,profit_lock_floor_profit}')::float END
  ) * 100 * quantity)::float AS "Exit trigger"
FROM levels WHERE $__timeFilter(time) ORDER BY time"""


def update_dashboard(path: Path, policies: dict[str, ProfitManagementSettings]) -> None:
    text = path.read_text()
    dashboard = json.loads(text)
    panel = next(panel for panel in dashboard["panels"] if panel["id"] == 3)
    panel["targets"][0]["rawSql"] = exit_trigger_sql(policies)
    panel["description"] = (
        "Exit trigger is the armed price-based exit level using the configured profit policy "
        "and Eastern time regime: peak × (1 − drawdown), including enabled profit floors "
        "and absolute loss stops. Values are total position dollars (×100×quantity). "
        "No line means no price-based exit is armed. Confirmation polls and quote-quality "
        "gates still apply; this is a trigger, not a guaranteed fill. Time-based exits and "
        "cash settlement are separate. Uses a snapshot of current bot settings."
    )
    panel["fieldConfig"]["overrides"] = [
        {"matcher": {"id": "byName", "options": name}, "properties": properties}
        for name, properties in (
            ("Peak", [{"id": "color", "value": {"mode": "fixed", "fixedColor": "green"}}]),
            ("Current", [{"id": "color", "value": {"mode": "fixed", "fixedColor": "yellow"}}]),
            ("Exit trigger", [
                {"id": "color", "value": {"mode": "fixed", "fixedColor": "red"}},
                {"id": "custom.lineStyle", "value": {"fill": "dash", "dash": [8, 6]}},
                {"id": "custom.lineWidth", "value": 2},
                {"id": "custom.lineInterpolation", "value": "stepAfter"},
                {"id": "custom.spanNulls", "value": False},
            ]),
        )
    ]
    # Preserve every other panel and the file's existing formatting.
    start = text.rfind("{", 0, text.index('"id": 3,'))
    _, length = json.JSONDecoder().raw_decode(text[start:])
    replacement = json.dumps(panel, indent=2).replace("\n", "\n    ")
    text = text[:start] + replacement + text[start + length:]
    annotations = dashboard.get("annotations", {"list": []})
    annotations["list"] = [a for a in annotations["list"] if a["name"] != "Drawdown regimes"]
    annotations["list"].append(regime_annotation(policies))
    replacement = json.dumps(annotations, indent=2).replace("\n", "\n  ")
    if "annotations" in dashboard:
        start = text.index('  "annotations": ') + len('  "annotations": ')
        _, length = json.JSONDecoder().raw_decode(text[start:])
        text = text[:start] + replacement + text[start + length:]
    else:
        text = text.replace('  "panels": [', '  "annotations": ' + replacement
                            + ',\n  "panels": [', 1)
    path.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dashboard", type=Path,
                        default=ROOT / "infra/grafana/dashboards/butterfly_trading.json")
    for asset, name in (("spx", "config.yaml"), ("ndx", "config_ndx.yaml"),
                        ("xsp", "config_xsp.yaml")):
        parser.add_argument(f"--{asset}-config", type=Path, default=ROOT / "configs" / name)
    args = parser.parse_args()
    policies = {
        asset.upper(): ProfitManagementSettings.model_validate(
            yaml.safe_load(getattr(args, f"{asset}_config").read_text())["profit_management"]
        )
        for asset in ("spx", "ndx", "xsp")
    }
    update_dashboard(args.dashboard, policies)


if __name__ == "__main__":
    main()
