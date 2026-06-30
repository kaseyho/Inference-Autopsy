import asyncio

import httpx

from autopsy.cli import _parse_concurrency
from autopsy.runner.workload_runner import BenchRunConfig, run_benchmark
from autopsy.traces.jsonl import read_jsonl
from autopsy.traces.schema import LoadMode, RequestStatus


def test_parse_concurrency_values() -> None:
    assert _parse_concurrency("1, 4,8") == [1, 4, 8]


def test_benchmark_runner_writes_traces_for_each_concurrency_level(tmp_path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        content = "\n\n".join(
            [
                'data: {"choices":[{"delta":{"role":"assistant"}}]}',
                'data: {"choices":[{"delta":{"content":"Hello"}}]}',
                'data: {"choices":[{"finish_reason":"stop","delta":{}}]}',
                "data: [DONE]",
            ]
        )
        return httpx.Response(200, content=content.encode("utf-8"))

    output = tmp_path / "bench.jsonl"
    result = asyncio.run(
        run_benchmark(
            BenchRunConfig(
                base_url="http://testserver/v1",
                model="fake-model",
                profile="short-chat",
                concurrency_values=[1, 2],
                max_requests=2,
                output=output,
            ),
            transport=httpx.MockTransport(handler),
        )
    )
    records = read_jsonl(output)

    assert result.progress.completed == 4
    assert result.progress.success == 4
    assert len(records) == 4
    assert {record.run_id for record in records} == {result.run_id}
    assert {record.concurrency for record in records} == {1, 2}
    assert [record.request_sequence_index for record in records] == [0, 1, 2, 3]
    assert all(record.status == RequestStatus.SUCCESS for record in records)
    assert all(record.load_mode == LoadMode.CLOSED_LOOP for record in records)
    assert all(record.profile == "short-chat" for record in records)


def test_benchmark_runner_preserves_provider_error_trace(tmp_path) -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": {"message": "boom"}})

    output = tmp_path / "errors.jsonl"
    result = asyncio.run(
        run_benchmark(
            BenchRunConfig(
                base_url="http://testserver/v1",
                model="fake-model",
                profile="short-chat",
                concurrency_values=[2],
                max_requests=3,
                output=output,
            ),
            transport=httpx.MockTransport(handler),
        )
    )
    records = read_jsonl(output)

    assert result.progress.completed == 3
    assert result.progress.error == 3
    assert len(records) == 3
    assert all(record.status == RequestStatus.ERROR for record in records)
    assert all(record.error is not None for record in records)
    assert all(record.error.provider_status_code == 500 for record in records)
