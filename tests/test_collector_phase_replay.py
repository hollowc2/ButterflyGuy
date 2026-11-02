"""Diagnostic FIFO burst model, not a production latency prediction."""

import statistics


def replay(phases):
    arrivals = []
    # Ten minutes: collector reads are distinct; monitor cadence never changes.
    for minute in range(10):
        for asset, phase in enumerate(phases):
            for operation, duration in [('spot', .55), ('chain', .35), ('history', .4)]:
                arrivals.append((minute * 60 + phase, 'collector', duration, asset, operation))
    for tick in range(300):
        for asset in range(3):
            arrivals.append((tick * 2, 'monitor', .2, asset, 'chain'))
    worker = 0
    waits, latencies, monitor_times = [], [], []
    for arrival, kind, duration, asset, operation in sorted(arrivals):
        start = max(arrival, worker)
        worker = start + duration
        waits.append(start - arrival)
        latencies.append(worker - arrival)
        if kind == 'monitor':
            monitor_times.append((arrival, asset))
    return {
        'attempts': len(arrivals),
        'queue_p95': statistics.quantiles(waits, n=100)[94],
        'latency_p95': statistics.quantiles(latencies, n=100)[94],
        'max_latency': max(latencies),
        'monitor_times': monitor_times,
    }


def test_stable_phases_reduce_simultaneous_burst_queueing():
    baseline, candidate = replay([0, 0, 0]), replay([0, 2, 4])
    assert baseline['attempts'] == candidate['attempts'] == 990
    assert baseline['monitor_times'] == candidate['monitor_times']
    assert candidate['queue_p95'] < baseline['queue_p95']
    assert candidate['latency_p95'] < baseline['latency_p95']
    assert candidate['max_latency'] < baseline['max_latency']
    print({name: {k: v for k, v in result.items() if k != 'monitor_times'}
           for name, result in [('baseline', baseline), ('candidate', candidate)]})
