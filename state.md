# Current Goal

Execute the approved CodebaseOS full production roadmap, beginning with durable PostgreSQL runtime wiring.

## Decisions

- Modular FastAPI monolith with provider-neutral interfaces.
- `uv` is the only Python workflow and `uv.lock` is committed.
- Read-only answers require versioned evidence, confidence, freshness, and abstention.
- One database is active per environment through `DATABASE_URL`; DBngin is local and Supabase is hosted.
- Supabase Storage is separate from the application database and stores private repository snapshots.

## Plan Status

- Existing implementation plan is complete for its defined foundation scope.
- Model adapter plan is complete at `docs/plans/2026-09-01-model-provider-adapters-implementation.md`.
- Full roadmap design is approved at `docs/specs/2026-09-01-codebaseos-production-roadmap-design.md`.
- Full roadmap is active at `docs/plans/2026-09-01-codebaseos-full-roadmap.md`.
- Phase 1 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-01-postgresql-runtime.md`.
- Phase 2 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-02-durable-indexing.md`.
- Phase 1 durable PostgreSQL runtime is complete.
- Phase 2 durable indexing pipeline is complete.
- Phase 3 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-03-github-runtime.md`.
- Current phase is Phase 3, GitHub App runtime integration.

## Evidence

- DBngin PostgreSQL is reachable at `127.0.0.1:5432`; database `codebaseos` contains the required schema.
- PostgreSQL backup/restore and deletion verification succeeded with disposable data.
- Groq returned HTTP 200 with generated content using the configured model.
- Running `/ready` reports `api`, `database`, `queue`, `github`, `model`, and `object_storage` as true.
- Latest test run reported 55 passed; compilation, route, stub, and diff checks succeeded.

## Open Issues

- The static query index remains an in-memory cache until a later durable index reconstruction phase.
- GitHub API transport/OAuth, Supabase Storage operations, hosted sessions, durable jobs, and production UI remain.
- CI requires a PostgreSQL service because the integration suite now exercises restart persistence.

## Current execution checkpoint

- Next action: write and approve the Phase 3 GitHub App runtime child plan.
- Last verification: full suite reported `64 passed, 1 warning`; compileall, stub scan, and diff checks succeeded; live
  `/ready` reported all six checks true.
- Required proof: GitHub installations can authenticate, fetch repositories, and trigger one durable indexing job.
- Environment status: local DBngin and Groq are live-tested; GitHub and Supabase need live runtime tests.
- Phase 2 result: `73 passed, 1 warning`; compileall, package build, stub scan, and `git diff --check` succeeded.
- CI diagnosis: master run `33447826826` failed at pytest because no PostgreSQL service was defined.
- CI fix branch: `codex-ci-postgres-service`, adding PostgreSQL 17 and `CODEBASEOS_DATABASE_URL` to the job.
- CI fix commit: `a04e758` is pushed; PR creation awaits `gh auth login` because the stored CLI token returns HTTP 401.
- Secrets are present only in ignored `.env` and are not copied into tracked state or documentation.
