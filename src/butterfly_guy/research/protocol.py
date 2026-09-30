"""The pre-registered holdout evaluation of the vendor sweep (D9).

`docs/research/next-sweep-preregistration-draft.md` ("Primary metric and gate", with
Revision 1) fixes how the sealed holdout is evaluated. This module holds those choices as
constants, and the checks the `holdout` command makes before and after it replays a single
holdout session. Nothing here takes a parameter that the draft fixes:

- arms: every variant registered up to the unseal's record, each paired with E0 on identical
  sessions (a session any arm cannot replay is dropped from every arm);
- sessions: the holdout, 2024-07-01 → 2026-03-12, under `vendor_1m`;
- metric: stressed marketable with intraday exits floored at $0 (Revision 1), per session
  with zeros on no-trade days; delayed-exit stressed for gate 4;
- test: moving-block bootstrap of the total paired difference, 10-session blocks, 10,000
  reps, seed 1, one index draw for both arms;
- k: the number of variants registered; each passes gate 1 only if the bootstrap lower bound
  is above zero. The drafted bound is at 1 − 0.10/k; since Revision 4 the bound's tail is the
  calibrated level recorded at registration (below);
- gates 2–4: positive in both halves (split after 2025-04-30); positive with the three
  largest-P&L sessions of either arm removed (the union of each arm's top three, removed
  from both); delayed-exit point estimate positive;
- gate 6 (Revision 5, the owner's decision D2 of 2026-09-29): the rule's own stressed P&L
  over the evaluated holdout sessions is above zero. Against a losing E0 a paired gain alone
  means only "loses less than E0"; a pass now also means the rule made money.

Gate 5 (H-SN1's noise secondary) has no statistic in the draft, so a registered H-SN1
variant is refused rather than evaluated with an invented one.

Gate-1 calibration (Revision 4, the owner's decision D4 of 2026-09-29). With a sparse, skewed
paired difference (a skip filter whose few skipped trades include large settled winners) the
percentile bootstrap passes a rule with no effect more often than 0.10/k. So at registration
each rule's development-window paired difference is shifted to mean zero and resampled in
10-session moving blocks to holdouts of the planned size; the percentile test is run on each
at every level of a fixed grid. For each k the recorded level is the loosest grid level whose
simulated false-pass rate is at most 0.10/k, never looser than the drafted 0.10/k.
"""

from __future__ import annotations

import datetime as dt

import numpy as np

from butterfly_guy.research.evaluate import block_bootstrap_indices
from butterfly_guy.research.holdout import HOLDOUT

BASELINE = "E0"
PROFILE = "vendor_1m"
STRESSED_EXIT_FLOOR = 0.0
EXIT_DELAY = 1
BLOCK, REPS, SEED = 10, 10_000, 1
FAMILY_ALPHA = 0.10
# Gate-1 calibration (Revision 4): simulated holdouts, bootstrap reps per holdout (the real
# test's), seed, grid.
CAL_SIMS, CAL_REPS, CAL_SEED = 2000, REPS, 1
CAL_K_MAX = 5
# Every drafted level 0.10/k is on the grid, so a rule that does not over-pass keeps it.
CAL_GRID = tuple(sorted({0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.045, 0.04, 0.035, 0.03, 0.025,
                         0.02, 0.0175, 0.015, 0.0125, 0.01, 0.0075, 0.005, 0.0025, 0.001,
                         *(FAMILY_ALPHA / k for k in range(1, CAL_K_MAX + 1))}, reverse=True))
SPLIT = dt.date(2025, 4, 30)  # H1 = HOLDOUT[0]..SPLIT, H2 = the rest
WINDOW = HOLDOUT
GATE5_UNDEFINED = frozenset({"HSN1", "HSN1_c148", "HSN1_c168"})
SCOPE = "holdout"


class ProtocolError(RuntimeError):
    """The holdout evaluation cannot run as pre-registered; nothing was replayed."""


def describe() -> dict:
    """The protocol as recorded in every holdout run's meta."""
    return {"baseline": BASELINE, "profile": PROFILE,
            "stressed_exit_floor": STRESSED_EXIT_FLOOR, "exit_delay_snapshots": EXIT_DELAY,
            "bootstrap": {"block": BLOCK, "reps": REPS, "seed": SEED},
            "family_alpha": FAMILY_ALPHA, "split": SPLIT.isoformat(),
            "window": [WINDOW[0].isoformat(), WINDOW[1].isoformat()],
            "gate1": "percentile block bootstrap at the level calibrated on development data "
                     "at registration (Revision 4)",
            "gate3": "union of each arm's three largest-P&L sessions removed from both arms",
            "gate6": "the rule's own stressed P&L over the evaluated sessions above zero "
                     "(Revision 5)"}


def _blocks(rng: np.random.Generator, n_src: int, n_out: int, reps: int) -> np.ndarray:
    """(reps, n_out) indices into a length-n_src series from moving blocks of BLOCK."""
    nb = int(np.ceil(n_out / BLOCK))
    starts = rng.integers(0, n_src - BLOCK + 1, size=(reps, nb))
    return (starts[:, :, None] + np.arange(BLOCK)).reshape(reps, -1)[:, :n_out]


def calibrate_gate1(diff_dev: np.ndarray, holdout_sessions: int, *, sims: int | None = None,
                    reps: int | None = None, seed: int = CAL_SEED) -> dict:
    """Gate-1 levels for k = 1..CAL_K_MAX from a rule's development-window paired
    difference (per session, zeros on no-trade days); see the module docstring."""
    sims = CAL_SIMS if sims is None else sims
    reps = CAL_REPS if reps is None else reps
    diff_dev = np.asarray(diff_dev, dtype=float)
    if len(diff_dev) < 2 * BLOCK:
        raise ProtocolError(f"{len(diff_dev)} development sessions are too few to calibrate "
                            "gate 1")
    null = diff_dev - diff_dev.mean()
    rng = np.random.default_rng(seed)
    grid = np.array(CAL_GRID)
    passes = np.zeros(len(grid))
    outer = _blocks(rng, len(null), holdout_sessions, sims)
    for s in range(sims):
        x = null[outer[s]]
        totals = x[_blocks(rng, holdout_sessions, holdout_sessions, reps)].sum(axis=1)
        passes += np.percentile(totals, 100 * grid) > 0
    rates = passes / sims
    levels, reached = {}, {}
    for k in range(1, CAL_K_MAX + 1):
        target = FAMILY_ALPHA / k
        ok = [float(g) for g, rate in zip(grid, rates, strict=True)
              if rate <= target and g <= target + 1e-12]
        levels[str(k)] = max(ok) if ok else float(grid.min())
        reached[str(k)] = bool(ok)
    return {"method": "percentile block bootstrap, null = development difference shifted to "
                      "mean zero, resampled to the planned holdout size",
            "holdout_sessions": int(holdout_sessions), "development_sessions": len(null),
            "sims": sims, "reps": reps, "seed": seed, "block": BLOCK,
            "false_pass": {f"{g:g}": round(float(rate), 4)
                           for g, rate in zip(grid, rates, strict=True)},
            "levels": levels, "reached": reached}


def registrations(records: list[dict], seq: int) -> list[dict]:
    """The `register` records up to and including `seq`, one per variant name."""
    regs = [r for r in records[:seq + 1] if r["event"] == "register"]
    names = [r["variant"] for r in regs]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        raise ProtocolError(f"variants registered more than once: {', '.join(dupes)}")
    return regs


def check_registered(regs: list[dict], catalog: dict) -> None:
    """Every registered variant must still be the catalog's definition, and evaluable."""
    if not regs:
        raise ProtocolError("nothing is registered")
    k = str(len(regs))
    for r in regs:
        name = r["variant"]
        if name == BASELINE:
            raise ProtocolError(f"{BASELINE} is the baseline, not a hypothesis")
        if name in GATE5_UNDEFINED:
            raise ProtocolError(
                f"{name} needs gate 5 (H-SN1's noise secondary), which has no statistic in "
                "the draft; fix it as a marked revision before registering H-SN1")
        v = catalog.get(name)
        if v is None:
            raise ProtocolError(f"{name} is registered but not in the catalog")
        if v.definition_hash() != r["definition_hash"]:
            raise ProtocolError(
                f"{name}: the catalog definition ({v.definition_hash()[:12]}) is not the "
                f"registered one ({r['definition_hash'][:12]})")
        if v.fit_window is not None and "fitted" not in r:
            raise ProtocolError(f"{name} is a fitted rule registered without its fitted "
                                "values; they cannot be checked")
        cal = r.get("gate1", {})
        if k not in cal.get("levels", {}):
            raise ProtocolError(f"{name} was registered without a gate-1 calibration for "
                                f"k = {k} (Revision 4)")
        if not cal.get("reached", {}).get(k, False):
            level = cal["levels"][k]
            raise ProtocolError(
                f"{name}: gate 1 cannot be calibrated to 0.10/{k}; even the {level:g} level "
                f"passes a no-effect rule {cal['false_pass'].get(f'{level:g}')} of the time "
                "on development data. Register fewer rules.")


def check_fitted(regs: list[dict], fitted_now: dict[str, dict]) -> None:
    """A fitted rule's re-fit on its development window must equal the registered value."""
    for r in regs:
        if "fitted" not in r:
            continue
        if r.get("fit_profile") != PROFILE:
            raise ProtocolError(f"{r['variant']} was fitted under {r.get('fit_profile')!r} "
                                f"at registration, not {PROFILE!r}")
        if fitted_now.get(r["variant"]) != r["fitted"]:
            raise ProtocolError(
                f"{r['variant']}: re-fitted {fitted_now.get(r['variant'])} on the development "
                f"window, registered {r['fitted']}; the development data or the fit changed")


def prior_holdout_runs(records: list[dict]) -> list[dict]:
    return [r for r in records if r["event"] == "evaluate" and r.get("scope") == SCOPE]


def check_rerun(records: list[dict], *, unseal_seq: int, dataset_hash: str,
                variants: list[str], code_unchanged_since) -> dict | None:
    """The draft allows one evaluation per registered hypothesis, with no re-runs after
    edits. A later run is allowed only as an exact reproduction of the first (same unseal,
    dataset and variants, and no code change since); it returns the first run's record so
    the caller can compare results. Anything else raises."""
    prior = prior_holdout_runs(records)
    if not prior:
        return None
    first = prior[0]
    same = [r for r in prior if r["run_id"] == first["run_id"]]
    why = []
    if first.get("unseal_seq") != unseal_seq:
        why.append(f"unseal record {first.get('unseal_seq')} (now {unseal_seq})")
    if first.get("dataset_hash") != dataset_hash:
        why.append(f"dataset {first.get('dataset_hash', '')[:12]} (now {dataset_hash[:12]})")
    if sorted(r["variant"] for r in same) != sorted(variants):
        why.append("a different set of arms")
    if not code_unchanged_since(first.get("git_sha", "")):
        why.append(f"code at {first.get('git_sha', '')[:12]} (src/ or configs/ changed since)")
    if why:
        raise ProtocolError(
            f"the holdout was already evaluated (run {first['run_id']}); a re-run after "
            f"edits is not allowed. It differs in: {'; '.join(why)}")
    return first


def gates(arm: np.ndarray, base: np.ndarray, arm_delayed: np.ndarray,
          base_delayed: np.ndarray, dates: list[dt.date], k: int,
          tail: float | None = None) -> dict:
    """The draft's gates 1–4 for one hypothesis against the baseline, on per-session P&L
    (zeros on no-trade days) over identical sessions. Gate 1's one-sided bound uses `tail`,
    the calibrated level recorded at registration; without it, the drafted 0.10/k."""
    if not (len(arm) == len(base) == len(arm_delayed) == len(base_delayed) == len(dates)):
        raise ValueError("paired arms must cover the same sessions")
    if k < 1:
        raise ValueError("k must be at least 1")
    diff = arm - base
    h1 = np.array([d <= SPLIT for d in dates], dtype=bool)
    idx = block_bootstrap_indices(len(diff), REPS, BLOCK, SEED)
    totals = diff[idx].sum(axis=1)
    drafted = FAMILY_ALPHA / k
    tail = drafted if tail is None else tail
    if not 0 < tail <= drafted + 1e-12:
        raise ValueError(f"gate-1 tail {tail} must be in (0, {drafted}]")
    level = 1 - tail
    lower = float(np.percentile(totals, 100 * tail)) if len(diff) else 0.0
    top = set(np.argsort(arm, kind="stable")[-3:]) | set(np.argsort(base, kind="stable")[-3:])
    keep = np.array([i not in top for i in range(len(diff))], dtype=bool)
    out = {
        "k": k, "level": level, "drafted_level": 1 - drafted, "sessions": len(dates),
        "h1_sessions": int(h1.sum()), "h2_sessions": int((~h1).sum()),
        "diff": float(diff.sum()), "diff_per_session": float(diff.mean()) if len(diff) else 0.0,
        "lower_bound": lower, "p_better": float((totals > 0).mean()) if len(diff) else 0.0,
        "h1_diff": float(diff[h1].sum()), "h2_diff": float(diff[~h1].sum()),
        "top3_sessions_removed": sorted(dates[i].isoformat() for i in top),
        "top3_removed_diff": float(diff[keep].sum()),
        "delayed_diff": float((arm_delayed - base_delayed).sum()),
        "own_net": float(arm.sum()), "baseline_net": float(base.sum()),
    }
    out["gate1"] = out["lower_bound"] > 0
    out["gate2"] = out["h1_diff"] > 0 and out["h2_diff"] > 0
    out["gate3"] = out["top3_removed_diff"] > 0
    out["gate4"] = out["delayed_diff"] > 0
    out["gate6"] = out["own_net"] > 0
    out["passed"] = (out["gate1"] and out["gate2"] and out["gate3"] and out["gate4"]
                     and out["gate6"])
    # Dollars to the cent; the level and P(better) to 4 decimals (0.975 must stay 0.975).
    return {key: (round(v, 6 if key in {"level", "drafted_level", "p_better"} else 2)
                  if isinstance(v, float) else v) for key, v in out.items()}


def markdown_section(gate_rows: dict[str, dict], fitted: dict[str, dict],
                     reproduction_of: str | None) -> list[str]:
    """The pre-registered verdict, placed above the standard run report."""
    k = next(iter(gate_rows.values()))["k"] if gate_rows else 0
    lines = [
        "## Pre-registered holdout verdict", "",
        f"Protocol: `docs/research/next-sweep-preregistration-draft.md` with its revisions. "
        f"Arms: every variant registered up to the unseal record, paired with {BASELINE}. "
        f"Stressed exits floored at ${STRESSED_EXIT_FLOOR:.2f}. Bootstrap: {BLOCK}-session "
        f"blocks, {REPS:,} reps, seed {SEED}. k = {k}; gate 1 at each rule's calibrated level "
        f"(Revision 4; drafted {100 * (1 - FAMILY_ALPHA / max(k, 1)):.1f}%). Halves split after "
        f"{SPLIT}.",
        "",
        "| Variant | Δ vs E0 | Gate-1 level | Lower bound | G1 | H1 Δ | H2 Δ | G2 "
        "| Δ top-3 removed | G3 | Delayed Δ | G4 | Own net | G6 | E0 net | Verdict |",
        "|---|---:|---:|---:|---|---:|---:|---|---:|---|---:|---|---:|---|---:|---|",
    ]

    def mark(ok: bool) -> str:
        return "pass" if ok else "FAIL"

    for name, g in gate_rows.items():
        lines.append(
            f"| {name} | {g['diff']:,.0f} | {100 * g['level']:.2f}% | {g['lower_bound']:,.0f} | "
            f"{mark(g['gate1'])} | "
            f"{g['h1_diff']:,.0f} | {g['h2_diff']:,.0f} | {mark(g['gate2'])} | "
            f"{g['top3_removed_diff']:,.0f} | {mark(g['gate3'])} | {g['delayed_diff']:,.0f} | "
            f"{mark(g['gate4'])} | {g['own_net']:,.0f} | {mark(g['gate6'])} | "
            f"{g['baseline_net']:,.0f} | "
            f"**{'PASS' if g['passed'] else 'FAIL'}** |")
    if fitted:
        lines += ["", "Fitted values re-fitted on the development window and checked equal to "
                  "the registered ones: " + "; ".join(
                      f"{n} {v}" for n, v in sorted(fitted.items())) + "."]
    if reproduction_of:
        lines += ["", f"This run reproduces holdout run {reproduction_of} (same unseal, "
                  "dataset, arms and code); it is recorded as another look."]
    lines += ["", "\"Own net\" is the rule's own stressed P&L; gate 6 (Revision 5) requires it "
              "above zero.", ""]
    return lines
