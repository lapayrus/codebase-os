# CodebaseOS Operations

## Local execution

```powershell
uv sync --locked --extra dev
uv run uvicorn codebase_os.main:app --reload --env-file .env
```

## Required production settings

- `CODEBASEOS_ENVIRONMENT=production`
- `CODEBASEOS_DATABASE_URL` set to PostgreSQL, not SQLite.
- `CODEBASEOS_GITHUB_APP_ID`, `CODEBASEOS_GITHUB_PRIVATE_KEY`, and
  `CODEBASEOS_GITHUB_WEBHOOK_SECRET` loaded from a secret manager.
- `CODEBASEOS_RETENTION_DAYS` set to the approved repository retention policy.

## Readiness

`/health` confirms the API process and reports the loaded repository count.

`/ready` reports API, database, queue, GitHub, model, and object-storage configuration readiness. In production it
returns 503 until a non-SQLite database and GitHub App credentials are configured; selected online integrations are
also checked in development.

The production readiness check must also verify database, queue, object storage,
GitHub provider, and model gateway connectivity before accepting indexing work.

## Data controls

Repository deletion must remove snapshots, evidence, memories, embeddings, and audit records
according to the configured retention policy.

Logs must contain request, tenant, repository, latency, and outcome fields, but never source
snippets, secrets, or raw model prompts.

## Model providers

Set `CODEBASEOS_MODEL_PROVIDER` to `none`, `openai`, `groq`, `cerebras`, `together`, `openrouter`, `openai-compatible`,
`anthropic`, or `gemini`. Set the API key and model name for every online provider; OpenAI-compatible providers also
require `CODEBASEOS_MODEL_BASE_URL`. Readiness validates this configuration without calling the provider.
