"""Exit (credit) limit rules for closing a butterfly, shared by live execution and research.

Every rule prices step `i` of the exit ladder from anchors the caller keeps: the median of
the last few observed fly bids (`bid_anchor`) and fly mids (`mid_anchor`), so one bad tick
cannot pin every later step. Limits are rounded up to a valid increment, so a step never
accepts less than the rule computes, and never price below the bid anchor.

- `bid_ladder` (default, today's ladder): bid + (steps - 1 - k) x step for k = i mod steps,
  so the cycle restarts at the top after the last step.
- `mid_capped_ladder`: `bid_ladder`, but never above the mid.
- `mid_walk`: mid at step 0, walking linearly to the bid at step `steps - 1`, then holding
  at the bid.

See docs/research/exit-ladder-pricing-plan.md.
"""

from __future__ import annotations

from butterfly_guy.core.entry_pricing import round_credit_limit

EXIT_PRICING_RULES = ("bid_ladder", "mid_capped_ladder", "mid_walk")
MIN_CREDIT = 0.05


def _credit(price: float, underlying: str) -> float:
    return round_credit_limit(max(MIN_CREDIT, price), underlying)


def exit_limit(
    rule: str,
    step: int,
    bid_anchor: float,
    mid_anchor: float,
    *,
    ladder_step: float,
    ladder_steps: int,
    underlying: str,
) -> float:
    """Credit limit for ladder step `step` (0-based, counting every submission)."""
    if ladder_steps < 1 or step < 0:
        raise ValueError("ladder_steps must be >= 1 and step >= 0")
    k = step % ladder_steps
    # Medians of different polls can cross; never let the mid anchor sit below the bid.
    mid = max(mid_anchor, bid_anchor)
    if rule == "bid_ladder":
        return _credit(bid_anchor + (ladder_steps - 1 - k) * ladder_step, underlying)
    if rule == "mid_capped_ladder":
        ladder = _credit(bid_anchor + (ladder_steps - 1 - k) * ladder_step, underlying)
        return min(ladder, _credit(mid, underlying))
    if rule == "mid_walk":
        frac = 1.0 if ladder_steps == 1 else min(step, ladder_steps - 1) / (ladder_steps - 1)
        return _credit(mid - frac * (mid - bid_anchor), underlying)
    raise ValueError(f"unknown exit pricing rule {rule!r}")

