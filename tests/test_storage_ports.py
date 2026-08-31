from datetime import datetime, timezone
import pytest

from codebase_os.storage.memory import InMemoryStore
from codebase_os.storage.records import EvidenceRecord, RepositoryRecord


def repository(repository_id: str) -> RepositoryRecord:
    return RepositoryRecord(repository_id, "demo", "local", "main", "abc123", datetime.now(timezone.utc))


def test_storage_is_tenant_scoped():
    store = InMemoryStore()
    store.save_repository("tenant-a", repository("repo-a"))
    store.save_repository("tenant-b", repository("repo-b"))
    assert [r.id for r in store.list_repositories("tenant-a")] == ["repo-a"]
    assert store.get_repository("tenant-a", "repo-b") is None


def test_evidence_requires_owned_repository():
    store = InMemoryStore()
    evidence = EvidenceRecord("e1", "repo-a", "abc123", "main.py", 1, 2, "return 1", "source")
    with pytest.raises(KeyError):
        store.save_evidence("tenant-a", evidence)


def test_evidence_deduplicates_by_id():
    store = InMemoryStore()
    store.save_repository("tenant-a", repository("repo-a"))
    evidence = EvidenceRecord("e1", "repo-a", "abc123", "main.py", 1, 2, "return 1", "source")
    store.save_evidence("tenant-a", evidence)
    store.save_evidence("tenant-a", evidence)
    assert len(store.list_evidence("tenant-a", "repo-a")) == 1

