# Phase 2 Testing Guide

## Purpose

Test the Phase 2 real request path:

```txt
CLI -> HTTPX async client -> OpenAI-compatible endpoint -> SSE parser -> TraceRecord -> JSONL
```

This guide assumes Windows PowerShell from the repository root:

```powershell
cd D:\cs\Work\Inference-Autopsy
```

## What Phase 2 Should Prove

By the end of testing, you should know whether:

- the package is installed correctly;
- the `autopsy` CLI is available;
- `autopsy single` accepts the expected flags;
- fake HTTP tests pass;
- a real OpenAI-compatible endpoint can be called;
- streamed chunks become token timestamps;
- failures still produce valid trace evidence.

## Step 1: Activate The Virtual Environment

Run:

```powershell
.\.venv\Scripts\Activate.ps1
```

Your prompt should change to:

```txt
(.venv) PS D:\cs\Work\Inference-Autopsy>
```

If activation is blocked by execution policy, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

This changes policy only for the current PowerShell process.

## Step 2: Install The Package In Editable Mode

Run:

```powershell
python -m pip install -e .
```

This matters because `autopsy` is a console script defined in `pyproject.toml`.
If the project is not installed into the active venv, PowerShell will not know
what `autopsy` means.

Expected result:

```txt
Successfully installed inference-autopsy-0.1.0
```

It is okay if pip also says dependencies are already satisfied.

## Step 3: Verify The CLI Is On PATH

Run:

```powershell
Get-Command autopsy
```

Expected result:

```txt
CommandType     Name        Version    Source
-----------     ----        -------    ------
Application     autopsy.exe            D:\cs\Work\Inference-Autopsy\.venv\Scripts\autopsy.exe
```

If this fails, use the direct venv path:

```powershell
.\.venv\Scripts\autopsy.exe --help
```

If the direct path works but `autopsy` does not, your venv is not active or
PowerShell has not refreshed the command path.

## Step 4: Verify Top-Level CLI Help

Run:

```powershell
autopsy --help
```

Fallback:

```powershell
.\.venv\Scripts\autopsy.exe --help
```

Expected commands:

```txt
generate-fake
summarize
single
```

If `single` is missing, reinstall:

```powershell
python -m pip install -e .
```

## Step 5: Verify `autopsy single` Help

Run:

```powershell
autopsy single --help
```

Expected required options:

```txt
--base-url
--model
--prompt
```

Expected optional options:

```txt
--output
--api-key
--temperature
--max-tokens
--timeout
--stream / --no-stream
```

This proves the CLI layer is wired correctly.

## Step 6: Run The Automated Test Suite

Run:

```powershell
pytest -q --basetemp=.tmp\pytest
```

If `pytest` is not recognized:

```powershell
python -m pytest -q --basetemp=.tmp\pytest
```

Expected result:

```txt
14 passed
```

What this proves:

- schema tests still pass;
- JSONL read/write still works;
- fake trace generation still works;
- summary metrics still work;
- SSE parser recognizes role, content, finish, done, blank, and malformed lines;
- HTTPX fake transport maps streaming chunks into a trace;
- malformed chunks preserve partial trace evidence;
- provider HTTP errors become error trace records.

## Step 7: Confirm Your Local Endpoint Is Running

Your command uses:

```txt
http://localhost:11434/v1
```

That usually means an Ollama OpenAI-compatible endpoint.

Check whether Ollama is reachable:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

Expected result:

```txt
models
------
...
```

If this fails, the endpoint is not running. Start Ollama, then retry.

Check the OpenAI-compatible model list too:

```powershell
Invoke-RestMethod http://localhost:11434/v1/models
```

Pick a model ID that actually appears in the output. In one local test, the
server exposed:

```txt
llama3:latest
```

Use that exact model string in `--model`.

Optional Ollama CLI check:

```powershell
ollama list
```

The model in `ollama list` should match the model used with `autopsy single`.
For example:

```txt
llama3:latest
```

If you want to use a model that is missing, pull it first:

```powershell
ollama pull qwen3:8b
```

## Step 8: Run One Real Streaming Request

Run:

```powershell
autopsy single --base-url http://localhost:11434/v1 --model llama3:latest --prompt "Write a haiku about GPUs." --output examples/traces/single.jsonl
```

Fallback if `autopsy` is still not recognized:

```powershell
.\.venv\Scripts\autopsy.exe single --base-url http://localhost:11434/v1 --model llama3:latest --prompt "Write a haiku about GPUs." --output examples/traces/single.jsonl
```

Expected output shape:

```txt
Status: success
Output tokens: <number>
TTFB: <number> ms
TTFT: <number> ms
Latency: <number> ms
Finish reason: stop
Wrote trace to examples\traces\single.jsonl
```

The exact numbers will vary.

## Step 9: Inspect The JSONL Trace

Run:

```powershell
Get-Content examples\traces\single.jsonl
```

You should see one JSON object on one line.

Important fields to inspect:

```txt
schema_version
run_id
request_id
model
base_url_hash
streaming
status
timings_ms.first_byte
timings_ms.first_token
timings_ms.request_end
token_times_ms
metrics.ttfb_ms
metrics.ttft_ms
metrics.itl_mean_ms
metrics.output_tps
error
```

For a successful streaming request:

- `status` should be `"success"`;
- `streaming` should be `true`;
- `first_byte` should not be null;
- `first_token` should not be null;
- `token_times_ms` should contain one entry per streamed content chunk;
- `error` should be null.

## Step 10: Summarize The Trace

Run:

```powershell
autopsy summarize examples\traces\single.jsonl
```

Fallback:

```powershell
.\.venv\Scripts\autopsy.exe summarize examples\traces\single.jsonl
```

Expected output:

```txt
Trace file: examples\traces\single.jsonl
Requests: 1
Success: 1
Timeouts: 0
Partials: 0
Errors: 0
Error rate: 0.00%
TTFT p50: <number> ms
TTFT p95: <number> ms
Request latency p95: <number> ms
```

This proves Phase 2 writes traces in the same shape Phase 1 metrics can read.

## Step 11: Test Non-Streaming Fallback

Run:

```powershell
autopsy single --base-url http://localhost:11434/v1 --model llama3:latest --prompt "Write one sentence about GPUs." --no-stream --output examples/traces/single-nonstream.jsonl
```

Expected behavior:

- the command should complete;
- `streaming` should be `false`;
- `first_byte` should be present;
- `first_token` will usually be null because non-streaming responses do not
  expose token-by-token timing;
- `token_times_ms` should be empty.

This proves the fallback path works, but it is less useful for latency
decomposition.

## Step 12: Test Provider Error Handling

Use a model name that does not exist:

```powershell
autopsy single --base-url http://localhost:11434/v1 --model definitely-not-a-real-model --prompt "hello" --output examples/traces/provider-error.jsonl
```

Expected behavior:

- command should not crash;
- `status` should be `error`;
- `error.error_type` should describe a provider or response error;
- the JSONL file should still contain a valid trace record.

This proves provider failures do not corrupt trace output.

## Step 13: Test Connection Failure Handling

Use a port where no endpoint is running:

```powershell
autopsy single --base-url http://localhost:9999/v1 --model llama3:latest --prompt "hello" --output examples/traces/connection-error.jsonl
```

Expected behavior:

- command should not crash;
- `status` should be `error`;
- `error.error_type` should be `request_error` or similar;
- timing evidence should still be recorded where available.

This proves transport failures become trace records.

## Step 14: Test Timeout Handling

Use an extremely short timeout:

```powershell
autopsy single --base-url http://localhost:11434/v1 --model llama3:latest --prompt "Write a long explanation of GPU memory." --timeout 0.001 --output examples/traces/timeout.jsonl
```

Expected behavior:

- command should not crash;
- `status` should be `timeout` or `partial`;
- `error.error_type` should be `timeout`;
- if any bytes or tokens arrived first, the trace should preserve them.

This proves timeout handling keeps partial evidence.

## Step 15: Know What A Good Phase 2 Trace Means

A good streaming trace is not just "the request worked."

It proves:

- `TTFB` was measured separately from `TTFT`;
- role-only chunks did not count as generated tokens;
- each content chunk produced a timestamp;
- ITL can be derived from `token_times_ms`;
- the endpoint identity was hashed instead of storing the raw base URL;
- prompt replay stores a prompt hash, not raw prompt text;
- the same JSONL trace can be summarized later.

## Common Failure Modes

### `autopsy` Is Not Recognized

Cause:

- venv is not active;
- package was not installed with `pip install -e .`;
- PowerShell PATH has not refreshed.

Fix:

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
autopsy --help
```

Fallback:

```powershell
.\.venv\Scripts\autopsy.exe --help
```

### `ModuleNotFoundError: No module named 'httpx'`

Cause:

- dependencies are not installed in the active venv.

Fix:

```powershell
python -m pip install -e .
```

### Endpoint Refuses Connection

Cause:

- Ollama or another OpenAI-compatible server is not running;
- wrong port;
- wrong base URL.

Fix:

```powershell
Invoke-RestMethod http://localhost:11434/api/tags
```

Then retry the `autopsy single` command.

### Model Not Found

Cause:

- the endpoint is running, but the model passed to `--model` is not installed or
  not served;
- the command used a model from an example instead of a model from `/v1/models`.

Fix:

```powershell
Invoke-RestMethod http://localhost:11434/v1/models
ollama list
```

Then rerun with the exact model ID shown by the endpoint, such as
`llama3:latest`. If you specifically want `qwen3:8b`, pull it before using it:

```powershell
ollama pull qwen3:8b
```

Important interpretation:

- `HTTP 404` with a provider message like `model 'qwen3:8b' not found` means the
  tool reached the endpoint and correctly wrote an error trace.
- It is a valid provider-error test, not a CLI or parser failure.

### Trace File Is Empty Or Missing

Cause:

- command failed before reaching trace finalization;
- output path was not passed;
- parent directory permission issue.

Fix:

```powershell
New-Item -ItemType Directory -Force examples\traces
autopsy single --base-url http://localhost:11434/v1 --model llama3:latest --prompt "hello" --output examples/traces/single.jsonl
```

## Interview Explanation

If asked what Phase 2 proves, say:

```txt
Phase 2 turns one real OpenAI-compatible chat completion into a durable trace.
The CLI stays thin. The HTTPX client owns transport. The SSE parser converts
provider stream lines into typed events. The trace-mapping layer records TTFB,
TTFT, token timestamps, request end, status, and structured errors. Even if the
stream fails halfway, the tool preserves partial evidence instead of dropping or
corrupting the run.
```

If asked why this matters:

```txt
Without this layer, later benchmark metrics are just terminal timings. With this
layer, every metric is reproducible from saved JSONL evidence.
```

## Phase 2 Done Criteria

Phase 2 is done when all are true:

- `autopsy single --help` works;
- `pytest -q --basetemp=.tmp\pytest` passes;
- one real streaming request writes JSONL;
- `autopsy summarize` can read that JSONL;
- timeout or provider errors produce valid trace records;
- you can explain TTFB, TTFT, ITL, parser behavior, and trace mapping without
  reading the code.
