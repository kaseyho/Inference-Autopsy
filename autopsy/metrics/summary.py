# Accepts a list of TraceRecord
# Computes Counts
# Computes Percentiles
# Compute Reliability rates
# Returns summary object or dictionary

from pathlib import Path
from autopsy.traces.schema import RequestStatus, TraceRecord
from autopsy.traces.jsonl import read_jsonl

def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * p)
    return ordered[index]

def summarize_records(records: list[TraceRecord]) -> dict[str, object]:
    total = len(records)
    success_count = sum(1 for r in records if r.status == RequestStatus.SUCCESS)
    timeout_count = sum(1 for r in records if r.status == RequestStatus.TIMEOUT)
    partial_count = sum(1 for r in records if r.status == RequestStatus.PARTIAL)
    error_count = sum(1 for r in records if r.status == RequestStatus.ERROR)

    ttfts = [r.metrics.ttft_ms for r in records if r.metrics.ttft_ms is not None]
    latencies = [
        r.metrics.request_latency_ms
        for r in records
        if r.metrics.request_latency_ms is not None
    ]

    return {
        "total_requests": total,
        "success_count": success_count,
        "timeout_count": timeout_count,
        "partial_count": partial_count,
        "error_count": error_count,
        "error_rate": (total - success_count) / total if total else 0,
        "timeout_rate": timeout_count / total if total else 0,
        "ttft_p50_ms": percentile(ttfts, 0.50),
        "ttft_p95_ms": percentile(ttfts, 0.95),
        "request_latency_p50_ms": percentile(latencies, 0.50),
        "request_latency_p95_ms": percentile(latencies, 0.95),
        "request_latency_p99_ms": percentile(latencies, 0.99),
    }

def summarize_trace_file(path: Path) -> dict[str, object]:
    records = read_jsonl(path)
    return summarize_records(records)