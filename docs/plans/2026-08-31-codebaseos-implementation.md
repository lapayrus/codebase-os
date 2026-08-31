# CodebaseOS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-optimized:subagent-driven-development`
> or `superpowers-optimized:executing-plans` to implement this plan task-by-task.

**Goal:** Evolve the current in-memory MVP into a secure, evidence-first repository intelligence platform.

**Architecture:** Keep a modular FastAPI monolith with provider-neutral ingestion, deterministic indexing,
layered retrieval, evidence validation, and replaceable persistence adapters.

**Tech Stack:** Python 3.12, `uv`, FastAPI, Pydantic, PostgreSQL, pytest, Tree-sitter,
GitHub App APIs, object storage, and an optional model gateway.

**Assumptions:** GitHub is the first provider; the plan does not implement GitLab or Bitbucket.
The code-answer boundary stays read-only; the plan does not add automatic code modification.

## File structure

- `src/codebase_os/`: application modules and provider-neutral interfaces.
- `src/codebase_os/storage/`: database and object-storage adapters.
- `src/codebase_os/providers/`: GitHub adapter and webhook verification.
- `src/codebase_os/retrieval/`: indexing, ranking, context packets, and validation.
- `src/codebase_os/static/`: accessible repository workspace UI.
- `tests/`: unit, API, integration, security, and evaluation fixtures.
- `docs/specs/`: approved product and architecture decisions.
- `docs/plans/`: executable task plans and progress checkboxes.

## Tasks

### Task 1: Establish durable project foundation

**Files:** Modify `pyproject.toml`, `.gitignore`; create `src/codebase_os/config.py`,
`src/codebase_os/errors.py`, `tests/test_config.py`.

**Security flag:** security, because configuration will define tenant and secret handling.

- [x] Add typed settings for environment, database URL, GitHub credentials, object storage,
  model provider, repository size limits, and retention days.
- [x] Validate secrets are read from environment or secret providers and never logged.
- [x] Add stable application errors: `RepositoryNotFound`, `IndexNotReady`, `PermissionDenied`,
  `EvidenceUnavailable`, and `ProviderError`.
- [x] Add `uv` commands to the README:

```powershell
uv sync --extra dev
uv run pytest -q
uv run uvicorn codebase_os.main:app --reload
```

- [x] Verify with `uv run pytest -q`; expect all tests to pass.

### Task 2: Replace in-memory models with persistence ports

**Files:** Create `src/codebase_os/storage/ports.py`, `src/codebase_os/storage/memory.py`,
`src/codebase_os/storage/postgres.py`, `tests/test_storage_ports.py`.

**Security flag:** security, because repository and evidence access become tenant-scoped.

- [x] Define repository, snapshot, evidence, relationship, memory, and answer-cache protocols.
- [x] Require `tenant_id` and repository ID on every read and write method.
- [x] Preserve the existing service behavior through the memory adapter.
- [x] Add PostgreSQL schema migrations for organizations, repositories, commits, files, symbols,
  relationships, evidence, memories, and audit events.
- [x] Add tests proving tenant A cannot retrieve tenant B records through either adapter.
- [x] Verify with `uv run pytest -q tests/test_storage_ports.py`.

### Task 3: Build provider-neutral repository ingestion

**Files:** Create `src/codebase_os/providers/base.py`, `src/codebase_os/providers/local.py`,
`src/codebase_os/ingestion/jobs.py`, `tests/test_ingestion.py`.

**Security flag:** security, because ingestion handles repository content and secrets.

- [x] Define `RepositorySnapshot` with provider, repository ID, branch, commit SHA, files,
  ignored paths, generated-file diagnostics, and source timestamps.
- [x] Move local indexing behind the provider interface without changing query response shape.
- [x] Enforce ignored directories, maximum file size, binary detection, and secret-pattern redaction
  in diagnostics and snippets.
- [x] Add idempotency by `(repository_id, commit_sha)` and incremental file replacement.
- [x] Verify duplicate snapshots do not create duplicate evidence.

### Task 4: Add GitHub App and webhook ingestion

**Files:** Create `src/codebase_os/providers/github.py`, `src/codebase_os/providers/webhooks.py`,
`tests/test_github_provider.py`, `tests/test_webhooks.py`.

**Security flag:** security, because this task handles OAuth credentials, signatures, and repository permissions.

- [x] Implement installation-token acquisition through a provider interface.
- [x] Verify webhook HMAC signatures using the raw request body and constant-time comparison.
- [x] Handle installation, push, branch, repository, and installation-deleted events.
- [x] Fetch only repositories visible to the installation and record the source permission snapshot.
- [x] Queue incremental indexing as idempotent jobs.
- [ ] Verify invalid signatures return 401, valid pushes enqueue one job, and deleted installations remove access.

### Task 5: Make retrieval hybrid and evidence-first

**Files:** Create `src/codebase_os/retrieval/lexical.py`, `structure.py`, `ranking.py`,
`context.py`, `validation.py`; modify `src/codebase_os/service.py`; create `tests/test_retrieval.py`.

**Security flag:** security, because retrieval must enforce repository permissions before snippets are returned.

- [x] Keep lexical search and symbol search as deterministic baseline signals.
- [x] Add relationship traversal for imports, calls, inheritance, routes, and tests.
- [x] Define `ContextPacket` with ranked evidence, token estimate, freshness, and omitted-item counts.
- [x] Rank exact symbols and paths above text matches, then combine lexical, structural, memory,
  and history scores with deterministic tie-breaking.
- [x] Define `validate_claims(claims, evidence)` to remove claims with invalid or empty evidence IDs.
- [x] Add explicit abstention when no evidence clears the configured threshold.
- [ ] Verify citation paths, line ranges, commit SHAs, confidence values, and token budgets.

### Task 6: Add layered memory and freshness

**Files:** Create `src/codebase_os/memory/service.py`, `src/codebase_os/memory/freshness.py`,
`tests/test_memory_freshness.py`.

**Security flag:** security, because memories can contain private operational knowledge.

- [x] Store human memories with author, tenant, repository, timestamps, source, and stale state.
- [x] Store system summaries and query packets keyed by commit and affected subsystem.
- [x] Mark evidence and summaries stale when their referenced files change.
- [x] Keep human memories visible until explicitly archived, while showing their age and affected commit.
- [x] Add history evidence from commit diffs without using commit messages as unverified facts.
- [ ] Verify changed files invalidate only dependent summaries and stale memories remain labeled.

### Task 7: Add secure API and engineering workspace

**Files:** Modify `src/codebase_os/main.py`; create `src/codebase_os/auth.py`,
`src/codebase_os/audit.py`, `src/codebase_os/static/app.js`, `tests/test_api.py`, `tests/test_auth.py`.

**Security flag:** security, because this task defines authentication, authorization, audit, and snippet access.

- [x] Add tenant and user context middleware with repository-level authorization.
- [x] Require authorization before service retrieval, memory access, and source rendering.
- [x] Add audit events for indexing, queries, memory writes, and repository deletion.
- [x] Keep existing endpoints compatible while adding typed error responses and request IDs.
- [x] Replace the static script with accessible loading, empty, error, evidence expansion,
  keyboard navigation, responsive layout, and freshness indicators.
- [ ] Verify API responses never expose unauthorized repository names or source snippets.

### Task 8: Add model gateway and evaluation benchmark

**Files:** Create `src/codebase_os/models/gateway.py`, `src/codebase_os/evaluation/benchmark.py`,
`tests/test_model_gateway.py`, `tests/fixtures/questions.json`.

**Security flag:** security, because customer code is sent to an optional external model provider.

- [x] Define a provider-neutral gateway that accepts only the bounded `ContextPacket`.
- [x] Require structured JSON claims with evidence IDs, confidence, and caveats.
- [x] Support a deterministic no-model mode for local development and tests.
- [x] Record model, prompt-token estimate, completion-token estimate, latency, and failure reason.
- [x] Build benchmark fixtures across behavior, architecture, history, impact, and abstention questions.
- [ ] Verify malformed model output is rejected and model failure returns a grounded retrieval response.

### Task 9: Production operations and release gate

**Files:** Create `Dockerfile`, `.github/workflows/ci.yml`, `docs/operations.md`,
`tests/test_retention.py`; modify `README.md`.

**Security flag:** security, because this task covers retention, deletion, deployment, and audit controls.

- [x] Add CI using `uv sync --locked --extra dev`, lint/type checks, tests, and package build.
- [x] Add health and readiness checks for API, database, queue, and provider dependencies.
- [x] Implement repository deletion, snapshot retention, audit retention, and job retry limits.
- [x] Add structured logs with request ID, tenant ID, repository ID, latency, and outcome,
  excluding code snippets, tokens, and secrets.
- [ ] Verify backup/restore and deletion behavior in an isolated test database.
- [ ] Run the release gate:

```powershell
uv sync --locked --extra dev
uv run pytest -q
uv run python -m compileall -q src
uv run python -c "from codebase_os.main import app; print(len(app.routes))"
```

## Stop conditions

- Stop after Task 5 if evidence support rate is below the agreed benchmark threshold.
- Stop before GitHub rollout if signature, permission, or deletion tests fail.
- Stop before model integration if deterministic retrieval cannot produce bounded context packets.
- Do not add code-writing actions until read-only citation correctness is measured and stable.
