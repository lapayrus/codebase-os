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
- Current phase is Phase 9, security, reliability, and deployment, on branch
  `codex-phase-09-security-reliability`.
- Phase 3 is merged through PR #5; Phase 4 branch is `codex-phase-04-supabase-storage`.
- Phase 4 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-04-supabase-storage.md`.
- Phase 4 snapshot storage slice is implemented with tenant-safe paths, private Supabase REST access, local adapter,
  worker upload, and repository deletion cleanup.
- Phase 5 branch is `codex-phase-05-grounded-model-answers`.
- Phase 5 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-05-grounded-model-answers.md`.
- Phase 5 query integration currently connects the model gateway and citation-validates model claims with safe fallback.
- Phase 5 records model identity in answer and audit metadata without credentials.
- Phase 5 is merged through PR #7; Phase 6 branch is `codex-phase-06-auth-tenancy`.
- Phase 6 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-06-auth-tenancy.md`.
- Phase 6 authentication boundary is implemented with production JWT verification and local-only header auth.
- Phase 6 is merged through PR #8; Phase 7 branch is `codex-phase-07-job-operations`.
- Phase 7 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-07-job-operations.md`.
- Phase 7 is merged through PR #9; Phase 8 child plan is ready at
  `docs/plans/2026-09-01-codebaseos-phase-08-production-ui.md`.
- Phase 8 adds the production repository intelligence workspace with repository controls, grounded answer rendering,
  evidence spans, memory context, deletion, loading states, permission errors, responsive layout, and accessibility.
- Phase 8 startup behavior uses the local snapshot adapter in development when the Supabase server key is absent;
  production still fails closed with `CODEBASEOS_OBJECT_STORAGE_SECRET_KEY` missing.
- Phase 9 child plan is ready at `docs/plans/2026-09-01-codebaseos-phase-09-security-reliability.md`.
- Phase 9 adds request-size/rate bounds, generic correlated 500 responses, environment knobs, CI dependency auditing,
  and backup/restore/rollback runbook procedures.

## Evidence

- DBngin PostgreSQL is reachable at `127.0.0.1:5432`; database `codebaseos` contains the required schema.
- PostgreSQL backup/restore and deletion verification succeeded with disposable data.
- Groq returned HTTP 200 with generated content using the configured model.
- Running `/ready` reports `api`, `database`, `queue`, `github`, `model`, and `object_storage` as true.
- Phase 3 focused runtime tests pass: GitHub transport, JWT construction, retries, snapshot fixtures, and durable jobs.
- Phase 9 verification: full pytest `100 passed`; focused security/config/UI tests `10 passed`; compileall, fresh-output
  package build, JavaScript syntax, stub scan, and diff checks passed.

## Open Issues

- The static query index remains an in-memory cache until a later durable index reconstruction phase.
- GitHub live installation registration and worker indexing remain for the Phase 3 exit gate.
- Supabase Storage operations, hosted sessions, and production UI remain in later phases.
- CI requires a PostgreSQL service because the integration suite now exercises restart persistence.

## Current execution checkpoint

- Next action: obtain explicit remote-push authorization, then complete live GitHub integration proof.
- Last verification: full suite reported `64 passed, 1 warning`; compileall, stub scan, and diff checks succeeded; live
  `/ready` reported all six checks true.
- Required proof: GitHub installations can authenticate, fetch repositories, and trigger one durable indexing job.
- Environment status: local DBngin and Groq are live-tested; GitHub and Supabase need live runtime tests.
- Phase 2 result: `73 passed, 1 warning`; compileall, package build, stub scan, and `git diff --check` succeeded.
- Phase 3 branch: `codex-phase-03-github-runtime`.
- Phase 3 implementation adds `httpx` and `PyJWT`, bounded GitHub transport, recursive snapshot retrieval, and durable
  ingestion job state.
- Phase 3 verification: `78 passed, 1 warning`; workspace-local pytest temp directory was required because system temp
  access is denied.
- Phase 3 worker verification: GitHub jobs claim, index, complete, and retry through durable storage.
- Phase 4 verification: `83 passed, 1 warning`; compileall and `git diff --check` passed.
- Phase 5 verification: `86 passed, 1 warning` before final audit integration; final rerun is required.
- Phase 6 verification: `89 passed, 3 warnings`; compileall and `git diff --check` passed.
- Live Groq smoke reached the configured endpoint but returned HTTP 403; local fallback behavior is verified, while
  upstream credential/model authorization remains open.
- CI diagnosis: master run `33447826826` failed at pytest because no PostgreSQL service was defined.
- CI fix branch: `codex-ci-postgres-service`, adding PostgreSQL 17 and `CODEBASEOS_DATABASE_URL` to the job.
- CI fix commit: `a04e758` is pushed; PR creation awaits `gh auth login` because the stored CLI token returns HTTP 401.
- Secrets are present only in ignored `.env` and are not copied into tracked state or documentation.
