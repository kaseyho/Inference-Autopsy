import random
from pathlib import Path

from autopsy.traces.jsonl import write_jsonl
from autopsy.traces.schema import (
    CacheMode,
    ErrorInfo,
    LoadMode,
    PromptRecordingMode,
    RequestMetrics,
    RequestStatus,
    ReplayInfo,
    Timings,
    TraceRecord,
)

# Create TraceRecord objects
def generate_fake_records(count: int = 100, seed: int = 7) -> list[TraceRecord]:
    rng = random.Random(seed)
    records: list[TraceRecord] = []
    for index in range(count):
        scenario = _choose_scenario(index)
        records.append(_make_record(index=index, scenario=scenario, rng=rng))
    return records


# Write TraceRecord objects to JSONL
def generate_fake_trace_file(path: Path, count: int = 100, seed: int = 7) -> None:
    records = generate_fake_records(count=count, seed=seed)
    write_jsonl(path, records)


def _choose_scenario(index: int) -> str:
    if index % 25 == 0:
        return "timeout_before_first_byte"
    if index % 17 == 0:
        return "partial_timeout_after_first_token"
    if index % 13 == 0:
        return "provider_error"
    if index % 7 == 0:
        return "stream_stall"
    if index % 5 == 0:
        return "slow_decode"
    if index % 3 == 0:
        return "high_ttft"
    return "healthy_success"


def _make_record(index: int, scenario: str, rng: random.Random) -> TraceRecord:
    run_id = "run_fake_001"
    request_id = f"req_{index:05d}"
    input_tokens = 120 + (index % 8) * 96
    output_tokens = 24 + (index % 6) * 8
    concurrency = 1 + (index % 4)

    first_byte: float | None = 70 + rng.randint(0, 35)
    first_token: float | None = first_byte + 80 + rng.randint(0, 60)
    token_gap = 32 + rng.randint(0, 16)
    status = RequestStatus.SUCCESS
    finish_reason: str | None = "stop"
    error: ErrorInfo | None = None

    if scenario == "high_ttft":
        input_tokens += 2400
        first_token = first_byte + 780 + rng.randint(0, 180)
    elif scenario == "slow_decode":
        output_tokens += 48
        token_gap = 95 + rng.randint(0, 30)
    elif scenario == "stream_stall":
        output_tokens += 16
        token_gap = 38 + rng.randint(0, 12)
    elif scenario == "timeout_before_first_byte":
        first_byte = None
        first_token = None
        output_tokens = 0
        status = RequestStatus.TIMEOUT
        finish_reason = None
        error = ErrorInfo(
            error_type="timeout",
            message="Request timed out before first byte.",
            retryable=True,
        )
    elif scenario == "partial_timeout_after_first_token":
        output_tokens = 8
        status = RequestStatus.PARTIAL
        finish_reason = None
        error = ErrorInfo(
            error_type="timeout",
            message="Request timed out after partial streamed output.",
            retryable=True,
            occurred_after_first_byte=True,
            occurred_after_first_token=True,
        )
    elif scenario == "provider_error":
        first_token = None
        output_tokens = 0
        status = RequestStatus.ERROR
        finish_reason = None
        error = ErrorInfo(
            error_type="provider_error",
            message="Provider returned a synthetic 500 error.",
            provider_status_code=500,
            retryable=True,
            occurred_after_first_byte=True,
        )

    token_times = _make_token_times(
        first_token=first_token,
        output_tokens=output_tokens,
        token_gap=token_gap,
        scenario=scenario,
    )
    request_end = _request_end(
        first_byte=first_byte,
        first_token=first_token,
        token_times=token_times,
        scenario=scenario,
    )

    timings = Timings(
        request_start=0.0,
        first_byte=first_byte,
        first_token=first_token,
        request_end=request_end,
    )
    metrics = _make_metrics(
        timings=timings,
        token_times=token_times,
        output_tokens=output_tokens,
    )

    return TraceRecord(
        run_id=run_id,
        request_id=request_id,
        request_sequence_index=index,
        profile=_profile_for_scenario(scenario),
        model="fake-model",
        base_url_hash="endpoint_fake",
        load_mode=LoadMode.CLOSED_LOOP,
        concurrency=concurrency,
        cache_mode=CacheMode.NONE,
        prompt_recording_mode=PromptRecordingMode.HASH_ONLY,
        input_tokens_estimated=input_tokens,
        output_tokens=output_tokens,
        streaming=True,
        status=status,
        finish_reason=finish_reason,
        timings_ms=timings,
        token_times_ms=token_times,
        metrics=metrics,
        replay=_replay_info(index=index, scenario=scenario, input_tokens=input_tokens),
        error=error,
    )


def _make_token_times(
    first_token: float | None,
    output_tokens: int,
    token_gap: int,
    scenario: str,
) -> list[float]:
    if first_token is None or output_tokens == 0:
        return []

    token_times: list[float] = []
    current = first_token
    for token_index in range(output_tokens):
        if scenario == "stream_stall" and token_index == max(1, output_tokens // 2):
            current += 850
        token_times.append(float(current))
        current += token_gap
    return token_times


def _request_end(
    first_byte: float | None,
    first_token: float | None,
    token_times: list[float],
    scenario: str,
) -> float | None:
    if scenario == "timeout_before_first_byte":
        return 10_000.0
    if token_times:
        return token_times[-1] + 45.0
    if first_token is not None:
        return first_token + 200.0
    if first_byte is not None:
        return first_byte + 120.0
    return None


def _make_metrics(
    timings: Timings,
    token_times: list[float],
    output_tokens: int,
) -> RequestMetrics:
    itls = [
        token_times[index] - token_times[index - 1]
        for index in range(1, len(token_times))
    ]
    request_latency = timings.request_end
    output_tps = None
    if output_tokens and timings.first_token is not None and timings.request_end is not None:
        generation_seconds = max((timings.request_end - timings.first_token) / 1000, 0.001)
        output_tps = output_tokens / generation_seconds

    return RequestMetrics(
        ttfb_ms=timings.first_byte,
        ttft_ms=timings.first_token,
        request_latency_ms=request_latency,
        itl_mean_ms=(sum(itls) / len(itls)) if itls else None,
        itl_p95_ms=_percentile(itls, 0.95),
        output_tps=output_tps,
        stall_count=sum(1 for gap in itls if gap >= 500),
    )


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * percentile)
    return ordered[index]


def _profile_for_scenario(scenario: str) -> str:
    if scenario == "high_ttft":
        return "rag-long"
    if scenario == "slow_decode":
        return "code-completion"
    if scenario == "stream_stall":
        return "mixed-realistic"
    return "short-chat"


def _replay_info(index: int, scenario: str, input_tokens: int) -> ReplayInfo:
    return ReplayInfo(
        messages_hash=f"msg_fake_{index:05d}",
        prompt_family=scenario,
        template_id="fake_trace_v1",
        template_seed=index,
        shape={
            "input_tokens_estimated": input_tokens,
            "scenario": scenario,
        },
    )
