# Model Provider Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers-optimized:subagent-driven-development (recommended) or superpowers-optimized:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tested OpenAI, OpenAI-compatible, Anthropic, and Gemini adapters selectable through configuration.

**Architecture:** Each adapter implements `ModelProvider.complete(question, packet) -> str` and delegates HTTP calls to
an injected transport. The transport is standard-library based and never logs request bodies or credentials. The
existing `ModelGateway` remains the boundary for structured-claim validation and grounded fallback.

**Tech Stack:** Python 3.11+, FastAPI/Pydantic settings, `urllib.request`, pytest, uv.

**Assumptions:** Adapters receive bounded `ContextPacket` values and return provider text containing JSON claims — they
will NOT implement streaming, tools, embeddings, provider failover, or live network tests.

## File structure

- Create `src/codebase_os/model_transport.py`: HTTP transport protocol and standard-library implementation.
- Create `src/codebase_os/model_providers.py`: OpenAI, OpenAI-compatible, Anthropic, and Gemini adapters.
- Create `src/codebase_os/model_factory.py`: provider alias selection and configuration validation.
- Modify `src/codebase_os/config.py`: typed model provider settings already present, with adapter-facing access.
- Modify `src/codebase_os/main.py`: construct readiness/model configuration through the factory boundary.
- Modify `docs/operations.md` and `.env.example`: provider setup and endpoint guidance.
- Create `tests/test_model_providers.py` and `tests/test_model_factory.py`: fake-transport contract tests.

### Task 1: Add the injectable transport contract

**Files:**
- Create: `src/codebase_os/models/transport.py`
- Test: `tests/test_model_providers.py`

**Security flag:** `security` — transports handle API keys, prompts, and repository evidence.

**Does NOT cover:** TLS certificate customization, proxy configuration, streaming, retries, or logging request bodies.

- [x] **Step 1: Write failing test**

Add a fake transport test that asserts the adapter-facing contract can receive method, URL, headers, and JSON payload,
then returns a JSON response body.

```python
def test_transport_contract_receives_json_request():
    transport = RecordingTransport('{"ok": true}')
    assert transport.request("POST", "https://example.test", {"x-api-key": "secret"}, {"a": 1}) == '{"ok": true}'
    assert transport.calls[0][0:2] == ("POST", "https://example.test")
```

- [x] **Step 2: Run test to verify it fails**

Run: `rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp tests/test_model_providers.py::test_transport_contract_receives_json_request`

Expected: FAIL because `RecordingTransport` and the transport contract do not exist.

- [x] **Step 3: Implement minimal change**

Define `JsonTransport(Protocol)` with `request(method, url, headers, payload) -> str`, a standard-library
`UrllibTransport`, and a test-only `RecordingTransport` in the test module. Encode JSON as UTF-8 and decode the response.

- [x] **Step 4: Run test to verify it passes**

Run the command from Step 2.

Expected: PASS with no network access.

### Task 2: Implement OpenAI and OpenAI-compatible adapters

**Files:**
- Create: `src/codebase_os/models/providers.py`
- Create: `src/codebase_os/models/factory.py`
- Test: `tests/test_model_providers.py`, `tests/test_model_factory.py`

**Security flag:** `security` — API keys and bounded code context are sent to external providers.

**Does NOT cover:** provider-specific tools, streaming, image inputs, or automatic failover.

- [x] **Step 1: Write failing tests**

Test `OpenAIProvider` and `OpenAICompatibleProvider` send `Authorization: Bearer <key>`, post to
`<base_url>/chat/completions`, send the configured model and a system instruction requiring JSON claims, and extract
`choices[0].message.content`.
Test factory aliases `openai`, `groq`, `cerebras`, `together`, `openrouter`, and `openai-compatible` to this adapter.

```python
def test_openai_compatible_provider_builds_chat_completion_request():
    transport = RecordingTransport('{"choices":[{"message":{"content":"{\\"claims\\":[]}"}}]}')
    provider = OpenAICompatibleProvider("https://api.example/v1", "key", "model", transport)
    assert provider.complete("Where?", ContextPacket((), 0, 0, "abc")) == '{"claims":[]}'
    method, url, headers, payload = transport.calls[0]
    assert (method, url, headers["Authorization"]) == ("POST", "https://api.example/v1/chat/completions", "Bearer key")
    assert payload["model"] == "model"
```

- [x] **Step 2: Run tests to verify they fail**

Run: `rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp tests/test_model_providers.py tests/test_model_factory.py`

Expected: FAIL because the adapter and factory do not exist.

- [x] **Step 3: Implement minimal change**

Serialize the bounded packet as evidence lines containing path, line range, commit, and snippet. Use one stable JSON
system instruction, the user question as the user message, and parse only the documented response field.

- [x] **Step 4: Run tests to verify they pass**

Run the command from Step 2.

Expected: PASS with fake transport only.

### Task 3: Implement Anthropic adapter

**Files:**
- Modify: `src/codebase_os/models/providers.py`
- Test: `tests/test_model_providers.py`

**Security flag:** `security` — API keys and repository evidence cross an external provider boundary.

**Does NOT cover:** prompt caching, tools, streaming, or provider beta headers.

- [x] **Step 1: Write failing test**

Assert POST to `<base_url>/messages`, `x-api-key`, `anthropic-version`, `content-type`, model, max tokens, system
instruction, and user message are present; extract concatenated text blocks from `content`.

- [x] **Step 2: Run test to verify it fails**

Run: `rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp tests/test_model_providers.py::test_anthropic_provider_extracts_text_blocks`

Expected: FAIL because `AnthropicProvider` does not exist.

- [x] **Step 3: Implement minimal change**

Use `x-api-key` and `anthropic-version: 2023-06-01`; reject missing `content` or missing text blocks with
`ProviderError` and never include the API key in the exception text.

- [x] **Step 4: Run test to verify it passes**

Run the command from Step 2.

Expected: PASS.

### Task 4: Implement Gemini adapter

**Files:**
- Modify: `src/codebase_os/models/providers.py`, `src/codebase_os/models/factory.py`
- Test: `tests/test_model_providers.py`, `tests/test_model_factory.py`

**Security flag:** `security` — the Gemini key and repository evidence are sent to an external endpoint.

**Does NOT cover:** safety settings, multimodal parts, streaming, or function calling.

- [x] **Step 1: Write failing test**

Assert POST to `<base_url>/models/<model>:generateContent`, API key is sent through the configured query/header
contract, contents contain the question and bounded evidence, and candidate text is extracted.

- [x] **Step 2: Run test to verify it fails**

Run: `rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp tests/test_model_providers.py::test_gemini_provider_extracts_candidate_text`

Expected: FAIL because `GeminiProvider` does not exist.

- [x] **Step 3: Implement minimal change**

Use the configured base URL and model, send the key without placing it in response errors, parse the first candidate’s
text parts, and raise `ProviderError` for an empty candidate response.

- [x] **Step 4: Run test to verify it passes**

Run the command from Step 2.

Expected: PASS.

### Task 5: Wire factory, readiness, configuration docs, and release verification

**Files:**
- Modify: `src/codebase_os/models/factory.py`, `src/codebase_os/main.py`, `src/codebase_os/config.py`, `.env.example`,
  `docs/operations.md`, `tests/test_model_factory.py`, `tests/test_api.py`

**Security flag:** `security` — this task validates external credential configuration and readiness gates.

**Does NOT cover:** live credential validation or network health probes; those require deployment secrets and endpoints.

- [x] **Step 1: Write failing tests**

Test `build_model_provider(Settings(...))` returns the selected adapter, returns `None` for `none`, and raises a
configuration error when a selected provider lacks key, model, or required base URL. Test `/ready` reports the selected
provider configuration state.

- [x] **Step 2: Run tests to verify they fail**

Run: `rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp tests/test_model_factory.py tests/test_api.py`

Expected: FAIL because the factory is not wired into readiness.

- [x] **Step 3: Implement minimal change**

Use the existing typed settings, instantiate adapters with `UrllibTransport`, expose supported provider aliases in
`.env.example`, and make readiness use factory validation without making a network request.

- [x] **Step 4: Run focused and full verification**

Run:

```powershell
rtk uv --cache-dir .uv-cache sync --locked --extra dev
rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp
rtk uv --cache-dir .uv-cache run python -m compileall -q src
rtk uv --cache-dir .uv-cache run python -c "from codebase_os.main import app; print(len(app.routes))"
rtk powershell.exe -NoProfile -Command "git diff --check"
```

Expected: all tests pass, compilation succeeds, the route count increases only for intentional readiness changes,
and `git diff --check` reports no errors.

## Stop conditions

- Stop before enabling a provider if adapter tests leak credentials or raw repository snippets in errors.
- Stop before claiming live provider readiness because this plan validates configuration, not external connectivity.
- Keep `none` mode as the deterministic default until a provider is explicitly configured.
