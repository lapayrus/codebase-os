# Model Provider Adapters Design

## Scope

Add provider-neutral model adapters for OpenAI, OpenAI-compatible endpoints, Anthropic, and Gemini.
The adapters must consume the existing bounded `ContextPacket` and return the existing structured model response shape.

Supported OpenAI-compatible services include Groq, Cerebras, Together, OpenRouter, and equivalent chat-completions
endpoints selected through configuration.

## Architecture and data flow

`Settings` -> `ModelProviderFactory` -> provider adapter -> injectable HTTP transport -> provider API.

The adapter builds a provider-specific request from the question and bounded evidence context, parses provider output
into structured JSON text, and returns it to `ModelGateway` for claim validation.

`ModelGateway` remains responsible for malformed structured output, provider failures, grounded fallback, and stable
local token estimates. Adapters do not log prompts, snippets, credentials, or raw provider responses.

## Interfaces and contracts

- Preserve `ModelProvider.complete(question, packet) -> str`.
- Add an injectable transport protocol so tests never require network access.
- OpenAI and compatible adapters use chat-completions request/response conventions.
- Anthropic uses its messages API, API-key header, and version header.
- Gemini uses its `generateContent` endpoint, API-key authentication, and candidate content parts.
- Factory aliases include `openai`, `groq`, `cerebras`, `together`, `openrouter`, `openai-compatible`, `anthropic`,
  `gemini`, and `none`.
- Base URLs, model names, and API keys come from typed settings; no credentials are hard-coded.

## Error handling

- Network, authentication, rate-limit, timeout, and provider-schema failures raise an adapter error.
- `ModelGateway` catches provider errors and returns the deterministic grounded-retrieval fallback.
- Malformed structured claim JSON remains a validation error and is never treated as a supported claim.
- Missing provider configuration fails readiness and factory construction with a clear configuration error.

## Testing strategy

- Test each adapter request headers, URL, payload, and response extraction with a fake transport.
- Test factory selection and aliases, including `none` mode.
- Test provider failures, malformed provider responses, and missing configuration.
- Run the existing full suite and release gate without network calls.

## Rollout and non-goals

The default remains deterministic `none` mode. A deployment enables one adapter by setting provider, API key, model,
and, for compatible services, base URL.

Streaming, tool calls, provider-specific advanced controls, automatic failover, and live credential validation are
out of scope for this increment.

## Failure-mode review

- Provider response schema changes are contained by adapter parsing and grounded fallback; severity: minor.
- Network and rate-limit failures return grounded retrieval rather than unsupported claims; severity: minor.
- Token metadata varies across providers, so local bounded-packet estimates remain authoritative; severity: minor.
