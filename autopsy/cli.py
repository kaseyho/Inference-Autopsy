import asyncio
from pathlib import Path

from autopsy.client.openai_compatible import SingleRequestConfig, run_single_request
from autopsy.fake.generate import generate_fake_trace_file
from autopsy.metrics.summary import summarize_trace_file
from autopsy.traces.jsonl import write_jsonl

import typer

app = typer.Typer(help="Inference Autopsy CLI.")

@app.command("generate-fake")
def generate_fake(
    output: Path = typer.Option(..., "--output", help="Path to write JSONL traces."),
    requests: int = typer.Option(100, "--requests", help="Number of fake requests."),
    seed: int = typer.Option(7, "--seed", help="Random seed for deterministic output."),
) -> None:
    """Generate fake trace records for local dev"""
    generate_fake_trace_file(path=output, count=requests, seed=seed)
    typer.echo(f"Wrote {requests} fake trace records to {output}")

@app.command("summarize")
def summarize(trace_file: Path) -> None:
    """Summarize a JSONL trace file."""
    summary = summarize_trace_file(trace_file)
    typer.echo(f"Trace file: {trace_file}")
    typer.echo(f"Requests: {summary['total_requests']}")
    typer.echo(f"Success: {summary['success_count']}")
    typer.echo(f"Timeouts: {summary['timeout_count']}")
    typer.echo(f"Partials: {summary['partial_count']}")
    typer.echo(f"Errors: {summary['error_count']}")
    typer.echo(f"Error rate: {summary['error_rate']:.2%}")
    typer.echo(f"TTFT p50: {summary['ttft_p50_ms']} ms")
    typer.echo(f"TTFT p95: {summary['ttft_p95_ms']} ms")
    typer.echo(f"Request latency p95: {summary['request_latency_p95_ms']} ms")


@app.command("single")
def single(
    base_url: str = typer.Option(..., "--base-url", help="OpenAI-compatible base URL."),
    model: str = typer.Option(..., "--model", help="Model name to request."),
    prompt: str = typer.Option(..., "--prompt", help="User prompt to send."),
    output: Path | None = typer.Option(None, "--output", help="Optional JSONL trace output."),
    api_key: str | None = typer.Option(None, "--api-key", help="Optional bearer API key."),
    temperature: float = typer.Option(0.2, "--temperature", help="Sampling temperature."),
    max_tokens: int = typer.Option(128, "--max-tokens", help="Maximum output tokens."),
    timeout_seconds: float = typer.Option(30.0, "--timeout", help="Request timeout in seconds."),
    stream: bool = typer.Option(True, "--stream/--no-stream", help="Use streaming response mode."),
) -> None:
    """Run one OpenAI-compatible chat completion and emit one trace."""
    config = SingleRequestConfig(
        base_url=base_url,
        model=model,
        prompt=prompt,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds,
        stream=stream,
    )
    record = asyncio.run(run_single_request(config))
    if output is not None:
        write_jsonl(output, [record])

    typer.echo(f"Status: {record.status}")
    typer.echo(f"Output tokens: {record.output_tokens}")
    typer.echo(f"TTFB: {record.metrics.ttfb_ms} ms")
    typer.echo(f"TTFT: {record.metrics.ttft_ms} ms")
    typer.echo(f"Latency: {record.metrics.request_latency_ms} ms")
    if record.finish_reason:
        typer.echo(f"Finish reason: {record.finish_reason}")
    if record.error is not None:
        typer.echo(f"Error: {record.error.error_type}: {record.error.message}")
    if output is not None:
        typer.echo(f"Wrote trace to {output}")
