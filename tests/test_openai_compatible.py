import asyncio
import json

import httpx

from autopsy.client.openai_compatible import SingleRequestConfig, run_single_request
from autopsy.traces.schema import RequestStatus


def test_streaming_single_request_maps_tokens_to_trace() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        assert payload["stream"] is True
        content = "\n\n".join(
            [
                'data: {"choices":[{"delta":{"role":"assistant"}}]}',
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                'data: {"choices":[{"delta":{"content":" world"}}]}',
                'data: {"choices":[{"finish_reason":"stop","delta":{}}]}',
                "data: [DONE]",
            ]
        )
        return httpx.Response(200, content=content.encode("utf-8"))

    record = asyncio.run(
        run_single_request(
            SingleRequestConfig(
                base_url="http://testserver/v1",
                model="fake-model",
                prompt="Say hello.",
            ),
            transport=httpx.MockTransport(handler),
        )
    )

    assert record.status == RequestStatus.SUCCESS
    assert record.streaming is True
    assert record.metrics.ttfb_ms is not None
    assert record.metrics.ttft_ms is not None
    assert len(record.token_times_ms) == 2
    assert record.output_tokens == 2
    assert record.finish_reason == "stop"


def test_streaming_malformed_chunk_preserves_partial_trace() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        content = "\n\n".join(
            [
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                "data: {bad",
            ]
        )
        return httpx.Response(200, content=content.encode("utf-8"))

    record = asyncio.run(
        run_single_request(
            SingleRequestConfig(
                base_url="http://testserver",
                model="fake-model",
                prompt="Say hello.",
            ),
            transport=httpx.MockTransport(handler),
        )
    )

    assert record.status == RequestStatus.PARTIAL
    assert record.metrics.ttft_ms is not None
    assert record.output_tokens == 1
    assert record.error is not None
    assert record.error.error_type == "stream_parse_error"


def test_provider_error_maps_to_error_trace() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "boom"}})

    record = asyncio.run(
        run_single_request(
            SingleRequestConfig(
                base_url="http://testserver/v1",
                model="fake-model",
                prompt="Say hello.",
            ),
            transport=httpx.MockTransport(handler),
        )
    )

    assert record.status == RequestStatus.ERROR
    assert record.error is not None
    assert record.error.provider_status_code == 500
