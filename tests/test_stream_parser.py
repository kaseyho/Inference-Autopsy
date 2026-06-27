from autopsy.client.stream_parser import StreamEventType, parse_sse_line


def test_parse_empty_line() -> None:
    event = parse_sse_line("")

    assert event.event_type == StreamEventType.EMPTY_LINE


def test_parse_role_chunk() -> None:
    event = parse_sse_line('data: {"choices":[{"delta":{"role":"assistant"}}]}')

    assert event.event_type == StreamEventType.ROLE_CHUNK
    assert event.role == "assistant"


def test_parse_content_chunk() -> None:
    event = parse_sse_line('data: {"choices":[{"delta":{"content":"Hello"}}]}')

    assert event.event_type == StreamEventType.CONTENT_CHUNK
    assert event.content == "Hello"


def test_parse_finish_chunk() -> None:
    event = parse_sse_line('data: {"choices":[{"finish_reason":"stop","delta":{}}]}')

    assert event.event_type == StreamEventType.FINISH_CHUNK
    assert event.finish_reason == "stop"


def test_parse_done_marker() -> None:
    event = parse_sse_line("data: [DONE]")

    assert event.event_type == StreamEventType.DONE_MARKER


def test_parse_malformed_chunk() -> None:
    event = parse_sse_line("data: {nope")

    assert event.event_type == StreamEventType.MALFORMED_CHUNK
    assert event.error_message is not None
