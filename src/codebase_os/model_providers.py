import json
from typing import Any

from .errors import ProviderError
from .model_transport import JsonTransport
from .retrieval.context import ContextPacket


SYSTEM_PROMPT = "Return only JSON with claims (text, confidence, evidence_ids) and caveats."


def context_text(packet: ContextPacket) -> str:
    return "\n".join(
        f"[{item.commit}] {item.path}:{item.start_line}-{item.end_line}\n{item.snippet}"
        for item in packet.evidence
    )


def response_json(raw: str) -> dict[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ProviderError("Model provider response was not valid JSON") from exc
    if not isinstance(value, dict):
        raise ProviderError("Model provider response was not an object")
    return value


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, base_url: str, api_key: str, model: str, transport: JsonTransport) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.transport = transport

    def complete(self, question: str, packet: ContextPacket) -> str:
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Question: {question}\nEvidence:\n{context_text(packet)}"},
            ],
        }
        try:
            raw = self.transport.request(
                "POST", f"{self.base_url}/chat/completions",
                {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, payload,
            )
            content = response_json(raw).get("choices", [])[0]["message"]["content"]
        except (ProviderError, KeyError, IndexError, TypeError) as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError("OpenAI-compatible response was missing message content") from exc
        except Exception as exc:
            raise ProviderError("OpenAI-compatible provider request failed") from exc
        if not isinstance(content, str) or not content:
            raise ProviderError("OpenAI-compatible response was missing message content")
        return content


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, base_url: str, api_key: str, model: str, transport: JsonTransport) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.transport = transport

    def complete(self, question: str, packet: ContextPacket) -> str:
        payload = {
            "model": self.model,
            "max_tokens": 2048,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": f"Question: {question}\nEvidence:\n{context_text(packet)}"}],
        }
        try:
            raw = self.transport.request(
                "POST", f"{self.base_url}/messages",
                {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}, payload,
            )
            blocks = response_json(raw).get("content", [])
            text = "".join(block.get("text", "") for block in blocks if isinstance(block, dict) and block.get("type") == "text")
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError("Anthropic provider response was invalid") from exc
        if not text:
            raise ProviderError("Anthropic provider response had no text blocks")
        return text


class GeminiProvider:
    name = "gemini"

    def __init__(self, base_url: str, api_key: str, model: str, transport: JsonTransport) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.transport = transport

    def complete(self, question: str, packet: ContextPacket) -> str:
        payload = {"contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\nQuestion: {question}\nEvidence:\n{context_text(packet)}"}]}]}
        try:
            raw = self.transport.request(
                "POST", f"{self.base_url}/models/{self.model}:generateContent",
                {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}, payload,
            )
            parts = response_json(raw).get("candidates", [])[0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
        except (ProviderError, KeyError, IndexError, TypeError) as exc:
            if isinstance(exc, ProviderError):
                raise
            raise ProviderError("Gemini provider response was missing candidate text") from exc
        except Exception as exc:
            raise ProviderError("Gemini provider request failed") from exc
        if not text:
            raise ProviderError("Gemini provider response had no candidate text")
        return text
