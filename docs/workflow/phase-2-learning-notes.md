# Phase 2 Learning Notes

## Purpose

Capture the key concepts to understand before building the real HTTP client and
stream parser for Phase 2.

## Reference When

Use this while learning Phase 2 and before implementing the first real
OpenAI-compatible request path.

## AI Agents Must Obey

Keep these notes concise and practical. Expand only when the project reaches the
corresponding implementation step.

## Topic 1: OpenAI-Compatible Chat Completions

The Phase 2 protocol boundary is the OpenAI-style chat completions API:

```txt
POST /v1/chat/completions
```

Core request fields:

```txt
model
messages
temperature
max_tokens
stream
```

Core request shape:

```json
{
  "model": "<model-id-from-/v1/models>",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Write a haiku about GPUs."}
  ],
  "temperature": 0.2,
  "max_tokens": 128,
  "stream": true
}
```

Typical non-streaming response fields:

```txt
id
object
created
model
choices
usage
```

Typical streaming chunk shape:

```json
{"choices":[{"delta":{"role":"assistant"}}]}
{"choices":[{"delta":{"content":"Hello"}}]}
{"choices":[{"delta":{"content":" world"}}]}
{"choices":[{"finish_reason":"stop","delta":{}}]}
```

The stream usually ends with:

```txt
data: [DONE]
```

Important notes:

- `messages` is the main input surface.
- `model` must match an ID actually served by the endpoint, such as an ID from
  `/v1/models`.
- `stream=true` is required for token timing.
- Not every chunk contains token text.
- First byte and first token are separate events.
- Providers vary, but this is the V1 compatibility boundary.

## Topic 2: HTTPX Async Basics

HTTPX is the HTTP client library for the real request path in Phase 2.

Core concepts:

```txt
httpx.AsyncClient
await client.post(...)
async with client.stream(...)
timeouts
exceptions
```

Important notes from the official docs:

- Use `httpx.AsyncClient` for async requests.
- Reuse the client instead of creating a new one in a hot loop.
- Use `async with` so the client closes cleanly.
- Use `async with client.stream(...)` for streaming responses.
- `response.aiter_lines()` is a good fit for SSE-style line parsing.
- HTTPX enforces timeouts by default.
- Useful error families include `RequestError`, `HTTPStatusError`, and timeout
  exceptions such as `ReadTimeout`.

Project fit:

- One real request in Phase 2 uses `AsyncClient`.
- Later concurrency also uses the same client foundation.
- Streaming and timeout handling must map cleanly into `TraceRecord`.

## Topic 3: SSE Streaming Format

Server-Sent Events are line-oriented responses that usually look like:

```txt
data: {"choices":[{"delta":{"role":"assistant"}}]}

data: {"choices":[{"delta":{"content":"Hello"}}]}

data: {"choices":[{"delta":{"content":" world"}}]}

data: [DONE]
```

Important notes:

- SSE is not one JSON document; it is a stream of event lines.
- Empty lines separate events.
- Not every event contains token text.
- A role-only chunk is not the first generated token.
- `[DONE]` means the stream is finished.
- Real providers may send malformed or partial chunks, so the parser must be
  tolerant without hiding errors.

Project fit:

- `response.aiter_lines()` maps naturally onto SSE.
- The parser should turn SSE lines into token events and finish markers.
- TTFB and TTFT depend on handling early non-token chunks correctly.

## Topic 4: TTFB vs TTFT vs ITL

These three metrics describe different parts of the user-visible response path:

```txt
TTFB = time to first response byte
TTFT = time to first generated token
ITL = inter-token latency
```

Important notes:

- TTFB can happen before TTFT.
- A role-only chunk may count for TTFB but not for TTFT.
- TTFT captures the delay before the first real generated text appears.
- ITL describes the gaps between generated tokens after generation has started.
- High TTFT with normal ITL suggests pre-generation delay.
- Normal TTFT with high ITL suggests slow decode or stream slowness.

Project fit:

- TTFB, TTFT, and ITL must be recorded separately.
- They should not be collapsed into one generic latency number.
- Diagnosis depends on their differences, not just their absolute values.

## Topic 5: Mapping SSE Chunks to Timestamps

The parser must map protocol events into trace timings:

```txt
request_start -> local monotonic zero point
first response bytes -> first_byte
first generated text token -> first_token
each later generated token -> token_times_ms entries
stream completion -> request_end
```

Important notes:

- A role-only chunk is not the first token.
- A chunk with no `delta.content` is not a token event.
- `[DONE]` marks stream completion, not the first token.
- Partial failures may still have valid `first_byte`, `first_token`, and some
  `token_times_ms`.

Project fit:

- TTFB comes from the first response activity.
- TTFT comes from the first real generated content token.
- ITL is derived from the token timestamp list.

## Topic 6: Parser Behavior

The Phase 2 parser should turn streamed SSE lines into structured events.

Core event types:

```txt
role_chunk
content_chunk
finish_chunk
done_marker
empty_line
malformed_chunk
```

Core parser responsibilities:

- Ignore blank separators safely.
- Recognize `data: [DONE]`.
- Parse JSON payloads after `data:`.
- Treat role-only chunks as metadata, not token events.
- Treat chunks with `delta.content` as generated text events.
- Preserve parse failures as structured errors.

Project fit:

- The parser should not compute p95 or error rates.
- The parser should not decide diagnosis labels.
- The parser should produce events that the trace-mapping layer can turn into
  `first_byte`, `first_token`, `token_times_ms`, and `request_end`.

## Topic 7: Trace-Mapping Layer

The trace-mapping layer turns parser events and transport outcomes into
`TraceRecord` fields.

Core responsibilities:

```txt
set first_byte
set first_token
append token_times_ms
set request_end
set finish_reason
set status
set structured error
```

Important notes:

- The parser says what a chunk means.
- The trace-mapping layer says what trace fields change because of that meaning.
- Partial failures should preserve all valid timing evidence gathered so far.
- Failed requests are still valid trace records.

Project fit:

- This is the bridge from HTTP plus SSE behavior to the canonical trace schema.
- The metrics layer depends on this mapping being correct.

## Topic 8: Single-Request Flow

The first real Phase 2 milestone is one end-to-end request:

```txt
CLI input
-> build request payload
-> send one OpenAI-compatible request
-> stream and parse SSE lines
-> map events into trace state
-> finalize one TraceRecord
-> print a small summary or write JSONL
```

Important notes:

- Start with one request before building concurrency.
- The real request path should produce the same trace shape as fake traces.
- Partial failures should still produce valid trace evidence.
- The CLI should stay thin and delegate to transport, parser, and trace-mapping
  modules.

Project fit:

- This is the bridge from Phase 1 fake traces to Phase 2 real traces.
- Once this works, the benchmark runner later just repeats the same path many
  times.

Current implementation files:

- `autopsy/client/openai_compatible.py`: HTTPX request path and trace mapping.
- `autopsy/client/stream_parser.py`: tolerant SSE line parser.
- `autopsy/cli.py`: thin `autopsy single` command.
- `tests/test_openai_compatible.py` and `tests/test_stream_parser.py`: fake
  transport and parser tests.
