# Inference Autopsy: Complete Project Guide

## Purpose

This is the human-facing master document for understanding, building, explaining,
and defending Inference Autopsy as a serious AI engineering project.

Unlike the AI operating docs, this guide is written for you: the project owner,
builder, and interview candidate. It explains what the project is, why it is
worth building, what must be implemented, what technical ideas it demonstrates,
what tradeoffs matter, how to scope it, how to demo it, and how to discuss it
deeply in interviews.

## Project Summary

Inference Autopsy is a local-first LLM inference profiling and regression
testing tool.

It benchmarks OpenAI-compatible LLM endpoints, records token-level streaming
traces, computes latency and reliability metrics, diagnoses likely bottlenecks,
generates static HTML reports, replays captured workloads, compares baseline and
candidate deployments, and fails CI when performance regresses.

The memorable pitch is:

```txt
Who killed my TTFT?
```

The serious pitch is:

```txt
Inference Autopsy is an open-source black-box profiler, workload replayer, and
regression tester for OpenAI-compatible LLM inference endpoints.
```

The deeper thesis is:

```txt
AI system latency is not one number. A request can be slow because of retrieval
delay, prompt assembly delay, first-token delay, slow decode, queueing, stream
stalls, cache-sensitive behavior, rate limits, tool latency, output bloat, or
tail-latency amplification. Inference Autopsy records enough evidence to
separate those symptoms, explain them, and prevent regressions from silently
shipping.
```

## Why This Project Is Strong for AI Engineering Internships

This project sits at the intersection of AI infrastructure, systems
measurement, backend engineering, developer tools, and applied LLM operations.

It is stronger than a typical LLM application because it demonstrates that you
understand the runtime behavior of model serving systems, not only how to call
an API.

It lets you talk about:

- OpenAI-compatible HTTP APIs.
- Server-sent event streaming.
- Async Python and concurrency control.
- Timing measurement and monotonic clocks.
- Token-level traces.
- TTFT, TTFB, ITL, throughput, and tail latency.
- Percentiles and regression thresholds.
- Queueing symptoms under load.
- Retrieval latency, prompt assembly latency, tool latency, and end-to-end
  latency.
- Retrieval recall and answer correctness as first-class tradeoffs.
- Cache-sensitive prompt behavior.
- Reproducibility through JSONL traces.
- Static report generation.
- CI performance gates.
- Black-box observability and its limits.

For Silicon Valley AI engineering internships, this matters because many teams
care about productionizing AI systems, not just prompting models. A project like
this shows you can reason about latency, reliability, instrumentation, testable
interfaces, and operational quality.

## What This Project Is Not

It is important to define the negative space.

Inference Autopsy is not:

- A hosted SaaS dashboard.
- A full observability platform.
- A distributed load-testing cluster.
- A Kubernetes operator.
- A vector database benchmark framework.
- A prompt management product.
- A model evaluation benchmark suite.
- A LangSmith, Helicone, Grafana, or Datadog clone.
- A provider-specific wrapper around one inference server.

It is intentionally a local CLI plus trace format plus static report plus replay
and CI gate workflow.

That restraint is a strength. It makes the project shippable, explainable, and
technically focused.

## Core User Problems

Inference Autopsy should answer seven questions.

### 1. How fast is this endpoint?

It should measure:

- Time to first byte.
- Time to first token.
- Inter-token latency.
- Request latency.
- Output tokens per second.
- p50, p90, p95, and p99 latency.
- Stream stalls.
- Error rate.
- Timeout rate.

### 1b. How fast is the whole AI system?

It should also measure:

- Retrieval latency.
- Prompt assembly latency.
- Tool latency.
- End-to-end latency.
- Retrieval recall.
- Answer correctness.
- Cost per successful task.

### 2. Why is it slow?

It should distinguish between externally visible symptoms:

- Long prompt prefill pressure.
- Slow decode.
- Tail-latency explosion.
- Streaming stalls.
- Queueing under load.
- Rate limits.
- Output bloat.
- Cache-sensitive latency.
- Warmup penalties.
- Retrieval failures.
- Prompt assembly overhead.
- Tool bottlenecks.

### 3. Does it collapse under load?

It should run concurrency and request-rate sweeps to detect:

- Tail amplification.
- Throughput plateau.
- Error-rate inflection.
- TTFT inflation.
- Saturation points.
- Queueing symptoms.

### 4. Do warmup or prefix reuse effects matter?

It should compare:

- Cold prompts.
- Warm prompts.
- Repeated-prefix workloads.
- Repeated-exact workloads.

It should never claim a definitive backend cache hit unless backend telemetry is
available. It can claim cache-sensitive behavior or latency patterns consistent
with cache benefit.

### 5. Can I reproduce the workload?

It should save enough trace data to support:

- Exact replay when prompts are recorded.
- Shape replay when prompts are not recorded.
- Baseline and candidate comparison.
- CI artifacts.
- Later report generation from saved traces.

It should also preserve enough context to reproduce:

- Retrieved documents.
- Prompt assembly inputs.
- Tool-call sequences.
- Expected answers or evaluation keys.

### 6. Did my deployment regress?

It should compare runs and fail gates such as:

```txt
ttft_p95 > +20%
itl_p95 > +15%
error_rate > 1%
tail_amplification_ratio > 2.5x
cache_benefit_ratio < -30%
```

It should also detect cases where:

- model latency stayed flat
- retrieval recall fell
- answer correctness fell
- end-to-end quality regressed

### 7. Can I explain the failure clearly?

It should produce evidence-backed diagnoses such as:

```txt
Cause of death: Queue Kraken

Evidence:
- TTFT p95 increased 3.4x from concurrency 1 to concurrency 16.
- ITL p95 changed by only 8%.
- Throughput plateaued after concurrency 8.

Likely driver:
The endpoint is consistent with queueing pressure before token generation.
```

## Product Wedge

The workflow should be:

```txt
benchmark
  -> trace
  -> metrics
  -> diagnosis
  -> report
  -> replay
  -> diff
  -> CI gate
```

This wedge is what differentiates the project from simple benchmark tools.

Many tools can run a benchmark. Inference Autopsy should make benchmark results
reproducible, explainable, comparable, and enforceable.

## Main Commands

The V1 command set should be small.

### `autopsy bench`

Runs a workload against an OpenAI-compatible endpoint and writes JSONL traces.

Example:

```bash
autopsy bench \
  --base-url http://localhost:8000/v1 \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --profile rag-long \
  --concurrency 1,4,8,16 \
  --max-requests 200 \
  --output runs/rag_long.jsonl
```

This is the most important command.

### `autopsy summarize`

Reads saved traces and prints a terminal summary.

Example:

```bash
autopsy summarize runs/rag_long.jsonl
```

This is useful before the HTML report exists and remains useful in CI.

### `autopsy report`

Reads saved traces and generates a static HTML report.

Example:

```bash
autopsy report runs/rag_long.jsonl \
  --html reports/rag_long.html
```

### `autopsy diff`

Compares baseline and candidate runs.

Example:

```bash
autopsy diff runs/baseline.jsonl runs/candidate.jsonl
```

With gates:

```bash
autopsy diff runs/baseline.jsonl runs/candidate.jsonl \
  --fail-if "ttft_p95 > +20%" \
  --fail-if "itl_p95 > +15%" \
  --fail-if "error_rate > 1%"
```

### `autopsy replay`

Replays a captured workload against another endpoint or model.

Example:

```bash
autopsy replay runs/baseline.jsonl \
  --base-url http://localhost:11434/v1 \
  --model qwen3:8b \
  --output runs/replay_ollama.jsonl
```

Replay is one of the strongest product features because it turns traces into
portable workload artifacts.

For AI system workflows, `bench` should also be able to represent stages such
as:

```txt
retrieval -> prompt assembly -> tool use -> LLM generation -> final answer
```

That is what makes this project stand out above a plain LLM latency profiler.

## Optional Wrapper Commands

After the core pipeline is stable, convenience commands can be added.

### `autopsy saturation`

A wrapper around `bench` configured for concurrency or request-rate sweeps.

### `autopsy cache`

A wrapper around `bench` configured for cold, warm, repeated-prefix, and
repeated-exact cache-sensitive workloads.

### `autopsy export`

Exports canonical metrics to JSON, Prometheus textfile format, or experimental
OpenTelemetry-shaped spans.

The important rule is that wrapper commands must not create separate metric or
trace logic. They should reuse the same pipeline.

### Higher-Level Modes

The project should eventually support benchmark modes for:

```txt
workflow tracing
retrieval benchmarking
agent/tool benchmarking
evaluation outcome analysis
```

## Required CLI Options

The benchmark command should eventually support:

```txt
--base-url
--api-key
--model
--profile
--concurrency
--request-rate
--duration
--max-requests
--timeout
--temperature
--max-tokens
--stream
--cache-mode
--prompt-recording-mode
--output
```

For higher-level workflow and eval runs, the project should also be able to
express:

```txt
--retrieval-mode
--docs-source
--answer-key
--judge-mode
--tool-mock
--tool-schema
--trace-stage-boundaries
```

The options are not just interface details. Each one ties to a measurable part
of inference behavior:

- `--base-url`: endpoint under test.
- `--model`: model or deployment name.
- `--profile`: workload shape.
- `--concurrency`: closed-loop parallel workers.
- `--request-rate`: open-loop arrival rate.
- `--duration`: time-bounded runs.
- `--max-requests`: request-bounded runs.
- `--timeout`: failure behavior.
- `--temperature`: generation setting.
- `--max-tokens`: output cap.
- `--stream`: streaming vs non-streaming mode.
- `--cache-mode`: cache-sensitive workload mode.
- `--prompt-recording-mode`: replay and privacy policy.
- `--output`: trace artifact location.

## OpenAI-Compatible Endpoint Support

V1 should focus on:

```txt
/v1/chat/completions
stream=true
stream=false
```

Target endpoint types:

- vLLM OpenAI-compatible server.
- Ollama OpenAI-compatible API.
- LiteLLM proxy.
- Hosted OpenAI-compatible inference providers.
- Internal company endpoints that follow OpenAI-style APIs.

This focus keeps the project practical. You do not need to support every model
server protocol.

## Streaming and SSE Parsing

Streaming is one of the most technically important parts of the project.

OpenAI-compatible streaming usually uses server-sent events. Responses arrive as
a sequence of chunks like:

```txt
data: {"choices":[{"delta":{"content":"Hello"}}]}

data: {"choices":[{"delta":{"content":" world"}}]}

data: [DONE]
```

However, real providers differ. Some chunks may:

- Contain role metadata but no token.
- Contain empty content.
- Include provider-specific fields.
- Arrive slowly.
- Be malformed.
- End early.
- Return errors mid-stream.

The parser must be tolerant enough to preserve trace integrity.

Important cases to handle:

- Normal content chunks.
- `[DONE]`.
- Empty SSE lines.
- Comments or keep-alive lines.
- Role-only first chunks.
- Chunks without `delta.content`.
- Malformed JSON.
- Timeout before first byte.
- Timeout after first byte.
- Timeout after first token.
- Partial response with generated tokens.
- Provider 429 or 500 errors.

The parser should separate:

- First byte time.
- First token time.
- Token timestamps.
- Stream completion.
- Error state.

This separation is what makes TTFT and TTFB meaningful.

## Timing Model

Latency calculations should use monotonic-relative timestamps.

That means:

- The run may have a wall-clock start time for metadata.
- Each request has monotonic timing measurements.
- `request_start` is the local zero point for that request.
- `first_byte`, `first_token`, and `request_end` are milliseconds relative to
  request start.

This avoids wall-clock jumps corrupting latency metrics.

Important timings:

```txt
request_start
first_byte
first_token
request_end
token_times_ms
```

Derived from those:

```txt
TTFB = first_byte - request_start
TTFT = first_token - request_start
request_latency = request_end - request_start
ITL = gaps between token timestamps
```

## TTFB, TTFT, and ITL

These three metrics are central to the project.

### TTFB

Time to first byte is the time from request start until the client receives the
first response bytes.

It can include:

- Network delay.
- Provider routing.
- Queueing.
- Initial server response delay.

### TTFT

Time to first token is the time from request start until the first generated
token appears.

It can include:

- Network delay.
- Queueing.
- Prompt prefill.
- Scheduling.
- Initial decode.

TTFT is often the most user-visible latency for chat systems.

### ITL

Inter-token latency is the gap between generated output tokens.

It reflects externally visible decode speed after generation begins.

If TTFT is high but ITL is normal, the problem is likely before generation or at
the start of generation. If ITL is high, the endpoint is slow while generating
tokens.

This distinction is one of the most important interview topics.

## Trace Format

The trace format is the backbone of the project.

Each request should be saved as one JSONL line.

V1 schema version:

```txt
0.2
```

Representative trace record:

```json
{
  "schema_version": "0.2",
  "run_id": "run_2026_05_30_001",
  "request_id": "req_00042",
  "request_sequence_index": 42,
  "profile": "rag-long",
  "model": "llama-3.1-8b",
  "base_url_hash": "endpoint_a",
  "load_mode": "closed_loop",
  "concurrency": 8,
  "request_rate": null,
  "cache_mode": "repeated-prefix",
  "prompt_recording_mode": "template_reference",
  "input_tokens_estimated": 4096,
  "input_token_count_method": "provider_usage_or_estimate",
  "output_tokens": 261,
  "streaming": true,
  "status": "success",
  "finish_reason": "stop",
  "attempt": 1,
  "retry_count": 0,
  "timings_ms": {
    "request_start": 0.0,
    "first_byte": 817.0,
    "first_token": 942.0,
    "request_end": 7610.0
  },
  "token_times_ms": [942.0, 971.0, 1001.0, 1033.0, 1208.0],
  "metrics": {
    "ttfb_ms": 817.0,
    "ttft_ms": 942.0,
    "request_latency_ms": 7610.0,
    "itl_mean_ms": 28.4,
    "itl_p95_ms": 71.2,
    "output_tps": 38.6,
    "stall_count": 2
  },
  "replay": {
    "messages_hash": "msg_abc123",
    "prompt_family": "rag-long",
    "prefix_group": "prefix_001",
    "template_id": "rag_long_v1",
    "template_seed": 12345,
    "shape": {
      "input_tokens_estimated": 4096,
      "expected_output_tokens": 256
    }
  },
  "error": null
}
```

For failed requests, `error` should be structured:

```json
{
  "error_type": "timeout",
  "message": "Request timed out after first token",
  "provider_status_code": null,
  "retryable": true,
  "occurred_after_first_byte": true,
  "occurred_after_first_token": true
}
```

The trace should preserve enough information to answer:

- What was requested?
- How was it requested?
- When did bytes and tokens arrive?
- How did the request end?
- Can this workload be replayed?
- Can this request be compared later?

## Run Metadata

Not everything belongs on every request line. Run-level metadata should be
stored once per run.

Required metadata:

```txt
run_id
run_started_at
tool_version
trace_schema_version
base_url_hash
model
profile
load_mode
concurrency_values
request_rate_values
max_requests
duration
timeout
warmup_policy
retry_policy
streaming
cache_modes
prompt_recording_mode
token_counting_method
```

This metadata makes reports reproducible and prevents benchmark results from
floating without context.

## Prompt Recording Modes

Replay and privacy are in tension.

To handle that clearly, support three prompt recording modes.

### `full`

Stores the full prompt/messages.

Pros:

- Supports exact replay.
- Best for local testing and demos.

Cons:

- May store sensitive data.
- Must be opt-in or clearly documented.

### `hash_only`

Stores only hashes of messages.

Pros:

- Safer for sensitive traces.
- Supports deduplication and comparison.

Cons:

- Cannot support exact replay.

### `template_reference`

Stores enough information to regenerate prompts from a known workload profile:

- Profile name.
- Template ID.
- Seed.
- Prompt family.
- Shape metadata.

Pros:

- Supports deterministic regeneration.
- Avoids storing raw prompts.

Cons:

- Requires the original profile and generator code.

The important rule:

```txt
No exact prompts, no exact replay.
```

If a trace is `hash_only`, exact replay should be refused. Shape replay can
still be offered.

## Workload Profiles

Workload profiles make the benchmark realistic.

Required built-ins:

```txt
short-chat
rag-long
code-completion
agent-json
prefix-cache
saturation
```

### `short-chat`

Purpose:

```txt
Measure endpoint overhead and basic chat latency.
```

Expected behavior:

- Short prompts.
- Short to moderate outputs.
- Good for smoke tests and CI.

### `rag-long`

Purpose:

```txt
Expose long-context TTFT and prefill sensitivity.
```

Expected behavior:

- Long input contexts.
- Moderate outputs.
- Useful for detecting Context Blobfish style failures.

### `code-completion`

Purpose:

```txt
Expose longer decode paths and output throughput.
```

Expected behavior:

- Medium prompts.
- Longer outputs.
- Useful for ITL and output TPS.

### `agent-json`

Purpose:

```txt
Test structured-output latency and reliability.
```

Expected behavior:

- JSON-like output requirements.
- Error-prone provider behavior.
- Useful for output validity and latency.

### `prefix-cache`

Purpose:

```txt
Measure whether repeated prefixes are associated with lower TTFT.
```

Expected behavior:

- Shared system or context prefix.
- Repeated-prefix and cold variants.
- Used for cache-sensitive analysis.

### `saturation`

Purpose:

```txt
Expose queueing pressure, tail amplification, and throughput plateaus.
```

Expected behavior:

- Short enough prompts to run many requests.
- Multiple concurrency or request-rate levels.
- Useful for load behavior.

## Load Modes

The project must distinguish closed-loop concurrency from open-loop request
rate.

### Closed-Loop Concurrency

Closed-loop concurrency means N workers run requests in parallel. Each worker
starts a new request only after its previous request finishes.

This models:

- Concurrent users.
- Worker pools.
- Basic load sweeps.

It answers:

- How does latency change as parallelism increases?
- Does p99 rise faster than p50?
- Does throughput improve with concurrency?

### Open-Loop Request Rate

Open-loop request rate schedules requests at a target arrival rate regardless of
completion.

This models:

- Incoming traffic pressure.
- Saturation.
- Queue buildup.

It answers:

- At what arrival rate does latency collapse?
- Does throughput plateau?
- Do errors appear after a rate threshold?

Do not mix these results without labeling them. They describe different
systems behavior.

## Metrics Engine

Metrics must be computed from saved traces.

That means:

- The benchmark runner records raw evidence.
- The metrics engine reads traces.
- Reports, summaries, diffs, exports, and diagnoses all use canonical metrics.

This prevents one-off terminal state from becoming the source of truth.

Required metrics:

```txt
ttfb_ms
ttft_ms
itl_mean_ms
itl_p50_ms
itl_p95_ms
request_latency_ms
output_tps
stall_count
stream_jitter_ms
error_rate
timeout_rate
tail_ratio
```

Required percentiles:

```txt
p50
p90
p95
p99
```

Required load metrics:

```txt
ttft_load_factor
tail_amplification_ratio
throughput_plateau_score
saturation_point
```

Required cache metrics:

```txt
cache_benefit_ratio
prefix_reuse_benefit_ratio
warmup_penalty_ratio
```

Required workflow metrics:

```txt
retrieval_latency_ms
prompt_assembly_latency_ms
tool_latency_ms
end_to_end_latency_ms
retrieval_recall
answer_correctness
latency_quality_tradeoff
tool_call_count
cost_usd
cost_latency_tradeoff
```

Useful grouping dimensions:

```txt
profile
model
base_url_hash
load_mode
concurrency
request_rate
cache_mode
input_token_bucket
output_token_bucket
status
prefix_group
```

## Percentiles

Percentiles are central because averages hide tail behavior.

p50 tells you the median experience.

p95 and p99 tell you what bad user experiences look like.

Tail ratio is:

```txt
p99 / p50
```

A high tail ratio means the median looks fine but some requests are much slower.

Interview point:

```txt
Median latency is where demos look good. Tail latency is where systems tell the
truth.
```

## Stream Stalls

A stream stall is a token gap above a configured threshold.

Example:

```txt
stall_threshold_ms = 500
```

If the token timestamps are:

```txt
[100, 130, 160, 920, 950]
```

Then the gap from 160 to 920 is a stall.

Stalls matter because a request can have acceptable total latency but feel bad
to a user if streaming pauses visibly.

## Output Throughput

Output tokens per second should be computed from generated output duration.

One reasonable formula:

```txt
output_tps = output_tokens / ((request_end_ms - first_token_ms) / 1000)
```

Be careful with one-token outputs. They may not have meaningful ITL or output
TPS. The tool should handle this gracefully.

## Saturation Analysis

Saturation analysis detects where increasing load stops improving throughput
and starts damaging latency or reliability.

Signals:

- Throughput stops increasing.
- p95 or p99 latency rises sharply.
- TTFT grows faster than ITL.
- Error rate increases.
- Timeout rate increases.

Useful derived metrics:

```txt
tail_amplification_ratio = high_load_p99 / low_load_p99
ttft_load_factor = high_load_ttft_p95 / low_load_ttft_p95
```

Example diagnosis:

```txt
Queue Kraken:
TTFT p95 increases sharply with concurrency while ITL remains mostly stable.
```

Interpretation:

The endpoint appears to be waiting longer before generation begins. This is
consistent with queueing, scheduler pressure, or rate limiting before decode.

Do not claim:

```txt
The GPU scheduler is definitely overloaded.
```

Unless backend telemetry proves it.

## Cache-Aware Analysis

Cache-aware benchmarking compares cold and warm prompt behavior from outside the
system.

Modes:

```txt
none
cold
warm
repeated-prefix
repeated-exact
```

Useful metrics:

```txt
cache_benefit_ratio = cold_ttft_p95 / warm_ttft_p95
prefix_reuse_benefit_ratio = cold_long_prefix_ttft_p95 / repeated_prefix_ttft_p95
warmup_penalty_ratio = first_n_ttft_p95 / steady_state_ttft_p95
```

Safe language:

- "Warm prompts were 2.3x faster than cold prompts."
- "The endpoint appears cache-sensitive."
- "The behavior is consistent with prefix reuse benefit."

Unsafe language:

- "The KV cache hit."
- "The provider cache missed."
- "The backend prefix cache is broken."

Black-box tools measure symptoms, not internal truth.

## Diagnosis Engine

V1 diagnosis should be rule-based.

No LLM is needed.

Required labels:

```txt
TTFT Whale
Decode Goblin
Tail Hydra
Context Blobfish
Queue Kraken
Saturation Cliff
Cache Mirage
Stream Stutter
Rate Limit Police
Output Hydra
```

### Future Workflow Labels

```txt
Retrieval Drift
Prompt Assembly Bottleneck
Tool Cascade
Answer Drift
Quality Regressor
```

Each diagnosis should include:

```txt
label
severity
confidence
evidence
likely_external_symptom
possible_internal_causes
suggested_next_tests
```

Example:

```txt
Cause of death: Context Blobfish
Severity: High
Confidence: 0.82

Evidence:
- TTFT p95 increased from 640ms at 512 input tokens to 3180ms at 8192 input tokens.
- ITL p95 changed by only 6%.
- Request latency increase was concentrated before the first generated token.

Likely external symptom:
Long prompts are strongly associated with first-token delay.

Possible internal causes:
Prompt prefill cost, context processing overhead, or lack of prefix reuse.

Suggested next tests:
- Bucket by input length.
- Run repeated-prefix profile.
- Compare with shorter context windows.
```

## Failure Labels

### TTFT Whale

First-token latency dominates request time.

Likely evidence:

- TTFT is high.
- ITL is normal.
- First token accounts for most request latency.

### Decode Goblin

Inter-token latency is high.

Likely evidence:

- ITL p95 is high.
- Output TPS is low.
- TTFT may be acceptable.

### Tail Hydra

p99 latency explodes while median looks fine.

Likely evidence:

- p99 / p50 ratio is high.
- Worst requests dominate user pain.

### Context Blobfish

Long prompts crush first-token latency.

Likely evidence:

- TTFT rises with input token bucket.
- ITL remains stable.

### Queue Kraken

TTFT and p99 rise sharply under load while ITL stays relatively stable.

Likely evidence:

- High-load TTFT p95 is much worse than low-load TTFT p95.
- ITL changes less than TTFT.

### Saturation Cliff

Throughput stops increasing while latency or errors keep rising.

Likely evidence:

- Throughput plateau.
- p95/p99 grows.
- Error rate may rise.

### Cache Mirage

Warm performance is good, but cold performance is poor.

Likely evidence:

- Cold TTFT p95 much higher than warm TTFT p95.
- Repeated workloads look much better than fresh prompts.

### Stream Stutter

Streaming has large token gaps.

Likely evidence:

- High stall count.
- Token gap histogram has long pauses.

### Rate Limit Police

429s, throttling, or retry behavior dominates.

Likely evidence:

- Provider 429 responses.
- Error rate rises with request rate.
- Retry count increases.

### Output Hydra

Output length unexpectedly inflates latency.

Likely evidence:

- Output tokens exceed expected range.
- Total latency rises with output length.
- TTFT may be normal.

## Static HTML Report

The static report is the main demo artifact.

It should be shareable without running a server.

Required sections:

```txt
Executive summary
Cause of death
Latency decomposition
Metric table
Latency percentiles
Concurrency or request-rate sweep
Cache autopsy
TTFT vs input length
ITL distribution
Token-gap histogram
Worst requests
Error breakdown
Baseline comparison
Recommendations
Benchmark methodology
Raw trace metadata
```

Workflow reports should also include:

```txt
retrieval latency
prompt assembly latency
tool latency
retrieval recall
answer correctness
quality/latency tradeoff
```

The report should answer:

- What happened?
- How bad was it?
- Where is the evidence?
- What should I test next?
- Can I trust the methodology?

Required chart candidates:

```txt
TTFT by concurrency
Request latency p50/p95/p99 by concurrency
Throughput vs concurrency
Error rate vs concurrency
TTFT cold vs warm
TTFT repeated-prefix vs cold
Request latency histogram
Token gap distribution
Input tokens vs TTFT scatter
Output tokens vs latency scatter
```

At least five should exist in the polished V1.

## Report Design Philosophy

The report should look like an engineering artifact, not a marketing page.

Design principles:

- Clear hierarchy.
- Units everywhere.
- Tables for exact values.
- Charts for trends.
- Plain-language takeaways.
- Visible methodology.
- Color used carefully.
- Accessible contrast.
- Static and portable.

The user should be able to understand the bottleneck without you narrating it.

## Diff Engine

The diff engine compares two saved runs:

```txt
baseline
candidate
```

It should report:

- Baseline value.
- Candidate value.
- Absolute change.
- Relative change.
- Whether the change breached a gate.

Example:

```txt
Metric              Baseline   Candidate   Change
TTFT p95            840ms      1210ms      +44.0%
ITL p95             39ms       47ms        +20.5%
Request p99         6.2s       9.8s        +58.1%
Error rate          0.1%       1.8%        +1.7pp
```

Diffing turns benchmarking from a one-off activity into regression testing.

## CI Gates

CI gates enforce performance contracts.

Example:

```bash
autopsy diff baseline.jsonl candidate.jsonl \
  --fail-if "ttft_p95 > +20%" \
  --fail-if "itl_p95 > +15%" \
  --fail-if "error_rate > 1%"
```

Expected behavior:

- Gate pass exits `0`.
- Gate failure exits non-zero.
- Invalid gate syntax fails closed.
- Output shows exact compared values.
- CI uploads traces and reports as artifacts.

This is a strong internship signal because it shows you understand how to turn
performance into an automated engineering contract.

## Replay

Replay is central to reproducibility.

There are two replay modes.

### Exact Replay

Exact replay resends the same messages.

Requires:

```txt
prompt_recording_mode = full
```

### Shape Replay

Shape replay regenerates similar prompts from stored workload shape.

Works with:

```txt
prompt_recording_mode = template_reference
prompt_recording_mode = hash_only
```

Shape replay is useful for privacy-preserving benchmarks, but it should be
labeled clearly because it is not identical to exact replay.

## Observability Export

Export is useful but secondary.

Start with:

```txt
JSON metrics export
```

Then optionally:

```txt
Prometheus textfile export
OpenTelemetry-shaped span export
```

The export path matters because it lets you say the project integrates with
observability workflows without building a dashboard.

Important rule:

Export code should consume canonical metrics. It should not recompute metrics
independently.

## Architecture

The conceptual architecture:

```txt
Typer CLI
  -> workload runner
  -> OpenAI-compatible HTTP client
  -> SSE stream parser
  -> trace recorder
  -> metrics engine
  -> diagnosis engine
  -> report generator
  -> diff and gate engine
  -> replay engine
```

Layer responsibilities:

- CLI parses commands and displays output.
- Workload runner schedules requests.
- Client sends requests and receives responses.
- Parser turns streaming chunks into token events.
- Recorder writes JSONL trace artifacts.
- Metrics engine computes canonical values.
- Diagnosis engine classifies failure modes.
- Report generator renders human-facing artifacts.
- Diff engine compares runs.
- Gate engine evaluates thresholds.
- Replay engine reconstructs workloads.

The key architecture rule:

```txt
Metrics are computed once and reused everywhere.
```

## Suggested Repository Structure

V1 should be structured but not over-fragmented.

```txt
autopsy/
  __init__.py
  cli.py
  client/
    openai_compatible.py
    stream_parser.py
  traces/
    schema.py
    jsonl.py
    metadata.py
  workloads/
    profiles.py
    generators.py
    builtins/
  metrics/
    core.py
    aggregation.py
    saturation.py
    cache.py
  diagnosis/
    rules.py
    labels.py
  reports/
    html.py
    charts.py
    templates/
  diff/
    compare.py
    gates.py
  replay/
    replay.py
tests/
  fixtures/
  unit/
  integration/
examples/
  traces/
  reports/
  ci/
docs/
```

Avoid creating too many packages before they earn their keep. The structure
should help testing and explanation, not perform architecture theater.

## Technology Stack

Recommended stack:

- Python for implementation.
- Typer for CLI.
- httpx for async HTTP.
- Pydantic for trace schema validation.
- orjson for fast JSON if needed.
- Rich for terminal summaries.
- Polars for larger metrics aggregation, or plain Python for early V1.
- Jinja2 for HTML templates.
- Plotly for static interactive charts.
- pytest for tests.
- ruff for linting and formatting.
- mypy for type checking.
- GitHub Actions for CI.

Do not add heavyweight infrastructure unless the core workflow is excellent.

## Testing Strategy

Testing is essential because metrics bugs destroy trust.

Required test areas:

- Trace schema validation.
- JSONL read/write.
- SSE stream parser.
- Timeout and partial stream handling.
- Percentile calculation.
- ITL calculation.
- Stall detection.
- Cache metrics.
- Saturation metrics.
- Diagnosis rules.
- Gate parser.
- Diff output.
- Replay mode behavior.
- Report generation smoke test.

Important fixtures:

- Healthy short-chat trace.
- Long-context TTFT-heavy trace.
- Slow decode trace.
- Tail-latency trace.
- Stream stall trace.
- Rate-limit trace.
- Queueing/saturation trace.
- Cache-sensitive trace.
- Partial response trace.
- Malformed stream trace.

Avoid live API calls in default tests. Use fake endpoints and saved fixtures.

## Development Phases

### Phase 1: Skeleton and Trace Foundation

Build:

- `pyproject.toml`.
- CLI skeleton.
- Pydantic schemas.
- JSONL reader/writer.
- Fake trace generator.
- Basic summary command.

Why it matters:

This gives you a testable artifact before real endpoints work.

### Phase 2: Streaming Client

Build:

- Async httpx client.
- OpenAI-compatible chat completion request.
- Streaming parser.
- Non-streaming fallback.
- Single-request tracing.

Why it matters:

This is the core systems piece. It turns model streaming into measurable events.

### Phase 3: Workload Runner

Build:

- Profile loader.
- Prompt generators.
- Closed-loop concurrency.
- Request count and duration limits.
- Basic progress output.
- Failure-tolerant execution.

Why it matters:

This turns one request into a benchmark.

### Phase 4: Metrics and Saturation

Build:

- Percentiles.
- TTFT, TTFB, ITL, latency, throughput.
- Grouping by profile/concurrency.
- Tail amplification.
- Throughput plateau detection.

Why it matters:

This is where raw traces become engineering insight.

### Phase 5: Diagnosis and Cache Modes

Build:

- Rule-based diagnosis.
- Evidence generation.
- Cache modes.
- Cache benefit metrics.
- Warmup penalty metrics.

Why it matters:

This creates the "autopsy" identity.

### Phase 6: Static Report

Build:

- HTML report.
- Summary cards.
- Metric tables.
- Charts.
- Diagnosis section.
- Methodology section.

Why it matters:

This creates the visual demo artifact.

### Phase 7: Diff and CI Gates

Build:

- Baseline/candidate comparison.
- Gate parser.
- Exit codes.
- GitHub Actions example.

Why it matters:

This turns profiling into regression prevention.

### Phase 8: Replay and Polish

Build:

- Exact replay.
- Shape replay.
- Sample traces.
- Sample reports.
- README polish.
- Blog post.
- Demo script.

Why it matters:

This makes the project feel complete.

## Demo Script

The demo should tell a story.

### Act 1: Healthy Endpoint

Run:

```bash
autopsy bench --profile short-chat --concurrency 1,4 --max-requests 40
```

Show:

- Reasonable TTFT.
- Reasonable ITL.
- Low error rate.

### Act 2: Long Prompt Pressure

Run:

```bash
autopsy bench --profile rag-long --concurrency 1,4 --max-requests 40
```

Show:

- TTFT increases with input length.
- Diagnosis: Context Blobfish or TTFT Whale.

### Act 3: Saturation

Run:

```bash
autopsy bench --profile saturation --concurrency 1,2,4,8,16 --max-requests 160
```

Show:

- p99 rises.
- Throughput plateaus.
- Diagnosis: Queue Kraken or Saturation Cliff.

### Act 4: Cache Sensitivity

Run:

```bash
autopsy bench --profile prefix-cache --cache-mode cold,warm,repeated-prefix
```

Show:

- Cold/warm TTFT difference.
- Cache-sensitive behavior.

### Act 4b: Retrieval Regression

Run:

```bash
autopsy bench --profile rag-qa --max-requests 40
```

Show:

- Model TTFT and ITL stay roughly flat.
- Retrieval recall drops.
- Answer correctness drops.
- The end-to-end workflow regresses even though the LLM stage looks stable.

### Act 5: Report

Generate:

```bash
autopsy report runs/demo.jsonl --html reports/demo.html
```

Show:

- Cause of death.
- Metrics.
- Charts.
- Methodology.

### Act 6: Replay and Diff

Run:

```bash
autopsy replay runs/baseline.jsonl --base-url http://localhost:11434/v1 --model qwen3:8b --output runs/replay.jsonl
autopsy diff runs/baseline.jsonl runs/replay.jsonl --fail-if "ttft_p95 > +20%"
```

Show:

- Candidate regression.
- CI-style failure.

## Blog Post Outline

Title:

```txt
Who Killed My TTFT? Building a Black-Box Profiler for LLM Inference Endpoints
```

Sections:

1. LLM inference latency is not one number.
2. Why existing benchmark summaries are not enough.
3. Designing a trace-first profiler.
4. Measuring TTFB, TTFT, ITL, stalls, and tail latency.
5. Handling messy SSE streams.
6. Detecting queueing and saturation symptoms.
7. Measuring cache-sensitive behavior from the outside.
8. Turning traces into reports.
9. Turning reports into CI gates.
10. What black-box tools can and cannot prove.

The blog should include measured results only after implementation. Do not
invent numbers.

## Resume Alignment

Your resume bullets should be true because the project demonstrates each claim.

### Bullet 1

```txt
Built an async benchmark runner for OpenAI-compatible LLM endpoints that records
request-level streaming traces, including TTFB, TTFT, inter-token latency, token
timestamps, output throughput, and error states.
```

Project evidence:

- `autopsy bench`.
- Async httpx runner.
- Trace JSONL.
- Timing fields.
- Metrics engine.

### Bullet 2

```txt
Implemented a tolerant SSE stream parser to handle provider-specific streaming
quirks, malformed chunks, delayed first tokens, partial responses, and
timeout/error cases without corrupting benchmark traces.
```

Project evidence:

- Stream parser module.
- Parser tests.
- Partial response fixtures.
- Structured error records.

### Bullet 3

```txt
Designed JSONL trace schemas for reproducible workload replay, preserving prompt
shape, model settings, concurrency level, cache mode, token timings, and request
outcomes for later diffing.
```

Project evidence:

- Pydantic schema.
- Prompt recording modes.
- Replay metadata.
- JSONL fixtures.

### Bullet 4

```txt
Built a metrics engine that computes p50/p95/p99 latency, tail ratios, stall
counts, throughput, error rates, and concurrency-sensitive regressions from
saved traces instead of one-off terminal timings.
```

Project evidence:

- Metrics module.
- Percentile tests.
- Saturation tests.
- Summary/report/diff all using same metrics.

### Bullet 5

```txt
Developed rule-based diagnosis reports for failure modes such as long-prompt
prefill pressure, slow decode, stream stalls, queueing collapse, rate limits,
output bloat, and cache-sensitive latency.
```

Project evidence:

- Diagnosis rules.
- Failure labels.
- Evidence text.
- Report diagnosis section.

### Bullet 6

```txt
Added baseline comparison and CI gates that fail builds when candidate
deployments breach latency or reliability thresholds.
```

Project evidence:

- `autopsy diff`.
- Gate parser.
- Non-zero exit codes.
- GitHub Actions example.

## Interview Explanation

A strong high-level answer:

```txt
I built Inference Autopsy because LLM inference latency is not one number. A
request can be slow because of prefill, decode, queueing, stream stalls, cache
sensitivity, rate limits, or output bloat. The tool records token-level traces
from OpenAI-compatible streaming endpoints, computes metrics like TTFB, TTFT,
ITL, p95/p99, stalls, and throughput, diagnoses likely bottlenecks, generates a
static report, replays workloads, and fails CI if a deployment regresses.
```

When asked what was hard:

```txt
The hard part was making black-box measurements honest. I do not see GPU
kernels, scheduler state, or KV-cache internals, so the tool has to separate
observable symptoms carefully and avoid overclaiming. For example, if TTFT grows
with concurrency but ITL stays flat, that is consistent with queueing before
generation, but I would not claim the scheduler is definitely the root cause
without backend telemetry.
```

When asked about streaming:

```txt
Streaming responses are messy. Providers can send role-only chunks, empty
content chunks, malformed JSON, delayed first tokens, or errors after partial
output. I built the parser so it records whatever timing evidence exists and
marks the request status accurately instead of dropping or corrupting the trace.
```

When asked about cache analysis:

```txt
Because this is black-box, I cannot prove a cache hit. What I can do is compare
cold, warm, repeated-prefix, and repeated-exact workloads. If repeated-prefix
TTFT is much lower than cold long-prompt TTFT, the endpoint is cache-sensitive or
benefiting from prefix reuse. The report uses that cautious language.
```

## Deep Technical Topics to Prepare

Be ready to explain:

- Why TTFT matters for chat UX.
- Why TTFB and TTFT can differ.
- How SSE streaming works.
- How async Python schedules concurrent requests.
- Why monotonic clocks are used for latency.
- How percentiles are computed.
- Why p99 can regress while p50 looks fine.
- How output length affects total latency.
- How long prompts affect prefill.
- How high concurrency can inflate TTFT.
- Why request-rate load differs from concurrency load.
- Why JSONL is a good trace format.
- Why replay requires prompt storage or regeneration.
- Why metrics should be computed from saved traces.
- How retrieval quality can regress while model latency stays constant.
- How workflow tracing exposes prompt assembly and tool bottlenecks.
- Why answer correctness and retrieval recall should be measured together with
  latency.
- Why CI gates fail closed.
- What black-box profiling cannot prove.

## Risk Register

| Risk | Severity | Mitigation |
| --- | ---: | --- |
| Scope creep into dashboard | High | Keep V1 CLI plus static reports |
| Distributed load-testing rabbit hole | High | Only implement local saturation analysis |
| Cache overclaiming | Medium | Use black-box-safe language |
| Streaming incompatibility | Medium | Build parser fixtures for provider variants |
| Metrics bugs | High | Use deterministic synthetic traces |
| Bad demo endpoint | Medium | Keep fake traces and local fallback |
| Report looks weak | Medium | Prioritize clear layout and five strong charts |
| Replay privacy concerns | Medium | Support prompt recording modes |
| Too many diagnosis labels | Medium | Start with ten tested labels |
| Too many profiles | Medium | Ship six strong profiles |

## What to Cut If Time Shrinks

Cut in this order:

1. OpenTelemetry-shaped export.
2. Prometheus export.
3. Optional diagnosis labels.
4. Extra workload profiles.
5. Dedicated `cache` and `saturation` wrapper commands.
6. Advanced chart polish.

Do not cut:

- Trace schema.
- Streaming parser.
- Metrics engine.
- Static report.
- Diagnosis engine.
- Diff gates.
- Replay.

Those are the spine of the project.

## Quality Bar

The project is resume-ready only when:

- The README explains the project clearly.
- The CLI can run an end-to-end demo.
- Sample traces are included.
- At least one sample report is included.
- Tests cover parser, metrics, diagnosis, gates, and schema.
- CI runs tests.
- The report looks polished enough to show a recruiter or engineer.
- The resume bullets are demonstrably true.

## Final Mental Model

The entire project can be compressed into one sentence:

```txt
Inference Autopsy turns messy AI system behavior into reproducible traces,
turns traces into trustworthy metrics, turns metrics into evidence-backed
diagnoses, and turns diagnoses into reports and CI gates.
```

If you can build that and explain every part, you will have a strong AI
engineering internship project.
