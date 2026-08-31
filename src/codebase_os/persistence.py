import hashlib

from .indexer import RepositoryIndex
from .indexing import IndexDecision, content_version, decide_index, file_hash
from .service import CodebaseService
from .storage.ports import Storage
from .storage.records import EvidenceRecord, MemoryRecord, RepositoryRecord


class PersistentCodebaseService:
    def __init__(self, storage: Storage, query_service: CodebaseService | None = None) -> None:
        self.storage = storage
        self.query_service = query_service or CodebaseService()

    def add_repository(self, index: RepositoryIndex, tenant_id: str) -> None:
        self.query_service.add_repository(index)
        self._save_repository(index, tenant_id, "succeeded")
        self._save_evidence(index, tenant_id)

    def index_repository(self, index: RepositoryIndex, tenant_id: str) -> IndexDecision:
        incoming_version = content_version(index.files)
        existing = self.storage.get_repository(tenant_id, index.name)
        decision = decide_index(
            existing.content_version if existing else None,
            incoming_version,
            existing.indexing_status if existing else None,
        )
        if decision is IndexDecision.UNCHANGED:
            self.query_service.add_repository(index)
            return decision
        previous = existing
        try:
            self._save_repository(index, tenant_id, "indexing", incoming_version)
            self._save_evidence(index, tenant_id)
            self.storage.delete_evidence_except_commit(tenant_id, index.name, index.commit)
            self._save_repository(index, tenant_id, "succeeded", incoming_version)
            self.query_service.add_repository(index)
            return decision
        except Exception:
            if previous is not None:
                self.storage.save_repository(tenant_id, previous)
            raise

    def _save_repository(self, index, tenant_id, status, version=None):
        self.storage.save_repository(
            tenant_id,
            RepositoryRecord(index.name, index.name, "local", "main", index.commit, self._indexed_at(), status, version),
        )

    def _save_evidence(self, index, tenant_id):
        for path, text in index.files.items():
            self.storage.save_evidence(
                tenant_id,
                EvidenceRecord(
                    self._evidence_id(index.name, index.commit, path),
                    index.name,
                    index.commit,
                    path,
                    1,
                    max(1, len(text.splitlines())),
                    text,
                    "source",
                    file_hash(text),
                ),
            )

    def add_memory(self, repository: str, text: str, memory_type: str, tenant_id: str):
        memory = self.query_service.add_memory(repository, text, memory_type)
        self.storage.save_memory(
            tenant_id,
            MemoryRecord(memory.id, repository, memory.text, memory.memory_type, memory.created_at, memory.stale),
        )
        return memory

    def query(self, question: str, repository: str | None = None, top_k: int = 8):
        return self.query_service.query(question, repository, top_k)

    @staticmethod
    def _indexed_at():
        from datetime import datetime, timezone
        return datetime.now(timezone.utc)

    @staticmethod
    def _evidence_id(repository: str, commit: str, path: str) -> str:
        return hashlib.sha256(f"{repository}:{commit}:{path}".encode()).hexdigest()[:32]
