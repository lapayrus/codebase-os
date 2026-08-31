from pathlib import Path
import uuid
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .indexer import index_repository
from .models import MemoryRequest, QueryRequest
from .service import CodebaseService
from .audit import AuditLog
from .auth import can_access, context_from_request

app = FastAPI(title="CodebaseOS", version="0.1.0", description="Evidence-first repository intelligence")
service = CodebaseService()
audit = AuditLog()
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "repositories": len(service.repositories)}


@app.post("/api/repositories/index")
def index(path: str, name: str | None = None) -> dict:
    try:
        repo = index_repository(path, name)
        service.add_repository(repo)
        return {"name": repo.name, "commit": repo.commit, "files": len(repo.files), "symbols": len(repo.symbols)}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/repositories")
def repositories() -> list[dict]:
    return [{"name": r.name, "commit": r.commit, "files": len(r.files), "symbols": len(r.symbols)} for r in service.repositories.values()]


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
def memories(repository: str):
    return service.memories.get(repository, [])


@app.get("/", include_in_schema=False)
def frontend():
    return FileResponse(Path(__file__).parent / "static" / "index.html")
