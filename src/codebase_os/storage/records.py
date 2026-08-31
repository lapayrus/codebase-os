from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RepositoryRecord:
    id: str
    name: str
    provider: str
    branch: str
    commit: str
    indexed_at: datetime


@dataclass(frozen=True)
class EvidenceRecord:
    id: str
    repository_id: str
    commit: str
    path: str
    start_line: int
    end_line: int
    snippet: str
    kind: str


@dataclass(frozen=True)
class MemoryRecord:
    id: str
    repository_id: str
    text: str
    memory_type: str
    created_at: datetime
    stale: bool = False

