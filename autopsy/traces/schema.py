# Enums for controlled string values
# Pydantic models for structured trace data
# TraceRecord model representing 1 JSONL line

from enum import StrEnum
from pydantic import BaseModel, Field

class RequestStatus(StrEnum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    PARTIAL = "partial"
    CANCELLED = "cancelled"

class LoadMode(StrEnum):
    CLOSED_LOOP = "closed_loop"
    OPEN_LOOP = "open_loop"

class CacheMode(StrEnum):
    NONE = "none"
    COLD = "cold"
    WARM = "warm"
    REPEATED_PREFIX = "repeated_prefix"
    REPEATED_EXACT = "repeated_exact"

class PromptRecordingMode(StrEnum):
    FULL = "full"
    HASH_ONLY = "hash_only"
    TEMPLATE_REFERENCE = "template_reference"

class Timings(BaseModel):
    request_start: float = 0.0
    first_byte: float | None = None
    first_token: float | None = None
    request_end: float | None = None

class RequestMetrics(BaseModel):
    ttfb_ms: float | None = None
    ttft_ms: float | None = None
    request_latency_ms : float | None = None
    itl_mean_ms: float | None = None
    itl_p95_ms: float | None = None
    output_tps: float | None = None
    stall_count: int = 0

class ReplayInfo(BaseModel):
    messages_hash: str | None = None
    prompt_family: str | None = None
    prefix_group: str | None = None
    template_id: str | None = None
    template_seed: int | None = None
    shape: dict[str, int | float | str] = Field(default_factory=dict)


class ErrorInfo(BaseModel):
    error_type: str
    message: str
    provider_status_code: int | None = None
    retryable: bool = False
    occurred_after_first_byte: bool = False
    occurred_after_first_token: bool = False

class TraceRecord(BaseModel):
    schema_version: str = "0.2"
    run_id: str
    request_id: str
    request_sequence_index: int = Field(ge=0)
    profile: str
    model: str
    base_url_hash: str
    load_mode: LoadMode
    concurrency: int | None = Field(default=None, ge=1)
    request_rate: float | None = Field(default=None, gt=0)
    cache_mode: CacheMode = CacheMode.NONE
    prompt_recording_mode: PromptRecordingMode
    input_tokens_estimated: int = Field(ge=0)
    input_token_count_method: str = "estimated"
    output_tokens: int = Field(ge=0)
    streaming: bool = True
    status: RequestStatus
    finish_reason: str | None = None
    attempt: int = Field(default=1, ge=1)
    retry_count: int = Field(default=0, ge=0)
    timings_ms: Timings
    token_times_ms: list[float] = Field(default_factory=list)
    metrics: RequestMetrics
    replay: ReplayInfo = Field(default_factory=ReplayInfo)
    error: ErrorInfo | None = None