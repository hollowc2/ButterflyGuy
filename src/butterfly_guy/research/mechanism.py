"""H-TS1 mechanism check on Cboe's public daily closes: DESCRIPTIVE, development window only.

Question: on sessions whose prior-close VIX1D/VIX is high, does SPX move less than VIX1D
implied? This informs whether the owner registers H-TS1. It evaluates no rule, writes no
registry record and changes nothing in the pre-registration draft.

Inputs: Cboe's `SPX_History.csv` (`DATE,SPX`, closes only) and the dataset's
`aux/vol_index_daily.parquet` (Cboe VIX1D and VIX). Both are filtered to the window before
anything is computed: the scored sessions 2022-05-16 -> 2024-06-28 plus the one SPX
session before the first (its closes are the first session's priors). `holdout.guard` is
called on the range, and a range outside the development period raises, so no value dated
2024-07-01 or later enters any computation, table or report.

Statistic per session t, with t-1 the previous SPX session (as in `features.DailyVol`):

    r_t = |ln(SPX_close_t / SPX_close_{t-1})| / (VIX1D_close_{t-1} / 100 / sqrt(252))

The decision rule is `DECISION_RULE`, fixed before the first run.

Limits: close-to-close includes the overnight move and the morning before entry, so this
is a proxy for the 10:00 -> close exposure, not a test of H-TS1. H-EV1, H-SN1 and H-LV1
cannot be checked with close-only index data.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import io
import math

import numpy as np
import pandas as pd

from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.features import DailyVol
from butterfly_guy.research.holdout import DEVELOPMENT, guard

LABEL = "DESCRIPTIVE — development window — not a rule evaluation"
SPX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/SPX_History.csv"
WINDOW = (dt.date(2022, 5, 16), dt.date(2024, 6, 28))
HALF_SPLIT = dt.date(2023, 6, 1)
BLOCK, REPS, SEED = 10, 10_000, 1
DECISION_RULE = (
    "Split sessions at the upper tercile of the prior VIX1D/VIX, numpy.quantile at 2/3 over "
    "the same sessions (top: ratio >= that value, as in HTS1). Statistic: mean r in the top "
    "tercile minus mean r in the other two. Moving-block bootstrap over sessions in date "
    "order: 10-session blocks, 10,000 reps, seed 1, tercile membership fixed per session. "
    "The mechanism is 'supported' only if the 90% interval (5th to 95th percentile) lies "
    "entirely below zero; otherwise 'not supported'. Both halves (split at 2023-06-01) and "
    "the tercile bounds are reported. Fixed 2026-09-28, before the first run."
)
LIMITS = (
    "Close-to-close includes the overnight move and the morning before entry, so this is a "
    "proxy for the 10:00 -> close exposure, not a test of H-TS1.",
    "H-EV1, H-SN1 and H-LV1 cannot be checked with close-only index data.",
)


def parse_spx_csv(data: bytes) -> pd.DataFrame:
    """Cboe's SPX_History.csv: `date` (datetime.date) and `close`."""
    df = pd.read_csv(io.BytesIO(data))
    df.columns = [c.strip().upper() for c in df.columns]
    if list(df.columns) != ["DATE", "SPX"]:
        raise ValueError(f"SPX_History.csv: unexpected columns {list(df.columns)}")
    out = pd.DataFrame({"date": pd.to_datetime(df["DATE"], format="%m/%d/%Y").dt.date,
                        "close": pd.to_numeric(df["SPX"], errors="coerce").astype("float64")})
    if out["date"].duplicated().any():
        raise ValueError("SPX_History.csv: duplicate dates")
    return out.sort_values("date", ignore_index=True)


def fetch_spx() -> bytes:
    import httpx

    with httpx.Client(follow_redirects=True, timeout=60.0,
                      headers={"User-Agent": "butterfly-guy-research"}) as client:
        resp = client.get(SPX_URL)
        resp.raise_for_status()
        return resp.content


def confine(spx: pd.DataFrame, vol_daily: pd.DataFrame, start: dt.date, end: dt.date
            ) -> tuple[pd.DataFrame, pd.DataFrame, dt.date]:
    """Both inputs cut to [the SPX session before `start`, `end`], before anything else.

    Raises `HoldoutSealedError` for a range touching the holdout and `ValueError` for one
    leaving the development period. Returns the confined tables and the first date kept."""
    guard(start, end, what="mechanism check")
    if start < DEVELOPMENT[0] or end > DEVELOPMENT[1]:
        raise ValueError(f"{start}..{end} is outside the development period "
                         f"{DEVELOPMENT[0]}..{DEVELOPMENT[1]}")
    earlier = spx.loc[spx["date"] < start, "date"]
    lo = earlier.max() if len(earlier) else start
    if lo < DEVELOPMENT[0]:
        raise ValueError(f"the session before {start} ({lo}) is outside the development period")
    spx_in = spx[(spx["date"] >= lo) & (spx["date"] <= end)].reset_index(drop=True)
    vdates = pd.to_datetime(vol_daily["date"]).dt.date
    vol_in = vol_daily[(vdates >= lo) & (vdates <= end)].reset_index(drop=True)
    return spx_in, vol_in, lo


def session_table(spx_in: pd.DataFrame, vol_in: pd.DataFrame, start: dt.date
                  ) -> tuple[pd.DataFrame, dict[str, str]]:
    """One row per scored session with r and the prior VIX1D/VIX; sessions without a
    prior VIX1D or VIX close are excluded (returned with their reason)."""
    vol = DailyVol(vol_in)
    dates, closes = spx_in["date"].tolist(), spx_in["close"].to_numpy(float)
    rows, excluded = [], {}
    for i in range(1, len(dates)):
        t, prev = dates[i], dates[i - 1]
        if t < start:
            continue
        f = vol.features(t, prev)
        v1d, ratio = f["vix1d_prior_close"], f["vix1d_vix_prior"]
        if v1d is None or ratio is None or not (closes[i] > 0 and closes[i - 1] > 0):
            excluded[t.isoformat()] = "no prior VIX1D/VIX close or SPX close"
            continue
        move = abs(math.log(closes[i] / closes[i - 1]))
        rows.append({"session": t, "prior_session": prev, "spx_close": closes[i],
                     "spx_prior_close": closes[i - 1], "vix1d_prior": v1d,
                     "vix_prior": f["vix_prior_close"], "ratio_prior": ratio,
                     "r": move / (v1d / 100 / math.sqrt(252))})
    cols = ["session", "prior_session", "spx_close", "spx_prior_close", "vix1d_prior",
            "vix_prior", "ratio_prior", "r"]
    return pd.DataFrame(rows, columns=cols), excluded


def tercile_split(ratio: np.ndarray) -> tuple[float, float, np.ndarray]:
    """(1/3 bound, 2/3 bound, top mask): top is ratio >= numpy.quantile(ratio, 2/3)."""
    q13, q23 = (float(np.quantile(ratio, q)) for q in (1 / 3, 2 / 3))
    return q13, q23, ratio >= q23


def statistic(r: np.ndarray, top: np.ndarray) -> float:
    """Mean r in the top tercile minus mean r in the rest (NaN if either is empty)."""
    if not top.any() or top.all():
        return float("nan")
    return float(r[top].mean() - r[~top].mean())


def bootstrap(r: np.ndarray, top: np.ndarray, block: int = BLOCK, reps: int = REPS,
              seed: int = SEED) -> dict:
    """Moving-block bootstrap of `statistic`, membership fixed per session."""
    idx = block_bootstrap_indices(len(r), reps, block, seed)
    rr, tt = r[idx], top[idx]
    n_top, n_rest = tt.sum(axis=1), (~tt).sum(axis=1)
    ok = (n_top > 0) & (n_rest > 0)
    d = (np.where(tt, rr, 0).sum(axis=1)[ok] / n_top[ok]
         - np.where(~tt, rr, 0).sum(axis=1)[ok] / n_rest[ok])
    lo, med, hi = np.percentile(d, [5, 50, 95])
    return {"ci90": [float(lo), float(hi)], "median": float(med), "reps_used": int(ok.sum()),
            "block": block, "reps": reps, "seed": seed}


def _group(r: np.ndarray) -> dict:
    return {"n": int(len(r)), "mean_r": float(r.mean()) if len(r) else None,
            "median_r": float(np.median(r)) if len(r) else None}


def _part(table: pd.DataFrame, top: np.ndarray) -> dict:
    r = table["r"].to_numpy(float)
    return {"sessions": int(len(r)), "first": str(table["session"].min()),
            "last": str(table["session"].max()), "top": _group(r[top]),
            "rest": _group(r[~top]), "difference": statistic(r, top),
            "bootstrap": bootstrap(r, top)}


def frame_sha256(df: pd.DataFrame) -> str:
    return hashlib.sha256(df.to_csv(index=False, lineterminator="\n").encode()).hexdigest()


def run(spx: pd.DataFrame, vol_daily: pd.DataFrame, start: dt.date = WINDOW[0],
        end: dt.date = WINDOW[1]) -> tuple[dict, pd.DataFrame]:
    """Results and the per-session table. Inputs are confined before anything else."""
    spx_in, vol_in, lo = confine(spx, vol_daily, start, end)
    table, excluded = session_table(spx_in, vol_in, start)
    ratio, r = table["ratio_prior"].to_numpy(float), table["r"].to_numpy(float)
    q13, q23, top = tercile_split(ratio)
    table = table.assign(top_tercile=top)
    whole = _part(table, top)
    hi90 = whole["bootstrap"]["ci90"][1]
    first_half = (table["session"] < HALF_SPLIT).to_numpy()
    results = {
        "label": LABEL,
        "question": "On sessions whose prior-close VIX1D/VIX is high, does SPX move less "
                    "than VIX1D implied?",
        "decision_rule": DECISION_RULE,
        "limits": list(LIMITS),
        "window": {"sessions": [start.isoformat(), end.isoformat()],
                   "inputs_from": lo.isoformat(), "half_split": HALF_SPLIT.isoformat()},
        "inputs_in_window": {
            "spx_rows": int(len(spx_in)), "spx_sha256": frame_sha256(spx_in),
            "vol_rows": int(len(vol_in)),
            "vol_sha256": frame_sha256(vol_in.sort_values(["index", "date"],
                                                          ignore_index=True)),
            "max_date": str(max(spx_in["date"].max(),
                                pd.to_datetime(vol_in["date"]).max().date())),
        },
        "excluded": excluded,
        "tercile_bounds": {"q1_3": q13, "q2_3": q23},
        "mean_r_all": float(r.mean()),
        "result": whole,
        "halves": {"H1": _part(table[first_half], top[first_half]),
                   "H2": _part(table[~first_half], top[~first_half])},
        "verdict": "supported" if hi90 < 0 else "not supported",
    }
    return results, table


def _f(x: float | None, nd: int = 3) -> str:
    return "—" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def markdown(results: dict, provenance: dict) -> str:
    res, b = results["result"], results["result"]["bootstrap"]
    inp = provenance["inputs"]
    lines = [
        f"# H-TS1 mechanism check {provenance['run_id']}",
        "",
        f"**{results['label']}**",
        "",
        f"Question: {results['question']}",
        "",
        f"**Verdict: {results['verdict']}** (fixed rule below).",
        "",
        "## Decision rule (fixed before running)",
        "",
        f"> {results['decision_rule']}",
        "",
        "r_t = |ln(SPX_close_t / SPX_close_{t-1})| / (VIX1D_close_{t-1} / 100 / sqrt(252)),"
        " with t-1 the previous SPX session.",
        "",
        "## Result",
        "",
        f"- Sessions {results['window']['sessions'][0]} → {results['window']['sessions'][1]}: "
        f"{res['sessions']} scored, {len(results['excluded'])} excluded (no prior close).",
        f"- Tercile bounds of the prior VIX1D/VIX: 1/3 = {_f(results['tercile_bounds']['q1_3'])},"
        f" 2/3 = {_f(results['tercile_bounds']['q2_3'])}.",
        f"- Mean r over all sessions: {_f(results['mean_r_all'])} (a normal move priced "
        "exactly by VIX1D gives about 0.80).",
        "",
        "| Part | Sessions | Top n | Top mean r | Top median r | Rest n | Rest mean r | "
        "Rest median r | Top − rest | 90% interval |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for name, part in (("All", res), ("H1 (< 2023-06-01)", results["halves"]["H1"]),
                       ("H2 (≥ 2023-06-01)", results["halves"]["H2"])):
        pb = part["bootstrap"]
        lines.append(
            f"| {name} | {part['sessions']} | {part['top']['n']} | {_f(part['top']['mean_r'])} "
            f"| {_f(part['top']['median_r'])} | {part['rest']['n']} | "
            f"{_f(part['rest']['mean_r'])} | {_f(part['rest']['median_r'])} | "
            f"{_f(part['difference'])} | [{_f(pb['ci90'][0])}, {_f(pb['ci90'][1])}] |")
    lines += [
        "",
        f"The verdict uses the whole window only (interval [{_f(b['ci90'][0])}, "
        f"{_f(b['ci90'][1])}], {b['reps_used']} of {b['reps']} reps usable). The halves use "
        "the whole-window threshold and are reported, not tested.",
        "",
        "## Limits",
        "",
        *[f"- {x}" for x in results["limits"]],
        "- Development data only; nothing dated 2024-07-01 or later was read into any "
        f"computation (latest input date {results['inputs_in_window']['max_date']}).",
        "- No registry record. This informs whether H-TS1 is registered; it changes nothing "
        "in the pre-registration draft.",
        "",
        "## Inputs",
        "",
        f"- `SPX_History.csv`: {inp['spx_csv']['source']}, sha256 `{inp['spx_csv']['sha256']}`"
        f" ({inp['spx_csv']['bytes']} bytes, read {inp['spx_csv']['read_at']}); in-window rows "
        f"{results['inputs_in_window']['spx_rows']}, sha256 "
        f"`{results['inputs_in_window']['spx_sha256']}`.",
        f"- `{inp['vol_daily']['file']}` on `{inp['vol_daily']['dataset']}`: sha256 "
        f"`{inp['vol_daily']['sha256']}`, aux_hash `{inp['vol_daily']['aux_hash']}`; in-window "
        f"rows {results['inputs_in_window']['vol_rows']}, sha256 "
        f"`{results['inputs_in_window']['vol_sha256']}`.",
        f"- Git `{provenance['git_sha'][:12]}`{' (dirty)' if provenance['git_dirty'] else ''};"
        f" command: `{provenance['command']}`",
        "",
        "## Artifact hashes",
        "",
        *[f"- `{f}`: `{h}`" for f, h in provenance["hashes"].items()],
        "",
    ]
    return "\n".join(lines)
