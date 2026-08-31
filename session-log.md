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
