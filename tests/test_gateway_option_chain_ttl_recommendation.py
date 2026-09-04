from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from gateway_option_chain_ttl_recommendation import (  # noqa: E402
    Histogram,
    parse_histograms,
)

SAMPLE_METRICS = """\
# HELP schwab_gateway_scheduler_queue_wait_seconds Time spent queued
# TYPE schwab_gateway_scheduler_queue_wait_seconds histogram
schwab_gateway_scheduler_queue_wait_seconds_bucket{operation="spot",priority_class="protected",le="0.5"} 5
schwab_gateway_scheduler_queue_wait_seconds_bucket{operation="option_chain",priority_class="protected",le="0.5"} 2
schwab_gateway_scheduler_queue_wait_seconds_bucket{operation="option_chain",priority_class="protected",le="1.0"} 8
schwab_gateway_scheduler_queue_wait_seconds_bucket{operation="option_chain",priority_class="protected",le="2.5"} 10
schwab_gateway_scheduler_queue_wait_seconds_bucket{operation="option_chain",priority_class="protected",le="+Inf"} 10
# HELP schwab_gateway_scheduler_upstream_execution_seconds duration
# TYPE schwab_gateway_scheduler_upstream_execution_seconds histogram
schwab_gateway_scheduler_upstream_execution_seconds_bucket{operation="option_chain",priority_class="protected",outcome="success",le="1.0"} 4
schwab_gateway_scheduler_upstream_execution_seconds_bucket{operation="option_chain",priority_class="protected",outcome="success",le="2.5"} 9
schwab_gateway_scheduler_upstream_execution_seconds_bucket{operation="option_chain",priority_class="protected",outcome="success",le="+Inf"} 10
"""


def test_parse_histograms_filters_by_operation():
    histograms = parse_histograms(SAMPLE_METRICS, operation="option_chain")
    queue_wait = histograms["schwab_gateway_scheduler_queue_wait_seconds"]
    assert queue_wait.buckets == {0.5: 2, 1.0: 8, 2.5: 10, float("inf"): 10}


def test_parse_histograms_empty_when_operation_missing():
    histograms = parse_histograms(SAMPLE_METRICS, operation="history")
    assert all(h.buckets == {} for h in histograms.values())


def test_histogram_percentile_picks_first_bucket_meeting_target():
    h = Histogram(buckets={0.5: 10, 1.0: 40, 2.0: 90, 4.0: 98, float("inf"): 100})
    assert h.percentile(0.5) == 2.0
    assert h.percentile(0.9) == 2.0
    assert h.percentile(0.99) == float("inf")


def test_histogram_percentile_none_when_empty():
    assert Histogram().percentile(0.99) is None
