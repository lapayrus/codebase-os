from ..indexer import RepositoryIndex
from ..models import Evidence


def search(index: RepositoryIndex, terms: list[str], limit: int = 8) -> list[Evidence]:
    return index.structural_evidence(terms)[:limit]


def related_files(index: RepositoryIndex, path: str) -> set[str]:
    imported = index.imports.get(path, set())
    return {candidate for candidate, values in index.imports.items() if candidate != path and (path in values or imported.intersection(values))}

