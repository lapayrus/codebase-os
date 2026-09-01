from pathlib import Path
import hashlib
import hmac
import json
from uuid import uuid4
from fastapi.testclient import TestClient
from codebase_os.indexer import index_repository
from codebase_os.config import get_settings
from codebase_os.main import app, github_access, github_jobs, runtime_storage, service


def test_query_rejects_repository_outside_access_header(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service.add_repository(index_repository(str(tmp_path), "secure"))
    response = TestClient(app).post('/api/query', headers={'x-repository-access': 'other'}, json={'repository': 'secure', 'question': 'Where is hello?'})
    assert response.status_code == 403
    service.repositories.pop('secure', None)


def test_index_route_writes_repository_to_runtime_storage(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")

    response = TestClient(app).post("/api/repositories/index", params={"path": str(tmp_path), "name": "runtime-repo"})

    assert response.status_code == 200
    assert runtime_storage.get_repository("local", "runtime-repo") is not None
    runtime_storage.delete_repository("local", "runtime-repo")
    service.repositories.pop("runtime-repo", None)


def test_index_route_reports_unchanged_content(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    client = TestClient(app)
    params = {"path": str(tmp_path), "name": "unchanged-repo"}

    client.post("/api/repositories/index", params=params)
    response = client.post("/api/repositories/index", params=params)

    assert response.status_code == 200
    assert response.json()["status"] == "unchanged"
    runtime_storage.delete_repository("local", "unchanged-repo")
    service.repositories.pop("unchanged-repo", None)


def test_delete_route_removes_durable_repository(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    TestClient(app).post("/api/repositories/index", params={"path": str(tmp_path), "name": "durable-delete"})

    response = TestClient(app).delete(
        "/api/repositories/durable-delete",
        headers={"x-repository-access": "durable-delete"},
    )

    assert response.status_code == 204
    assert runtime_storage.get_repository("local", "durable-delete") is None


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
    delivery_id = f"d-{uuid4().hex}"
    before = github_jobs.status().get("queued", 0)
    response = TestClient(app).post(
        "/api/webhooks/github",
        headers={"x-hub-signature-256": signature, "x-github-event": "push", "x-github-delivery": delivery_id},
        content=body,
    )
    assert response.status_code == 202
    assert github_jobs.status().get("queued", 0) == before + 1
    duplicate = TestClient(app).post(
        "/api/webhooks/github",
        headers={"x-hub-signature-256": signature, "x-github-event": "push", "x-github-delivery": delivery_id},
        content=body,
    )
    assert duplicate.status_code == 202
    assert duplicate.json() == {"queued": 0}
    get_settings.cache_clear()


def test_job_status_endpoint_reports_durable_queue(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "development")
    get_settings.cache_clear()
    response = TestClient(app).get("/api/operations/jobs")
    assert response.status_code == 200
    assert "jobs" in response.json()
    get_settings.cache_clear()


def test_memory_read_rejects_repository_outside_access_header(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service.add_repository(index_repository(str(tmp_path), "private-memory"))
    service.add_memory("private-memory", "internal detail", "gotcha")
    response = TestClient(app).get(
        "/api/memories/private-memory",
        headers={"x-repository-access": "other"},
    )
    assert response.status_code == 403
    service.repositories.pop("private-memory", None)
    service.memories.pop("private-memory", None)


def test_repository_list_filters_repositories_outside_access_header(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service.add_repository(index_repository(str(tmp_path), "private-list"))
    response = TestClient(app).get(
        "/api/repositories",
        headers={"x-repository-access": "other"},
    )
    assert response.status_code == 200
    assert response.json() == []
    service.repositories.pop("private-list", None)


def test_repository_delete_requires_access_and_removes_local_data(tmp_path: Path):
    (tmp_path / "main.py").write_text("def hello():\n    return 'hi'\n", encoding="utf-8")
    service.add_repository(index_repository(str(tmp_path), "deletable"))
    service.add_memory("deletable", "temporary detail", "gotcha")

    denied = TestClient(app).delete(
        "/api/repositories/deletable",
        headers={"x-repository-access": "other"},
    )
    assert denied.status_code == 403

    deleted = TestClient(app).delete(
        "/api/repositories/deletable",
        headers={"x-repository-access": "deletable"},
    )
    assert deleted.status_code == 204
    assert "deletable" not in service.repositories
    assert "deletable" not in service.memories


def test_readiness_reports_local_dependencies_ready(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "development")
    get_settings.cache_clear()
    response = TestClient(app).get("/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"
    assert response.json()["checks"] == {
        "api": True, "database": True, "queue": True, "github": True,
        "model": True, "object_storage": True,
    }
    get_settings.cache_clear()


def test_production_readiness_rejects_sqlite_and_missing_github(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "production")
    monkeypatch.setenv("CODEBASEOS_DATABASE_URL", "sqlite:///local.db")
    monkeypatch.delenv("CODEBASEOS_GITHUB_APP_ID", raising=False)
    monkeypatch.delenv("CODEBASEOS_GITHUB_PRIVATE_KEY", raising=False)
    monkeypatch.delenv("CODEBASEOS_GITHUB_WEBHOOK_SECRET", raising=False)
    get_settings.cache_clear()
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert response.json()["checks"]["database"] is False
    assert response.json()["checks"]["github"] is False
    get_settings.cache_clear()


def test_production_query_requires_bearer_session(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "production")
    monkeypatch.setenv("CODEBASEOS_SUPABASE_JWT_SECRET", "session-secret")
    get_settings.cache_clear()
    response = TestClient(app).post("/api/query", json={"question": "Where is auth?"})
    assert response.status_code == 401
    get_settings.cache_clear()


def test_readiness_rejects_incomplete_selected_model_provider(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "development")
    monkeypatch.setenv("CODEBASEOS_MODEL_PROVIDER", "online")
    monkeypatch.delenv("CODEBASEOS_MODEL_API_KEY", raising=False)
    monkeypatch.setenv("CODEBASEOS_MODEL_NAME", "online-model")
    monkeypatch.setenv("CODEBASEOS_MODEL_BASE_URL", "https://models.example/v1")
    get_settings.cache_clear()

    response = TestClient(app).get("/ready")

    assert response.status_code == 503
    assert response.json()["checks"]["model"] is False
    get_settings.cache_clear()


def test_readiness_accepts_configured_supabase_storage(monkeypatch):
    monkeypatch.setenv("CODEBASEOS_ENVIRONMENT", "development")
    monkeypatch.setenv("CODEBASEOS_OBJECT_STORAGE_PROVIDER", "supabase")
    monkeypatch.setenv("CODEBASEOS_OBJECT_STORAGE_BUCKET", "repository-snapshots")
    monkeypatch.setenv("CODEBASEOS_SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setenv("CODEBASEOS_SUPABASE_PROJECT_ID", "project")
    monkeypatch.setenv("CODEBASEOS_SUPABASE_PUBLISHABLE_KEY", "publishable")
    monkeypatch.delenv("CODEBASEOS_OBJECT_STORAGE_ENDPOINT", raising=False)
    monkeypatch.delenv("CODEBASEOS_OBJECT_STORAGE_ACCESS_KEY", raising=False)
    monkeypatch.delenv("CODEBASEOS_OBJECT_STORAGE_SECRET_KEY", raising=False)
    get_settings.cache_clear()

    response = TestClient(app).get("/ready")

    assert response.status_code == 200
    assert response.json()["checks"]["object_storage"] is True
    get_settings.cache_clear()
