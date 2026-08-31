from datetime import datetime, timezone

from codebase_os.indexer import RepositoryIndex
from codebase_os.persistence import PersistentCodebaseService


class RecordingStore:
    def __init__(self):
        self.repositories = {}
        self.evidence = {}
        self.memories = {}

    def save_repository(self, tenant_id, repository):
        self.repositories[tenant_id, repository.id] = repository

    def save_evidence(self, tenant_id, evidence):
        self.evidence.setdefault((tenant_id, evidence.repository_id), []).append(evidence)

    def save_memory(self, tenant_id, memory):
        self.memories.setdefault((tenant_id, memory.repository_id), []).append(memory)


def sample_index():
    return RepositoryIndex(
        name="repo-a",
        root="C:/repo-a",
        commit="abc123",
        files={"main.py": "def answer():\n    return 1\n"},
    )


def test_add_repository_persists_metadata_and_evidence():
    storage = RecordingStore()
    service = PersistentCodebaseService(storage)
    indexed = sample_index()

    service.add_repository(indexed, tenant_id="tenant-a")

    assert storage.repositories["tenant-a", indexed.name].commit == indexed.commit
    assert storage.evidence["tenant-a", indexed.name]


def test_add_memory_persists_with_tenant_scope():
    storage = RecordingStore()
    service = PersistentCodebaseService(storage)

    service.add_memory("repo-a", "remember this", "decision", tenant_id="tenant-a")

    assert storage.memories["tenant-a", "repo-a"][0].text == "remember this"
