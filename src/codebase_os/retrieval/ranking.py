from ..models import Evidence


KIND_WEIGHT = {"structure": 1.0, "source": 0.8, "memory": 0.7, "history": 0.6}


def rank(items: list[Evidence]) -> list[Evidence]:
    return sorted(items, key=lambda item: (-(item.relevance * KIND_WEIGHT.get(item.kind, 0.5)), item.path, item.start_line))

