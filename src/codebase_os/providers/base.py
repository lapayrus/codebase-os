from dataclasses import dataclass, field
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SnapshotFile:
    path: str
    content: str
    size_bytes: int
    modified_at: datetime


@dataclass(frozen=True)
class RepositorySnapshot:
    provider: str
    repository_id: str
    name: str
    branch: str
    commit: str
    files: tuple[SnapshotFile, ...]
    skipped_paths: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()
    source_permissions: tuple[str, ...] = ()


class RepositoryProvider(Protocol):
    def snapshot(self, repository_id: str, branch: str = "main") -> RepositorySnapshot: ...

