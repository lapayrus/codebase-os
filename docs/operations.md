# CodebaseOS Operations

## Local execution

```powershell
uv sync --locked --extra dev
uv run uvicorn codebase_os.main:app --reload
```

## Required production settings

- `CODEBASEOS_ENVIRONMENT=production`
- `CODEBASEOS_DATABASE_URL` set to PostgreSQL, not SQLite.
- `CODEBASEOS_GITHUB_APP_ID`, `CODEBASEOS_GITHUB_PRIVATE_KEY`, and
  `CODEBASEOS_GITHUB_WEBHOOK_SECRET` loaded from a secret manager.
- `CODEBASEOS_RETENTION_DAYS` set to the approved repository retention policy.

## Readiness

`/health` confirms the API process and reports the loaded repository count.

The production readiness check must also verify database, queue, object storage,
GitHub provider, and model gateway connectivity before accepting indexing work.

## Data controls

Repository deletion must remove snapshots, evidence, memories, embeddings, and audit records
according to the configured retention policy.

Logs must contain request, tenant, repository, latency, and outcome fields, but never source
snippets, secrets, or raw model prompts.

