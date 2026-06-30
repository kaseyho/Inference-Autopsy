# Phase 3 Testing Guide

## Purpose

Test the Phase 3 workload runner:

```txt
profile -> generated prompts -> closed-loop async workers -> TraceRecord JSONL
```

## Automated Tests

From the repository root:

```powershell
.\.venv\Scripts\pytest.exe -q --basetemp=C:\tmp\ia-pytest
```

Expected:

```txt
19 passed
```

This verifies:

- deterministic built-in profile prompt generation;
- concurrency parsing;
- `bench` runner output with fake HTTPX transport;
- provider errors become valid trace records;
- Phase 1 and Phase 2 behavior still works.

## CLI Smoke Test

Check that `bench` is available:

```powershell
.\.venv\Scripts\autopsy.exe --help
.\.venv\Scripts\autopsy.exe bench --help
```

Expected command:

```txt
bench
```

## Live Ollama Test

First confirm the model served by Ollama:

```powershell
Invoke-RestMethod http://localhost:11434/v1/models
```

Use the exact model ID returned, for example:

```txt
llama3:latest
```

Run a tiny benchmark:

```powershell
.\.venv\Scripts\autopsy.exe bench --base-url http://localhost:11434/v1 --model llama3:latest --profile short-chat --concurrency 1,2 --max-requests 3 --output runs/short_chat.jsonl
```

Expected behavior:

- 6 total traces are written;
- 3 traces have `concurrency = 1`;
- 3 traces have `concurrency = 2`;
- all traces share the same `run_id`;
- every trace has `load_mode = "closed_loop"`;
- failed requests are still written as trace records.

Inspect the output:

```powershell
Get-Content runs\short_chat.jsonl
```

Summarize it:

```powershell
.\.venv\Scripts\autopsy.exe summarize runs/short_chat.jsonl
```

## Built-In Profiles

Phase 3 currently supports:

```txt
short-chat
rag-long
long-output
```

Example:

```powershell
.\.venv\Scripts\autopsy.exe bench --base-url http://localhost:11434/v1 --model llama3:latest --profile rag-long --concurrency 1 --max-requests 3 --output runs/rag_long.jsonl
```

## What Phase 3 Proves

Phase 3 is complete when:

- `autopsy bench --help` works;
- tests pass;
- a benchmark writes one JSONL line per request;
- concurrency sweeps produce labeled traces;
- request failures do not crash the whole benchmark;
- Phase 4 can read the saved traces for metrics.
