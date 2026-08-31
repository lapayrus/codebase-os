import httpx
import pytest

from codebase_os.storage.snapshots import InMemorySnapshotStore, SupabaseSnapshotStore, snapshot_path


def test_snapshot_path_is_tenant_scoped_and_rejects_traversal():
    assert snapshot_path("tenant", "repo", "abc") == "tenants/tenant/repositories/repo/abc.snapshot"
    with pytest.raises(ValueError):
        snapshot_path("tenant/../other", "repo", "abc")


def test_in_memory_snapshot_store_round_trip_and_delete():
    store = InMemorySnapshotStore()
    store.put("tenant", "repo", "abc", b"data")
    assert store.get("tenant", "repo", "abc") == b"data"
    store.delete("tenant", "repo", "abc")
    assert store.objects == {}


def test_supabase_snapshot_store_uses_private_authenticated_object_api():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.method == "GET":
            return httpx.Response(200, content=b"data")
        return httpx.Response(200, json={})

    store = SupabaseSnapshotStore("https://project.supabase.co", "snapshots", "server-key", httpx.MockTransport(handler))
    store.put("tenant", "repo", "abc", b"data")
    assert store.get("tenant", "repo", "abc") == b"data"
    store.delete("tenant", "repo", "abc")
    assert all(request.headers["authorization"] == "Bearer server-key" for request in calls)
    assert all("tenants/tenant/repositories/repo/abc.snapshot" in str(request.url) for request in calls)
