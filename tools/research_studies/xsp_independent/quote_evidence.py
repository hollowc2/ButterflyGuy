"""Read-only held-leg availability audit; no policy relaxation or P&L estimates.

Classifies every MR2 width-four accepted entry's cutoff and each unresolved
lifecycle event. A close-side diagnostic is NOT an executable complex quote.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
RUN = ROOT / "reports/research/xsp-realization-2026-11-11/realization/run-01"
DEFAULT_OUT = ROOT / "reports/research/xsp-fallback-2026-11-12/quote-audit"
PRIORITY = ("absent_row", "nonfinite_price", "negative_price", "crossed_market", "zero_zero",
            "required_side_nonfinite_size", "required_side_zero_bid_no_size",
            "required_side_undersized", "unused_side_nonfinite_size", "unused_side_undersized")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def finite(value) -> bool:
    return bool(pd.notna(value) and np.isfinite(value))


def leg_evidence(row: pd.Series | None, *, role: str) -> dict:
    """Inherited both-sided filter versus transaction-necessary closing size.

    Price sanity is retained for both diagnostics; only unused-side SIZE
    requirements are distinguished. Zero displayed required size is unavailable,
    even if its price is zero. Signed package values are never floored.
    """
    size = 2 if role == "body" else 1
    needed = "ask" if role == "body" else "bid"
    unused = "bid" if role == "body" else "ask"
    base = {"role": role, "required_side": needed, "contracts": size,
            "quote_event_age_known": False}
    if row is None:
        return {**base, "labels": ["absent_row"], "primary_reason": "absent_row",
                "both_sides_valid": False, "close_side_valid": False}
    values = {k: float(row[k]) if finite(row[k]) else None
              for k in ("bid", "ask", "bid_size", "ask_size")}
    labels = []
    bid, ask = values["bid"], values["ask"]
    price_ok = True
    if bid is None or ask is None:
        labels.append("nonfinite_price")
        price_ok = False
    else:
        if bid < 0 or ask < 0:
            labels.append("negative_price")
            price_ok = False
        if ask < bid:
            labels.append("crossed_market")
            price_ok = False
        if bid == ask == 0:
            labels.append("zero_zero")
            price_ok = False
        if ask <= 0:
            price_ok = False
    sizes_valid = {}
    for side, label in ((needed, "required"), (unused, "unused")):
        quoted_size = values[side + "_size"]
        sizes_valid[side] = quoted_size is not None and quoted_size >= size
        if quoted_size is None:
            labels.append(label + "_side_nonfinite_size")
        elif quoted_size < size:
            labels.append(label + "_side_undersized")
            if side == "bid" and bid == 0 and ask is not None and ask > 0 and quoted_size == 0:
                labels.append(label + "_side_zero_bid_no_size")
    close_valid = price_ok and sizes_valid[needed]
    both_valid = close_valid and sizes_valid[unused]
    primary = next((r for r in PRIORITY if r in labels), "valid")
    return {**base, **values, "labels": labels, "primary_reason": primary,
            "both_sides_valid": bool(both_valid), "close_side_valid": bool(close_valid)}


def snapshot_evidence(quotes: pd.DataFrame, entry: dict, when: pd.Timestamp) -> dict:
    snap = quotes[(quotes.timestamp == when) & (quotes.right == entry["right"])]
    legs = []
    for role, strike in (("lower", entry["center"] - entry["width"]),
                         ("body", entry["center"]),
                         ("upper", entry["center"] + entry["width"])):
        found = snap[snap.strike == strike]
        if len(found) > 1:
            raise ValueError("ambiguous raw held-leg quote")
        evidence = leg_evidence(found.iloc[0] if len(found) else None, role=role)
        legs.append({"strike": strike, **evidence})
    both = all(leg["both_sides_valid"] for leg in legs)
    close = all(leg["close_side_valid"] for leg in legs)
    labels = sorted({label for leg in legs for label in leg["labels"]})
    primary = next((r for r in PRIORITY if r in labels), "valid")
    # An unused-side diagnostic requires every transaction-needed side to be
    # valid, not merely one leg with an unused-side failure.
    if close and not both:
        primary = "solely_unused_side_size_filter"
    value = None
    if close:
        value = legs[0]["bid"] - 2 * legs[1]["ask"] + legs[2]["bid"]
    return {"timestamp": when.isoformat(), "right": entry["right"],
            "center": entry["center"], "width": entry["width"], "legs": legs,
            "labels": labels, "primary_reason": primary, "both_sides_valid": both,
            "close_side_valid": close, "solely_unused_side_rejection": close and not both,
            "signed_component_close_value": value,
            "component_value_class": ("unavailable_required_side" if value is None else
                                      "payable_close" if value < 0 else
                                      "zero_close" if value == 0 else "positive_close"),
            "complex_fill_demonstrated": False}


def proxy_evidence(quotes: pd.DataFrame, when: pd.Timestamp) -> dict:
    """Diagnose frozen same-minute parity input, without changing its thresholds."""
    q = quotes[quotes.timestamp == when].copy()
    valid = (np.isfinite(q.bid) & np.isfinite(q.ask) & (q.bid >= 0) & (q.ask > 0)
             & (q.ask >= q.bid) & (q.bid_size >= 1) & (q.ask_size >= 1))
    q = q[valid].copy()
    q["mid"] = (q.bid + q.ask) / 2
    pairs = q[q.right == "CALL"][["strike", "mid"]].merge(
        q[q.right == "PUT"][["strike", "mid"]], on="strike", suffixes=("_c", "_p"))
    pairs["straddle"] = pairs.mid_c + pairs.mid_p
    selected = pairs.sort_values(["straddle", "strike"]).head(5)
    forward = selected.strike + selected.mid_c - selected.mid_p
    dispersion = float(forward.max() - forward.min()) if len(forward) else None
    reason = ("timestamp_absent" if not len(quotes[quotes.timestamp == when]) else
              "insufficient_usable_call_put_pairs" if len(selected) < 3 else
              "pair_dispersion_above_0.50" if dispersion > .50 else "valid")
    return {"usable_pairs": len(pairs), "selected_pairs": len(selected),
            "dispersion": dispersion, "primary_reason": reason,
            "proxy_valid": reason == "valid", "source_event_ages_known": False}


def event_times(row: dict) -> list[pd.Timestamp]:
    """All missing minute snapshots in the FIRST recorded unresolved event."""
    status, cutoff = row["status"], pd.Timestamp(row["cutoff"])
    if status == "excluded_fallback_exit_quote":
        return [cutoff]
    if status == "excluded_trigger_exit_quote":
        trigger = pd.Timestamp(row["trigger_time"])
        return [t for t in pd.date_range(trigger + pd.Timedelta(minutes=1),
                                         trigger + pd.Timedelta(minutes=2), freq="min") if t <= cutoff]
    if status == "excluded_center_anchor_missing":
        return [pd.Timestamp(row["entry_time"])]
    if "gap_time" in row and "gap_seconds" in row:
        end = pd.Timestamp(row["gap_time"])
        previous = end - pd.Timedelta(seconds=row["gap_seconds"])
        # Prefix gap_time is the first recovered usable observation, not part of
        # the missing interval. Terminal gap_time is the cutoff itself.
        last = end if "terminal" in status else end - pd.Timedelta(minutes=1)
        return list(pd.date_range(previous + pd.Timedelta(minutes=1), last, freq="min"))
    raise ValueError(f"unknown unresolved event {status}")


def counts(snapshots: list[dict]) -> dict:
    return {"snapshots": len(snapshots),
            "primary_reasons": dict(Counter(s["primary_reason"] for s in snapshots)),
            "multi_label_snapshots": dict(Counter(label for s in snapshots for label in set(s["labels"]))),
            "both_sides_valid": sum(s["both_sides_valid"] for s in snapshots),
            "close_side_valid": sum(s["close_side_valid"] for s in snapshots),
            "solely_unused_side_rejection": sum(s["solely_unused_side_rejection"] for s in snapshots),
            "component_value_classes": dict(Counter(s["component_value_class"] for s in snapshots)),
            "per_leg": {role: {"primary_reasons": dict(Counter(
                leg["primary_reason"] for s in snapshots for leg in s["legs"] if leg["role"] == role)),
                "multi_labels": dict(Counter(label for s in snapshots for leg in s["legs"]
                                             if leg["role"] == role for label in set(leg["labels"])))}
                for role in ("lower", "body", "upper")}}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, default=RUN)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    entries = [json.loads(line) for line in (args.run / "entries.jsonl").read_text().splitlines()]
    journal = [json.loads(line) for line in (args.run / "journal.jsonl").read_text().splitlines()]
    entries = [r for r in entries if r["family"] == "MR2" and r["width"] == 4 and r["status"] == "accepted"]
    unresolved = [r for r in journal if r["family"] == "MR2" and r["width"] == 4
                  and r["policy"] in ("center_cross", "net_profit_25pct") and r["status"] != "completed"]
    assert len(entries) == 105 and len({r["date"] for r in entries}) == 105
    assert len(unresolved) == 151
    snapshots, cutoffs, events, inputs = [], [], [], []
    for n, entry in enumerate(sorted(entries, key=lambda r: r["date"])):
        day = entry["date"]
        path = ROOT / f"data/thetadata/xsp_0dte/quote_1m/2026/{day}.parquet"
        quotes = pd.read_parquet(path)
        if (set(quotes.symbol) != {"XSP"} or set(pd.to_datetime(quotes.expiration).dt.strftime("%Y-%m-%d")) != {day}
                or quotes.duplicated(["timestamp", "strike", "right"]).any()):
            raise ValueError("raw quote identity/uniqueness failure")
        inputs.append({"date": day, "path": str(path.relative_to(ROOT)), "sha256": sha(path)})
        cutoff = snapshot_evidence(quotes, entry, pd.Timestamp(entry["cutoff"]))
        cutoff.update(date=day, context="all_accepted_cutoffs", snapshot_id=f"{day}/cutoff")
        cutoffs.append(cutoff)
        snapshots.append(cutoff)
        for row in (r for r in unresolved if r["date"] == day):
            times = event_times(row)
            event_snaps = []
            for i, when in enumerate(times):
                snap = snapshot_evidence(quotes, entry, when)
                snap.update(date=day, context="unresolved_event", policy=row["policy"],
                            original_status=row["status"], snapshot_id=f"{day}/{row['policy']}/{i}")
                if "center" in row["status"]:
                    snap["proxy_input"] = proxy_evidence(quotes, when)
                event_snaps.append(snap)
                snapshots.append(snap)
            events.append({"date": day, "policy": row["policy"], "original_status": row["status"],
                           "entry_time": row["entry_time"], "cutoff": row["cutoff"],
                           "trigger_time": row.get("trigger_time"), "gap_time": row.get("gap_time"),
                           "gap_seconds": row.get("gap_seconds"), "snapshot_count": len(event_snaps),
                           "first_audited_snapshot": times[0].isoformat() if times else None,
                           "snapshot_ids": [s["snapshot_id"] for s in event_snaps],
                           "first_snapshot_primary": event_snaps[0]["primary_reason"] if event_snaps else "no_candidate_timestamp",
                           "any_inherited_both_side_valid": any(s["both_sides_valid"] for s in event_snaps),
                           "any_required_close_side_valid": any(s["close_side_valid"] for s in event_snaps),
                           "all_snapshots_required_close_side_valid": all(s["close_side_valid"] for s in event_snaps),
                           "any_solely_unused_side_rejection": any(s["solely_unused_side_rejection"] for s in event_snaps),
                           "snapshot_primary_counts": counts(event_snaps)["primary_reasons"],
                           "proxy_primary_counts": dict(Counter(s["proxy_input"]["primary_reason"]
                                                                for s in event_snaps if "proxy_input" in s))})
        if n % 20 == 0:
            print(f"audited {n + 1}/{len(entries)} sessions", flush=True)
    grouped = {}
    for policy in ("center_cross", "net_profit_25pct"):
        policy_events = [e for e in events if e["policy"] == policy]
        grouped[policy] = {"unresolved_events": len(policy_events),
                           "status_counts": dict(Counter(e["original_status"] for e in policy_events)),
                           "first_snapshot_primary_counts": dict(Counter(e["first_snapshot_primary"] for e in policy_events)),
                           "events_with_any_required_close_side_valid": sum(e["any_required_close_side_valid"] for e in policy_events),
                           "events_with_all_required_close_side_valid": sum(e["all_snapshots_required_close_side_valid"] for e in policy_events),
                           "events_with_any_inherited_valid": sum(e["any_inherited_both_side_valid"] for e in policy_events),
                           "events_with_any_unused_side_only_rejection": sum(e["any_solely_unused_side_rejection"] for e in policy_events),
                           "by_original_status": {status: {"events": len(rs := [e for e in policy_events if e["original_status"] == status]),
                                                           "first_snapshot_primary_counts": dict(Counter(e["first_snapshot_primary"] for e in rs)),
                                                           "any_required_close_valid": sum(e["any_required_close_side_valid"] for e in rs),
                                                           "any_inherited_valid": sum(e["any_inherited_both_side_valid"] for e in rs),
                                                           "any_unused_side_only_rejection": sum(e["any_solely_unused_side_rejection"] for e in rs),
                                                           "proxy_primary_counts": dict(sum((Counter(e["proxy_primary_counts"]) for e in rs), Counter()))}
                                                  for status in sorted({e["original_status"] for e in policy_events})}}
    summary = {"scope": "All105 accepted MR2width4 entries;151 unresolved lifecycle events; no P&L inspection or strategy change",
               "cutoffs": counts(cutoffs), "unresolved_policies": grouped,
               "raw_snapshot_records": len(snapshots),
               "interpretation": {"side_specific_quotes": "Diagnostic only; necessary displayed closing sizes are not proof of a complex fill",
                                  "zero_bid": "Zero bid plus positive ask and zero bid size means absent displayed buyer on that side, not evidence of a free executable exit",
                                  "negative_component_value": "Payable modeled close, not impossible/unsellable; signed value retained",
                                  "unused_side": "Attribution of stricter inherited both-side size filter; no filter is changed",
                                  "gaps": "Event gaps refer to frozen required input paths; held-leg validity does not establish a valid underlying proxy",
                                  "ages": "Raw NBBO snapshots lack individual leg last-update age; proxy source-event ages also unknown"},
               "primary_reason_priority": PRIORITY,
               "created_at_utc": pd.Timestamp.now(tz="UTC").isoformat()}
    for filename, rows in (("events.jsonl", events), ("raw-snapshots.jsonl", snapshots)):
        with (args.out / filename).open("x") as f:
            for row in rows:
                f.write(json.dumps(row, allow_nan=False) + "\n")
    (args.out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    manifest = {"inputs": inputs, "study_inputs": {str(args.run / name): sha(args.run / name)
                for name in ("entries.jsonl", "journal.jsonl")},
                "source_sha256": sha(Path(__file__)), "pandas": pd.__version__, "numpy": np.__version__,
                "outputs": {name: sha(args.out / name) for name in ("events.jsonl", "raw-snapshots.jsonl", "summary.json")}}
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
