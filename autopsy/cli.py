# - Create a Typer App
# - Register `generate-fake`
# - Register `summarize` 
#  - Call functions from other modules

from pathlib import Path
from autopsy.fake.generate import generate_fake_trace_file
from autopsy.metrics.summary import summarize_trace_file

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