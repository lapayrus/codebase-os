from datetime import datetime, timezone
from dataclasses import replace
import pytest

from codebase_os.storage.memory import InMemoryStore
from codebase_os.storage.postgres import PostgresStore
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


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []
        self.rowcount = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        self.rowcount = 0
        if query.startswith("INSERT INTO repositories"):
            self.connection.repositories[(params[0], params[1])] = params
        elif query.startswith("DELETE FROM repositories"):
            self.rowcount = int(self.connection.repositories.pop((params[0], params[1]), None) is not None)
        elif query.startswith("SELECT"):
            tenant_id, repository_id = params
            self.rows = [
                (record[1], record[2], record[3], record[4], record[5], record[6])
                for (owner, repo_id), record in self.connection.repositories.items()
                if owner == tenant_id and repo_id == repository_id
            ]

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.repositories = {}

    def cursor(self):
        return FakeCursor(self)

    def commit(self):
        pass


def test_postgres_store_isolates_same_repository_id_by_tenant():
    store = PostgresStore(FakeConnection())
    store.save_repository("tenant-a", replace(repository("shared"), name="tenant-a-copy"))
    store.save_repository("tenant-b", replace(repository("shared"), name="tenant-b-copy"))

    assert store.get_repository("tenant-a", "shared").name == "tenant-a-copy"
    assert store.get_repository("tenant-b", "shared").name == "tenant-b-copy"
    assert store.get_repository("tenant-a", "tenant-b-only") is None


def test_memory_delete_cascades_owned_data_without_cross_tenant_deletion():
    store = InMemoryStore()
    store.save_repository("tenant-a", repository("shared"))
    store.save_repository("tenant-b", repository("shared"))
    store.save_evidence("tenant-a", EvidenceRecord("a-evidence", "shared", "abc123", "main.py", 1, 1, "x", "source"))

    store.delete_repository("tenant-a", "shared")

    assert store.get_repository("tenant-a", "shared") is None
    assert store.list_evidence("tenant-a", "shared") == []
    assert store.get_repository("tenant-b", "shared") is not None


def test_postgres_delete_is_tenant_scoped():
    connection = FakeConnection()
    store = PostgresStore(connection)
    store.save_repository("tenant-a", repository("shared"))
    store.save_repository("tenant-b", repository("shared"))

    assert store.delete_repository("tenant-a", "shared") is True
    assert store.get_repository("tenant-a", "shared") is None
    assert store.get_repository("tenant-b", "shared") is not None
