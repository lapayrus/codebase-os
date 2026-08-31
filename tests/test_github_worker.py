from codebase_os.indexer import RepositoryIndex
from codebase_os.persistence import PersistentCodebaseService
from codebase_os.providers.github import GitHubIngestionWorker
from codebase_os.providers.webhooks import DurableIngestionQueue, IngestionJob
from codebase_os.service import CodebaseService
from codebase_os.storage.memory import InMemoryStore
from codebase_os.storage.snapshots import InMemorySnapshotStore


class FakeGitHub:
    def repository_snapshot(self, full_name, branch):
        return RepositoryIndex(full_name, "", "commit-1", {"README.md": "hello"})


def test_worker_claims_indexes_and_completes_durable_job():
    storage = InMemoryStore()
    queue = DurableIngestionQueue(storage)
    job = IngestionJob("delivery-1", 7, "acme/demo", "push")
    assert queue.enqueue(job)
    service = PersistentCodebaseService(storage, CodebaseService())
    snapshots = InMemorySnapshotStore()
    assert GitHubIngestionWorker(queue, FakeGitHub(), service, snapshots).run_once("tenant")
    assert storage.get_repository("tenant", "acme/demo") is not None
    assert snapshots.get("tenant", "acme/demo", "commit-1") == b'{"README.md": "hello"}'
    assert queue.claim() is None
