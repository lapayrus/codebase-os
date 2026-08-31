from collections import defaultdict

from .records import EvidenceRecord, MemoryRecord, RepositoryRecord


class InMemoryStore:
    def __init__(self) -> None:
        self._repositories: dict[tuple[str, str], RepositoryRecord] = {}
        self._evidence: dict[tuple[str, str], list[EvidenceRecord]] = defaultdict(list)
        self._memories: dict[tuple[str, str], list[MemoryRecord]] = defaultdict(list)

    def save_repository(self, tenant_id: str, repository: RepositoryRecord) -> None:
        self._repositories[(tenant_id, repository.id)] = repository

    def get_repository(self, tenant_id: str, repository_id: str) -> RepositoryRecord | None:
        return self._repositories.get((tenant_id, repository_id))

    def delete_repository(self, tenant_id: str, repository_id: str) -> bool:
        key = (tenant_id, repository_id)
        if key not in self._repositories:
            return False
        del self._repositories[key]
        self._evidence.pop(key, None)
        self._memories.pop(key, None)
        return True

    def list_repositories(self, tenant_id: str) -> list[RepositoryRecord]:
        return [record for (owner, _), record in self._repositories.items() if owner == tenant_id]

    def save_evidence(self, tenant_id: str, evidence: EvidenceRecord) -> None:
        if not self.get_repository(tenant_id, evidence.repository_id):
            raise KeyError(evidence.repository_id)
        bucket = self._evidence[(tenant_id, evidence.repository_id)]
        if evidence.id not in {item.id for item in bucket}:
            bucket.append(evidence)

    def list_evidence(self, tenant_id: str, repository_id: str) -> list[EvidenceRecord]:
        return list(self._evidence[(tenant_id, repository_id)])

    def save_memory(self, tenant_id: str, memory: MemoryRecord) -> None:
        if not self.get_repository(tenant_id, memory.repository_id):
            raise KeyError(memory.repository_id)
        bucket = self._memories[(tenant_id, memory.repository_id)]
        if memory.id not in {item.id for item in bucket}:
            bucket.append(memory)

    def list_memories(self, tenant_id: str, repository_id: str) -> list[MemoryRecord]:
        return list(self._memories[(tenant_id, repository_id)])
