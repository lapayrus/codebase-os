import jwt
import pytest
import time
from fastapi import Request

from codebase_os.auth import AuthContext, can_access, context_from_request
from codebase_os.config import Settings


def test_explicit_repository_access_is_enforced():
    context = AuthContext("tenant-a", "user-a", frozenset({"repo-a"}))
    assert can_access(context, "repo-a")
    assert not can_access(context, "repo-b")


def test_local_context_without_allowlist_can_access_indexed_repo():
    assert can_access(AuthContext("local", "local", frozenset()), "repo-a")


def test_production_context_requires_verified_bearer_session():
    request = Request({"type": "http", "headers": [(b"authorization", b"Bearer invalid")]})
    with pytest.raises(PermissionError):
        context_from_request(request, Settings(environment="production", supabase_jwt_secret="session-secret"))


def test_production_context_reads_tenant_and_repository_claims():
    token = jwt.encode(
        {"sub": "user-1", "tenant_id": "tenant-1", "repositories": ["repo-a"], "exp": int(time.time()) + 300},
        "session-secret",
        algorithm="HS256",
    )
    request = Request({"type": "http", "headers": [(b"authorization", f"Bearer {token}".encode())]})
    context = context_from_request(request, Settings(environment="production", supabase_jwt_secret="session-secret"))
    assert context == AuthContext("tenant-1", "user-1", frozenset({"repo-a"}))
