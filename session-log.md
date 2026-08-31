## 2026-08-31 17:00 [saved]
Goal: Establish a durable, evidence-first implementation path for CodebaseOS.
Decisions:
- Use a modular FastAPI monolith because early reliability matters more than service independence.
- Use `uv` exclusively because reproducible Python environments are a project constraint.
- Keep code actions read-only because trust and citation correctness precede mutation.
- Make GitHub the first provider because the product starts from GitHub repositories.
Rejected: Generic chatbot positioning; autonomous code changes; microservices before measured scale.
Open: Configure PostgreSQL and GitHub App credentials before production integration.
