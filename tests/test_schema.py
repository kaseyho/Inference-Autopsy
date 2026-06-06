# Valid success record works
# Bad enum value fails
# Negative token counts fail
# TImeout record can include an error

import pytest
from pydantic import ValidationError

from autopsy.traces.schema import (
    CacheMode,
    LoadMode,
    PromptRecordingMode,
    RequestMetrics,
    RequestStatus,
    Timings,
    TraceRecord,
)


def make_record() -> TraceRecord:
    return TraceRecord(
        run_id="run_001",
        request_id="req_001",
        request_sequence_index=0,
        profile="short-chat",
        model="fake-model",
        base_url_hash="endpoint_a",
        load_mode=LoadMode.CLOSED_LOOP,
        concurrency=1,
        cache_mode=CacheMode.NONE,
        prompt_recording_mode=PromptRecordingMode.HASH_ONLY,
        input_tokens_estimated=100,
        output_tokens=20,
        status=RequestStatus.SUCCESS,
        timings_ms=Timings(first_byte=100, first_token=150, request_end=700),
        token_times_ms=[150, 180, 210],
        metrics=RequestMetrics(ttfb_ms=100, ttft_ms=150, request_latency_ms=700),
    )


def test_valid_trace_record() -> None:
    record = make_record()
    assert record.request_id == "req_001"


def test_invalid_status_rejected() -> None:
    data = make_record().model_dump()
    data["status"] = "banana"
    with pytest.raises(ValidationError):
        TraceRecord.model_validate(data)