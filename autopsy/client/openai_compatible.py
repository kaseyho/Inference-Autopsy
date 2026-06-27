import hashlib
import time
from dataclasses import dataclass
from uuid import uuid4

import httpx

from autopsy.client.stream_parser import StreamEventType, parse_sse_line
from autopsy.traces.derive import derive_request_metrics
from autopsy.traces.schema import (
    CacheMode,
    ErrorInfo,
    LoadMode,
    PromptRecordingMode,
    ReplayInfo,
    RequestStatus,
    Timings,
    TraceRecord,
)


@dataclass(frozen=True)
class SingleRequestConfig:
    base_url: str
    model: str
    prompt: str
    api_key: str | None = None
    temperature: float = 0.2
    max_tokens: int = 128
    timeout_seconds: float = 30.0
    stream: bool = True


async def run_single_request(
    config: SingleRequestConfig,
    transport: httpx.AsyncBaseTransport | None = None,
) -> TraceRecord:
    timeout = httpx.Timeout(config.timeout_seconds)
    async with httpx.AsyncClient(timeout=timeout, transport=transport) as client:
        if config.stream:
            return await _run_streaming_request(config=config, client=client)
        return await _run_non_streaming_request(config=config, client=client)


async def _run_streaming_request(
    config: SingleRequestConfig,
    client: httpx.AsyncClient,
) -> TraceRecord:
    start = time.perf_counter()
    first_byte: float | None = None
    first_token: float | None = None
    request_end: float | None = None
    token_times: list[float] = []
    output_parts: list[str] = []
    finish_reason: str | None = None
    status = RequestStatus.SUCCESS
    error: ErrorInfo | None = None

    try:
        async with client.stream(
            "POST",
            _chat_completions_url(config.base_url),
            headers=_headers(config.api_key),
            json=_payload(config),
        ) as response:
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                first_byte = _elapsed_ms(start)
                request_end = first_byte
                status = RequestStatus.ERROR
                error = _http_status_error(exc, first_byte, first_token)
                return _trace_record(
                    config=config,
                    status=status,
                    timings=Timings(
                        first_byte=first_byte,
                        first_token=first_token,
                        request_end=request_end,
                    ),
                    token_times=token_times,
                    output_tokens=0,
                    finish_reason=finish_reason,
                    error=error,
                )

            async for line in response.aiter_lines():
                now = _elapsed_ms(start)
                if first_byte is None:
                    first_byte = now

                event = parse_sse_line(line)
                if event.event_type == StreamEventType.CONTENT_CHUNK:
                    if first_token is None:
                        first_token = now
                    token_times.append(now)
                    output_parts.append(event.content or "")
                elif event.event_type == StreamEventType.FINISH_CHUNK:
                    finish_reason = event.finish_reason
                elif event.event_type == StreamEventType.DONE_MARKER:
                    request_end = now
                    break
                elif event.event_type == StreamEventType.MALFORMED_CHUNK:
                    request_end = now
                    status = RequestStatus.PARTIAL if token_times else RequestStatus.ERROR
                    error = ErrorInfo(
                        error_type="stream_parse_error",
                        message=event.error_message or "Malformed streaming chunk.",
                        retryable=False,
                        occurred_after_first_byte=first_byte is not None,
                        occurred_after_first_token=first_token is not None,
                    )
                    break

            if request_end is None:
                request_end = _elapsed_ms(start)
                if status == RequestStatus.SUCCESS and finish_reason is None:
                    status = RequestStatus.PARTIAL
                    error = ErrorInfo(
                        error_type="stream_ended_without_done",
                        message="Stream ended before a done marker or finish reason.",
                        retryable=True,
                        occurred_after_first_byte=first_byte is not None,
                        occurred_after_first_token=first_token is not None,
                    )
    except httpx.TimeoutException as exc:
        request_end = _elapsed_ms(start)
        status = RequestStatus.PARTIAL if token_times else RequestStatus.TIMEOUT
        error = _timeout_error(exc, first_byte, first_token)
    except httpx.RequestError as exc:
        request_end = _elapsed_ms(start)
        status = RequestStatus.ERROR
        error = ErrorInfo(
            error_type="request_error",
            message=str(exc),
            retryable=True,
            occurred_after_first_byte=first_byte is not None,
            occurred_after_first_token=first_token is not None,
        )

    timings = Timings(
        first_byte=first_byte,
        first_token=first_token,
        request_end=request_end,
    )
    return _trace_record(
        config=config,
        status=status,
        timings=timings,
        token_times=token_times,
        output_tokens=len(output_parts),
        finish_reason=finish_reason,
        error=error,
    )


async def _run_non_streaming_request(
    config: SingleRequestConfig,
    client: httpx.AsyncClient,
) -> TraceRecord:
    start = time.perf_counter()
    first_byte: float | None = None
    request_end: float | None = None
    finish_reason: str | None = None
    output_tokens = 0
    status = RequestStatus.SUCCESS
    error: ErrorInfo | None = None

    try:
        response = await client.post(
            _chat_completions_url(config.base_url),
            headers=_headers(config.api_key),
            json=_payload(config),
        )
        first_byte = _elapsed_ms(start)
        request_end = first_byte
        response.raise_for_status()
        data = response.json()
        choice = (data.get("choices") or [{}])[0]
        if isinstance(choice, dict):
            finish_reason = choice.get("finish_reason")
            message = choice.get("message") or {}
            content = message.get("content") if isinstance(message, dict) else None
            output_tokens = _estimate_tokens(content or "")
    except httpx.HTTPStatusError as exc:
        status = RequestStatus.ERROR
        error = _http_status_error(exc, first_byte, None)
    except httpx.TimeoutException as exc:
        request_end = _elapsed_ms(start)
        status = RequestStatus.TIMEOUT
        error = _timeout_error(exc, first_byte, None)
    except (httpx.RequestError, ValueError, KeyError, TypeError) as exc:
        request_end = request_end or _elapsed_ms(start)
        status = RequestStatus.ERROR
        error = ErrorInfo(
            error_type="response_error",
            message=str(exc),
            retryable=isinstance(exc, httpx.RequestError),
            occurred_after_first_byte=first_byte is not None,
        )

    timings = Timings(first_byte=first_byte, first_token=None, request_end=request_end)
    return _trace_record(
        config=config,
        status=status,
        timings=timings,
        token_times=[],
        output_tokens=output_tokens,
        finish_reason=finish_reason,
        error=error,
    )


def _trace_record(
    config: SingleRequestConfig,
    status: RequestStatus,
    timings: Timings,
    token_times: list[float],
    output_tokens: int,
    finish_reason: str | None,
    error: ErrorInfo | None,
) -> TraceRecord:
    metrics = derive_request_metrics(
        timings=timings,
        token_times=token_times,
        output_tokens=output_tokens,
    )
    return TraceRecord(
        run_id=f"run_single_{uuid4().hex[:12]}",
        request_id="req_00000",
        request_sequence_index=0,
        profile="single",
        model=config.model,
        base_url_hash=_hash_base_url(config.base_url),
        load_mode=LoadMode.CLOSED_LOOP,
        concurrency=1,
        cache_mode=CacheMode.NONE,
        prompt_recording_mode=PromptRecordingMode.HASH_ONLY,
        input_tokens_estimated=_estimate_tokens(config.prompt),
        output_tokens=output_tokens,
        streaming=config.stream,
        status=status,
        finish_reason=finish_reason,
        timings_ms=timings,
        token_times_ms=token_times,
        metrics=metrics,
        replay=ReplayInfo(
            messages_hash=_hash_text(config.prompt),
            prompt_family="single",
            shape={
                "temperature": config.temperature,
                "max_tokens": config.max_tokens,
                "stream": str(config.stream),
            },
        ),
        error=error,
    )


def _payload(config: SingleRequestConfig) -> dict[str, object]:
    return {
        "model": config.model,
        "messages": [{"role": "user", "content": config.prompt}],
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
        "stream": config.stream,
    }


def _headers(api_key: str | None) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def _chat_completions_url(base_url: str) -> str:
    normalized = base_url.rstrip("/")
    if normalized.endswith("/v1"):
        return f"{normalized}/chat/completions"
    return f"{normalized}/v1/chat/completions"


def _elapsed_ms(start: float) -> float:
    return (time.perf_counter() - start) * 1000


def _estimate_tokens(text: str) -> int:
    return len(text.split()) if text else 0


def _hash_base_url(base_url: str) -> str:
    return f"endpoint_{_hash_text(base_url)[:12]}"


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _http_status_error(
    exc: httpx.HTTPStatusError,
    first_byte: float | None,
    first_token: float | None,
) -> ErrorInfo:
    status_code = exc.response.status_code
    return ErrorInfo(
        error_type="provider_error",
        message=f"Provider returned HTTP {status_code}.",
        provider_status_code=status_code,
        retryable=status_code == 429 or status_code >= 500,
        occurred_after_first_byte=first_byte is not None,
        occurred_after_first_token=first_token is not None,
    )


def _timeout_error(
    exc: httpx.TimeoutException,
    first_byte: float | None,
    first_token: float | None,
) -> ErrorInfo:
    return ErrorInfo(
        error_type="timeout",
        message=str(exc) or "Request timed out.",
        retryable=True,
        occurred_after_first_byte=first_byte is not None,
        occurred_after_first_token=first_token is not None,
    )
