Inference Autopsy Midpoint: From One Request To A Real Benchmark
ai
engineering
profiling
benchmarks

I just finished Phase 3 of Inference Autopsy, and the project feels different now.

The earlier phases were about proving that the trace was real. Phase 1 gave me the first spine of the system: schema, fake traces, JSONL, and summary metrics. Phase 2 connected that spine to one real OpenAI-compatible request, including streaming, TTFB, TTFT, token timestamps, and structured errors.

Phase 3 changed the project from "can I measure one request?" into "can I run a workload and preserve evidence for every request?" That is a much more serious question.

The Benchmark Loop Is The Project Becoming Real

The biggest milestone in Phase 3 was adding `autopsy bench`.

That command now runs built-in workload profiles against an OpenAI-compatible endpoint, sweeps through concurrency levels, and writes one JSONL trace per request. The current path looks like this:

profile -> generated prompts -> closed-loop async workers -> TraceRecord JSONL

That is the first version of the product shape I actually wanted. I can point the tool at an endpoint, choose a workload, run multiple requests, and come away with a trace file that can be summarized later.

The important part is not just that requests run in a loop. The important part is that the loop keeps the same evidence discipline as the single-request path. Each request still becomes a trace. Each trace still has status, timings, metrics, replay metadata, profile information, and concurrency labels.

That matters because the benchmark runner should not become a separate little universe. It should produce the same kind of evidence that reports, diffs, replay, and CI gates will use later.

Why Closed-Loop Concurrency Came First

I also learned why benchmark methodology needs restraint.

It would be easy to jump straight into request rates, saturation curves, and impressive-looking load test language. But Phase 3 uses closed-loop concurrency first. That means a fixed number of async workers keep making requests until each concurrency level has completed its quota.

This is simpler, easier to explain, and harder to mislabel.

The trace records include `load_mode = "closed_loop"` because the benchmark should be honest about what it measured. Concurrency is not the same thing as requests per second. A concurrency sweep can show tail latency growth and endpoint behavior under parallel work, but it should not pretend to be an open-loop traffic generator.

That was one of the bigger lessons from this phase: a benchmark is not just code that sends many requests. A benchmark is a claim. The tool has to label that claim carefully.

Profiles Made The Workload Legible

Phase 3 also added built-in workload profiles:

short-chat

rag-long

long-output

These are still simple, but they are enough to make the benchmark more meaningful than one toy prompt repeated forever. Different prompt shapes stress different parts of inference. A short chat prompt is good for endpoint overhead. A RAG-style long prompt is better for prefill and TTFT sensitivity. A long-output prompt makes decode and output throughput more visible.

The prompts are generated deterministically from the request sequence index. That choice feels small, but it matters a lot. Random prompts make two runs harder to compare. Deterministic variation gives me controlled differences without losing reproducibility.

That has become a theme of the project: every feature has to answer the reproducibility question. If I cannot explain why a request happened, what shape it had, and how to replay or compare it later, then the benchmark is not giving me strong evidence yet.

The Hard Part Was Not Just Async

The obvious challenge in Phase 3 was concurrency. The runner needed async workers, shared counters, sequence assignment, file writes, and progress updates.

But the deeper challenge was keeping concurrency from damaging the trace story.

Each request needed a stable sequence index. Each concurrency level needed to be labeled. All records in one benchmark needed the same run ID. Writes needed to be append-friendly without corrupting the JSONL file. Provider errors still had to become valid trace records instead of crashing the whole run.

That last part is important. A benchmark where failures disappear is lying by omission. If an endpoint returns a 500, times out, or fails partway through, that is not noise to throw away. That is part of the system behavior.

Phase 3 made that principle more concrete for me. Success traces are useful, but failure traces are often where the diagnosis starts.

What I Learned About Trace-First Design

The phrase "trace-first" feels less abstract after this phase.

At the beginning, JSONL traces felt like a storage choice. Now they feel more like the center of gravity for the whole tool.

The runner does not need to compute every final answer while the benchmark is running. Its job is to preserve request-level evidence. The metrics layer can summarize that evidence later. Reports can visualize it. Diffs can compare it. CI gates can enforce it.

That separation keeps the product cleaner. The benchmark runner records what happened. The metrics layer interprets it. The report layer explains it.

I can see why this matters more clearly now. If the runner becomes the only place where metrics exist, the system becomes fragile. If every command computes metrics differently, the tool becomes untrustworthy. But if every command reads the same trace evidence, the project has a much stronger foundation.

What Got Easier To Explain

Phase 3 also made the interview story sharper.

Before this phase, I could say that Inference Autopsy measured real streaming behavior for one request. That was useful, but still narrow.

Now I can say the tool runs workload profiles, performs closed-loop concurrency sweeps, writes one durable trace per request, preserves failures as data, and lets later commands compute metrics from the saved evidence.

That is a much better story.

It also gives me a cleaner way to explain the project architecture:

CLI -> workload runner -> OpenAI-compatible client -> SSE parser -> JSONL traces -> metrics

Each layer has a job. The CLI stays thin. The runner coordinates work. The client handles the request path. The parser understands streaming chunks. The trace file becomes the source of truth.

That kind of separation is not glamorous, but it is what makes the project feel like engineering instead of a demo script.

The Challenges I Still See

Finishing Phase 3 also made the next gaps more obvious.

The benchmark can now produce useful traces, but the reporting story is still ahead. Right now, `summarize` gives a basic view of counts and latency percentiles. That is not enough for the full product. The next step is turning these traces into a report that can show concurrency behavior, latency percentiles, request failures, token gaps, and the worst individual requests.

The workload profiles are also still early. They are useful enough for Phase 3, but the project will eventually need richer profile definitions, better input length control, and more realistic workload shapes.

There is also a careful line to hold around claims. Inference Autopsy is a black-box profiler. It can show externally visible symptoms and patterns. It should not pretend to see GPU scheduler internals, cache hits, or backend batching decisions unless the backend exposes those signals.

That humility is part of making the tool credible.

Where The Project Stands Now

At this midpoint, Inference Autopsy has a working foundation:

trace schema

JSONL trace storage

fake trace generation

summary metrics

real OpenAI-compatible single requests

tolerant streaming parsing

non-streaming fallback

structured provider and transport errors

built-in workload profiles

closed-loop concurrency sweeps

append-friendly benchmark output

That is enough for the project to start producing real evidence, not just scaffolding.

What I have learned is that performance tooling is mostly about disciplined boundaries. A vague benchmark gives vague answers. A trace-first benchmark gives you something you can inspect, replay, summarize, and challenge.

Phase 3 did not finish Inference Autopsy. It made the project honest enough for the next phases to matter.

The tool can now run a workload. The next job is to make the results impossible to misunderstand.
