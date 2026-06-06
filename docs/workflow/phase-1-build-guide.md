# Phase 1 Build Guide

## Purpose

This guide explains Phase 1 slowly and concretely. It tells you what to create,
what to type, what each file is responsible for, what code shape to write, and
how to check your work.

This is a teaching guide. It is not product code.

## Reference When

Use this while building the first working version of Inference Autopsy.

## AI Agents Must Obey

Do not write product code from this guide unless explicitly asked. This guide is
for teaching, planning, and implementation sequencing.

## The Phase 1 Outcome

At the end of Phase 1, you should be able to run:

```bash
autopsy --help
autopsy generate-fake --output examples/traces/fake.jsonl
autopsy summarize examples/traces/fake.jsonl
pytest
```

Those commands prove the first spine of the project works:

```txt
CLI -> Pydantic schema -> fake TraceRecord objects -> JSONL file -> summary metrics
```

No real model endpoint is needed yet. No streaming client yet. No report yet.
Phase 1 is about making trace evidence real.

## Why the CLI Should Stay Thin

The CLI should stay thin because the CLI is just the door into the product.

The CLI should do:

- Parse command-line arguments.
- Call real functions in other modules.
- Print results.
- Return exit codes.

The CLI should not do:

- Trace schema design.
- JSONL parsing details.
- Fake trace scenario generation.
- Percentile math.
- Error-rate math.
- Report logic.

The wrong shape:

```txt
autopsy summarize
  -> reads JSONL inside cli.py
  -> calculates p95 inside cli.py
  -> counts errors inside cli.py
  -> prints output
```

The better shape:

```txt
autopsy summarize
  -> cli.py parses path
  -> jsonl.py reads TraceRecord objects
  -> summary.py computes metrics
  -> cli.py prints output
```

This matters because the same metrics will later be reused by:

- `autopsy summarize`
- `autopsy report`
- `autopsy diff`
- `autopsy export`
- tests

If the logic is trapped inside the CLI, every future command has to duplicate it
or call the CLI awkwardly. That is how projects become brittle.

Interview answer:

```txt
I kept the CLI thin because command-line parsing is not the source of truth. The
CLI delegates to reusable schema, JSONL, and metrics modules, so reports, diffs,
CI gates, and tests all use the same metric definitions.
```

## Step 0: Understand the Files You Will Create

You will create this structure:

```txt
pyproject.toml
autopsy/
  __init__.py
  cli.py
  traces/
    __init__.py
    schema.py
    jsonl.py
  fake/
    __init__.py
    generate.py
  metrics/
    __init__.py
    summary.py
tests/
  test_schema.py
  test_jsonl.py
  test_summary.py
examples/
  traces/
```

Each file has one job:

- `pyproject.toml`: declares dependencies and the `autopsy` command.
- `autopsy/cli.py`: Typer command definitions only.
- `autopsy/traces/schema.py`: Pydantic models and enums.
- `autopsy/traces/jsonl.py`: read and write trace files.
- `autopsy/fake/generate.py`: create deterministic fake traces.
- `autopsy/metrics/summary.py`: compute summary metrics from trace records.
- `tests/test_schema.py`: schema validation tests.
- `tests/test_jsonl.py`: JSONL round-trip tests.
- `tests/test_summary.py`: summary metric tests.

## Step 1: Create `pyproject.toml`

What you are doing:

You are making the repo installable as a Python package and creating a CLI entry
point named `autopsy`.

What to put in the file:

```toml
[project]
name = "inference-autopsy"
version = "0.1.0"
description = "Trace-first profiler and regression tester for AI inference systems."
requires-python = ">=3.11"
dependencies = [
  "typer>=0.12",
  "pydantic>=2",
  "rich>=13",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "ruff>=0.5",
]

[project.scripts]
autopsy = "autopsy.cli:app"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["autopsy"]
```

What this means:

- `dependencies` are packages needed to run the tool.
- `dev` dependencies are packages needed while developing.
- `project.scripts` creates the terminal command.
- `autopsy = "autopsy.cli:app"` means "load the Typer app from
  `autopsy/cli.py`."
- `packages = ["autopsy"]` tells Hatch that the Python package folder is named
  `autopsy`.

Important:

Do not run `pip install -e ".[dev]"` yet if the `autopsy/` folder does not
exist. Hatch needs the package folder to exist before it can install the project
in editable mode.

You will run the install command after Step 2.

## Step 2: Create the Package Folders

What you are doing:

You are creating Python packages. A folder becomes an importable package when it
contains `__init__.py`.

Folders to create:

```txt
autopsy/
autopsy/traces/
autopsy/fake/
autopsy/metrics/
tests/
examples/traces/
```

Files to create:

```txt
autopsy/__init__.py
autopsy/traces/__init__.py
autopsy/fake/__init__.py
autopsy/metrics/__init__.py
```

These `__init__.py` files can be empty in Phase 1.

Now create and activate the virtual environment, then install the package:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Checkpoint:

```bash
python -c "import typer, pydantic, rich; print('ok')"
```

You should see:

```txt
ok
```

Checkpoint:

```bash
python -c "import autopsy; print('ok')"
```

You should see:

```txt
ok
```

## Step 3: Create the First Typer CLI

File:

```txt
autopsy/cli.py
```

What this file should do:

- Create a Typer app.
- Register `generate-fake`.
- Register `summarize`.
- Call functions from other modules.

Code shape to write:

```python
from pathlib import Path

import typer

app = typer.Typer(help="Inference Autopsy CLI.")


@app.command("generate-fake")
def generate_fake(
    output: Path = typer.Option(..., "--output", help="Path to write JSONL traces."),
    requests: int = typer.Option(100, "--requests", help="Number of fake requests."),
    seed: int = typer.Option(7, "--seed", help="Random seed for deterministic output."),
) -> None:
    """Generate fake trace records for local development."""
    # Later this will call autopsy.fake.generate.generate_fake_trace_file.
    typer.echo(f"Would generate {requests} fake records at {output} with seed {seed}.")


@app.command("summarize")
def summarize(trace_file: Path) -> None:
    """Summarize a JSONL trace file."""
    # Later this will call autopsy.metrics.summary.summarize_trace_file.
    typer.echo(f"Would summarize {trace_file}.")
```

Why this first version is allowed:

- It proves Typer command registration.
- It proves the command names are correct.
- It gives you something to run before schema and JSONL exist.

Commands to run:

```bash
autopsy --help
autopsy generate-fake --output examples/traces/fake.jsonl
autopsy summarize examples/traces/fake.jsonl
```

Checkpoint:

- `autopsy --help` shows both commands.
- `generate-fake` prints a message.
- `summarize` prints a message.

Do not add real logic to `cli.py` yet. Keep it thin.

## Step 4: Design the Trace Schema

File:

```txt
autopsy/traces/schema.py
```

What this file should contain:

- Enums for controlled string values.
- Pydantic models for structured trace data.
- A `TraceRecord` model representing one JSONL line.

Enums to define:

```python
from enum import StrEnum


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
```

Why enums matter:

- They prevent typos like `"sucess"`.
- They make allowed values obvious.
- They make tests easier.

Models to define:

```python
from pydantic import BaseModel, Field


class Timings(BaseModel):
    request_start: float = 0.0
    first_byte: float | None = None
    first_token: float | None = None
    request_end: float | None = None


class RequestMetrics(BaseModel):
    ttfb_ms: float | None = None
    ttft_ms: float | None = None
    request_latency_ms: float | None = None
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
```

Then define `TraceRecord`:

```python
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
```

Important beginner note:

`Field(ge=0)` means "greater than or equal to zero."

`Field(gt=0)` means "greater than zero."

`None` means the value may be missing because the request failed before that
event happened.

Checkpoint:

Write a tiny test in your head:

- A success record should have `status = success` and `error = None`.
- A timeout record should have `status = timeout` and a non-null `error`.
- A timeout before first byte should allow `first_byte = None`.

## Step 5: Write Schema Tests

File:

```txt
tests/test_schema.py
```

What to test:

- A valid success record works.
- A bad enum value fails.
- Negative token counts fail.
- A timeout record can include an error.

Test shape:

```python
import pytest
from pydantic import ValidationError

from autopsy.traces.schema import (
    CacheMode,
    LoadMode,
    PromptRecordingMode,
    RequestMetrics,
    RequestStatus,
    Timings,
    TraceRecord,
)


def make_record() -> TraceRecord:
    return TraceRecord(
        run_id="run_001",
        request_id="req_001",
        request_sequence_index=0,
        profile="short-chat",
        model="fake-model",
        base_url_hash="endpoint_a",
        load_mode=LoadMode.CLOSED_LOOP,
        concurrency=1,
        cache_mode=CacheMode.NONE,
        prompt_recording_mode=PromptRecordingMode.HASH_ONLY,
        input_tokens_estimated=100,
        output_tokens=20,
        status=RequestStatus.SUCCESS,
        timings_ms=Timings(first_byte=100, first_token=150, request_end=700),
        token_times_ms=[150, 180, 210],
        metrics=RequestMetrics(ttfb_ms=100, ttft_ms=150, request_latency_ms=700),
    )


def test_valid_trace_record() -> None:
    record = make_record()
    assert record.request_id == "req_001"


def test_invalid_status_rejected() -> None:
    data = make_record().model_dump()
    data["status"] = "banana"
    with pytest.raises(ValidationError):
        TraceRecord.model_validate(data)
```

Command to run:

```bash
pytest tests/test_schema.py
```

Checkpoint:

- Tests pass.
- You understand why `"banana"` fails.

## Step 6: Build JSONL Helpers

File:

```txt
autopsy/traces/jsonl.py
```

Functions to write:

```txt
write_jsonl(path, records)
read_jsonl(path)
```

Code shape:

```python
import json
from collections.abc import Iterable
from pathlib import Path

from autopsy.traces.schema import TraceRecord


def write_jsonl(path: Path, records: Iterable[TraceRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            line = record.model_dump_json()
            file.write(line)
            file.write("\n")


def read_jsonl(path: Path) -> list[TraceRecord]:
    records: list[TraceRecord] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            try:
                records.append(TraceRecord.model_validate(data))
            except Exception as exc:
                raise ValueError(f"Invalid trace record on line {line_number}: {exc}") from exc
    return records
```

Why `read_jsonl` returns `TraceRecord` objects:

- The rest of the app should not handle raw dictionaries.
- Validation happens at the boundary.
- Metrics code can trust the shape.

Command to run after writing tests:

```bash
pytest tests/test_jsonl.py
```

## Step 7: Write JSONL Tests

File:

```txt
tests/test_jsonl.py
```

What to test:

- Write one or more records.
- Read them back.
- Confirm the request IDs match.

Test shape:

```python
from pathlib import Path

from autopsy.traces.jsonl import read_jsonl, write_jsonl
from tests.test_schema import make_record


def test_jsonl_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "trace.jsonl"
    records = [make_record()]

    write_jsonl(path, records)
    loaded = read_jsonl(path)

    assert len(loaded) == 1
    assert loaded[0].request_id == "req_001"
```

Beginner note:

`tmp_path` is a pytest fixture. Pytest gives you a temporary folder for the
test. You do not need to create it yourself.

## Step 8: Build Fake Trace Generation

File:

```txt
autopsy/fake/generate.py
```

Functions to write:

```txt
generate_fake_records(count, seed)
generate_fake_trace_file(path, count, seed)
```

The first function creates `TraceRecord` objects.

The second function writes them to JSONL.

Code shape:

```python
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
    Timings,
    TraceRecord,

)


def generate_fake_records(count: int = 100, seed: int = 7) -> list[TraceRecord]:
    rng = random.Random(seed)
    records: list[TraceRecord] = []
    for index in range(count):
        scenario = _choose_scenario(index)
        records.append(_make_record(index=index, scenario=scenario, rng=rng))
    return records


def generate_fake_trace_file(path: Path, count: int = 100, seed: int = 7) -> None:
    records = generate_fake_records(count=count, seed=seed)
    write_jsonl(path, records)
```

Scenario selection:

```python
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
```

Why this pattern is useful:

- It is deterministic.
- It creates mixed outcomes.
- It does not depend on randomness for status distribution.
- The seed can still vary timings slightly.

Record creation idea:

```txt
healthy_success:
  first_byte = about 80ms
  first_token = about 160ms
  request_end = about 900ms

high_ttft:
  first_byte = about 100ms
  first_token = about 900ms
  request_end = about 1800ms

slow_decode:
  first_byte = about 100ms
  first_token = about 180ms
  token gaps are larger

stream_stall:
  one token gap is very large

timeout_before_first_byte:
  first_byte = None
  first_token = None
  request_end = timeout value
  status = timeout
  error is present

partial_timeout_after_first_token:
  first_byte exists
  first_token exists
  some token_times exist
  request_end exists
  status = partial or timeout
  error is present
```

Important rule:

Every fake record must still validate with Pydantic.

## Step 9: Connect `generate-fake` CLI to the Fake Generator

File:

```txt
autopsy/cli.py
```

Replace the placeholder body with:

```python
from autopsy.fake.generate import generate_fake_trace_file


@app.command("generate-fake")
def generate_fake(
    output: Path = typer.Option(..., "--output", help="Path to write JSONL traces."),
    requests: int = typer.Option(100, "--requests", help="Number of fake requests."),
    seed: int = typer.Option(7, "--seed", help="Random seed for deterministic output."),
) -> None:
    """Generate fake trace records for local development."""
    generate_fake_trace_file(path=output, count=requests, seed=seed)
    typer.echo(f"Wrote {requests} fake trace records to {output}")
```

Command to run:

```bash
autopsy generate-fake --output examples/traces/fake.jsonl --requests 50
```

Checkpoint:

Open the file and confirm:

- It exists.
- It has 50 lines.
- Each line is one JSON object.
- There is no giant JSON array.

Command:

```bash
Get-Content examples/traces/fake.jsonl | Select-Object -First 3
```

## Step 10: Build Summary Metrics

File:

```txt
autopsy/metrics/summary.py
```

What this module does:

- Accepts a list of `TraceRecord`.
- Computes counts.
- Computes percentiles.
- Computes reliability rates.
- Returns a summary object or dictionary.

Start with simple helper functions:

```python
from autopsy.traces.schema import RequestStatus, TraceRecord


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = round((len(ordered) - 1) * p)
    return ordered[index]
```

Beginner note:

This percentile function is simple and good enough for Phase 1. Later you can
make it more statistically precise.

Summary shape:

```python
def summarize_records(records: list[TraceRecord]) -> dict[str, object]:
    total = len(records)
    success_count = sum(1 for r in records if r.status == RequestStatus.SUCCESS)
    timeout_count = sum(1 for r in records if r.status == RequestStatus.TIMEOUT)
    partial_count = sum(1 for r in records if r.status == RequestStatus.PARTIAL)
    error_count = sum(1 for r in records if r.status == RequestStatus.ERROR)

    ttfts = [r.metrics.ttft_ms for r in records if r.metrics.ttft_ms is not None]
    latencies = [
        r.metrics.request_latency_ms
        for r in records
        if r.metrics.request_latency_ms is not None
    ]

    return {
        "total_requests": total,
        "success_count": success_count,
        "timeout_count": timeout_count,
        "partial_count": partial_count,
        "error_count": error_count,
        "error_rate": (total - success_count) / total if total else 0,
        "timeout_rate": timeout_count / total if total else 0,
        "ttft_p50_ms": percentile(ttfts, 0.50),
        "ttft_p95_ms": percentile(ttfts, 0.95),
        "request_latency_p50_ms": percentile(latencies, 0.50),
        "request_latency_p95_ms": percentile(latencies, 0.95),
        "request_latency_p99_ms": percentile(latencies, 0.99),
    }
```

Then add file-level summary:

```python
from pathlib import Path

from autopsy.traces.jsonl import read_jsonl


def summarize_trace_file(path: Path) -> dict[str, object]:
    records = read_jsonl(path)
    return summarize_records(records)
```

## Step 11: Connect `summarize` CLI to Summary Metrics

File:

```txt
autopsy/cli.py
```

Replace the placeholder body with:

```python
from autopsy.metrics.summary import summarize_trace_file


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
```

Command to run:

```bash
autopsy summarize examples/traces/fake.jsonl
```

Checkpoint:

You should see:

```txt
Trace file: examples/traces/fake.jsonl
Requests: 50
Success: ...
Timeouts: ...
Partials: ...
Errors: ...
Error rate: ...
TTFT p50: ...
TTFT p95: ...
Request latency p95: ...
```

## Step 12: Write Summary Tests

File:

```txt
tests/test_summary.py
```

What to test:

- Counts are correct.
- Error rate includes timeout, partial, and error records.
- Percentile returns something expected for a small list.

Test shape:

```python
from autopsy.fake.generate import generate_fake_records
from autopsy.metrics.summary import summarize_records


def test_summary_counts() -> None:
    records = generate_fake_records(count=30, seed=7)
    summary = summarize_records(records)

    assert summary["total_requests"] == 30
    assert summary["success_count"] < 30
    assert summary["error_rate"] > 0


def test_summary_has_ttft_percentiles() -> None:
    records = generate_fake_records(count=30, seed=7)
    summary = summarize_records(records)

    assert summary["ttft_p50_ms"] is not None
    assert summary["ttft_p95_ms"] is not None
```

Command:

```bash
pytest tests/test_summary.py
```

## Step 13: Run the Full Phase 1 Check

Run:

```bash
autopsy --help
autopsy generate-fake --output examples/traces/fake.jsonl --requests 50
autopsy summarize examples/traces/fake.jsonl
pytest
```

Phase 1 is complete when all four commands work.

## Troubleshooting

If `autopsy` is not recognized:

```bash
pip install -e ".[dev]"
```

If imports fail:

- Check that every package folder has `__init__.py`.
- Check that your terminal is in the repo root.
- Check that your virtual environment is activated.

If JSONL reading fails:

- Confirm each line is one JSON object.
- Confirm the file is not a JSON array.
- Confirm every record has required fields.

If Pydantic validation fails:

- Read the field name in the error.
- Check enum values exactly.
- Check that nullable fields use `None`, not missing random strings.

If summary metrics look wrong:

- Print the loaded records count.
- Check whether failed records have missing TTFT values.
- Confirm metrics are read from JSONL, not from the fake generator directly.

## What Not To Build Yet

Do not build these in Phase 1:

- Real HTTP client.
- SSE parser.
- Async benchmark runner.
- HTML report.
- Diff gates.
- Replay.
- OpenTelemetry export.
- Agent orchestration.
- Full eval framework.

These are later phases. Phase 1 is the trace foundation.

## Beginner Mental Model

Think of Phase 1 like this:

```txt
schema.py says what a valid trace is
generate.py creates fake valid traces
jsonl.py saves and loads those traces
summary.py computes metrics from loaded traces
cli.py exposes those operations to the terminal
tests prove each piece works
```

That is the whole phase. If you keep each file to that job, the project will
feel much less mysterious.

## Phase 1 Completion Checklist

- `pyproject.toml` exists.
- `autopsy --help` works.
- `schema.py` defines Pydantic trace models.
- Schema tests pass.
- `jsonl.py` writes and reads JSONL records.
- JSONL tests pass.
- `generate.py` creates deterministic fake traces.
- `generate-fake` writes `examples/traces/fake.jsonl`.
- `summary.py` computes counts and percentiles from records.
- `summarize` prints meaningful metrics.
- Summary tests pass.
- `pytest` passes.
- No real endpoint is required.
- No core logic is trapped inside `cli.py`.
