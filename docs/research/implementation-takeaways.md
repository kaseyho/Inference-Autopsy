# Implementation Takeaways

This file turns research into concrete build decisions for Inference Autopsy.
Each takeaway should connect a source or concept to an implementation choice.

## Takeaway: Metrics must be computed from saved traces

Sources:

- GuideLLM
- AIPerf
- Project trace design

Project decision:

Inference Autopsy computes metrics from JSONL traces, not from transient runner
state.

Implementation impact:

- The runner records evidence.
- The metrics module reads traces.
- Reports, diffs, diagnosis, summaries, and exports reuse canonical metrics.
- Terminal output is a view over saved evidence, not the source of truth.
- Tests can validate metrics from deterministic fixture traces.

Why this matters:

- Reproducibility is the core product wedge.
- If metrics only exist in memory during a run, later report generation, replay,
  and CI diffing become less trustworthy.

What to avoid:

- Do not compute one version of p95 in the runner and another in reports.
- Do not let report code recompute metrics differently from diff code.
- Do not discard failed requests before metrics are computed.

## Takeaway: Use OpenAI-compatible endpoints as V1 protocol boundary

Sources:

- vLLM OpenAI-compatible server docs
- Ollama OpenAI-compatible API behavior
- LiteLLM OpenAI-style proxy model
- Project scope constraints

Project decision:

V1 supports OpenAI-compatible chat completion endpoints only.

Implementation impact:

- The first client targets `/v1/chat/completions`.
- The request shape follows OpenAI-style chat messages.
- Streaming support focuses on OpenAI-style SSE chunks.
- Compatibility testing starts with vLLM, Ollama, LiteLLM, and hosted
  OpenAI-compatible providers.
- Non-OpenAI APIs are future adapter work, not V1 scope.

Why this matters:

- It keeps the protocol surface small enough to finish in two months.
- It lets the project go deep on tracing, metrics, replay, diagnosis, and CI
  gates instead of shallowly supporting many provider APIs.
- Many real inference systems expose OpenAI-compatible interfaces, so the scope
  is still practically useful.

What to avoid:

- Do not add Anthropic, Gemini, Bedrock, or custom provider clients before the
  core OpenAI-compatible path is excellent.
- Do not build an adapter framework before there is one strong adapter.
- Do not let provider compatibility replace the main project thesis.

## Takeaway: Use tolerant SSE parsing

Sources:

- OpenAI-compatible streaming behavior
- vLLM streaming behavior
- Provider-specific streaming quirks
- Project trace integrity requirements

Project decision:

The SSE parser must be tolerant of real-world streaming variation and must
preserve partial evidence when streams fail.

Implementation impact:

- The parser handles `data:` lines, empty lines, role-only chunks, chunks with no
  content, provider-specific fields, malformed JSON, `[DONE]`, and mid-stream
  errors.
- The trace records first byte, first token, token timestamps, completion, and
  error state separately.
- Partial streams become explicit trace records instead of corrupt output.
- Sanitized debug logging can capture raw-ish chunk context without exposing
  secrets by default.

Why this matters:

- TTFT, ITL, stream stalls, and partial-response reliability all depend on
  parser correctness.
- A brittle parser would make the tool look unreliable in exactly the area it
  claims to understand.

What to avoid:

- Do not assume every chunk has `choices[0].delta.content`.
- Do not drop a request just because it failed after partial output.
- Do not log raw prompts, API keys, or sensitive chunks by default.
- Do not treat TTFB and TTFT as the same event.

## Takeaway: Separate TTFB, TTFT, and ITL

Sources:

- LLM serving metrics literature
- GuideLLM and AIPerf metric framing
- Project latency decomposition design

Project decision:

Inference Autopsy treats TTFB, TTFT, and ITL as separate first-class metrics.

Implementation impact:

- The client records first response byte separately from first generated token.
- The parser ignores role-only or metadata-only chunks when measuring TTFT.
- The metrics engine computes inter-token gaps from token timestamps.
- Reports explain whether latency is concentrated before generation or during
  generation.
- Diagnosis rules can distinguish TTFT-heavy failures from decode-heavy
  failures.

Why this matters:

- TTFB can reflect connection, routing, or initial server response behavior.
- TTFT reflects externally visible delay before the first generated token.
- ITL reflects decode speed and streaming smoothness after generation begins.
- Separating them makes diagnosis much more credible.

What to avoid:

- Do not use first byte as first token.
- Do not compute ITL for one-token outputs without handling the edge case.
- Do not collapse all latency into request duration.
- Do not diagnose slow decode from TTFT alone.

## Takeaway: Treat cache behavior as black-box-sensitive, not definitive

Sources:

- vLLM prefix caching docs
- PagedAttention background
- Black-box profiling limits
- Project cache autopsy design

Project decision:

Inference Autopsy measures cache-sensitive latency patterns, but does not claim
definitive cache hits or misses without backend telemetry.

Implementation impact:

- The benchmark supports cache modes: `none`, `cold`, `warm`,
  `repeated-prefix`, and `repeated-exact`.
- The metrics engine computes cold/warm TTFT differences, cache benefit ratios,
  prefix reuse benefit ratios, and warmup penalty ratios.
- Reports use language like "consistent with prefix reuse benefit" and
  "cache-sensitive behavior."
- Diagnosis labels such as `Cache Mirage` must include cautious wording.

Why this matters:

- Cache-aware benchmarking is a strong AI-infra signal.
- Overclaiming backend cache state would make the tool less credible.
- The project can still reveal useful behavior from the outside.

What to avoid:

- Do not say a KV cache definitely hit or missed.
- Do not infer backend cache internals from one warm/cold comparison.
- Do not build a cache layer.
- Do not make cache analysis depend on vLLM-only internals in V1.

## Takeaway: Support closed-loop concurrency before open-loop request rate

Sources:

- Benchmark methodology
- Load-testing concepts
- Project two-month scope

Project decision:

V1 implements closed-loop concurrency first, then adds open-loop request-rate
support once the core runner is stable.

Implementation impact:

- The first runner can use a fixed number of async workers.
- Trace records include `load_mode`.
- Reports label concurrency results as closed-loop.
- Request-rate scheduling is added carefully later for saturation analysis.
- Saturation diagnosis must not mix closed-loop and open-loop data without
  labeling.

Why this matters:

- Closed-loop concurrency is easier to implement and explain.
- It is enough for early concurrency sweeps and tail amplification.
- Open-loop request rate is valuable but easier to get wrong.

What to avoid:

- Do not call closed-loop concurrency "RPS."
- Do not claim request-rate saturation before implementing open-loop scheduling.
- Do not hide load mode in trace metadata.
- Do not build a distributed load generator in V1.

## Takeaway: Use JSONL for append-friendly traces

Sources:

- Project trace design
- Benchmark artifact needs
- CLI and CI workflow constraints

Project decision:

Request traces are stored as newline-delimited JSON, with one request record per
line.

Implementation impact:

- The recorder can append records as requests complete.
- Partial runs still produce inspectable artifacts.
- CI can upload trace files easily.
- Metrics, reports, replay, and diff can stream or batch-read traces.
- Human debugging remains simple because each line is inspectable JSON.

Why this matters:

- JSONL is simple, portable, and easy to process with Python, shell tools,
  DuckDB, Polars, or other analysis tools.
- It supports the "no trace, no reproducibility" principle.

What to avoid:

- Do not require a database for V1.
- Do not store only aggregate metrics.
- Do not make trace files impossible to inspect manually.
- Do not silently skip malformed lines without reporting them.

## Takeaway: Keep OTel export optional

Sources:

- OpenTelemetry GenAI conventions
- Observability export goals
- Project scope constraints

Project decision:

OpenTelemetry-shaped export is a later optional export layer, not a V1 core
dependency.

Implementation impact:

- The canonical data model remains JSONL traces plus derived metrics.
- JSON metrics export is the first export target if export is implemented.
- Prometheus textfile export can come next.
- OTel-shaped spans can be added after the trace model stabilizes.
- Export code consumes canonical metrics and trace records.

Why this matters:

- OTel gives useful vocabulary and future integration potential.
- Making it core too early would add scope and dependency complexity.
- The project should not become an observability platform.

What to avoid:

- Do not require an OTel collector for local reports.
- Do not make OTel the internal trace storage format.
- Do not chase complete semantic-convention coverage in V1.
- Do not let export work delay benchmark, trace, metrics, report, replay, or
  diff functionality.

## Takeaway: Keep eval frameworks out of V1 core

Sources:

- OpenAI Evals
- Anthropic eval writing guidance
- Project product boundary

Project decision:

Inference Autopsy is an inference profiling and regression tool, not a model
quality evaluation framework.

Implementation impact:

- Workload profiles can learn from eval design discipline, but they measure
  serving behavior.
- V1 does not implement grading, LLM-as-judge, task scoring, or dataset
  management.
- Future work may combine eval workloads with latency traces, but that is not
  part of the core build.

Why this matters:

- It keeps the project focused on AI infrastructure.
- It prevents scope creep into a separate and very large product category.
- It helps explain the difference between "is the model good?" and "is the
  endpoint serving the model reliably and fast?"

What to avoid:

- Do not build an eval runner in V1.
- Do not add grading logic.
- Do not create benchmark workloads that require subjective scoring.
- Do not position the project as a replacement for OpenAI Evals or Anthropic
  eval workflows.

## Takeaway: Trace the full AI system workflow

Sources:

- Project scope upgrade
- Workflow tracing concepts
- Retrieval and prompt assembly tradeoff design

Project decision:

Inference Autopsy should trace retrieval latency, prompt assembly latency, LLM
latency, tool latency, and end-to-end latency instead of only model latency.

Implementation impact:

- The trace model needs stage boundaries.
- Reports need a workflow view in addition to model latency views.
- The benchmark runner must preserve context for retrieval and tool stages.
- The project can explain where time was spent across the full system.

What to avoid:

- Do not collapse all stages into one total latency number.
- Do not treat LLM latency as the whole system.
- Do not make the workflow trace depend on backend internals.

## Takeaway: Pair latency with evaluation outcomes

Sources:

- Evaluation outcome concepts
- Production tradeoff design
- Escaped-regression requirement

Project decision:

Inference Autopsy should record question, retrieved docs, answer, expected
answer, retrieval recall, answer correctness, and latency together when the
workflow uses retrieval or evaluation.

Implementation impact:

- The trace or evaluation record must hold quality and latency side by side.
- The report should show latency/quality tradeoffs.
- Regression detection should catch cases where latency is stable but quality
  degrades.

What to avoid:

- Do not build a latency-only benchmark and call it complete.
- Do not separate quality evaluation from trace evidence.
- Do not miss regressions where model latency stays flat but retrieval quality
  falls.

## Takeaway: Benchmark agent and tool workflows explicitly

Sources:

- Agent/tool benchmark concepts
- AI engineering internship relevance

Project decision:

Inference Autopsy should support agentic tasks with tool-call counts, tool
latency, success, cost, and end-to-end latency.

Implementation impact:

- The schema needs tool-related fields.
- The report needs cost and success visibility.
- Benchmarking should expose whether more tool calls made the agent worse.

What to avoid:

- Do not measure only model time for an agent run.
- Do not ignore cost.
- Do not assume fewer tool calls automatically mean a better result.
