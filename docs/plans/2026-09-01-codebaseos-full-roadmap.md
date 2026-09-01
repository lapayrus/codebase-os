# CodebaseOS Full Production Roadmap

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers-optimized:subagent-driven-development` or
> `superpowers-optimized:executing-plans` to implement each phase task-by-task.
> Steps use checkbox syntax for tracking.

**Goal:** Build CodebaseOS into a production-ready, durable, secure, observable repository intelligence application.
**Architecture:** One active PostgreSQL database is selected by `DATABASE_URL`; DBngin serves local development,
Supabase serves hosted environments, and Supabase Storage holds private snapshots.
The existing provider-neutral retrieval and model boundaries remain stable while runtime persistence, GitHub,
authentication, jobs, UI, and deployment are completed in vertical phases.
**Tech Stack:** Python, FastAPI, Pydantic, PostgreSQL, Supabase, GitHub App APIs, provider-neutral model adapters,
uv, pytest, Docker.
**Assumptions:** Local and hosted environments select one database each; this excludes dual-write synchronization.
Supabase Storage may be used from local development; this excludes making local storage a production dependency.

## Execution rules

- Each phase gets a child plan before implementation begins.
- Each behavior change starts with a failing test.
- Each phase ends with fresh verification and an updated `state.md` checkpoint.
- `session-log.md` stores durable decisions and rejected approaches, not test logs or task checklists.
- `project-map.md` is refreshed after major file-structure changes.
- Secrets are never written to plans, state, logs, command output, or chat.
- A phase is complete only when its exit gate passes.

## Phase 0 — Existing foundation

Status: completed baseline.

- [x] FastAPI application, health, readiness, indexing, querying, memories, and UI routes.
- [x] Repository traversal, symbol extraction, evidence records, retrieval, citations, confidence, and abstention.
- [x] Tenant-scoped in-memory storage and PostgreSQL schema/adapter foundations.
- [x] GitHub webhook verification and idempotent queue primitives.
- [x] Memory freshness and retention foundations.
- [x] OpenAI, OpenAI-compatible, Groq, Anthropic, and Gemini adapter foundations.
- [x] CI, Docker, readiness, deletion, backup/restore, and release-gate foundations.

Exit gate: baseline tests, compilation, stub scan, route checks, DBngin verification, and Groq smoke verification pass.

## Phase 1 — Durable PostgreSQL runtime

Status: next.

- [ ] Add a PostgreSQL runtime connection factory.
- [ ] Select one database from `DATABASE_URL` during application composition.
- [ ] Wire `PostgresStore` into repository, evidence, memory, audit, and deletion flows.
- [ ] Add startup schema validation and connection failure handling.
- [ ] Keep in-memory indexing only as a bounded query cache.
- [ ] Add restart persistence and tenant-isolation integration tests against DBngin.

Exit gate: index, restart, query, and delete data while proving durable persistence and tenant isolation.

## Phase 2 — Durable indexing pipeline

- [ ] Convert indexed repository output into durable repository and evidence records.
- [ ] Add content-version and file-hash idempotency.
- [ ] Track pending, running, succeeded, and failed indexing states.
- [ ] Add partial-failure recovery and retry-safe re-indexing.
- [ ] Remove stale evidence from current retrieval results.
- [ ] Add database-backed re-index, purge, and deletion tests.

Exit gate: repeated commits do not duplicate data, changed files update correctly, and failed indexing is retryable.

## Phase 3 — GitHub App runtime integration

- [ ] Add GitHub App identity and installation-token transport.
- [ ] Fetch installation repositories, metadata, trees, and file contents.
- [ ] Connect validated push and installation webhooks to durable jobs.
- [ ] Deduplicate webhook events with durable idempotency keys.
- [ ] Add GitHub rate-limit, retry, and permission snapshot handling.
- [ ] Add authenticated GitHub integration tests with secret-free fixtures.

Exit gate: an installation can register, a repository can index, and a duplicate webhook creates one job.

## Phase 4 — Supabase Storage snapshots

- [ ] Define tenant-safe snapshot object paths and metadata.
- [ ] Implement private Supabase Storage upload and download.
- [ ] Connect snapshots to repository indexing jobs.
- [ ] Add replacement, retention, and repository deletion cleanup.
- [ ] Prevent direct unauthenticated browser access to snapshots.
- [ ] Add storage integration tests and staging smoke checks.

Exit gate: snapshots upload privately, support indexing reads, obey retention, and disappear after deletion.

## Phase 5 — Model-grounded answer generation

- [ ] Connect `/api/query` to the model gateway.
- [ ] Build bounded context packets from authorized retrieval evidence.
- [ ] Validate model claims against citations before response delivery.
- [ ] Preserve deterministic no-model mode and safe provider failure behavior.
- [ ] Record selected provider and model in audit data without storing secrets.
- [ ] Add Groq end-to-end and fake-transport adapter tests.

Exit gate: generated answers expose valid citations, reject unsupported claims, and identify the configured model.

## Phase 6 — Authentication and authorization

- [x] Validate Supabase sessions in hosted environments.
- [x] Link GitHub identities, installations, repositories, and tenants.
- [x] Restrict development authentication to local mode.
- [x] Enforce authorization before retrieval, snippets, memories, and storage objects.
- [x] Add session expiry, denied-access audit, and cross-tenant tests.

Exit gate: production requests require valid sessions and cannot cross tenant or repository boundaries.

## Phase 7 — Background jobs and operations

- [ ] Add a durable queue abstraction and local worker.
- [ ] Implement leases, retries, bounded backoff, stale-job recovery, and dead-letter state.
- [ ] Add indexing progress and operational status endpoints.
- [ ] Add structured logs, correlation IDs, and metrics.
- [ ] Document local worker and hosted worker startup.

Exit gate: webhook jobs survive restarts, retry safely, and expose actionable failure status.

## Phase 8 — Production UI

- [x] Add authenticated session status and permission-denied handling.
- [x] Add repository selection and local indexing status.
- [x] Add query results with citations, confidence, caveats, and abstention.
- [x] Add memory and repository deletion controls.
- [x] Add loading, empty, error, and permission-denied states.
- [x] Add accessibility, responsive layout, and static browser-contract tests.

Exit gate: an authenticated user can select, index, query, inspect citations, and delete an authorized repository.

## Phase 9 — Security, reliability, and deployment

- [x] Review secrets, webhook verification, tenant boundaries, and storage policies.
- [x] Add migration execution, backup, restore, and rollback procedures.
- [x] Add liveness, readiness, rate limits, request-size limits, and error redaction.
- [x] Add CI database integration, dependency, and vulnerability checks.
- [x] Document deployment, rollback, retention, and disaster recovery.

Exit gate: deployment fails closed on missing production requirements and recovery procedures are verified.

## Phase 10 — Release acceptance

- [ ] Run local DBngin acceptance tests.
- [ ] Run Supabase staging acceptance tests.
- [ ] Run GitHub webhook and incremental indexing acceptance tests.
- [ ] Run Groq query, tenant-isolation, deletion, retention, and browser suites.
- [ ] Confirm observability, backup/restore evidence, and environment matrix.
- [ ] Resolve all critical and high-severity release blockers.
- [ ] Tag the first production release.

Exit gate: local, staging, and production-like flows work end to end with release evidence recorded.

## Cross-session state contract

At every session boundary, `state.md` must contain:

- Current goal.
- Active phase and child plan path.
- Completed task range.
- Exact next task.
- Blockers and required user input.
- Latest verification command and result.
- Environment readiness matrix without secret values.

`session-log.md` must contain only durable decisions, rejected approaches, and carry-forward constraints.
When a design changes, the old decision is marked superseded instead of deleted.
