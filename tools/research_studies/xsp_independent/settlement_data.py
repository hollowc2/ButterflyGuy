"""Native Cboe-published 2026 XSP settlement, never an intraday quote proxy.

SPX close divided by ten is a diagnostic only. Cboe's proposed three-decimal
change was postponed by C2024070501; no implementation date is assumed here.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

SPEC_URL = "https://www.cboe.com/tradable_products/sp_500/mini_spx_options/specifications"
PRECISION_URL = ("https://cdn.cboe.com/resources/product_update/2024/"
                 "05162024_Update-Cboe-Global-Indices-Change-in-Index-Price-Format-on-Cboe-Mini-SPX-Index.pdf")
POSTPONEMENT_URL = ("https://cdn.cboe.com/resources/product_update/2024/"
                    "Schedule-Update-Cboe-Global-Indices-Change-in-Index-Price-Format-on-Cboe-Mini-SPX-Index.pdf")
SOURCE_TYPE = "cboe_native_xsp_published_settlement"
ROUNDING_RULE = "As published by Cboe; no derivation or re-rounding"
ENDPOINTS = {"weekly": ("cboe-weeklys-2026.json", "https://www.cboe.com/index_settlement_values/get_sv_data/W/2026/"),
             "standard": ("cboe-monthly-2026.json", "https://www.cboe.com/index_settlement_values/get_sv_data/S/2026/"),
             "eom": ("cboe-eom-2026.json", "https://www.cboe.com/index_settlement_values/get_sv_data/M/2026/")}
ROOT = Path(__file__).resolve().parents[3]
RECEIPT = ROOT / "reports/thetadata_completion/2026-10-01/thetadata-daily/9f7d847ae966.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scaled_close_diagnostic(source_close: str | Decimal) -> Decimal:
    """Exact mathematical scaling only; NOT an authoritative settlement input."""
    close = Decimal(str(source_close))
    if not close.is_finite() or close <= 0:
        raise ValueError("invalid official closing observation")
    if close != close.quantize(Decimal("0.01")):
        raise ValueError("SPX source precision differs from verified two-decimal close")
    return (close / Decimal(10)).quantize(Decimal("0.001"))


def tent_value(center: float, width: float, settlement: float) -> float:
    """Long 1/-2/1 symmetric call OR put butterfly intrinsic, option points."""
    k, w, s = (Decimal(str(x)) for x in (center, width, settlement))
    if not all(x.is_finite() for x in (k, w, s)) or w <= 0 or s <= 0:
        raise ValueError("invalid butterfly or settlement")
    return float(max(Decimal(0), w - abs(s - k)))


def cash_settlement_pnl(entry: float, center: float, width: float, settlement: float,
                        *, entry_stress: float = 0.0, opening_fee: float = 2.60) -> float:
    """One fly, USD. Opening assumptions only; no exit fill/closing fee/stress.

    opening_fee is a research assumption, not a verified broker exercise tariff.
    """
    e, stress, fee = (Decimal(str(x)) for x in (entry, entry_stress, opening_fee))
    if not all(x.is_finite() for x in (e, stress, fee)) or e <= 0 or stress < 0 or fee < 0:
        raise ValueError("invalid entry accounting")
    payoff = Decimal(str(tent_value(center, width, settlement)))
    return float((payoff - e - stress) * 100 - fee)


def official_closes(path: Path) -> dict[str, str]:
    by_date = {}
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != ["DATE", "SPX"]:
            raise ValueError("unexpected official Cboe SPX CSV schema")
        for row in reader:
            day = dt.datetime.strptime(row["DATE"], "%m/%d/%Y").date().isoformat()
            if day in by_date:
                raise ValueError("duplicate official source date")
            by_date[day] = row["SPX"]
    return by_date


def native_rows(raw_dir: Path, dates: list[str], closes: dict[str, str]) -> list[dict]:
    """Exact instrument filter, agreement on overlapping sources, missing stays missing."""
    if len(set(dates)) != len(dates):
        raise ValueError("duplicate cohort date")
    found: dict[str, tuple[Decimal, list[str], list[str]]] = {}
    for category, (filename, url) in ENDPOINTS.items():
        source_rows = json.loads((raw_dir / filename).read_text(), parse_float=Decimal)["data"]
        local_dates = set()
        for source in source_rows:
            if source.get("trading_symbol") != "XSP" or source.get("settlement_symbol") != "XSP":
                continue
            date = source["expiration_date"]
            if date not in dates:
                continue
            if date in local_dates:
                raise ValueError("duplicate date/instrument within native source")
            local_dates.add(date)
            value = Decimal(str(source["settlement_value"]))
            if not value.is_finite() or value <= 0:
                raise ValueError("invalid native published settlement")
            if date in found:
                old, categories, urls = found[date]
                if value != old:
                    raise ValueError("conflicting native published settlements")
                categories.append(category)
                urls.append(url)
            else:
                found[date] = (value, [category], [url])
    rows = []
    for date in sorted(dates):
        close = closes.get(date)
        exact = scaled_close_diagnostic(close) if close else None
        value, categories, urls = found.get(date, (None, [], []))
        rows.append({"date": date, "settlement": str(value) if value is not None else "",
                     "source_type": SOURCE_TYPE if value is not None else "missing_native_settlement",
                     "source_close": close or "", "rounding_rule": ROUNDING_RULE,
                     "source_url": "|".join(urls), "source_categories": "|".join(categories),
                     "scaled_close_exact_diagnostic": str(exact) if exact is not None else "",
                     "scaled_close_half_up_2dp_diagnostic": str(exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) if exact is not None else "",
                     "published_minus_scaled_diagnostic": str(value - exact) if value is not None and exact is not None else ""})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True,
                        help="Directory of preserved public source document downloads")
    args = parser.parse_args()
    # Raw document downloads may already live below this directory, but outputs
    # are exclusive-create. Never overwrite either old derived or raw evidence.
    args.out.mkdir(parents=True, exist_ok=True)
    if (args.out / "native-manifest.json").exists() or (args.out / "settlements-native.csv").exists():
        raise FileExistsError("use a new settlement evidence output")
    receipt = json.loads(RECEIPT.read_text())
    source = Path(receipt["SPX"]["path"])
    if sha256(source) != receipt["SPX"]["sha256"]:
        raise ValueError("official source snapshot does not match preserved provider receipt")
    dates = [p.stem for p in sorted((ROOT / "data/thetadata/xsp_0dte/quote_1m/2026").glob("*.parquet"))
             if "2026-01-02" <= p.stem <= "2026-09-28"]
    rows = native_rows(args.documents, dates, official_closes(source))
    docs = {
        "cboe-xsp-specification.html": SPEC_URL,
        "cboe-xsp-precision-20240516.pdf": PRECISION_URL,
        "cboe-xsp-precision-postponed-20240705.pdf": POSTPONEMENT_URL,
        "cboe-page-app.js": "https://www.cboe.com/_cache/js/e4a8925feb4a99b7687a4ef2c06fe299.js",
        "cboe-weeklys-settlement.html": "https://www.cboe.com/index_settlement_values/weeklys_settlement_values/"}
    docs.update({filename: url for filename, url in ENDPOINTS.values()})
    documents = {}
    for name, url in docs.items():
        p = args.documents / name
        if not p.is_file() or not p.stat().st_size:
            raise ValueError(f"missing preserved contract evidence: {p}")
        documents[name] = {"source_url": url, "sha256": sha256(p), "path": str(p),
                           "retrieved_at_utc": dt.datetime.fromtimestamp(p.stat().st_mtime, dt.UTC).isoformat()}
    with (args.out / "settlements-native.csv").open("x", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    manifest = {
        "created_at_utc": dt.datetime.now(dt.UTC).isoformat(),
        "scope": {"instrument": "XSP", "series": "standard, weekly and EOM PM-settled XSP; not XSPAM/XSR/SET",
                  "start_inclusive": "2026-01-02", "end_inclusive": "2026-09-28",
                  "cohort": "dates with local actual XSP0DTE option partitions", "cohort_dates": dates},
        "rows": len(rows), "available": sum(bool(r["settlement"]) for r in rows),
        "missing_dates": [r["date"] for r in rows if not r["settlement"]],
        "source_type": SOURCE_TYPE, "diagnostic_spx_close_source": receipt["SPX"],
        "original_receipt_path": str(RECEIPT), "original_receipt_sha256": sha256(RECEIPT),
        "contract_documents": documents,
        "selection": "Native published JSON rows with trading_symbol=XSP AND settlement_symbol=XSP; never XSPBW/XSPBX/NANOS/XSR/SET",
        "precision": {"rule": ROUNDING_RULE,
                      "authority": "Native Cboe published values; proposed three-decimal change C2024051602 postponed by C2024070501 to date yet to be determined",
                      "three_decimal_implementation_claimed": False,
                      "notice_effective_date_visually_verified": "C2024070501 strikes July22,2024 and replaces with date yet to be determined"},
        "native_daily_xsp_observation": True,
        "availability": "Terminal exercise-settlement input only; same-session closing value cannot enter a prior intraday signal",
        "accounting": "Intrinsic payoff*100 minus entry debit and opening fee; no closing order, closing fee, or closing slippage modeled",
        "limitations": ["Current public settlement-history snapshot; historical publication/correction timestamps unknown",
                        "SPX close scaling/rounding columns are crosscheck diagnostics, never substituted for native settlement",
                        "No broker exercise/assignment reconciliation or separately verified broker exercise tariff",
                        "No final-minute quotes, parity proxy, or intraday SPX scaling substituted for settlement"],
        "files": {"settlements-native.csv": sha256(args.out / "settlements-native.csv")},
        "superseded_artifacts": "settlements.csv and manifest.json from earlier unsupported three-decimal derivation; preserved with SUPERSEDED.json and never consumed here",
        "source_sha256": sha256(Path(__file__)),
    }
    with (args.out / "native-manifest.json").open("x") as handle:
        json.dump(manifest, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"rows": manifest["rows"], "available": manifest["available"],
                      "missing_dates": manifest["missing_dates"], "out": str(args.out)}))


if __name__ == "__main__":
    main()
