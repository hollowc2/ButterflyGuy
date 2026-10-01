"""Offline ThetaData partitions. Raw files are read-only; imports have immutable identity."""
from __future__ import annotations

import datetime as dt
import fcntl
import json
import os
import shutil
import tempfile
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from butterfly_guy.research.dataset import (
    Dataset,
    Manifest,
    chain_to_table,
    default_cache_root,
    session_dir,
    sha256_file,
    write_table,
)
from butterfly_guy.research.event_calendar import EventCalendar
from butterfly_guy.research.history import (
    INDEX_MAX_AGE_S,
    VIX_BY,
    GuardedSource,
    HistoryPlan,
    QualityNotPassedError,
    _table,
    build_session,
    daily_range,
    has_print,
    index_on_grid,
    minute_grid,
    quality_passed,
    session_close,
)
from butterfly_guy.research.holdout import Unseal, guard, in_holdout
from butterfly_guy.research.market import et_us
from butterfly_guy.research.thetadata import (
    FILE_TZ,
    MINUTE_FILE_ORIGIN,
    load_minute_file,
    parse_cboe,
)

SETS = {"spxw_0dte": ("SPXW", "SPX", 0, 5.0),
        "spxw_1dte": ("SPXW", "SPX", 1, 5.0),
        "ndxp_0dte": ("NDXP", "NDX", 0, 5.0),
        "xsp_0dte": ("XSP", "XSP", 0, 0.5)}
KINDS = ("quote_1m", "ohlc_1m", "open_interest", "eod")
MAPPING_VERSION = "thetadata-local-1"


class LocalThetaDataSource:
    """Direct Python access uses the same date guard as the CLI, before resolving paths.

    Minute quotes describe state at grid time, not time of last NBBO change. Their
    observation age is bounded to 120 seconds; last-update age is unknown (NaN).
    Optional OI/trade/EOD inputs are deliberately unused by the observed-price profile.
    """

    def __init__(self, archive: Path, set_name: str, dataset: str, support: Dataset,
                 *, minutes: dict[str, Path] | None = None, unseal: Unseal | None = None,
                 daily_cache: Path | None = None):
        if set_name not in SETS:
            raise ValueError(f"unsupported archive set {set_name}")
        self.archive, self.set_name, self.dataset = Path(archive), set_name, dataset
        self.root_symbol, self.underlying, self.dte, self.strike_grid = SETS[set_name]
        self.support, self.minutes, self.unseal = support, minutes or {}, unseal
        self._minutes = {}
        self._stale = {}
        self._minute_hashes = {}
        self.raw_refs: dict[str, dict] = {}
        self.identities: dict[dt.date, dt.date] = {}
        self._catalog = None
        self.daily_cache = daily_cache
        self._daily_records = None
        self._daily = {}

    def _guard(self, start: dt.date, end: dt.date):
        guard(start, end, what="local ThetaData read", dataset=self.dataset, unseal=self.unseal)

    def path(self, d: dt.date, kind: str = "quote_1m") -> Path:
        self._guard(d, d)
        if kind not in KINDS:
            raise ValueError(f"unsupported kind {kind}")
        if self.dte:
            if self._catalog is None:
                catalog = self.archive / "catalog.jsonl"
                self._catalog = {}
                if catalog.is_file():
                    for line in catalog.read_text().splitlines():
                        rec = json.loads(line)
                        if rec["set"] == self.set_name:
                            self._catalog[rec["date"]] = rec["expiration"]
            if str(d) in self._catalog:
                exp = dt.date.fromisoformat(self._catalog[str(d)])
                self._guard(exp, exp)
        path = self.archive / self.set_name / kind / str(d.year) / f"{d}.parquet"
        # A symlink must not disguise a protected partition or escape the archive.
        resolved = path.resolve()
        if not resolved.is_relative_to(self.archive.resolve()) or resolved.name != path.name:
            raise ValueError("archive path escapes its declared date/root")
        return path

    def sessions(self, start: dt.date, end: dt.date) -> list[dt.date]:
        self._guard(start, end)
        return [d for d in pd.date_range(start, end).date if self.path(d).is_file()]

    def cost_estimate(self, start: dt.date, end: dt.date):
        self._guard(start, end)
        return None

    def _minute(self, symbol: str):
        if symbol not in self._minutes:
            self._minute_hashes[symbol] = sha256_file(self.minutes[symbol])
            self._minutes[symbol], self._stale[symbol] = load_minute_file(self.minutes[symbol])
        return self._minutes[symbol]

    def _cached_daily(self, index: str) -> pd.DataFrame:
        if self._daily_records is None:
            self._daily_records = json.loads(Path(self.daily_cache).read_text())
        record = self._daily_records[index]
        path = Path(record["path"])
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"changed cached {index} daily input")
        if index not in self._daily:
            self._daily[index] = parse_cboe(path.read_bytes(), index)
        return self._daily[index]

    def describe(self) -> dict:
        inputs = {}
        for rel in ("spot_ticks.parquet", "daily_bars.parquet"):
            if sha256_file(self.support.root / rel) != self.support.manifest.files[rel]["sha256"]:
                raise ValueError("changed supporting input; use a new dataset identity")
        for s, p in self.minutes.items():
            m = self._minute(s)
            if sha256_file(p) != self._minute_hashes[s]:
                raise ValueError("minute input changed; create a new source/dataset identity")
            inputs[s] = {"path": str(p), "sha256": sha256_file(p), "tz": FILE_TZ,
                         "stamp": "bar end", "origin": MINUTE_FILE_ORIGIN,
                         "stale_days_excluded": self._stale[s],
                         "usable_last_date": str(m.date.max())}
        if self.daily_cache:
            for symbol in ("SPX", "VIX"):
                self._cached_daily(symbol)
        return {"vendor": "ThetaData", "access": "local Parquet; offline",
                "archive": str(self.archive.resolve()), "set": self.set_name,
                "option_root": self.root_symbol, "underlying": self.underlying,
                "mapping_version": MAPPING_VERSION, "index_files": inputs,
                "daily_cache": self._daily_records,
                "strike_grid": self.strike_grid, "multiplier": 100,
                "premium_tick": "0.01" if self.underlying == "XSP" else
                                "0.05 below 3.00; 0.10 otherwise",
                "expiration_cutoff": "16:00 ET; 13:00 scheduled early close",
                "support": {"dataset": self.support.name, "hash": self.support.hash,
                            "source": self.support.manifest.source},
                "capabilities": ["observed_bid_ask", "quote_sizes"],
                "unavailable": ["IV", "Greeks", "last_quote_update_time"],
                "quote_timestamp": "minute grid observation; last NBBO update unknown"}

    def index_bars(self, d: dt.date, symbol: str) -> pd.DataFrame:
        self._guard(d, d)
        if symbol in self.minutes:
            m = self._minute(symbol)
            if m.empty:
                return pd.DataFrame(columns=["ts_us", "price"])
            day = m.loc[m.date == d, ["ts_us", "price"]]
            if not day.empty or d <= m.date.max() or in_holdout(d):
                return day.reset_index(drop=True)
        # Never fill the protected index gap with recorded observations.
        if in_holdout(d):
            return pd.DataFrame(columns=["ts_us", "price"])
        ts, px = self.support.spot_ticks(symbol)
        keep = (ts >= et_us(d, 9, 30)) & (ts <= et_us(d, 16, 0))
        return pd.DataFrame({"ts_us": ts[keep], "price": px[keep]})

    def daily_bars(self, start: dt.date, end: dt.date) -> pd.DataFrame:
        self._guard(start, end)
        b = self.support.daily_bars()
        out = b[b.date.between(start, end)].copy()
        if self.daily_cache:
            spx = self._cached_daily("SPX")
            spx = spx[spx.date.between(start, end)].copy().assign(underlying="SPX")
            intraday = out[out.underlying == "SPX"].set_index("date")
            if "SPX" in self.minutes:
                m = self._minute("SPX")
                m = m[m.date.between(start, end)]
                g = m.groupby("date")
                local = pd.DataFrame({"open": g.open.first(), "high": g.high.max(),
                                      "low": g.low.min()})
                intraday = pd.concat([local, intraday]).groupby(level=0).first()
            spx = spx.join(intraday[["open", "high", "low"]], on="date")
            vix = self._cached_daily("VIX")
            vix = vix[vix.date.between(start, end)].copy().assign(underlying="$VIX")
            out = pd.concat([out[~out.underlying.isin(["SPX", "$VIX"])], spx, vix],
                            ignore_index=True)

        if self.underlying != "SPX":
            settlement = self.support.manifest.source.get("settlement", {}).get(self.underlying)
            required = {"NDX": "XQC", "XSP": "XSP"}[self.underlying]
            if not settlement or settlement.get("symbol") != required or not settlement.get(
                    "source_url"):
                out.loc[out.underlying == self.underlying, "close"] = np.nan
        return out

    def quotes(self, d: dt.date, strikes: tuple[float, float]) -> pd.DataFrame:
        self._guard(d, d)
        if self.dte:
            dates = sorted(set(self._cached_daily("SPX").date if self.daily_cache
                               else self.support.daily_bars().date))
            future = [x for x in dates if x > d]
            if not future:
                raise ValueError(f"{d}: calendar has no next trading session")
            self._guard(future[0], future[0])
        path = self.path(d)
        if not path.is_file():
            return pd.DataFrame(columns=["ts_us", "strike", "t", "bid", "ask"])
        pf = pq.ParquetFile(path)
        required = ["symbol", "expiration", "strike", "right", "timestamp", "bid", "ask"]
        sizes = [s for s in ("bid_size", "ask_size") if s in pf.schema_arrow.names]
        # Whole-session identity is checked even when pricing only a bounded strike band.
        df = pf.read(columns=required + sizes).to_pandas()
        exp = pd.to_datetime(df.expiration).dt.date
        if df.empty or set(df.symbol) != {self.root_symbol} or len(set(exp)) != 1:
            raise ValueError(f"{d}: empty or mixed option root/expiration")
        expiration = exp.iloc[0]
        self._guard(expiration, expiration)
        if (not self.dte and expiration != d) or (self.dte and expiration <= d):
            raise ValueError(f"{d}: expiration {expiration} inconsistent with {self.set_name}")
        # Recorded calendar of daily sessions handles weekends and holidays.
        if self.dte:
            dates = sorted(set(self._cached_daily("SPX").date if self.daily_cache
                               else self.support.daily_bars().date))
            between = [x for x in dates if d < x <= expiration]
            if between != [expiration]:
                raise ValueError(f"{d}: missing calendar or not one trading session to expiry")
        ts = pd.to_datetime(df.timestamp)
        if ts.dt.tz is None:
            raise ValueError("archive timestamps must be timezone-aware")
        if set(ts.dt.tz_convert("America/New_York").dt.date) != {d}:
            raise ValueError(f"{d}: timestamp outside trade session")
        k = df.strike.to_numpy(float)
        if not np.isfinite(k).all() or not np.allclose(k / self.strike_grid,
                                                    np.round(k / self.strike_grid),
                                                    rtol=0, atol=1e-8):
            raise ValueError(f"{d}: strike outside listed grid {self.strike_grid}")
        t = df.right.str.upper().map({"CALL": "C", "PUT": "P"})
        if t.isna().any():
            raise ValueError("invalid option right")
        df = df.assign(ts_us=ts.dt.tz_convert("UTC").astype("datetime64[us, UTC]")
                       .astype("int64"), t=t)
        if df.duplicated(["ts_us", "strike", "t"]).any():
            raise ValueError(f"{d}: duplicate contract observation")
        df = df[df.strike.between(*strikes)].copy()
        absent = (df.bid == 0) & (df.ask == 0)
        df.loc[absent, ["bid", "ask"]] = np.nan
        self.identities[d] = expiration
        self.raw_refs[str(d)] = {"path": str(path.resolve()), "sha256": sha256_file(path),
                                 "rows": pf.metadata.num_rows, "expiration": str(expiration)}
        return df[["ts_us", "strike", "t", "bid", "ask", *sizes]]


def inventory(roots: list[Path]) -> dict:
    """Catalog/file reconciliation. Protected partitions are statted, never opened."""
    groups = {}
    problems = []
    for root in roots:
        records = {}
        for line in (root / "catalog.jsonl").read_text().splitlines():
            r = json.loads(line)
            key = (r["set"], r["kind"], r["date"])
            if key in records and records[key] != r:
                problems.append({"root": str(root), "key": key, "reason": "duplicate_request"})
            records[key] = r
        files = {tuple([p.parts[-4], p.parts[-3], p.stem]): p
                 for p in root.glob("*/*/*/*.parquet")}
        for key in sorted(set(records) | set(files)):
            set_name, kind, date = key
            bucket = groups.setdefault((root.name, set_name, kind, date[:4]), Counter())
            rec, path = records.get(key), files.get(key)
            bucket["requests"] += int(rec is not None)
            bucket["no_data"] += int(rec is not None and rec["status"] == "no_data")
            if path is None:
                if rec and rec["status"] == "ok":
                    bucket["missing_file"] += 1
                continue
            bucket["files"] += 1
            bucket["bytes"] += path.stat().st_size
            if in_holdout(dt.date.fromisoformat(date)):
                bucket["protected_metadata_unchecked"] += 1
                continue
            try:
                rows = pq.ParquetFile(path).metadata.num_rows
                bucket["rows"] += rows
                if rows == 0 or (rec and rows != rec.get("rows")):
                    bucket["incomplete"] += 1
                else:
                    bucket["verified_files"] += 1
            except (OSError, pa.ArrowInvalid):
                bucket["incomplete"] += 1
    return {"groups": [{"root": k[0], "set": k[1], "kind": k[2], "year": k[3], **v}
                       for k, v in sorted(groups.items())], "problems": problems,
            "expected_expirations": "catalog requests; absent weekdays are not failures; "
                                    "no independently cached vendor expiration list",
            "replay_coverage": "requires audit-local; file counts are not usable sessions"}


def audit(source: LocalThetaDataSource, start: dt.date, end: dt.date) -> list[dict]:
    """Input intersection, without interpreting a no-trade decision as an exclusion."""
    source._guard(start, end)
    rows = []
    cal = EventCalendar()
    bars = source.daily_bars(*daily_range(HistoryPlan(start, end, source.dataset))[0])
    for d in pd.date_range(start, end).date:
        if d.weekday() >= 5:
            rows.append({"date": str(d), "status": "non_session", "reasons": []})
            continue
        reasons = []
        if not source.path(d).is_file():
            reasons.append("absent_option_data")
        grid = minute_grid(d, session_close(d, cal))
        spot = index_on_grid(source.index_bars(d, source.underlying), grid, d, INDEX_MAX_AGE_S)
        if not np.isfinite(spot).any():
            reasons.append("missing_index_observations")
        else:
            from butterfly_guy.core.config import load_config
            from butterfly_guy.research.entry import REPO_ROOT, RunContext
            config = load_config(config_path=REPO_ROOT / "configs" / {
                "SPX": "config.yaml", "NDX": "config_ndx.yaml", "XSP": "config_xsp.yaml"
            }[source.underlying])
            lo, hi = RunContext(config, source.underlying).window(d)
            required = (grid >= lo) & (grid <= hi)
            if not np.isfinite(spot[required]).all():
                reasons.append("incomplete_required_interval")
        if not has_print(source.index_bars(d, "$VIX"), d, VIX_BY):
            reasons.append("missing_vix")
        for sym in (source.underlying, "$VIX"):
            prior = bars[(bars.underlying == sym) & (bars.date < d)]
            if prior.empty or not np.isfinite(prior.sort_values("date").iloc[-1]["close"]):
                reasons.append(f"missing_prior_close:{sym}")
        if source.path(d).is_file():
            try:
                q = source.quotes(d, (-np.inf, np.inf))
                if q.empty or not (np.isfinite(q.bid) & np.isfinite(q.ask)).any():
                    reasons.append("absent_option_quotes")
            except (ValueError, OSError, pa.ArrowInvalid) as exc:
                reasons.append("invalid_option_data: " + str(exc))
        same = bars[(bars.underlying == source.underlying) & (bars.date == d)]
        if not source.dte and (same.empty or not np.isfinite(same.iloc[0]["close"])):
            reasons.append("missing_settlement")
        if same.empty or not np.isfinite(same.iloc[0]["open"]):
            reasons.append("missing_open")
        rows.append({"date": str(d), "status": "usable" if not reasons else "excluded",
                     "reasons": reasons,
                     "missing_index_grid_points": int((~np.isfinite(spot)).sum())})
    return rows


def import_local(source: LocalThetaDataSource, plan: HistoryPlan, cache: Path | None = None,
                 quality_dataset: Dataset | None = None) -> Manifest:
    """Immutable range export. Atomic directory publication; interrupted stages can retry.

    Existing published imports are verified and resumed without rewriting any bytes.
    A changed input or request requires a new identity, even before registration.
    """
    guard(plan.start, plan.end, what="local import", dataset=plan.dataset, unseal=plan.unseal)
    source._guard(plan.start, plan.end)
    if source.dataset != plan.dataset or Path(plan.dataset).name != plan.dataset:
        raise ValueError("source/output dataset identity mismatch")
    if not plan.dataset.startswith(f"{source.underlying.lower()}_{source.dte}dte_local_"):
        raise ValueError("use a separate <asset>_<dte>dte_local_<name> dataset")
    cache = cache or default_cache_root()
    root = cache / plan.dataset
    identity = {"mapping_version": MAPPING_VERSION, "range": [str(plan.start), str(plan.end)],
                "strike_margin": plan.strike_margin, "quote_freshness_s": INDEX_MAX_AGE_S,
                "kind": "local_parquet", "schema": 3}
    description = source.describe()
    raw_inputs = {str(d): {"path": str(source.path(d).resolve()),
                          "sha256": sha256_file(source.path(d))}
                  for d in source.sessions(plan.start, plan.end)}
    if root.exists():
        old = Dataset(root)
        if old.manifest.source != description or old.manifest.export != identity:
            raise ValueError("changed source/range; use a new dataset identity")
        old_inputs = old.manifest.history[0]["requested_raw_inputs"]
        if raw_inputs != old_inputs:
            raise ValueError("changed raw input/discovery; use a new dataset identity")
        for ref in old.manifest.history[0]["raw_inputs"].values():
            d = dt.date.fromisoformat(Path(ref["path"]).stem)
            source._guard(d, d)
            if sha256_file(source.path(d)) != ref["sha256"]:
                raise ValueError(f"changed raw input {d}; use a new dataset identity")
        if old.verify():
            raise ValueError("published dataset failed verification")
        return old.manifest
    if plan.require_quality and plan.start < dt.date(2026, 3, 13):
        if (quality_dataset is None or not quality_passed(quality_dataset.manifest)
                or not any(h.get("mode") == "vendor_quality" and h.get("pass") is True
                           and h.get("dataset_hash") == quality_dataset.hash
                           and h.get("range") == ["2026-03-13", "2026-09-25"]
                           for h in quality_dataset.manifest.history)
                or quality_dataset.manifest.source != description
                or quality_dataset.manifest.export.get("mapping_version") != MAPPING_VERSION):
            raise QualityNotPassedError("earlier import needs vendor-quality approval on a "
                                        "local validation dataset with identical source/mapping")
        if quality_dataset.verify():
            raise QualityNotPassedError("validation dataset failed manifest verification")
        for ref in quality_dataset.manifest.history[0]["requested_raw_inputs"].values():
            d = dt.date.fromisoformat(Path(ref["path"]).stem)
            source._guard(d, d)
            if sha256_file(source.path(d)) != ref["sha256"]:
                raise QualityNotPassedError("validation raw input changed since quality approval")
    cache.mkdir(parents=True, exist_ok=True)
    # Exclusive claim prevents simultaneous publication/resumption of a dataset name.
    lock = cache / f".{plan.dataset}.lock"
    fd = os.open(lock, os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(fd)
        raise ValueError("another import holds the dataset publication lock") from None
    stage = Path(tempfile.mkdtemp(prefix=f".{plan.dataset}.", dir=cache))
    try:
        m = Manifest(plan.dataset, source.underlying, description, identity)
        rows, ticks, excluded = [], [], {}
        cal = EventCalendar()
        approved_exclusions = {d: h["reason"]
                               for h in source.support.manifest.source.get(
                                   "approved_exclusions", []) for d in h["sessions"]}
        for d in source.sessions(plan.start, plan.end):
            if str(d) in approved_exclusions:
                excluded[str(d)] = "approved_quality_exclusion: " + approved_exclusions[str(d)]
                continue
            built = build_session(GuardedSource(source, plan.dataset, plan.unseal), d,
                                  session_close(d, cal), plan.strike_margin,
                                  underlying=source.underlying, integer_strikes=False)
            if isinstance(built, str):
                excluded[str(d)] = built
                continue
            chain = built.chain
            chain.underlying, chain.option_root = source.underlying, source.root_symbol
            chain.expiration = source.identities[d]
            # Grid observation age is known; actual quote last-update age is not.
            for t in ("C", "P"):
                age = chain.fields[f"{t}_quote_age_s"]
                chain.fields[f"{t}_observation_age_s"] = age.copy()
                stale = age > INDEX_MAX_AGE_S
                for f in ("bid", "ask", "mark"):
                    chain.fields[f"{t}_{f}"][stale] = np.nan
                chain.fields[f"{t}_quote_age_s"] = np.full(age.shape, np.nan)
            updates = source.quotes(d, (chain.strikes[0], chain.strikes[-1]))
            for t in ("C", "P"):
                for f in ("bid_size", "ask_size"):
                    if f not in updates:
                        continue
                    a = np.full((len(chain.ts), len(chain.strikes)), np.nan)
                    for k, g in updates[updates.t == t].groupby("strike"):
                        g = g.sort_values("ts_us")
                        ix = np.searchsorted(g.ts_us, chain.ts, side="right") - 1
                        ok = ix >= 0
                        a[ok, chain.column(k)] = g[f].to_numpy()[ix[ok]]
                    chain.fields[f"{t}_{f}"] = a
            rel = session_dir(d)
            m.files[f"{rel}/chain.parquet"] = write_table(chain_to_table(chain),
                                                        stage / rel / "chain.parquet")
            m.files[f"{rel}/clock.parquet"] = write_table(_table(built.clock),
                                                        stage / rel / "clock.parquet")
            rows.append({**built.row, "expiration": chain.expiration,
                         "underlying": source.underlying, "option_root": source.root_symbol,
                         "trading_sessions_to_expiry": source.dte,
                         "calendar_days_to_expiry": (chain.expiration - d).days})
            ticks.append(built.ticks)
        if not rows:
            raise ValueError("no sessions normalized; run audit-local for missing inputs")
        for name, frame in (("sessions.parquet", pd.DataFrame(rows)),
                            ("spot_ticks.parquet", pd.concat(ticks, ignore_index=True)),
                            ("daily_bars.parquet", source.daily_bars(*daily_range(plan)[0]))):
            m.files[name] = write_table(_table(frame), stage / name)
        m.history.append({"mode": "local_import", "range": identity["range"],
                          "raw_inputs": source.raw_refs, "requested_raw_inputs": raw_inputs,
                          "sessions_skipped": excluded,
                          "dataset_hash": m.dataset_hash, "holdout_sessions": 0})
        m.updated_at = dt.datetime.now(dt.UTC).isoformat()
        import subprocess
        m.exporter_git_sha = subprocess.check_output(["git", "rev-parse", "HEAD"],
                                                     text=True).strip()
        m.save(stage / "manifest.json")
        if Dataset(stage).verify():
            raise ValueError("staged dataset failed verification")
        stage.rename(root)
        return m
    finally:
        os.close(fd)
        if stage.exists():
            shutil.rmtree(stage)
