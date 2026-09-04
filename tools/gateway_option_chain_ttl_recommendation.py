"""Recommend a real SCHWAB_GATEWAY_OPTION_CHAIN_CACHE_TTL_SECONDS from live metrics.

Follow-up to SchwabGateway PR #4 (2026-09-04), which raised the TTL *ceiling*
to 8s but left the deployed value at 4s pending real `operation="option_chain"`
histogram data — the container had zero samples at merge time. Run this after
a full trading session to compute the actual queue-wait + execution p99 and
recommend a TTL with headroom, instead of guessing.

Usage (on Helios, or anywhere that can reach the gateway):

    python tools/gateway_option_chain_ttl_recommendation.py \\
        --gateway-url http://127.0.0.1:8011 \\
        --headroom-seconds 1.0

Reads GET {gateway-url}/metrics (Prometheus text exposition format) and
computes p99 for schwab_gateway_scheduler_queue_wait_seconds{operation="option_chain"}
and schwab_gateway_scheduler_upstream_execution_seconds{operation="option_chain"},
summed (queue wait + execution ≈ end-to-end, matching what the soak observed
as chain_*_first latency). Recommends max(observed_p99 + headroom, current_ttl),
capped at the 8s code ceiling (MAX_OPTION_CHAIN_CACHE_TTL_SECONDS in
SchwabGateway's upstream.py/config.py as of PR #4 — bump the ceiling first if
real p99 exceeds it).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field

import httpx

METRIC_NAMES = (
    "schwab_gateway_scheduler_queue_wait_seconds",
    "schwab_gateway_scheduler_upstream_execution_seconds",
)
OPTION_CHAIN_TTL_CEILING_SECONDS = 8.0  # keep in sync with SchwabGateway PR #4

BUCKET_RE = re.compile(
    r'^(?P<name>\w+)_bucket\{(?P<labels>[^}]*)\}\s+(?P<count>[\d.eE+]+)\s*$'
)
LABEL_RE = re.compile(r'(\w+)="([^"]*)"')


@dataclass
class Histogram:
    buckets: dict[float, float] = field(default_factory=dict)  # le -> cumulative count

    def percentile(self, p: float) -> float | None:
        if not self.buckets:
            return None
        total = max(self.buckets.values())
        if total <= 0:
            return None
        target = total * p
        for le in sorted(self.buckets):
            if self.buckets[le] >= target:
                return le
        return None


def parse_histograms(text: str, *, operation: str) -> dict[str, Histogram]:
    result: dict[str, Histogram] = {name: Histogram() for name in METRIC_NAMES}
    for line in text.splitlines():
        match = BUCKET_RE.match(line)
        if not match or match["name"] not in result:
            continue
        labels = dict(LABEL_RE.findall(match["labels"]))
        if labels.get("operation") != operation:
            continue
        le = labels.get("le")
        if le is None:
            continue
        le_value = float("inf") if le == "+Inf" else float(le)
        result[match["name"]].buckets[le_value] = float(match["count"])
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gateway-url", default="http://127.0.0.1:8011")
    parser.add_argument("--operation", default="option_chain")
    parser.add_argument("--percentile", type=float, default=0.99)
    parser.add_argument("--headroom-seconds", type=float, default=1.0)
    parser.add_argument("--current-ttl-seconds", type=float, default=4.0)
    args = parser.parse_args()

    response = httpx.get(f"{args.gateway_url}/metrics", timeout=10.0)
    response.raise_for_status()
    histograms = parse_histograms(response.text, operation=args.operation)

    queue_wait = histograms["schwab_gateway_scheduler_queue_wait_seconds"]
    execution = histograms["schwab_gateway_scheduler_upstream_execution_seconds"]
    queue_p = queue_wait.percentile(args.percentile)
    exec_p = execution.percentile(args.percentile)

    if queue_p is None or exec_p is None:
        print(
            f"No {args.operation!r} samples yet for one or both histograms "
            f"(queue_wait={queue_p}, execution={exec_p}). Run this again after "
            "a full trading session has passed through the gateway.",
            file=sys.stderr,
        )
        return 1

    if queue_p == float("inf") or exec_p == float("inf"):
        print(
            f"p{int(args.percentile * 100)} fell in the +Inf bucket for one or both "
            "histograms — scheduler.py uses Prometheus's default bucket boundaries "
            "(..., 2.5, 5.0, 7.5, 10.0, +Inf), so this means the real percentile is "
            "above 10s. That's a bigger scheduler-contention problem than a TTL "
            "number can fix — investigate before picking a new TTL.",
            file=sys.stderr,
        )
        return 1

    end_to_end_p = queue_p + exec_p
    recommended = max(end_to_end_p + args.headroom_seconds, args.current_ttl_seconds)
    capped = min(recommended, OPTION_CHAIN_TTL_CEILING_SECONDS)

    print(f"operation={args.operation!r} p{int(args.percentile * 100)}:")
    print(f"  queue_wait_seconds     ≈ {queue_p:.3f}s")
    print(f"  upstream_execution_seconds ≈ {exec_p:.3f}s")
    print(f"  end-to-end (sum)       ≈ {end_to_end_p:.3f}s")
    print(f"  current deployed TTL   = {args.current_ttl_seconds:.1f}s")
    print(f"  recommended TTL        = {capped:.1f}s (headroom={args.headroom_seconds}s)")
    if recommended > OPTION_CHAIN_TTL_CEILING_SECONDS:
        print(
            f"  WARNING: recommendation ({recommended:.1f}s) exceeds the "
            f"{OPTION_CHAIN_TTL_CEILING_SECONDS}s code ceiling — the ceiling "
            "itself needs raising in SchwabGateway before this can be applied.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
