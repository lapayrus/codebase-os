# Phase 10: Release Acceptance

**Goal:** Record repeatable evidence that the local and production-like CodebaseOS paths are ready for release.

**Exit gate:** Local, staging, and production-like flows work end to end with release evidence recorded and no critical
or high-severity blockers.

## Tasks

- [x] Run local DBngin PostgreSQL acceptance tests.
- [ ] Run Supabase staging configuration and snapshot acceptance checks.
- [x] Run GitHub webhook and incremental indexing acceptance tests.
- [x] Run Groq query, tenant isolation, deletion, retention, and browser-contract suites.
- [x] Confirm observability, backup/restore evidence, and environment matrix.
- [ ] Record blockers and release decision.
- [ ] Tag the first production release after merge approval.

## Current evidence

- DBngin integration: `2 passed`.
- Full automated suite: `100 passed`.
- Exact local command `uv run pytest -q`: `100 passed` after configuring workspace-local `.pytest-tmp`.
- Production-like `/ready`: HTTP 200 with all checks true.
- `.env` startup selects `SupabaseSnapshotStore`.
- Fresh package artifacts build successfully.
- Live local HTTP check with `uvicorn --app-dir src`: readiness HTTP 200 and repository indexing HTTP 200 for 1522 files.
- Supabase staging mutation and final release tag remain operator-controlled.
