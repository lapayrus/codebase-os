# Phase 1 PostgreSQL Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-optimized:executing-plans` for sequential execution.
> Steps use checkbox syntax for tracking.

**Goal:** Make PostgreSQL the durable runtime source for repository metadata, evidence, memories, audit events, and
deletion while preserving the current query behavior.
**Architecture:** A runtime factory creates one connection-backed `PostgresStore` from `Settings.database_url`.
The application keeps its in-memory repository index as a bounded query cache, while every durable record operation
is mirrored to PostgreSQL and can be recovered after process restart.
**Tech Stack:** Python 3.11+, FastAPI, psycopg 3, PostgreSQL, pytest, uv.
**Assumptions:** The first runtime driver is PostgreSQL; SQLite remains the explicit local fallback until this phase
removes it from the application composition. DBngin provides the integration database during local verification.

## File map

- Create `src/codebase_os/runtime.py` for database driver loading, connection creation, and storage composition.
- Modify `src/codebase_os/storage/postgres.py` for typed initialization and connection lifecycle expectations.
- Modify `src/codebase_os/main.py` for application storage composition and durable route operations.
- Modify `src/codebase_os/service.py` for storage-backed repository and memory persistence hooks.
- Modify `src/codebase_os/storage/ports.py` only if the service bridge requires a missing storage contract.
- Modify `pyproject.toml` and `uv.lock` for the PostgreSQL runtime dependency.
- Create `tests/test_runtime.py` for factory selection and failure behavior.
- Create `tests/test_postgres_integration.py` for DBngin restart persistence and tenant isolation.
- Modify `tests/test_api.py` for route composition and deletion persistence behavior.
- Modify `docs/operations.md` and `.env.example` for local and hosted database startup requirements.

## Security and data-boundary requirements

- Tenant ID must be passed to every storage operation.
- Database credentials must never appear in exceptions, logs, tests, plans, or state files.
- Production must reject SQLite and missing PostgreSQL configuration.
- Repository deletion must remove only the selected tenant's records.
- Integration tests must use disposable repository IDs and clean them in teardown.

### Task 1: Add the PostgreSQL runtime driver and factory

**Files:**
- Create: `src/codebase_os/runtime.py`
- Modify: `pyproject.toml`, `uv.lock`
- Test: `tests/test_runtime.py`

**Security flag:** security

**Does NOT cover:** Supabase Storage, Supabase Auth, GitHub API calls, or connection pooling.

- [x] **Step 1: Write the failing factory tests**

```python
def test_build_storage_uses_postgres_for_postgresql_url(monkeypatch):
    settings = Settings(database_url="postgresql://user:pass@localhost/codebaseos")
    fake_connection = object()
    storage = build_storage(settings, connector=lambda _: fake_connection)
    assert isinstance(storage, PostgresStore)
    assert storage.connection is fake_connection


def test_build_storage_rejects_sqlite_in_production():
    settings = Settings(environment="production", database_url="sqlite:///./codebaseos.db")
    with pytest.raises(ValueError, match="production requires PostgreSQL"):
        build_storage(settings, connector=lambda _: object())
```

- [x] **Step 2: Run the focused tests to verify failure**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_runtime.py`
Expected: FAIL because `codebase_os.runtime.build_storage` does not exist.

- [x] **Step 3: Add the dependency and implement the minimal factory**

Run: `rtk uv --cache-dir .uv-cache add "psycopg[binary]>=3.2,<4"`

Implement `build_storage(settings, connector=connect)` in `src/codebase_os/runtime.py`.
It must accept `postgresql://` and `postgres://`, reject SQLite in production, and construct `PostgresStore`.

- [x] **Step 4: Verify dependency and focused tests**

Run: `rtk uv --cache-dir .uv-cache sync --locked --extra dev; rtk uv --cache-dir .uv-cache run pytest -q tests/test_runtime.py`
Expected: dependency resolution succeeds and all runtime factory tests pass.

### Task 2: Make schema initialization and connection failures explicit

**Files:**
- Modify: `src/codebase_os/runtime.py`, `src/codebase_os/storage/postgres.py`
- Test: `tests/test_runtime.py`, `tests/test_storage_ports.py`

**Security flag:** security

**Does NOT cover:** Automatic schema migrations between incompatible versions.

- [x] **Step 1: Write failing initialization tests**

```python
def test_initialize_storage_creates_schema_before_serving():
    connection = FakeConnection()
    storage = PostgresStore(connection)
    initialize_storage(storage)
    assert connection.committed is True
    assert connection.executed_schema is True


def test_connection_failure_is_redacted():
    with pytest.raises(RuntimeError, match="database connection failed") as error:
        build_storage(Settings(database_url="postgresql://user:secret@localhost/db"), connector=raise_error)
    assert "secret" not in str(error.value)
```

- [x] **Step 2: Run focused tests and confirm failure**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_runtime.py tests/test_storage_ports.py`
Expected: FAIL because runtime initialization and redacted connection handling are absent.

- [x] **Step 3: Implement initialization and redacted errors**

Add `initialize_storage(storage)` that invokes `PostgresStore.initialize()` once during composition.
Catch driver connection errors and raise a stable `RuntimeError("database connection failed")` without the URL.

- [x] **Step 4: Verify the focused suite**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_runtime.py tests/test_storage_ports.py`
Expected: PASS with no credential text in failure output.

### Task 3: Add a storage-backed service bridge

**Files:**
- Create: `src/codebase_os/persistence.py`
- Modify: `src/codebase_os/service.py`, `src/codebase_os/storage/ports.py`
- Test: `tests/test_persistence.py`

**Security flag:** security

**Does NOT cover:** Reconstructing the full static query index from PostgreSQL.

- [x] **Step 1: Write failing persistence tests**

```python
def test_add_repository_persists_metadata_and_evidence():
    storage = RecordingStore()
    service = PersistentCodebaseService(storage)
    indexed = sample_index()
    service.add_repository(indexed, tenant_id="tenant-a")
    assert storage.repositories["tenant-a", indexed.name].commit == indexed.commit
    assert storage.evidence["tenant-a", indexed.name]


def test_add_memory_persists_with_tenant_scope():
    storage = RecordingStore()
    service = PersistentCodebaseService(storage)
    service.add_memory("repo-a", "remember this", "decision", tenant_id="tenant-a")
    assert storage.memories["tenant-a", "repo-a"][0].text == "remember this"
```

- [x] **Step 2: Run the focused tests to confirm failure**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_persistence.py`
Expected: FAIL because the storage-backed service bridge is absent.

- [x] **Step 3: Implement persistence conversion**

Create `PersistentCodebaseService` as a composition wrapper around the existing query service.
Convert repository files and evidence into `RepositoryRecord` and `EvidenceRecord`, and convert memories into
`MemoryRecord`, always passing the caller's tenant ID to the storage port.

- [x] **Step 4: Verify persistence tests and existing service tests**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_persistence.py tests/test_service.py tests/test_storage_ports.py`
Expected: PASS with existing in-memory behavior unchanged.

### Task 4: Wire durable storage into FastAPI routes

**Files:**
- Modify: `src/codebase_os/main.py`
- Test: `tests/test_api.py`

**Security flag:** security

**Does NOT cover:** Hosted authentication or GitHub identity mapping.

- [x] **Step 1: Write failing route persistence tests**

```python
def test_index_route_writes_repository_to_runtime_storage(monkeypatch):
    response = client.post("/api/repositories/index", params={"path": str(sample_repo)})
    assert response.status_code == 200
    assert runtime_storage.get_repository("default", response.json()["name"]) is not None


def test_delete_route_removes_durable_repository(monkeypatch):
    client.post("/api/repositories/index", params={"path": str(sample_repo)})
    response = client.delete("/api/repositories/sample-repo", headers={"x-repositories": "sample-repo"})
    assert response.status_code == 204
    assert runtime_storage.get_repository("default", "sample-repo") is None
```

- [x] **Step 2: Run API tests to confirm failure**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_api.py`
Expected: FAIL because routes currently use only module-level in-memory state.

- [x] **Step 3: Compose runtime storage and route calls**

Create module-level runtime composition through `get_settings()` and `build_storage()`.
Initialize PostgreSQL when selected, pass request tenant context into persistence operations, and retain the existing
in-memory index for query execution until Phase 2 reconstructs durable indexes.

- [x] **Step 4: Verify API and regression behavior**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_api.py tests/test_service.py tests/test_persistence.py`
Expected: PASS with route writes and deletes reaching the selected storage.

### Task 5: Prove DBngin restart persistence and document operations

**Files:**
- Create: `tests/test_postgres_integration.py`
- Modify: `docs/operations.md`, `.env.example`, `state.md`

**Security flag:** security

**Does NOT cover:** Production deployment to Supabase or cloud migration execution.

- [x] **Step 1: Write the DBngin integration test**

```python
@pytest.mark.integration
def test_repository_survives_store_recreation(dbngin_database_url):
    first = build_storage(Settings(database_url=dbngin_database_url))
    initialize_storage(first)
    first.save_repository("phase1-test", repository("restart-repo"))
    second = build_storage(Settings(database_url=dbngin_database_url))
    assert second.get_repository("phase1-test", "restart-repo") is not None
    assert second.delete_repository("phase1-test", "restart-repo") is True
```

- [x] **Step 2: Run the integration test against DBngin**

Run: `rtk uv --cache-dir .uv-cache run pytest -q tests/test_postgres_integration.py -m integration`
Expected: PASS against `CODEBASEOS_DATABASE_URL` without printing credentials.

- [x] **Step 3: Document local and hosted database startup**

Document DBngin PostgreSQL as the local target, Supabase PostgreSQL as the hosted target, the required
`CODEBASEOS_DATABASE_URL`, schema initialization, and the disposable-data cleanup command.

- [x] **Step 4: Run the complete phase verification gate**

Run: `rtk uv --cache-dir .uv-cache sync --locked --extra dev; rtk uv --cache-dir .uv-cache run pytest -q; rtk uv --cache-dir .uv-cache run python -m compileall -q src; git diff --check`
Expected: all tests pass, compilation succeeds, and diff checks report no errors.

- [x] **Step 5: Update cross-session state**

Record the completed Phase 1 task range, exact verification output, database target used, and the first task of
Phase 2 in `state.md`; append only durable architecture decisions to `session-log.md`.
