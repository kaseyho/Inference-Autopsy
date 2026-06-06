# Test:
# Counts are correct 
# Error rate includes timeout, partial, and error recors
# Percentile returns something expected for a small list

from autopsy.fake.generate import generate_fake_records
from autopsy.metrics.summary import summarize_records

def test_summary_counts() -> None:
    records = generate_fake_records(count=30, seed=7)
    summary = summarize_records(records)

    assert summary["total_requests"] == 30
    assert summary["success_count"] < 30
    assert summary["error_rate"] > 0

def test_summary_has_ttft_percentiles() -> None:
    records = generate_fake_records(count=30, seed=7)
    summary = summarize_records(records)

    assert summary["ttft_p50_ms"] is not None
    assert summary["ttft_p95_ms"] is not None