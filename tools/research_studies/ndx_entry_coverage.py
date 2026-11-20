"""Offline NDX scan-coverage / ask-eligibility ablation; never submits orders.

Inputs are frozen saved chains and previously audited snapshot metadata. Outputs
are selection opportunities, not fills or an economic backtest.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import logging
import math
from collections import Counter, defaultdict
from pathlib import Path

import structlog

from butterfly_guy.core.config import AppConfig, EntrySettings, StrategySettings
from butterfly_guy.data.schemas import ButterflyCandidate, OptionQuote
from butterfly_guy.strategy.butterfly_builder import ButterflyBuilder, vix_target_center
from butterfly_guy.strategy.butterfly_selector import ButterflySelector
from butterfly_guy.strategy.entry_selection import select_entry_candidate
from butterfly_guy.strategy.width_selection import select_cross_width_candidate

VARIANTS = {"B0": (False, False), "C1": (True, False),
            "E1": (False, True), "CE1": (True, True)}


def select_candidate(
    quotes: list[OptionQuote], spot: float, direction: str, vix: float,
    settings: StrategySettings, tolerance: float, *,
    complete_target: bool = False, require_ask: bool = False,
) -> tuple[ButterflyCandidate | None, int]:
    """Apply existing ranking after the two independently controlled changes."""
    if settings.vix_width_buckets:
        raise ValueError("This frozen NDX comparison requires fixed wing widths")
    bests = []
    eligible = 0
    for width in settings.wing_widths:
        target = vix_target_center(vix, spot, direction, wing_width=width)
        scan_range = settings.spot_range
        if complete_target:
            scan_range = max(scan_range, math.ceil(abs(target - spot) + tolerance))
        cfg = settings.model_copy(update={"wing_widths": [width], "spot_range": scan_range})
        candidates = ButterflyBuilder(cfg).build_candidates(quotes, spot, direction)
        if require_ask:
            cap = settings.max_cost_per_width[width]
            candidates = [c for c in candidates if math.isfinite(c.ask) and c.ask <= cap]
        eligible += sum(abs(c.center_strike - target) <= tolerance for c in candidates)
        best = ButterflySelector(cfg).select_best(candidates, target, tolerance)
        if best:
            bests.append(best)
    return select_cross_width_candidate(bests), eligible


def identity(candidate: ButterflyCandidate | None) -> tuple | None:
    return None if candidate is None else (
        candidate.direction, candidate.wing_width, candidate.center_strike, candidate.cost,
    )


def compare(chains: Path, snapshots: Path, contract_path: Path, out: Path) -> dict:
    contract = json.loads(contract_path.read_text())
    settings_data = contract["settings"]
    settings_data["max_cost_per_width"] = {
        int(k): v for k, v in settings_data["max_cost_per_width"].items()
    }
    settings = StrategySettings(**settings_data)
    tolerance = contract["center_tolerance"]
    # model_construct avoids environment credentials and configuration overrides.
    config = AppConfig.model_construct(strategy=settings, entry=EntrySettings(
        strike_selection_method="VIX", center_tolerance=tolerance,
    ))
    metadata = json.loads(snapshots.read_text())
    grouped = defaultdict(list)
    with chains.open() as stream:
        for row in csv.DictReader(stream):
            timestamp = dt.datetime.fromisoformat(row["snapshot_time"]).isoformat()
            grouped[timestamp].append(row)
    journal = []
    parity_checks = 0
    stress = contract["cost_stress"]
    drag = (stress["slippage_points_per_spread"]
            + stress["commission_dollars_per_contract"]
            * stress["contracts_per_butterfly"] / stress["multiplier"])
    for snapshot in metadata:
        timestamp = snapshot["ts"]
        spot, vix, direction = snapshot["spot"], snapshot["vix"], snapshot["direction"]
        rows = grouped[timestamp]
        # Missing exported legs must not masquerade as a failed strategy filter.
        for width in settings.wing_widths:
            target = vix_target_center(vix, spot, direction, wing_width=width)
            if abs(target - spot) + tolerance + width >= 1000:
                raise ValueError("Frozen +/-1000-point export cannot cover target and wings")
        quotes = [OptionQuote(
            symbol=r["symbol"], underlying="NDX", expiration=dt.date.fromisoformat(r["expiration"]),
            strike=float(r["strike"]), option_type=r["option_type"], bid=float(r["bid"]),
            ask=float(r["ask"]), mark=float(r["mark"]),
        ) for r in rows]
        production = select_entry_candidate(
            quotes=quotes, spot=spot, direction=direction, vix=vix, config=config, asset="NDX",
        ).candidate
        eligibility = {}
        for name, (complete, ask) in VARIANTS.items():
            candidate, count = select_candidate(
                quotes, spot, direction, vix, settings, tolerance,
                complete_target=complete, require_ask=ask,
            )
            eligibility[name] = count
            if name == "B0":
                assert identity(candidate) == identity(production), timestamp
                parity_checks += 1
            cap = settings.max_cost_per_width[candidate.wing_width] if candidate else None
            if candidate and ask:
                assert candidate.ask <= cap
            journal.append({
                "ts": timestamp, "date": snapshot["date"], "variant": name,
                "before_recorded_entry": snapshot["before_entry"], "eligible_candidates": count,
                "selected": candidate is not None,
                "width": candidate.wing_width if candidate else None,
                "center": candidate.center_strike if candidate else None,
                "distance_points": candidate.distance_from_spot if candidate else None,
                "mark_points": candidate.cost if candidate else None,
                "ask_points": candidate.ask if candidate else None,
                "cap_points": cap,
                "ask_within_cap": candidate.ask <= cap if candidate else None,
                "ask_plus_costs_points": round(candidate.ask + drag, 6) if candidate else None,
                "ask_plus_costs_within_cap": candidate.ask + drag <= cap if candidate else None,
            })
        assert eligibility["C1"] >= eligibility["B0"]
        assert eligibility["CE1"] >= eligibility["E1"]
    daily = []
    for day in sorted({r["date"] for r in journal}):
        for variant in VARIANTS:
            rows = [r for r in journal if r["date"] == day and r["variant"] == variant]
            picked = [r for r in rows if r["selected"]]
            daily.append({
                "date": day, "variant": variant, "snapshots": len(rows),
                "selection_opportunities": len(picked),
                "selected_ask_within_cap": sum(r["ask_within_cap"] for r in picked),
                "selected_ask_plus_costs_within_cap": sum(r["ask_plus_costs_within_cap"] for r in picked),
                "pre_recorded_entry_opportunities": sum(r["before_recorded_entry"] for r in picked),
                "widths": dict(Counter(r["width"] for r in picked)),
                "first_opportunity": picked[0] if picked else None,
            })
    totals = {}
    for variant in VARIANTS:
        rows = [r for r in daily if r["variant"] == variant]
        totals[variant] = {"sessions_with_opportunity": sum(r["selection_opportunities"] > 0 for r in rows),
                           **{key: sum(r[key] for r in rows) for key in (
                               "selection_opportunities", "selected_ask_within_cap",
                               "selected_ask_plus_costs_within_cap", "pre_recorded_entry_opportunities")}}
    result = {"decision": "refine", "economic_decision": "insufficient evidence",
              "scope": contract["classification"], "daily": daily, "totals": totals,
              "production_baseline_parity_checks": parity_checks,
              "snapshot_count": len(metadata), "limitations": contract["limitations"]}
    out.mkdir(parents=True, exist_ok=False)
    (out / "summary.json").write_text(json.dumps(result, indent=2))
    (out / "journal.jsonl").write_text("".join(json.dumps(r) + "\n" for r in journal))
    paths = [chains, snapshots, contract_path, Path(__file__)]
    (out / "manifest.json").write_text(json.dumps({
        "created_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "inputs": {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    }, indent=2))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--chains", type=Path, required=True)
    parser.add_argument("--snapshots", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.ERROR))
    result = compare(args.chains, args.snapshots, args.contract, args.out)
    print(json.dumps(result["totals"], indent=2))


if __name__ == "__main__":
    main()
