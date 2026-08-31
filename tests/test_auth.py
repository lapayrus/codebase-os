from codebase_os.auth import AuthContext, can_access


def test_explicit_repository_access_is_enforced():
    context = AuthContext("tenant-a", "user-a", frozenset({"repo-a"}))
    assert can_access(context, "repo-a")
    assert not can_access(context, "repo-b")


def test_local_context_without_allowlist_can_access_indexed_repo():
    assert can_access(AuthContext("local", "local", frozenset()), "repo-a")

