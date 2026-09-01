from codebase_os.indexer import RepositoryIndex
from codebase_os.indexing import IndexDecision, content_version, decide_index
from codebase_os.persistence import PersistentCodebaseService
from codebase_os.storage.memory import InMemoryStore
from codebase_os.indexer import index_repository


def test_indexing_accepts_unicode_source_content(tmp_path):
    (tmp_path / "docs.md").write_text("Flow → session", encoding="utf-8")
    index = index_repository(str(tmp_path), "unicode-repo")
    assert index.files["docs.md"] == "Flow → session"


def test_content_version_is_stable_for_file_order():
    first = content_version({"b.py": "2", "a.py": "1"})
    second = content_version({"a.py": "1", "b.py": "2"})
    assert first == second


def test_identical_content_is_unchanged():
    version = content_version({"main.py": "return 1"})
    assert decide_index(version, version, "succeeded") is IndexDecision.UNCHANGED


def test_changed_content_requires_reindex():
    assert decide_index("old", "new", "succeeded") is IndexDecision.REINDEX


def test_failed_content_is_retryable():
    assert decide_index("old", "new", "failed") is IndexDecision.RETRY


def test_same_content_is_not_written_twice():
    service = PersistentCodebaseService(InMemoryStore())
    index = RepositoryIndex("repo", "C:/repo", "commit", files={"main.py": "return 1"})

    assert service.index_repository(index, "tenant") is IndexDecision.REINDEX
    assert service.index_repository(index, "tenant") is IndexDecision.UNCHANGED


def test_changed_content_replaces_old_evidence_after_success():
    store = InMemoryStore()
    service = PersistentCodebaseService(store)
    first = RepositoryIndex("repo", "C:/repo", "commit-1", files={"main.py": "return 1"})
    second = RepositoryIndex("repo", "C:/repo", "commit-2", files={"main.py": "return 2"})

    service.index_repository(first, "tenant")
    service.index_repository(second, "tenant")

    evidence = store.list_evidence("tenant", "repo")
    assert [item.commit for item in evidence] == ["commit-2"]
