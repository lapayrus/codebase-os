from dataclasses import dataclass
from ..models import Evidence
from .ranking import rank


@dataclass(frozen=True)
class ContextPacket:
    evidence: tuple[Evidence, ...]
    token_estimate: int
    omitted_count: int
    commit: str


def build_context_packet(evidence: list[Evidence], commit: str, limit: int = 8, token_budget: int = 1800) -> ContextPacket:
    ranked = rank(evidence)
    selected: list[Evidence] = []
    used = 0
    for item in ranked:
        cost = max(1, len(item.snippet.split()))
        if len(selected) >= limit or used + cost > token_budget:
            continue
        selected.append(item)
        used += cost
    return ContextPacket(tuple(selected), used, max(0, len(ranked) - len(selected)), commit)

