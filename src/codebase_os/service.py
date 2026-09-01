from collections import defaultdict
import re
import uuid

from .indexer import RepositoryIndex
from .models import Answer, Claim, Evidence, Memory
from .models_gateway import ModelGateway
from .retrieval.context import build_context_packet
from .retrieval.validation import validate_claims


class CodebaseService:
    def __init__(self, gateway: ModelGateway | None = None) -> None:
        self.repositories: dict[str, RepositoryIndex] = {}
        self.memories: dict[str, list[Memory]] = defaultdict(list)
        self.gateway = gateway

    def add_repository(self, index: RepositoryIndex) -> None:
        self.repositories[index.name] = index

    def add_memory(self, repository: str, text: str, memory_type: str) -> Memory:
        memory = Memory(id=str(uuid.uuid4()), repository=repository, text=text, memory_type=memory_type)  # type: ignore[arg-type]
        self.memories[repository].append(memory)
        return memory

    def query(self, question: str, repository: str | None = None, top_k: int = 8) -> Answer:
        index = self._select(repository)
        terms = self._terms(question)
        evidence = index.structural_evidence(terms) + index.evidence_for(terms, top_k=top_k)
        evidence += [Evidence(repository=index.name, commit=index.commit, path="[memory]", start_line=1, end_line=1,
            snippet=m.text, kind="memory", relevance=0.8) for m in self.memories[index.name] if not m.stale and any(t in m.text.lower() for t in terms)]
        evidence = self._dedupe(evidence)
        if not evidence:
            return Answer(question=question, answer="I could not find enough repository evidence to answer this confidently.",
                claims=[], evidence=[], caveats=["Try naming a symbol, endpoint, file, service, or behavior."], repository=index.name, commit=index.commit, tokens_estimate=32)
        packet = build_context_packet(evidence, index.commit, limit=top_k)
        evidence = list(packet.evidence)
        claims = validate_claims(self._claims(evidence), evidence)
        answer_text = " ".join(claim.text for claim in claims) or "The repository contains related evidence, but it is not sufficient for a supported conclusion."
        caveats = ["Structural matches identify likely entry points; runtime wiring may add relationships not visible statically."] if any(item.kind == "structure" for item in evidence) else []
        model = "none"
        if self.gateway is not None:
            try:
                model_response = self.gateway.answer(question, packet, evidence)
            except ValueError:
                model_response = None
                caveats.append("Model response was invalid; showing grounded retrieval evidence.")
            if model_response is not None:
                model_claims = validate_claims(model_response.claims, evidence)
                caveats.extend(model_response.caveats)
                if model_claims:
                    claims = model_claims
                    answer_text = " ".join(claim.text for claim in claims)
                    model = model_response.model
                elif self.gateway.provider is not None:
                    claims = []
                    answer_text = "The model provider did not return a supported answer. Review the cited repository evidence."
        return Answer(question=question, answer=answer_text, claims=claims, evidence=evidence, caveats=caveats,
            repository=index.name, commit=index.commit, tokens_estimate=packet.token_estimate, model=model)

    def _select(self, repository: str | None) -> RepositoryIndex:
        if repository:
            if repository not in self.repositories:
                raise KeyError(repository)
            return self.repositories[repository]
        if not self.repositories:
            raise RuntimeError("No repositories indexed")
        return next(iter(self.repositories.values()))

    @staticmethod
    def _terms(question: str) -> list[str]:
        words = re.findall(r"[A-Za-z_][A-Za-z0-9_./:-]{2,}", question.lower())
        stop = {"where", "what", "which", "does", "this", "that", "with", "from", "into", "about", "show", "give", "the", "and", "for"}
        return list(dict.fromkeys(w for w in words if w not in stop))[:12]

    @staticmethod
    def _claims(evidence: list[Evidence]) -> list[Claim]:
        primary = evidence[0]
        claims = [Claim(text=f"The strongest repository evidence for this question is in {primary.path}, around lines {primary.start_line}-{primary.end_line}.", confidence="high" if primary.kind == "structure" else "medium", evidence_ids=[0])]
        if len(evidence) > 1:
            claims.append(Claim(text=f"Related evidence appears in {evidence[1].path}, suggesting the behavior spans more than one source location.", confidence="medium", evidence_ids=[1]))
        return claims

    @staticmethod
    def _dedupe(items: list[Evidence]) -> list[Evidence]:
        seen = set(); result = []
        for item in items:
            key = (item.path, item.start_line, item.snippet)
            if key not in seen:
                seen.add(key); result.append(item)
        return result
