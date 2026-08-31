# Phase 2 Durable Indexing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-optimized:executing-plans` to implement this plan.
> Steps use checkbox syntax for tracking.

**Goal:** Make repository indexing durable, idempotent, version-aware, and safely recoverable after partial failure.
**Architecture:** PostgreSQL stores repository indexing status, content version, file hashes, and evidence ownership.
The current in-memory `RepositoryIndex` remains a query cache, while durable records determine whether an incoming
snapshot is new, unchanged, failed, or stale.
**Tech Stack:** Python, FastAPI, Pydantic, psycopg 3, PostgreSQL, pytest, uv.
**Assumptions:** Phase 1 runtime storage is available on `master`; this phase does not implement GitHub transport,
background workers, Supabase Storage, or hosted authentication.

## Migration contract

- Expand the existing schema with nullable status/version/hash columns.
- Preserve all existing repository and evidence rows during upgrade.
- Backfill existing rows as `succeeded` with their current commit as content version.
- Verify the expanded schema before using new fields.
- Keep rollback as removing only the new columns after new readers are disabled.
- Do not delete historical evidence until replacement indexing succeeds.

## File map

- Create `src/codebase_os/indexing.py` for content hashing, idempotency decisions, and indexing state transitions.
- Modify `src/codebase_os/storage/postgres.py` for additive schema and version-aware repository/evidence writes.
- Modify `src/codebase_os/storage/records.py` for indexing status, content version, and file hash fields.
- Modify `src/codebase_os/persistence.py` for transactional index persistence and stale-evidence replacement.
- Modify `src/codebase_os/main.py` to return indexing status and use the durable decision path.
- Create `tests/test_indexing.py` for deterministic hashing and state transitions.
- Modify `tests/test_storage_ports.py` for expanded record persistence.
- Create `tests/test_indexing_integration.py` for DBngin idempotency and failure recovery.
- Modify `docs/operations.md` for migration and re-index procedures.

### Task 1: Add deterministic content-version and idempotency decisions

**Files:** Create `src/codebase_os/indexing.py`; create `tests/test_indexing.py`.
**Security flag:** security.
**Does NOT cover:** GitHub event delivery, queue leases, or model generation.

- [x] Write tests proving identical repository content returns `unchanged`, changed content returns `reindex`, and
  failed content returns `retry`.
- [x] Run `rtk uv --cache-dir .uv-cache run pytest -q tests/test_indexing.py` and observe the missing-module failure.
- [x] Implement `content_version`, `file_hash`, and `IndexDecision` with stable SHA-256 hashing.
- [x] Re-run the focused tests and expect all decision tests to pass.

### Task 2: Add the reversible PostgreSQL schema expansion

**Files:** Modify `src/codebase_os/storage/records.py`, `src/codebase_os/storage/postgres.py`;
modify `tests/test_storage_ports.py`.
**Security flag:** security.
**Does NOT cover:** Destructive historical evidence cleanup.

- [x] Write tests proving schema initialization adds status/version/hash fields without dropping existing rows.
- [x] Run `rtk uv --cache-dir .uv-cache run pytest -q tests/test_storage_ports.py` and observe the missing-field failure.
- [x] Add additive `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statements and preserve existing `SCHEMA_SQL` creation.
- [x] Map null legacy status to `succeeded` and keep writes tenant-scoped.
- [x] Run the storage suite and expect all tests to pass.

### Task 3: Persist idempotent indexing with safe replacement

**Files:** Modify `src/codebase_os/persistence.py`; create `tests/test_indexing_integration.py`.
**Security flag:** security.
**Does NOT cover:** Background execution or cross-process job coordination.

- [x] Write tests proving the same commit creates no duplicate evidence, a changed commit replaces stale evidence only
  after successful writes, and a failed write leaves the prior succeeded version queryable.
- [x] Run `rtk uv --cache-dir .uv-cache run pytest -q tests/test_indexing_integration.py` and observe failure.
- [x] Implement transaction-scoped staging, commit/version update, and post-success stale-evidence deletion.
- [x] Use disposable tenant and repository IDs; clean every test record in `finally` blocks.
- [x] Run the DBngin integration tests and expect all tests to pass.

### Task 4: Wire status reporting, operations, and phase verification

**Files:** Modify `src/codebase_os/main.py`, `docs/operations.md`, `state.md`;
modify `tests/test_api.py`.
**Security flag:** security.
**Does NOT cover:** User-facing indexing progress UI, which belongs to Phase 8.

- [x] Write API tests proving unchanged indexing is reported without duplicate writes and failed indexing exposes a
  retryable status.
- [x] Run `rtk uv --cache-dir .uv-cache run pytest -q tests/test_api.py` and observe failure.
- [x] Wire the durable decision and status response into the indexing route without changing query response shape.
- [x] Document forward migration, rollback, re-index, and stale-data recovery commands.
- [x] Run `rtk uv --cache-dir .uv-cache sync --locked --extra dev`.
- [x] Run `rtk uv --cache-dir .uv-cache run pytest -q` and expect zero failures.
- [x] Run `rtk uv --cache-dir .uv-cache run python -m compileall -q src`.
- [x] Run the source stub scan and `git diff --check`.
- [x] Update `state.md` to Phase 3 and record exact verification output.
