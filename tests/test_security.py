from fastapi import Request
from fastapi.testclient import TestClient

from codebase_os.security import RequestGuard
from codebase_os.main import app, service


def test_request_guard_rejects_oversized_content_length():
    guard = RequestGuard(max_request_bytes=10, rate_limit=10)
    assert guard.check_size(10) is None
    assert guard.check_size(11) == "request body exceeds the configured limit"


def test_request_guard_limits_api_requests_per_client():
    guard = RequestGuard(max_request_bytes=1000, rate_limit=2)
    assert guard.check_rate("client-a") is None
    assert guard.check_rate("client-a") is None
    assert guard.check_rate("client-a") == "rate limit exceeded"
    assert guard.check_rate("client-b") is None


def test_request_guard_uses_forwarded_client_identity():
    guard = RequestGuard(max_request_bytes=1000, rate_limit=1)
    assert guard.client_key(Request({"type": "http", "headers": [(b"x-forwarded-for", b"a, b")], "client": ("local", 1)})) == "a"


def test_unhandled_errors_are_redacted_and_correlated(monkeypatch):
    def fail(*args, **kwargs):
        raise OSError("secret database password leaked")

    monkeypatch.setattr(service, "query", fail)
    response = TestClient(app).post("/api/query", headers={"x-request-id": "req-123"}, json={"question": "hello"})
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error", "request_id": "req-123"}
    assert "secret" not in response.text
