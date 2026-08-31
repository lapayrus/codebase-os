# Project Map
_Generated: 2026-08-31 17:00 | Git: no commits | Staleness: timestamps_

## Directory Structure
`src/codebase_os/` — Python application package.
`src/codebase_os/static/` — browser UI for repository questions.
`src/codebase_os/providers/` — provider-neutral snapshots, local ingestion, and GitHub primitives.
`src/codebase_os/retrieval/` — lexical/structural ranking, bounded context, and claim validation.
`src/codebase_os/memory/` — durable-memory shape and freshness invalidation logic.
`src/codebase_os/storage/` — tenant-scoped storage ports, memory adapter, and PostgreSQL adapter.
`src/codebase_os/evaluation/` — benchmark case and scoring primitives.
`tests/` — service and indexing tests.
`docs/specs/` — approved product and architecture designs.
`docs/plans/` — executable implementation plans.

## Key Files
`pyproject.toml` — `uv` project metadata, runtime dependencies, and pytest configuration.
`src/codebase_os/indexer.py` — local repository traversal, symbol extraction, imports, and evidence.
`src/codebase_os/models.py` — Pydantic API and evidence domain models.
`src/codebase_os/service.py` — in-memory repository, memory, retrieval, and answer orchestration.
`src/codebase_os/main.py` — FastAPI routes for indexing, querying, memories, health, and UI.
`src/codebase_os/models_gateway.py` — optional structured model gateway with deterministic no-model mode.
`src/codebase_os/retention.py` — retention cutoff and purge selection helpers.
`src/codebase_os/static/index.html` — current single-page query interface.
`tests/test_service.py` — baseline behavior tests for evidence, abstention, and memory.
`docs/specs/2026-08-31-codebaseos-design.md` — approved architecture and product boundaries.
`docs/plans/2026-08-31-codebaseos-implementation.md` — ordered production implementation tasks.

## Critical Constraints
- Use `uv` commands for Python installation, locking, tests, and runtime execution.
- Answers must remain read-only and claim-to-evidence validated.
- Permission checks must occur before retrieval and source snippet access.
- Static relationships are incomplete; answers must expose caveats and support abstention.
- Local ingestion is the current provider boundary; GitHub is the first planned adapter.
- `uv --cache-dir .uv-cache` is required on this host because the default uv cache path is unavailable.

## Hot Files
`src/codebase_os/service.py`, `src/codebase_os/indexer.py`, `src/codebase_os/main.py`,
`docs/plans/2026-08-31-codebaseos-implementation.md`
