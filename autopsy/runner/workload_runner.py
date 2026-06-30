import asyncio
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from time import perf_counter
from uuid import uuid4

import httpx

from autopsy.client.openai_compatible import (
    RequestTraceContext,
    SingleRequestConfig,
    run_single_request,
)
from autopsy.traces.derive import derive_request_metrics
from autopsy.traces.jsonl import append_jsonl_record, write_jsonl
from autopsy.traces.schema import (
    CacheMode,
    ErrorInfo,
    LoadMode,
    PromptRecordingMode,
    RequestStatus,
    Timings,
    TraceRecord,
)
from autopsy.workloads.profiles import GeneratedPrompt, generate_prompt, get_profile


@dataclass(frozen=True)
class BenchRunConfig:
    base_url: str
    model: str
    profile: str
    concurrency_values: list[int]
    max_requests: int
    output: Path
    api_key: str | None = None
    timeout_seconds: float = 30.0
    stream: bool = True


@dataclass
class BenchProgress:
    completed: int = 0
    success: int = 0
    error: int = 0
    timeout: int = 0
    partial: int = 0
    cancelled: int = 0

    def record(self, status: RequestStatus) -> None:
        """Update simple run counters from one completed trace."""
        self.completed += 1
        if status == RequestStatus.SUCCESS:
            self.success += 1
        elif status == RequestStatus.ERROR:
            self.error += 1
        elif status == RequestStatus.TIMEOUT:
            self.timeout += 1
        elif status == RequestStatus.PARTIAL:
            self.partial += 1
        elif status == RequestStatus.CANCELLED:
            self.cancelled += 1


@dataclass(frozen=True)
class BenchRunResult:
    run_id: str
    output: Path
    progress: BenchProgress
    elapsed_seconds: float


async def run_benchmark(
    config: BenchRunConfig,
    transport: httpx.AsyncBaseTransport | None = None,
) -> BenchRunResult:
    """Run closed-loop benchmark levels and append traces as they finish."""
    _validate_config(config)
    run_id = f"run_{uuid4().hex[:12]}"
    progress = BenchProgress()
    write_lock = asyncio.Lock()
    progress_lock = asyncio.Lock()
    next_sequence_index = 0
    start = perf_counter()

    # Start each benchmark output from a clean file. Individual traces are then
    # appended as they finish, so interrupted runs still preserve completed work.
    write_jsonl(config.output, [])

    timeout = httpx.Timeout(config.timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        for concurrency in config.concurrency_values:
            next_sequence_index = await _run_concurrency_level(
                config=config,
                run_id=run_id,
                concurrency=concurrency,
                start_sequence_index=next_sequence_index,
                client=client,
                write_lock=write_lock,
                progress_lock=progress_lock,
                progress=progress,
            )

    return BenchRunResult(
        run_id=run_id,
        output=config.output,
        progress=progress,
        elapsed_seconds=perf_counter() - start,
    )


async def _run_concurrency_level(
    config: BenchRunConfig,
    run_id: str,
    concurrency: int,
    start_sequence_index: int,
    client: httpx.AsyncClient,
    write_lock: asyncio.Lock,
    progress_lock: asyncio.Lock,
    progress: BenchProgress,
) -> int:
    next_index = start_sequence_index
    assigned = 0
    assignment_lock = asyncio.Lock()

    async def claim_index() -> int | None:
        nonlocal next_index, assigned
        async with assignment_lock:
            if assigned >= config.max_requests:
                return None
            sequence_index = next_index
            next_index += 1
            assigned += 1
            return sequence_index

    workers = [
        asyncio.create_task(
            _worker(
                worker_id=worker_id,
                claim_index=claim_index,
                config=config,
                run_id=run_id,
                concurrency=concurrency,
                client=client,
                write_lock=write_lock,
                progress_lock=progress_lock,
                progress=progress,
            )
        )
        for worker_id in range(concurrency)
    ]
    await asyncio.gather(*workers)
    return next_index


async def _worker(
    worker_id: int,
    claim_index: Callable[[], Awaitable[int | None]],
    config: BenchRunConfig,
    run_id: str,
    concurrency: int,
    client: httpx.AsyncClient,
    write_lock: asyncio.Lock,
    progress_lock: asyncio.Lock,
    progress: BenchProgress,
) -> None:
    profile = get_profile(config.profile)

    while True:
        sequence_index = await claim_index()
        if sequence_index is None:
            return

        generated = generate_prompt(profile, sequence_index)
        trace_context = _trace_context(
            generated=generated,
            run_id=run_id,
            sequence_index=sequence_index,
            profile_name=config.profile,
            concurrency=concurrency,
            worker_id=worker_id,
        )

        try:
            record = await run_single_request(
                config=SingleRequestConfig(
                    base_url=config.base_url,
                    model=config.model,
                    prompt=generated.prompt,
                    api_key=config.api_key,
                    temperature=profile.temperature,
                    max_tokens=profile.max_tokens,
                    timeout_seconds=config.timeout_seconds,
                    stream=config.stream,
                ),
                trace_context=trace_context,
                client=client,
            )
        except Exception as exc:
            record = _unexpected_error_record(
                config=config,
                generated=generated,
                trace_context=trace_context,
                error=exc,
            )

        async with write_lock:
            append_jsonl_record(config.output, record)

        async with progress_lock:
            progress.record(record.status)
            print(
                f"Completed {progress.completed} | "
                f"success={progress.success} error={progress.error} "
                f"timeout={progress.timeout} partial={progress.partial}"
            )


def _trace_context(
    generated: GeneratedPrompt,
    run_id: str,
    sequence_index: int,
    profile_name: str,
    concurrency: int,
    worker_id: int,
) -> RequestTraceContext:
    shape = dict(generated.shape)
    shape["worker_id"] = worker_id

    return RequestTraceContext(
        run_id=run_id,
        request_id=f"req_{sequence_index:06d}",
        request_sequence_index=sequence_index,
        profile=profile_name,
        load_mode=LoadMode.CLOSED_LOOP,
        concurrency=concurrency,
        cache_mode=CacheMode.NONE,
        prompt_family=generated.prompt_family,
        template_id=generated.template_id,
        template_seed=generated.template_seed,
        shape=shape,
    )


def _unexpected_error_record(
    config: BenchRunConfig,
    generated: GeneratedPrompt,
    trace_context: RequestTraceContext,
    error: Exception,
) -> TraceRecord:
    timings = Timings(request_end=0.0)
    metrics = derive_request_metrics(timings=timings, token_times=[], output_tokens=0)
    shape = dict(trace_context.shape or {})
    shape.setdefault("temperature", get_profile(config.profile).temperature)
    shape.setdefault("max_tokens", get_profile(config.profile).max_tokens)
    shape.setdefault("stream", str(config.stream))

    return TraceRecord(
        run_id=trace_context.run_id,
        request_id=trace_context.request_id,
        request_sequence_index=trace_context.request_sequence_index,
        profile=trace_context.profile,
        model=config.model,
        base_url_hash="endpoint_unavailable",
        load_mode=trace_context.load_mode,
        concurrency=trace_context.concurrency,
        cache_mode=trace_context.cache_mode,
        prompt_recording_mode=PromptRecordingMode.HASH_ONLY,
        input_tokens_estimated=len(generated.prompt.split()),
        output_tokens=0,
        streaming=config.stream,
        status=RequestStatus.ERROR,
        timings_ms=timings,
        token_times_ms=[],
        metrics=metrics,
        replay={
            "messages_hash": None,
            "prompt_family": trace_context.prompt_family,
            "template_id": trace_context.template_id,
            "template_seed": trace_context.template_seed,
            "shape": shape,
        },
        error=ErrorInfo(
            error_type="runner_error",
            message=str(error),
            retryable=False,
        ),
    )


def _validate_config(config: BenchRunConfig) -> None:
    if config.max_requests < 1:
        raise ValueError("max_requests must be at least 1.")
    if not config.concurrency_values:
        raise ValueError("At least one concurrency level is required.")
    if any(level < 1 for level in config.concurrency_values):
        raise ValueError("Concurrency levels must be positive integers.")
    get_profile(config.profile)
