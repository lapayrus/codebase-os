from dataclasses import dataclass
import json
from typing import Protocol

from .models import Claim, Evidence
from .retrieval.context import ContextPacket


@dataclass(frozen=True)
class ModelResponse:
    claims: list[Claim]
    caveats: list[str]
    model: str
    prompt_tokens: int
    completion_tokens: int


class ModelProvider(Protocol):
    def complete(self, question: str, packet: ContextPacket) -> str: ...


class ModelGateway:
    def __init__(self, provider: ModelProvider | None = None) -> None:
        self.provider = provider

    def answer(self, question: str, packet: ContextPacket, evidence: list[Evidence]) -> ModelResponse:
        if self.provider is None:
            return ModelResponse([], ["No model provider configured; showing grounded retrieval evidence."], "none", packet.token_estimate, 0)
        raw = self.provider.complete(question, packet)
        try:
            payload = json.loads(raw)
            claims = [Claim.model_validate(item) for item in payload.get("claims", [])]
            caveats = [str(item) for item in payload.get("caveats", [])]
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError("Model response was not valid structured JSON") from exc
        return ModelResponse(claims, caveats, getattr(self.provider, "name", "custom"), packet.token_estimate, len(raw.split()))

