# Project Spec: Inference Autopsy

## Purpose

Define the non-ambiguous project contract for Inference Autopsy as a
AI engineering internship project.

## Reference When

Read this before implementing the package skeleton, CLI, trace schema, metrics,
diagnosis engine, report generator, replay workflow, diff gates, or demo.

## AI Agents Must Obey

This file is the hard product contract. If implementation ideas conflict with
this spec, this spec wins unless the maintainer explicitly updates it.

## Target

Inference Autopsy must credibly support this framing:

```txt
Inference Autopsy - LLM Inference Profiler & Regression Tester
Python, Typer, httpx, Pydantic, Polars, Plotly, GitHub Actions
```

The final project must minimally justify these claims:

- Built an async benchmark runner for OpenAI-compatible LLM endpoints that
  records request-level streaming traces, including TTFB, TTFT, inter-token
  latency, token timestamps, output throughput, and error states.
- Implemented a tolerant SSE stream parser to handle provider-specific
  streaming quirks, malformed chunks, delayed first tokens, partial responses,
  and timeout/error cases without corrupting benchmark traces.
- Designed JSONL trace schemas for reproducible workload replay, preserving
  prompt shape, model settings, concurrency level, cache mode, token timings,
  and request outcomes for later diffing.
- Built a metrics engine that computes p50/p95/p99 latency, tail ratios, stall
  counts, throughput, error rates, and concurrency-sensitive regressions from
  saved traces instead of one-off terminal timings.
- Developed rule-based diagnosis reports for failure modes such as long-prompt
  prefill pressure, slow decode, stream stalls, queueing collapse, rate limits,
  output bloat, and cache-sensitive latency.
- Added baseline comparison and CI gates that fail builds when candidate
  deployments breach latency or reliability thresholds.

Every feature in this spec exists to make those claims true, demonstrable, and
easy to discuss in depth.

## Core Thesis

AI system latency is not one number.

Inference Autopsy is an open-source black-box profiler, workload replayer, and
regression tester for OpenAI-compatible LLM inference endpoints. It records
request-level and token-level traces, decomposes latency into externally visible
signals, diagnoses likely bottlenecks, produces static reports, replays saved
workloads, and fails CI when deployments regress.

The wedge is:

```txt
benchmark -> trace -> metrics -> diagnose -> report -> replay -> diff -> CI gate
```

The tool does not claim to observe backend internals directly. It infers likely
external symptoms from black-box measurements and uses careful language:

- Say "likely driver", "symptom", or "consistent with".
- Do not say "definitive root cause" unless backend telemetry proves it.

## Workflow Tracing

The project must profile the full AI system pipeline, not only the LLM call.

Required workflow stages:

```txt
retrieval_latency
prompt_assembly_latency
llm_latency
tool_latency
end_to_end_latency
```

Required workflow metrics:

```txt
retrieval_latency_ms
prompt_assembly_latency_ms
llm_latency_ms
tool_latency_ms
end_to_end_latency_ms
```

Hard rules:

- Stage boundaries must be preserved in the trace.
- The report must show where time was spent across the pipeline.
- LLM latency is one stage, not the whole system.
- A project that only measures model latency is not yet the intended project.

## Evaluation Outcomes

The project must connect latency with answer quality and retrieval quality.

Required evaluation fields:

```txt
question
retrieved_docs
answer
expected_answer
retrieval_recall
answer_correctness
latency
```

Required evaluation metrics:

```txt
retrieval_recall
answer_correctness
latency
latency_quality_tradeoff
```

Hard rules:

- The tool must be able to say when latency improved but answer quality fell.
- The tool must be able to say when retrieval quality degraded while model
  latency stayed constant.
- Evaluation outcomes are part of the core trace story, not a side feature.

## Agent and Tool Benchmarks

The project must support agentic workflows, not just single-turn chat.

Required agent/tool fields:

```txt
task
tool_calls
tool_latency_ms
tool_call_count
success
cost_usd
end_to_end_latency_ms
```

Required agent/tool metrics:

```txt
tool_call_count
tool_latency_ms
end_to_end_latency_ms
success_rate
cost_usd
cost_latency_tradeoff
```

Hard rules:

- The tool must record how many tool calls were required.
- The tool must record success and cost, not only latency.
- A faster agent run is not automatically a better run.

## Escaped Regression

The project must be able to answer this question:

```txt
What regression escaped your tool because model latency stayed constant but
retrieval quality degraded?
```

Required answer shape:

- Model latency stayed roughly flat.
- Retrieval recall dropped.
- Answer correctness dropped.
- The end-to-end workflow regressed despite stable model timing.

Example escaped regression:

```txt
The first version missed a retrieval regression because it only measured model
latency. TTFT and ITL stayed flat, but retrieval recall dropped from 0.91 to
0.67, answer correctness fell, and the final answer quality degraded. The fix
is to trace retrieval latency, prompt assembly latency, retrieval recall, and
answer correctness alongside model latency.
```

## Product Boundaries

### Must Be

- A polished local Python CLI.
- A trace-first profiling tool.
- OpenAI-compatible endpoint focused.
- Useful with vLLM, Ollama, LiteLLM, and hosted OpenAI-compatible providers.
- Capable of streaming and non-streaming measurement.
- Capable of producing static HTML reports.
- Capable of CI regression gating.
- Capable of tracing retrieval, prompt assembly, tool use, answer quality, and
  end-to-end tradeoffs for AI system workflows.

### Must Not Become

- A hosted SaaS dashboard.
- A distributed load-testing system.
- A Kubernetes operator.
- A vector database benchmark suite.
- A full observability backend.
- A LangSmith, Helicone, Grafana, or prompt-management clone.
- A provider-specific SDK wrapper.

### Hard Scope Rule

If a feature does not improve trace quality, metric quality, diagnosis quality,
 replayability, report clarity, or CI regression detection, it is out of scope
for V1. For higher-level AI system workflows, the feature must also improve
visibility into retrieval, prompt assembly, tool use, answer quality, or
end-to-end tradeoffs.

## V1 Success Criteria

V1 is successful when a user can:

1. Run an OpenAI-compatible benchmark.
2. Save request-level JSONL traces.
3. Measure TTFB, TTFT, ITL, latency percentiles, throughput, stalls, and errors.
4. Diagnose at least six externally visible failure modes.
5. Generate a static HTML report.
6. Replay a saved workload.
7. Compare baseline and candidate traces.
8. Fail CI on a latency or reliability regression.
9. Explain what happened using evidence from the trace.
10. Explain whether a regression came from retrieval quality, prompt assembly,
    tool latency, model latency, or end-to-end behavior.

## Commands

### Required V1 Commands

These commands must exist in V1:

```txt
autopsy bench
autopsy report
autopsy diff
autopsy replay
autopsy summarize
```

### Required V1 Flags

`autopsy bench` must support:

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

### Required Workflow/Eval Inputs

The project must also be able to express these concepts in workflow or eval
runs:

```txt
--retrieval-mode
--docs-source
--answer-key
--judge-mode
--tool-mock
--tool-schema
--trace-stage-boundaries
```

### Wrapper Commands Are Optional

These commands may be added after the core pipeline is stable:

```txt
autopsy saturation
autopsy cache
autopsy export
autopsy diagnose
```

Hard rule: wrapper commands must delegate to the same trace, metrics, and
diagnosis pipeline as `bench`, `summarize`, `report`, and `diff`. They must not
create parallel logic.

### Higher-Level Modes

The project must eventually support benchmark modes for:

```txt
workflow tracing
retrieval benchmarking
agent/tool benchmarking
evaluation outcome analysis
```

## Load Testing Semantics

The project must distinguish two load modes.

### Closed-Loop Concurrency

Closed-loop concurrency means N workers each issue a request, wait for it to
finish, then issue the next request.

Use this for:

- Basic concurrency sweeps.
- Tail amplification under concurrent users.
- Throughput and latency by worker count.

### Open-Loop Request Rate

Open-loop request rate means requests are scheduled at a target rate regardless
of whether previous requests have completed.

Use this for:

- Saturation testing.
- Queueing pressure.
- Rate-limit behavior.
- Arrival-rate stress.

Hard rule: every trace and report must record whether load mode was
`closed_loop` or `open_loop`. Queueing analysis must not mix the two modes
without labeling them.

## Cache-Aware Benchmarking

Cache-aware benchmarking is required for the target, but the tool must be
honest about what it can infer.

### Required Cache Modes

```txt
cold
warm
repeated-prefix
repeated-exact
none
```

### Allowed Claims

The tool may claim:

- Warm/cold latency difference.
- Prefix-reuse benefit.
- Repeated-prompt behavior.
- Cache-sensitive latency.
- Cache behavior is consistent with a likely cache benefit or miss.

### Forbidden Claims

The tool must not claim:

- A definitive cache hit.
- A definitive cache miss.
- Backend KV-cache state.
- Provider internal cache implementation.

Unless backend telemetry is explicitly provided.

### Required Metrics

```txt
cold_ttft_p95_ms
warm_ttft_p95_ms
cache_benefit_ratio
prefix_reuse_benefit_ratio
warmup_penalty_ratio
```

### Required Workflow Metrics

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

## Prompt Recording and Replay

Replay requires recoverable workload inputs. Hashes alone are insufficient.

### Required Prompt Recording Modes

```txt
full
hash_only
template_reference
```

### Mode Semantics

- `full`: store full messages in trace records or a linked artifact. Supports
  exact replay. May contain sensitive data.
- `hash_only`: store hashes only. Supports shape replay and diffing, but not
  exact replay.
- `template_reference`: store profile name, template parameters, prompt family,
  and seed. Supports deterministic regeneration when the profile is available.

Hard rule: `autopsy replay` must refuse exact replay from `hash_only` traces and
offer shape replay instead.

## Trace Schema

Each request is one JSONL line. V1 schema version is `0.2`.

### Required Top-Level Fields

```txt
schema_version
run_id
request_id
request_sequence_index
profile
model
base_url_hash
load_mode
concurrency
request_rate
cache_mode
prompt_recording_mode
input_tokens_estimated
input_token_count_method
output_tokens
streaming
status
finish_reason
attempt
retry_count
timings_ms
token_times_ms
metrics
replay
error
```

### Required Timing Fields

`timings_ms` must use monotonic-relative milliseconds from request start:

```txt
request_start
first_byte
first_token
request_end
```

Hard rule: wall-clock timestamps may be stored in run metadata, but latency
calculations must use monotonic-relative timings.

### Required Replay Fields

```txt
messages_hash
prompt_family
prefix_group
template_id
template_seed
shape
```

### Required Error Fields

When `error` is not null, it must include:

```txt
error_type
message
provider_status_code
retryable
occurred_after_first_byte
occurred_after_first_token
```

## Workflow Trace Shape

For AI system workflows, the trace must be able to represent stage boundaries
and stage outcomes, not just model call timing.

### Required Workflow Fields

```txt
retrieval_latency_ms
prompt_assembly_latency_ms
llm_latency_ms
tool_latency_ms
end_to_end_latency_ms
retrieved_docs
question
answer
expected_answer
retrieval_recall
answer_correctness
```

### Required Agent/Tool Fields

```txt
task
tool_calls
tool_call_count
success
cost_usd
```

### Hard Rules

- Retrieval, prompt assembly, tool use, LLM generation, and end-to-end timing
  must be separable.
- Evaluation outcomes must be traceable to the same run as latency metrics.
- A workflow trace without stage boundaries is incomplete.

## Run Metadata

Run-level metadata should be stored once per run, either in a sidecar JSON file
or as a clearly marked metadata JSONL record.

Required run metadata:

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

## Streaming Parser

The SSE parser is a core technical feature.

### Must Handle

- Standard OpenAI-style `data:` events.
- `[DONE]`.
- Empty lines.
- Provider-specific extra fields.
- Chunks without content.
- Role-only initial chunks.
- Delayed first token.
- Malformed JSON chunks.
- Partial streams.
- Timeout before first byte.
- Timeout after first byte.
- Timeout after first token.
- Provider errors mid-stream.

### Hard Rules

- Parser errors must not corrupt trace files.
- Partial responses must be represented explicitly.
- First byte and first token must be measured separately.
- A request that fails after partial output must still record available timings
  and token timestamps.
- Raw chunks may be logged only in sanitized debug mode.

## Metrics Engine

Metrics must be computed from saved traces, not from transient terminal state.

### Required Core Metrics

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

### Required Percentiles

```txt
p50
p90
p95
p99
```

### Required Load Metrics

```txt
ttft_load_factor
tail_amplification_ratio
throughput_plateau_score
saturation_point
```

### Required Cache Metrics

```txt
cache_benefit_ratio
prefix_reuse_benefit_ratio
warmup_penalty_ratio
```

### Required Grouping Dimensions

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

Hard rule: metric definitions must be implemented once and reused by summary,
report, diff, export, and diagnosis code.

## Diagnosis Engine

Diagnosis is rule-based in V1. No LLM is required.

### Required V1 Labels

Implement these first:

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

### Optional Later Labels

```txt
Cache Miss Coffin
Prefix Cache Savior
Warmup Vampire
Backpressure Bat
Cold Start Corpse
JSON Skeleton
Retry Zombie
```

### Future Workflow Labels

```txt
Retrieval Drift
Prompt Assembly Bottleneck
Tool Cascade
Answer Drift
Quality Regressor
```

### Required Diagnosis Fields

Every diagnosis must include:

```txt
label
severity
confidence
evidence
likely_external_symptom
possible_internal_causes
suggested_next_tests
```

### Hard Language Rule

Diagnosis output must say "likely driver" or "consistent with" for internal
causes. It must not overclaim internal scheduler, GPU, batching, or cache state.

## Reports

Static HTML report generation is required.

### Required Sections

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

### Required Charts

At least five of these must be present:

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

Hard rule: every chart must have units, a plain-language takeaway, and source
metrics traceable to the saved JSONL.

## Diff and CI Gates

Diff and gate evaluation are required for V1.

### Gate Syntax

V1 must support:

```txt
ttft_p95 > +20%
itl_p95 > +15%
error_rate > 1%
tail_amplification_ratio > 2.5x
cache_benefit_ratio < -30%
```

### Required Behavior

- Invalid gate syntax fails closed.
- Failed gates exit non-zero.
- Output includes baseline value, candidate value, change, and threshold.
- GitHub Actions examples must show artifact upload for traces and reports.

## Observability Export

Observability export is useful but must not distract from the core.

### Required If Time Allows

```txt
JSON metrics export
```

### Optional

```txt
Prometheus textfile export
OpenTelemetry-shaped span export
```

Hard rule: export code must consume canonical metrics. It must not recompute
metrics independently.

## Workload Profiles

### Required Built-In Profiles

```txt
short-chat
rag-long
code-completion
agent-json
prefix-cache
saturation
```

### Optional Profiles

```txt
long-context
mixed-realistic
cold-start
```

Hard rule: five strong, tested profiles are better than twenty weak profiles.

## Repository Structure

V1 should start flatter than the long-term architecture to avoid premature
abstraction.

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

Hard rule: do not add packages before there is a real boundary and tests that
benefit from it.

## Eight-Week Build Order

### Week 1: CLI, Schema, Fake Trace

Deliver:

- `pyproject.toml`.
- Typer CLI skeleton.
- Pydantic trace schema.
- JSONL reader/writer.
- Fake trace generator.
- `autopsy summarize`.
- Schema tests.

Working commands:

```bash
autopsy --help
autopsy generate-fake --output examples/traces/fake.jsonl
autopsy summarize examples/traces/fake.jsonl
```

### Week 2: Streaming Client and Parser

Deliver:

- Async httpx client.
- `/v1/chat/completions`.
- Streaming and non-streaming support.
- TTFB, TTFT, token timestamp capture.
- Tolerant SSE parser tests.

Working command:

```bash
autopsy single --base-url http://localhost:11434/v1 --model qwen3:8b --prompt "Write a haiku about GPUs."
```

### Week 3: Workload Runner

Deliver:

- Profile loader.
- Prompt generators.
- Closed-loop concurrency.
- Request-rate scheduling skeleton.
- Progress output.
- Partial failure handling.

Working command:

```bash
autopsy bench --base-url http://localhost:11434/v1 --model qwen3:8b --profile short-chat --concurrency 1,4 --max-requests 40 --output runs/short_chat.jsonl
```

### Week 4: Metrics and Saturation

Deliver:

- Core metrics.
- Percentiles.
- Grouping.
- Tail amplification.
- Throughput plateau detection.
- Saturation summary.

Success criteria:

- Metrics are deterministic from saved traces.
- Percentile tests use synthetic traces.
- Worst requests are identifiable.

### Week 5: Diagnosis and Cache Modes

Deliver:

- Rule-based diagnosis engine.
- Required V1 labels.
- Cache modes.
- Cache benefit ratio.
- Warmup penalty ratio.
- Evidence text.

Success criteria:

- No LLM needed for diagnosis.
- Every diagnosis has a test fixture.
- Cache claims use black-box-safe language.

### Week 6: Static Report

Deliver:

- HTML report.
- Metric tables.
- At least five charts.
- Diagnosis section.
- Saturation section.
- Cache autopsy section.
- Methodology metadata.

Success criteria:

- Opens locally without server.
- Looks professional.
- Explains bottleneck without voiceover.

### Week 7: Diff and CI Gates

Deliver:

- Baseline/candidate comparison.
- Gate parser.
- Relative, absolute, and multiplier thresholds.
- Exit code 1 on failed gates.
- GitHub Actions example.

Success criteria:

- Detects TTFT, ITL, error-rate, tail, and cache regressions.
- Produces clear CI output.

### Week 8: Replay, Polish, Demo

Deliver:

- Exact replay for `full` traces.
- Shape replay for `hash_only` traces.
- README polish.
- Sample traces.
- Sample reports.
- Demo script.
- Blog outline.

Success criteria:

- End-to-end demo works from trace to report to diff.
- Bullets are true.
- Explanation is evidence-backed.

## Demo Contract

The demo must show:

1. A healthy short-chat run.
2. A long-context run with TTFT pressure.
3. A concurrency or request-rate run with tail amplification.
4. A cache-sensitive run comparing cold and warm or repeated-prefix behavior.
5. A static report.
6. A replay against a second endpoint or model.
7. A diff that fails a CI-style gate.

## Talking Points

The project must prepare the builder to discuss:

- Why TTFT and ITL measure different parts of inference latency.
- Why TTFB and TTFT are not identical.
- How SSE streaming works and why providers differ.
- How malformed or partial streams are represented safely.
- Why benchmark metrics must come from saved traces.
- How closed-loop concurrency differs from open-loop request rate.
- How tail latency and p99/p50 ratios expose regressions.
- How cache-sensitive latency can be measured from the outside.
- Why black-box diagnosis must avoid overclaiming internals.
- How CI gates turn performance into an enforceable contract.

## Cut List

If time shrinks, cut in this order:

1. OpenTelemetry-shaped spans.
2. Prometheus export.
3. Optional diagnosis labels.
4. Extra workload profiles.
5. Dedicated `cache` and `saturation` wrapper commands.
6. Advanced chart polish.

Do not cut:

- Trace schema.
- Streaming parser.
- Metrics engine.
- Diagnosis engine.
- Static report.
- Diff gates.
- Replay.

## Final Hard Rules

- No trace, no reproducibility.
- No saved trace, no metric claim.
- No evidence, no diagnosis.
- No exact prompts, no exact replay.
- No backend telemetry, no definitive backend root cause.
- No duplicate metric implementations.
- No hosted dashboard in V1.
- No distributed workers in V1.
- No untested gate parser.
- No claims that the repo cannot demonstrate.
- No AI-system regression blind spot where retrieval quality or tool behavior
  degrades while model latency looks stable.
