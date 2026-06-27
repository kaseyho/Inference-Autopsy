# Known Issues

## Purpose

Track known limitations and defects so agents do not rediscover them.

## Reference When

Use before debugging, planning, or evaluating risk.

## AI Agents Must Obey

Update this file when a meaningful issue is found or resolved.

## Current Known Issues

- Token counting may be approximate when providers do not return usage metadata.
- OpenAI-compatible streaming responses vary across servers.
- Local Ollama examples must use a model ID actually returned by `/v1/models`;
  otherwise `/v1/chat/completions` can return HTTP 404 with a provider
  `model not found` error.
- Hosted measurements include network and provider variance.
- Replay cannot guarantee deterministic model outputs.

## Issue Template

```md
## <short title>

Status: open | investigating | resolved
Owner: <name>
Found: YYYY-MM-DD

Impact:
<who or what is affected>

Notes:
<what is known>

Resolution:
<filled when resolved>
```
