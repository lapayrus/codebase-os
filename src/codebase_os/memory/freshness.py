from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class MemoryReference:
    memory_id: str
    repository_id: str
    commit: str | None
    paths: frozenset[str]


def affected_memory_ids(references: Iterable[MemoryReference], changed_paths: set[str], new_commit: str) -> list[str]:
    affected = []
    for reference in references:
        if reference.commit != new_commit and (not reference.paths or reference.paths.intersection(changed_paths)):
            affected.append(reference.memory_id)
    return affected

