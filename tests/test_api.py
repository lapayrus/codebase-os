from pathlib import Path
import hashlib
import hmac
import json
from fastapi.testclient import TestClient
from codebase_os.indexer import index_repository
from codebase_os.config import get_settings
from codebase_os.main import app, github_access, github_jobs, service


def test_query_rejects_repository_outside_access_header(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service.add_repository(index_repository(str(tmp_path), "secure"))
    response = TestClient(app).post('/api/query', headers={'x-repository-access': 'other'}, json={'repository': 'secure', 'question': 'Where is hello?'})
    assert response.status_code == 403
    service.repositories.pop('secure', None)


def test_github_webhook_invalid_signature_returns_401(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_GITHUB_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    response = TestClient(app).post(
        "/api/webhooks/github",
        headers={"x-hub-signature-256": "sha256=invalid", "x-github-event": "push", "x-github-delivery": "d-1"},
        content=b'{}',
    )
    assert response.status_code == 401
    get_settings.cache_clear()


def test_github_push_webhook_enqueues_one_job(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_GITHUB_WEBHOOK_SECRET", "secret")
    get_settings.cache_clear()
    body = json.dumps({"installation": {"id": 7}, "repository": {"full_name": "acme/demo"}}).encode()
    signature = "sha256=" + hmac.new(b"secret", body, hashlib.sha256).hexdigest()
    github_access.grant(7, ["acme/demo"])
    before = len(github_jobs.jobs)
    response = TestClient(app).post(
        "/api/webhooks/github",
        headers={"x-hub-signature-256": signature, "x-github-event": "push", "x-github-delivery": "d-2"},
        content=body,
    )
    assert response.status_code == 202
    assert len(github_jobs.jobs) == before + 1
    get_settings.cache_clear()
