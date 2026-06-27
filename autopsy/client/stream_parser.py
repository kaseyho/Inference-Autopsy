import json
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class StreamEventType(StrEnum):
    EMPTY_LINE = "empty_line"
    ROLE_CHUNK = "role_chunk"
    CONTENT_CHUNK = "content_chunk"
    FINISH_CHUNK = "finish_chunk"
    DONE_MARKER = "done_marker"
    UNKNOWN_CHUNK = "unknown_chunk"
    MALFORMED_CHUNK = "malformed_chunk"


@dataclass(frozen=True)
class StreamEvent:
    event_type: StreamEventType
    content: str | None = None
    role: str | None = None
    finish_reason: str | None = None
    error_message: str | None = None


def parse_sse_line(line: str) -> StreamEvent:
    stripped = line.strip()
    if not stripped:
        return StreamEvent(StreamEventType.EMPTY_LINE)

    if stripped.startswith("data:"):
        payload = stripped.removeprefix("data:").strip()
    else:
        payload = stripped

    if payload == "[DONE]":
        return StreamEvent(StreamEventType.DONE_MARKER)

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        return StreamEvent(
            StreamEventType.MALFORMED_CHUNK,
            error_message=f"Malformed SSE JSON chunk: {exc.msg}",
        )

    return _event_from_payload(data)


def _event_from_payload(data: Any) -> StreamEvent:
    choices = data.get("choices") if isinstance(data, dict) else None
    if not isinstance(choices, list) or not choices:
        return StreamEvent(StreamEventType.UNKNOWN_CHUNK)

    choice = choices[0]
    if not isinstance(choice, dict):
        return StreamEvent(StreamEventType.UNKNOWN_CHUNK)

    finish_reason = choice.get("finish_reason")
    delta = choice.get("delta") or {}
    if not isinstance(delta, dict):
        delta = {}

    content = delta.get("content")
    if isinstance(content, str) and content:
        return StreamEvent(StreamEventType.CONTENT_CHUNK, content=content)

    if finish_reason is not None:
        return StreamEvent(StreamEventType.FINISH_CHUNK, finish_reason=str(finish_reason))

    role = delta.get("role")
    if isinstance(role, str):
        return StreamEvent(StreamEventType.ROLE_CHUNK, role=role)

    return StreamEvent(StreamEventType.UNKNOWN_CHUNK)
