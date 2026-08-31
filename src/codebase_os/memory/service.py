from dataclasses import dataclass, replace
from datetime import datetime, timezone
import uuid


@dataclass(frozen=True)
class ProjectMemory:
    id: str
    tenant_id: str
    repository_id: str
    text: str
    memory_type: str
    source: str
    commit: str | None
    created_at: datetime
    stale: bool = False


class MemoryService:
    def __init__(self) -> None:
        self._items: dict[str, ProjectMemory] = {}

    def add(self, tenant_id: str, repository_id: str, text: str, memory_type: str,
            source: str = "human", commit: str | None = None) -> ProjectMemory:
        item = ProjectMemory(str(uuid.uuid4()), tenant_id, repository_id, text, memory_type, source, commit,
                             datetime.now(timezone.utc))
        self._items[item.id] = item
        return item

    def list(self, tenant_id: str, repository_id: str) -> list[ProjectMemory]:
        return [item for item in self._items.values() if item.tenant_id == tenant_id and item.repository_id == repository_id]

    def mark_stale(self, memory_id: str) -> ProjectMemory:
        item = self._items[memory_id]
        updated = replace(item, stale=True)
        self._items[memory_id] = updated
        return updated

