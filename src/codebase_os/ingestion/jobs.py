from dataclasses import dataclass
from .base import RepositorySnapshot


@dataclass(frozen=True)
class IngestionResult:
    repository_id: str
    commit: str
    indexed: bool
    file_count: int


class IngestionJobRunner:
    def __init__(self) -> None:
        self._processed: set[tuple[str, str]] = set()

    def process(self, snapshot: RepositorySnapshot) -> IngestionResult:
        key = (snapshot.repository_id, snapshot.commit)
        if key in self._processed:
            return IngestionResult(snapshot.repository_id, snapshot.commit, False, len(snapshot.files))
        self._processed.add(key)
        return IngestionResult(snapshot.repository_id, snapshot.commit, True, len(snapshot.files))

