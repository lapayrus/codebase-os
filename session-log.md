## 2026-08-31 17:00 [saved]
Goal: Establish a durable, evidence-first implementation path for CodebaseOS.
Decisions:
- Use a modular FastAPI monolith because early reliability matters more than service independence.
- Use `uv` exclusively because reproducible Python environments are a project constraint.
- Keep code actions read-only because trust and citation correctness precede mutation.
- Make GitHub the first provider because the product starts from GitHub repositories.
Rejected: Generic chatbot positioning; autonomous code changes; microservices before measured scale.
Open: Configure PostgreSQL and GitHub App credentials before production integration.

## 2026-08-31 18:10 [saved]
Goal: Provision a free Supabase backend for CodebaseOS development.
Decisions:
- Create a new Supabase project in Nerve Organization because the user rejected reusing the inactive project.
- Use ap-south-1 because the project is being developed from India.
- Keep repository snapshots private and enable RLS on all application tables.
Rejected: Reusing Nerve Local; public snapshot storage; exposing service-role credentials.
Open: Add server-side Supabase database access after credentials are supplied securely.

## 2026-09-01 12:00 [saved]
Goal: Confirm durable task tracking and record local GitHub integration readiness.
Decisions:
- Use `docs/plans/2026-08-31-codebaseos-implementation.md` as the authoritative task list.
- Use `state.md` for current progress, blockers, and verification evidence across sessions.
- Keep GitHub credentials local and ignored; never copy secret values into tracked files or chat.
Rejected: Treating a temporary Cloudflare URL as a permanent deployment endpoint.
Open: Implement and test GitHub webhook and OAuth callback routes.
## 2026-09-01 [saved]
Goal: Establish the full phased roadmap and durable cross-session execution contract.
Decisions:
- Use one active PostgreSQL database per environment through `DATABASE_URL` to prevent split-brain persistence.
- Use DBngin locally and Supabase PostgreSQL for hosted environments to match deployment reality.
- Treat Supabase Storage as separate private snapshot storage, not a second application database.
- Execute ten production phases with child plans, verification gates, and `state.md` checkpoints.
Rejected: Dual-writing local and Supabase databases in one runtime.
Rejected: Treating readiness configuration checks as proof of end-to-end runtime integration.
Open: Write and approve the Phase 1 durable PostgreSQL child plan.
## 2026-09-01 [saved]
Goal: Make CI execute the PostgreSQL integration suite with the same durable runtime assumption as local development.
Decisions:
- Add a PostgreSQL 17 GitHub Actions service because integration tests require restart persistence.
- Provide `CODEBASEOS_DATABASE_URL` at the CI job level so application composition uses PostgreSQL.
Rejected: Skipping integration tests in CI or silently falling back to in-memory storage.
Open: Merge the CI service fix through a dedicated pull request.

## 2026-09-01 [saved]
Goal: Preserve the CI fix handoff after remote PR authentication failed.
Decisions:
- Keep the CI service fix on `codex-ci-postgres-service` until its PR is created and merged.
- Require valid GitHub CLI authentication before creating or merging pull requests.
Rejected: Bypassing the PR workflow through direct master pushes.
Open: Run `gh auth login`, then create and merge the CI fix PR.
## 2026-09-01 14:00 [saved]
Goal: Start Phase 3 GitHub App runtime integration from the merged Phase 2 master state.
Decisions:
- Base the phase branch on `master` and keep PR creation and merging with the user.
- Use a provider-neutral GitHub transport boundary with fixture-backed tests before live calls.
- Make webhook delivery and ingestion job state durable before wiring repository indexing.
Open: Implement the Phase 3 child plan and verify the runtime exit gate.
## 2026-09-01 14:30 [saved]
Goal: Implement the first Phase 3 GitHub runtime slice on the dedicated master-based branch.
Decisions:
- Use `httpx` and `PyJWT` as production dependencies for authenticated GitHub App transport.
- Keep repository snapshot retrieval fixture-testable and bounded for text size and binary content.
- Persist webhook ingestion uniqueness and retry state through the existing storage abstraction.
Evidence:
- Focused Phase 3 tests pass: `8 passed`.
- Full regression suite passes: `78 passed, 1 warning` with a workspace-local pytest temp directory.
Open: Add live/API dispatch proof and complete the remaining Phase 3 exit-gate tasks.
