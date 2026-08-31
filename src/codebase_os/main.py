from pathlib import Path
import json
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .indexer import index_repository
from .models import MemoryRequest, QueryRequest
from .service import CodebaseService
from .audit import AuditLog
from .auth import can_access, context_from_request
from .config import get_settings
from .model_factory import build_model_provider
from .providers.webhooks import GitHubWebhookProcessor, IngestionJobQueue, InstallationAccess

app = FastAPI(title="CodebaseOS", version="0.1.0", description="Evidence-first repository intelligence")
service = CodebaseService()
audit = AuditLog()
github_jobs = IngestionJobQueue()
github_access = InstallationAccess()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "repositories": len(service.repositories)}


@app.get("/ready")
def readiness() -> JSONResponse:
    settings = get_settings()
    github_values = (settings.github_app_id, settings.github_private_key, settings.github_webhook_secret)
    model_values = (settings.model_api_key, settings.model_name, settings.model_base_url)
    storage_values = (settings.object_storage_endpoint, settings.object_storage_access_key,
                      settings.object_storage_secret_key)
    supabase_storage_ready = all((settings.supabase_url, settings.supabase_project_id,
                                  settings.supabase_publishable_key, settings.object_storage_bucket))
    try:
        build_model_provider(settings)
        model_ready = True
    except ValueError:
        model_ready = False
    checks = {
        "api": True,
        "database": settings.environment != "production" or not settings.database_url.startswith("sqlite"),
        "queue": True,
        "github": (
            settings.environment != "production" and not any(value is not None for value in github_values)
        ) or all(value is not None for value in github_values),
        "model": model_ready and (settings.model_provider == "none" or all(value is not None for value in model_values)),
        "object_storage": settings.object_storage_provider == "local" or (
            settings.object_storage_provider == "supabase" and supabase_storage_ready
        ) or all(value is not None for value in storage_values),
    }
    ready = all(checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "not_ready", "checks": checks},
    )


@app.post("/api/repositories/index")
def index(path: str, name: str | None = None) -> dict:
    try:
        repo = index_repository(path, name)
        service.add_repository(repo)
        return {"name": repo.name, "commit": repo.commit, "files": len(repo.files), "symbols": len(repo.symbols)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/webhooks/github", status_code=202)
async def github_webhook(request: Request) -> dict[str, int]:
    secret = get_settings().github_webhook_secret
    if secret is None:
        raise HTTPException(status_code=503, detail="GitHub webhook integration is not configured")
    body = await request.body()
    processor = GitHubWebhookProcessor(secret.get_secret_value(), github_jobs, github_access)
    try:
        return processor.handle(
            body,
            request.headers.get("x-hub-signature-256", ""),
            request.headers.get("x-github-event", ""),
            request.headers.get("x-github-delivery", ""),
        )
    except PermissionError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except (ValueError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid GitHub webhook payload") from exc


@app.get("/api/repositories")
def repositories(http_request: Request) -> list[dict]:
    context = context_from_request(http_request)
    return [
        {"name": r.name, "commit": r.commit, "files": len(r.files), "symbols": len(r.symbols)}
        for r in service.repositories.values()
        if can_access(context, r.name)
    ]


@app.delete("/api/repositories/{repository}", status_code=204)
def delete_repository(repository: str, http_request: Request) -> None:
    context = context_from_request(http_request)
    if not can_access(context, repository):
        raise HTTPException(status_code=403, detail="Repository access denied")
    if repository not in service.repositories:
        raise HTTPException(status_code=404, detail="Unknown repository")
    service.repositories.pop(repository)
    service.memories.pop(repository, None)
    audit.record(context.tenant_id, context.user_id, "repository.delete", repository,
                 http_request.headers.get("x-request-id", str(uuid.uuid4())))


@app.post("/api/query")
def query(request: QueryRequest, http_request: Request):
    try:
        context = context_from_request(http_request)
        repository = request.repository or next(iter(service.repositories), None)
        if repository and not can_access(context, repository):
            raise HTTPException(status_code=403, detail="Repository access denied")
        audit.record(context.tenant_id, context.user_id, "query", repository, http_request.headers.get("x-request-id", str(uuid.uuid4())))
        return service.query(request.question, request.repository, request.top_k)
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown repository: {exc.args[0]}") from exc


@app.post("/api/memories")
def create_memory(request: MemoryRequest, http_request: Request):
    context = context_from_request(http_request)
    if not can_access(context, request.repository):
        raise HTTPException(status_code=403, detail="Repository access denied")
    if request.repository not in service.repositories:
        raise HTTPException(status_code=404, detail="Index the repository before adding memory")
    audit.record(context.tenant_id, context.user_id, "memory.create", request.repository, http_request.headers.get("x-request-id", str(uuid.uuid4())))
    return service.add_memory(request.repository, request.text, request.memory_type)


@app.get("/api/memories/{repository}")
def memories(repository: str, http_request: Request):
    context = context_from_request(http_request)
    if not can_access(context, repository):
        raise HTTPException(status_code=403, detail="Repository access denied")
    return service.memories.get(repository, [])


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
