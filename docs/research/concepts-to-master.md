# Concepts to Master

This file is the study checklist for Inference Autopsy. Each concept should be
learned only deeply enough to build the project well and explain the relevant
tradeoffs in a technical conversation.

## Streaming APIs and SSE

What I need to know:

- SSE means server-sent events: the server keeps one HTTP response open and
  sends incremental `data:` events.
- OpenAI-compatible streaming usually sends JSON chunks followed by
  `data: [DONE]`.
- A streaming chunk may contain a token, role metadata, tool-call metadata,
  provider-specific fields, empty content, or an error.
- TTFB is measured when the first response bytes arrive.
- TTFT is measured when the first generated token arrives.
- TTFB and TTFT can differ because the server may send non-token metadata before
  the first generated token.
- Streaming parsers must handle partial responses, malformed chunks, delayed
  first tokens, timeout cases, and provider quirks without corrupting traces.

Why it matters for this project:

- Inference Autopsy depends on token-level streaming traces.
- The project's strongest low-level systems claim is a tolerant SSE parser.
- Correct TTFT, ITL, stream stall, and partial-response metrics require reliable
  streaming event handling.
- Bad parser behavior would make every downstream metric untrustworthy.

How I would explain it in a conversation:

- "The endpoint streams tokens over a long-lived HTTP response. I treat the
  stream as evidence: first byte, first token, each token timestamp, completion,
  and any error state are all recorded. Real providers do not always send clean
  token chunks, so the parser has to tolerate role-only chunks, malformed JSON,
  delayed first tokens, and partial streams while still preserving whatever
  timing evidence exists."

What I do not need for V1:

- Full support for every provider's proprietary streaming protocol.
- Browser `EventSource` support.
- Bidirectional streaming.
- Tool-call streaming reconstruction beyond recording basic chunk behavior.
- Perfect semantic parsing of every possible OpenAI-compatible extension.

## Async Python and Concurrency

What I need to know:

- `asyncio` is useful for IO-bound workloads where many requests spend most of
  their time waiting on network responses.
- `httpx.AsyncClient` can manage concurrent HTTP requests and connection reuse.
- Tasks can be scheduled concurrently with `asyncio.create_task` or task groups.
- Semaphores can limit concurrency.
- Timeouts and cancellation must be explicit.
- Exceptions inside concurrent tasks must be captured so one failed request does
  not destroy the whole benchmark run.
- Streaming loops need careful cleanup so connections are not leaked.

Why it matters for this project:

- The benchmark runner needs many in-flight requests without using one thread
  per request.
- Async execution makes concurrency sweeps practical.
- Timeout, cancellation, and partial failure behavior directly affect trace
  correctness.
- The runner must keep producing valid traces even when some requests fail.

How I would explain it in a conversation:

- "The workload is IO-bound because each benchmark worker mostly waits for HTTP
  responses and streamed tokens. Async Python lets one process manage many
  in-flight requests efficiently. I used explicit concurrency limits, timeouts,
  and per-request error capture so failed or slow requests become trace records
  instead of crashing the benchmark."

What I do not need for V1:

- Multiprocessing.
- Distributed workers.
- Custom event loops.
- Advanced scheduler internals.
- Kernel-level networking optimization.
- A full load-testing cluster.

## Closed-Loop vs Open-Loop Load

What I need to know:

- Closed-loop concurrency means a fixed number of workers each send a request,
  wait for completion, then send the next request.
- Open-loop request rate means requests are launched according to a target
  arrival rate regardless of whether previous requests have completed.
- Closed-loop load answers "what happens with N concurrent users/workers?"
- Open-loop load answers "what happens when traffic arrives at X requests per
  second?"
- These modes produce different system behavior and should not be mixed without
  labeling.
- Closed-loop tests can hide queue growth because request arrival slows when
  responses slow down.
- Open-loop tests can expose saturation more aggressively because arrivals
  continue even when the service is falling behind.

Why it matters for this project:

- Inference Autopsy wants to detect queueing and saturation symptoms.
- The report must label whether results came from concurrency or request-rate
  tests.
- Interviewers may ask whether "concurrency 16" means the same thing as "16
  requests per second"; it does not.

How I would explain it in a conversation:

- "I separate closed-loop concurrency from open-loop request rate because they
  answer different questions. Closed-loop concurrency models a fixed number of
  users or workers. Open-loop request rate models traffic arriving at a target
  rate even if the server slows down. Saturation and queueing analysis is more
  meaningful when the load mode is explicit."

What I do not need for V1:

- A perfect production traffic simulator.
- Multi-node coordinated open-loop load generation.
- Advanced arrival distributions beyond simple fixed or jittered rates.
- Full queueing theory implementation.

## Queueing and Saturation

What I need to know:

- Queueing occurs when requests wait before being processed because the service
  is busy or rate limited.
- Saturation occurs when adding more load no longer increases useful throughput
  and instead increases latency or errors.
- Black-box tools cannot directly observe the internal queue, scheduler, GPU, or
  batching state.
- Externally visible symptoms can still be useful: TTFT inflation, p99 growth,
  throughput plateau, timeout growth, and error-rate inflection.
- If TTFT grows sharply under load while ITL stays mostly stable, the slowdown is
  likely before or at the start of generation rather than during token decode.
- Tail amplification compares high-load tail latency against low-load tail
  latency.

Why it matters for this project:

- Queueing and saturation analysis make the project feel like AI infrastructure,
  not just basic benchmarking.
- This supports the diagnosis labels `Queue Kraken` and `Saturation Cliff`.
- It gives me a strong conversation topic around production inference behavior.

How I would explain it in a conversation:

- "Since the tool is black-box, I cannot see the backend queue directly. Instead
  I look for symptoms: p99 rising faster than p50, TTFT increasing with
  concurrency, throughput flattening, and errors appearing at higher load. If
  ITL stays stable while TTFT grows, that suggests requests are waiting before
  generation rather than decoding slowly."

What I do not need for V1:

- Backend scheduler instrumentation.
- GPU utilization metrics.
- Formal queueing model fitting.
- Distributed saturation testing.
- Automatic capacity planning recommendations.

## KV Cache and Prefix Caching

What I need to know:

- During autoregressive generation, models reuse key/value tensors from previous
  context instead of recomputing attention for all previous tokens each step.
- KV cache memory can become a major serving constraint.
- Prefix caching can reuse computation for shared prompt prefixes across
  requests when the backend supports it.
- Repeated system prompts, repeated RAG context prefixes, and exact prompt reuse
  can benefit from prefix caching.
- A black-box client usually cannot prove whether a cache hit occurred.
- It can compare cold, warm, repeated-prefix, and repeated-exact workloads to
  measure cache-sensitive latency behavior.

Why it matters for this project:

- Cache-aware benchmarking is one of the project's differentiators.
- It helps explain why warm benchmark results may hide poor cold performance.
- It supports labels like `Cache Mirage` and later `Prefix Cache Savior`.
- It creates a natural bridge to vLLM prefix caching and PagedAttention
  discussions.

How I would explain it in a conversation:

- "I treat cache behavior carefully because the tool is black-box. I do not say
  a KV cache definitely hit or missed. Instead, I run cold, warm,
  repeated-prefix, and repeated-exact workloads and compare TTFT. If repeated
  prefixes are much faster than cold long prompts, that is evidence of
  cache-sensitive latency or prefix-reuse benefit."

What I do not need for V1:

- Implementing a cache.
- Reading backend KV cache state.
- Proving exact cache hits or misses.
- Supporting every backend's cache configuration.
- Optimizing cache eviction policies.

## PagedAttention

What I need to know:

- PagedAttention is a serving technique associated with vLLM that manages KV
  cache memory using a paging-inspired design.
- The problem it addresses is that KV cache memory can be large, fragmented, and
  difficult to manage efficiently across many requests.
- Better KV cache management can improve throughput and make serving long or
  concurrent requests more efficient.
- PagedAttention is backend-internal; a black-box profiler does not observe it
  directly.
- Understanding it helps explain why long prompts, many concurrent requests, and
  cache behavior affect LLM serving performance.

Why it matters for this project:

- It gives me deeper backend context for symptoms Inference Autopsy observes.
- It helps me discuss vLLM intelligently without pretending my tool measures
  internal memory pages.
- It connects long-context latency, concurrency pressure, and cache behavior to
  real serving-system design.

How I would explain it in a conversation:

- "PagedAttention is relevant background because it shows how important KV cache
  memory management is for LLM serving. My tool does not inspect PagedAttention
  internals, but if long-context or high-concurrency workloads show TTFT growth,
  tail amplification, or throughput plateaus, I can discuss how backend memory
  and scheduling mechanisms such as KV cache management might contribute."

What I do not need for V1:

- Reimplementing PagedAttention.
- Proving vLLM's internal memory behavior.
- GPU kernel details.
- Writing a model server.
- Deep CUDA memory management.

## Trace-Based Reproducibility

What I need to know:

- A benchmark result is much more useful when the raw request-level evidence is
  saved.
- JSONL is append-friendly, easy to inspect, and easy to process later.
- Trace records should include inputs or prompt shape, model settings, load
  settings, timings, token timestamps, status, and errors.
- Metrics should be computed from saved traces rather than transient runner
  state.
- Replay requires either full prompts or enough template/seed information to
  regenerate prompts.
- Hash-only traces are useful for privacy and comparison but cannot support
  exact replay.

Why it matters for this project:

- Trace-based reproducibility is the core product wedge.
- It enables report generation after the run, baseline/candidate diffing,
  replay, CI artifacts, and debugging.
- It makes benchmark claims defensible because every metric can point back to
  saved evidence.

How I would explain it in a conversation:

- "I designed the tool around traces instead of one-off terminal timings. The
  runner records request-level JSONL evidence, and the metrics engine reads that
  evidence later. That means reports, diffs, replay, and CI gates all use the
  same source of truth. It also makes the benchmark debuggable when a provider
  returns partial streams or errors."

What I do not need for V1:

- A database.
- Hosted trace storage.
- Distributed trace ingestion.
- Perfect deterministic model outputs.
- Storing sensitive prompts by default.

## Benchmark Methodology

What I need to know:

- Benchmark results depend heavily on workload shape, input length, output
  length, concurrency, request rate, timeout policy, warmup policy, streaming
  mode, and token counting method.
- Median metrics are not enough; tail metrics matter.
- Synthetic toy prompts can hide real bottlenecks.
- Failed and timed-out requests must be included in reliability metrics.
- Warmup and cache behavior should be labeled so results are not misleading.
- Methodology metadata belongs in reports.

Why it matters for this project:

- The report needs to be trusted by engineers.
- Without methodology metadata, a benchmark result is hard to reproduce or
  interpret.
- This protects the project from becoming a shallow benchmark script.

How I would explain it in a conversation:

- "The methodology is part of the result. I record the model, endpoint hash,
  profile, concurrency or request rate, request count, timeout policy, streaming
  mode, cache mode, token counting method, and prompt recording mode. That way a
  report does not just say 'p95 was slow'; it explains under what workload and
  measurement conditions the result happened."

What I do not need for V1:

- A comprehensive benchmark suite for every workload type.
- Perfect production traffic replay.
- Statistical significance tooling.
- Automated benchmark recommendation systems.
- Hardware-level profiling.

## CI Regression Gates

What I need to know:

- A regression gate compares a baseline run and a candidate run.
- Gates can use relative thresholds, absolute thresholds, and multipliers.
- Gate failures should exit non-zero in CI.
- Invalid gate expressions should fail closed.
- Output should show baseline value, candidate value, change, and threshold.
- CI should upload traces and reports as artifacts when possible.

Why it matters for this project:

- CI gates turn benchmarking into an engineering workflow.
- They make the project practical for preventing deployment regressions.
- They support one of the strongest resume bullets.

How I would explain it in a conversation:

- "The diff command compares saved baseline and candidate traces using canonical
  metrics. A gate like `ttft_p95 > +20%` fails the build if the candidate's p95
  first-token latency regresses beyond the threshold. The key is that CI is not
  rerunning ad hoc calculations; it is evaluating metrics from reproducible
  trace artifacts."

What I do not need for V1:

- A full policy engine.
- A hosted baseline registry.
- Complex expression language features.
- Automatic flake detection.
- Multi-branch performance history dashboards.

## Observability and OTel GenAI

What I need to know:

- OpenTelemetry provides common concepts for traces, metrics, spans, attributes,
  and exporters.
- GenAI semantic conventions aim to standardize how model calls and AI workload
  telemetry are represented.
- Useful attributes may include model name, provider, operation, token counts,
  status, and latency.
- OTel can be useful as an export target, but it should not become the core data
  model for V1.
- Inference Autopsy's canonical source of truth should remain JSONL traces and
  derived metrics.

Why it matters for this project:

- Observability export is a good extension story.
- It helps position the project as compatible with production telemetry
  workflows.
- It gives me vocabulary for talking to infra teams.
- It should stay optional so V1 does not turn into a full observability product.

How I would explain it in a conversation:

- "The core tool records its own JSONL traces because that is simple, portable,
  and replayable. But the trace model is designed so important fields like model,
  endpoint hash, token counts, latency, status, and error type could later be
  exported into OpenTelemetry-shaped spans or metrics using GenAI conventions.
  I kept that as an export layer rather than making OTel the core dependency."

What I do not need for V1:

- Running an OTel collector.
- Full semantic-convention coverage.
- Vendor-specific observability integrations.
- Grafana dashboards.
- Production distributed tracing.
- OTel as the internal trace storage format.

## Evals vs Inference Profiling

What I need to know:

- Evals measure model behavior, task quality, correctness, safety, or preference
  alignment.
- Inference profiling measures serving behavior: latency, throughput,
  reliability, streaming quality, and regressions.
- A model can score well on evals but be too slow or unreliable for production.
- A model can be fast but produce low-quality answers.
- Eval frameworks can inspire workload design, but Inference Autopsy is not an
  eval framework in V1.

Why it matters for this project:

- It clarifies project positioning.
- It prevents scope creep into model-quality evaluation.
- It helps me explain why OpenAI Evals and Anthropic eval writing are background
  knowledge rather than core implementation dependencies.
- It creates a future direction: combine quality evals with latency traces.

How I would explain it in a conversation:

- "Evals and inference profiling answer different questions. Evals ask whether
  the model behavior is good for a task. Inference profiling asks whether the
  endpoint serves that model fast and reliably. Inference Autopsy focuses on the
  second question. A future extension could run eval workloads through the same
  trace pipeline to measure quality and serving performance together."

What I do not need for V1:

- A grading framework.
- LLM-as-judge evaluation.
- Dataset management.
- Human preference evaluation.
- Safety eval suites.
- Replacing OpenAI Evals or Anthropic eval workflows.

## Workflow Tracing and AI System Profiling

What I need to know:

- An AI system is bigger than the LLM call.
- Common stages include retrieval, prompt assembly, tool use, model
  generation, and final response assembly.
- Each stage can have its own latency profile and failure mode.
- A system can get worse even if model latency stays constant.
- Tracing stage boundaries makes it possible to see where time was spent.
- Workflow traces should preserve enough structure to compare latency and
  quality together.

Why it matters for this project:

- This is the step that makes the project stand out more than a plain LLM
  benchmark.
- It turns the tool into an AI system profiler instead of a model-only profiler.
- It lets me explain why a production assistant regressed even if the model
  stage looked fine.

How I would explain it in a conversation:

- "The model call is only one stage. A production AI system also spends time on
  retrieval, prompt assembly, tool use, and final answer composition. I want
  Inference Autopsy to trace those boundaries so I can see whether the system
  got slower because retrieval drifted, prompt assembly got heavier, a tool
  started taking longer, or the model itself regressed."

What I do not need for V1:

- Full distributed tracing across every microservice.
- Every possible workflow stage type.
- Deep backend instrumentation of all retrieval systems.
- A complete agent orchestration platform.

## Evaluation Outcomes and Tradeoffs

What I need to know:

- Good AI systems are not just fast; they are correct enough and useful enough.
- Evaluation outcomes can include question, retrieved docs, answer, expected
  answer, retrieval recall, answer correctness, and latency.
- A system can improve latency while hurting answer quality.
- A system can improve answer quality while hurting latency.
- Tradeoffs should be measured together, not separately.

Why it matters for this project:

- This is how the project becomes a production tradeoff tool.
- It lets me say whether an optimization made the system better or merely
  faster.
- It directly supports the escaped-regression question.

How I would explain it in a conversation:

- "I do not want a benchmark that only says the model got faster. I want to
  know whether the retrieval stage got worse, whether the answer correctness
  declined, and whether the end-to-end user outcome changed. That is the kind of
  tradeoff real production teams care about."

What I do not need for V1:

- A full eval platform.
- Human preference labeling infrastructure.
- LLM-judge sophistication.
- Dataset curation tooling.

## Agent and Tool Benchmarks

What I need to know:

- Agentic systems do work by calling tools.
- Tool calls have their own latency, count, cost, and failure behavior.
- A fast agent that makes many unnecessary tool calls may still be bad.
- Benchmarking agents requires recording task success and cost alongside
  latency.
- Tool latency should be separate from model latency.

Why it matters for this project:

- This is the next level up from pure chat benchmarking.
- It makes the project much more relevant to real AI engineering roles.
- It helps me discuss tradeoffs like cost, latency, and task success together.

How I would explain it in a conversation:

- "For agent benchmarks, I want to know whether the task succeeded, how many
  tool calls it used, what those tool calls cost, and how long the whole flow
  took. That lets me see whether a supposedly faster agent was actually worse
  because it made more tool calls or failed the task."

What I do not need for V1:

- A general agent orchestration framework.
- A marketplace of tools.
- Full tool-call semantic parsing for every provider.
- Production billing integration.
