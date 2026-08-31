import pytest

from codebase_os.errors import ProviderError
from codebase_os.model_providers import AnthropicProvider, GeminiProvider, OpenAICompatibleProvider, OpenAIProvider
from codebase_os.retrieval.context import ContextPacket
from codebase_os.models import Evidence


class RecordingTransport:
    def __init__(self, response: str):
        self.response = response
        self.calls = []

    def request(self, method, url, headers, payload):
        self.calls.append((method, url, headers, payload))
        return self.response


def packet():
    evidence = Evidence(repository="demo", commit="abc", path="main.py", start_line=1, end_line=2, snippet="return True")
    return ContextPacket((evidence,), 2, 0, "abc")


def test_transport_contract_receives_json_request():
    transport = RecordingTransport('{"ok": true}')
    assert transport.request("POST", "https://example.test", {"x-api-key": "secret"}, {"a": 1}) == '{"ok": true}'
    assert transport.calls[0][0:2] == ("POST", "https://example.test")


def test_openai_compatible_provider_builds_chat_completion_request():
    transport = RecordingTransport('{"choices":[{"message":{"content":"{\\"claims\\":[]}"}}]}')
    provider = OpenAICompatibleProvider("https://api.example/v1", "key", "model", transport)
    assert provider.complete("Where?", packet()) == '{"claims":[]}'
    method, url, headers, payload = transport.calls[0]
    assert (method, url, headers["Authorization"]) == ("POST", "https://api.example/v1/chat/completions", "Bearer key")
    assert payload["model"] == "model"
    assert payload["messages"][0]["role"] == "system"


def test_openai_provider_uses_same_contract():
    transport = RecordingTransport('{"choices":[{"message":{"content":"{}"}}]}')
    assert OpenAIProvider("https://api.openai.com/v1", "key", "model", transport).complete("Q", packet()) == "{}"


def test_anthropic_provider_extracts_text_blocks():
    transport = RecordingTransport('{"content":[{"type":"text","text":"{"},{"type":"text","text":"}"}]}')
    provider = AnthropicProvider("https://api.anthropic.com", "key", "model", transport)
    assert provider.complete("Where?", packet()) == "{}"
    method, url, headers, payload = transport.calls[0]
    assert (method, url, headers["x-api-key"], headers["anthropic-version"]) == (
        "POST", "https://api.anthropic.com/messages", "key", "2023-06-01"
    )
    assert payload["model"] == "model"


def test_gemini_provider_extracts_candidate_text():
    transport = RecordingTransport('{"candidates":[{"content":{"parts":[{"text":"{}"}]}}]}')
    provider = GeminiProvider("https://generativelanguage.googleapis.com/v1beta", "key", "model", transport)
    assert provider.complete("Where?", packet()) == "{}"
    method, url, headers, payload = transport.calls[0]
    assert (method, url) == ("POST", "https://generativelanguage.googleapis.com/v1beta/models/model:generateContent")
    assert headers["x-goog-api-key"] == "key"
    assert payload["contents"]


def test_provider_rejects_empty_response_without_leaking_key():
    provider = GeminiProvider("https://example.test", "secret-key", "model", RecordingTransport("{}"))
    with pytest.raises(ProviderError, match="provider response") as error:
        provider.complete("Where?", packet())
    assert "secret-key" not in str(error.value)
