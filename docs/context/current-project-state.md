# Current Project State

## Purpose

Give humans and AI agents a fast, current snapshot of the repository.

## Reference When

Read at the start of any task.

## AI Agents Must Obey

Update this file when project structure, implementation status, or core scope
changes.

## Snapshot

As of 2026-06-27, the repository contains:

- `README.md` with product vision, target CLI, metrics, trace format, report
  sections, planned stack, and development commands.
- `LICENSE`.
- This `docs/` operating system.
- A Python package skeleton under `autopsy/`.
- Phase 1 trace schema, JSONL helpers, fake trace generation, and summary
  metrics.
- Phase 2 single-request path for OpenAI-compatible chat completions:
  HTTPX async transport, tolerant SSE parsing, trace mapping, and `autopsy
  single`.

## Product Scope

Inference Autopsy targets:

- OpenAI-compatible chat completion endpoints.
- Streaming and non-streaming measurements.
- JSONL traces.
- Static HTML reports.
- Baseline diffs.
- CI regression gates.
- Replay from captured traces.

## Implementation Assumptions

- Primary language: Python.
- CLI framework: Typer.
- HTTP client: httpx.
- Schema validation: Pydantic.
- Tests: pytest.
- Formatting and linting: ruff.
- Type checking: mypy.
