from codebase_os.memory.freshness import MemoryReference, affected_memory_ids
from codebase_os.memory.service import MemoryService


def test_memories_are_tenant_and_repository_scoped():
    service = MemoryService()
    service.add("tenant-a", "repo-a", "Use the staging gate.", "convention")
    service.add("tenant-b", "repo-a", "Private detail.", "gotcha")
    assert len(service.list("tenant-a", "repo-a")) == 1


def test_changed_paths_invalidate_only_dependent_memories():
    refs = [MemoryReference("m1", "repo", "old", frozenset({"auth.py"})),
            MemoryReference("m2", "repo", "old", frozenset({"billing.py"}))]
    assert affected_memory_ids(refs, {"auth.py"}, "new") == ["m1"]


def test_stale_memory_remains_visible_and_labeled():
    service = MemoryService()
    stale = service.add("tenant-a", "repo-a", "Old auth convention.", "convention", commit="old")
    fresh = service.add("tenant-a", "repo-a", "Current billing convention.", "convention", commit="new")

    service.mark_stale(stale.id)
    memories = {item.id: item for item in service.list("tenant-a", "repo-a")}

    assert memories[stale.id].stale is True
    assert memories[fresh.id].stale is False
