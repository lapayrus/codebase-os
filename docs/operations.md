# CodebaseOS Operations

## Local execution

```powershell
uv sync --locked --extra dev
uv run uvicorn codebase_os.main:app --reload --env-file .env
```

Local runtime persistence uses DBngin PostgreSQL.
Set `CODEBASEOS_DATABASE_URL=postgresql://postgres@127.0.0.1:5432/codebaseos` after starting DBngin.

The application initializes the required schema on startup.
Verify restart persistence with `uv run pytest -q tests/test_postgres_integration.py -m integration`.

Hosted environments set `CODEBASEOS_DATABASE_URL` to the Supabase PostgreSQL connection string.
Only one database URL is active in a running process.

## Indexing migration and recovery

Schema initialization applies additive indexing columns for existing databases.
It preserves repositories and evidence, and backfills legacy repositories as `succeeded`.

To re-index a repository, call `POST /api/repositories/index` with its path and name.
An unchanged content version returns `status=unchanged`; changed content returns `status=reindex`.

New evidence is written before evidence from an older commit is removed.
If indexing fails, the prior succeeded repository version remains available for retrieval.

Rollback disables new indexing writes before removing only the additive indexing columns in a reviewed migration.
Do not delete historical evidence manually while an indexing operation is running.

## Required production settings

- `CODEBASEOS_ENVIRONMENT=production`
- `CODEBASEOS_DATABASE_URL` set to PostgreSQL, not SQLite.
- `CODEBASEOS_GITHUB_APP_ID`, `CODEBASEOS_GITHUB_PRIVATE_KEY`, and
  `CODEBASEOS_GITHUB_WEBHOOK_SECRET` loaded from a secret manager.
- `CODEBASEOS_RETENTION_DAYS` set to the approved repository retention policy.
- `CODEBASEOS_MAX_REQUEST_BYTES` and `CODEBASEOS_RATE_LIMIT_PER_MINUTE` set for deployment capacity.
- `CODEBASEOS_SUPABASE_JWT_SECRET` set for hosted JWT verification; keep it server-side.
- `CODEBASEOS_OBJECT_STORAGE_ENDPOINT`, `CODEBASEOS_OBJECT_STORAGE_ACCESS_KEY`, and
  `CODEBASEOS_OBJECT_STORAGE_SECRET_KEY` set for Supabase S3-compatible snapshot storage.

## Readiness

`/health` confirms the API process and reports the loaded repository count.

`/ready` reports API, database, queue, GitHub, model, and object-storage configuration readiness. In production it
returns 503 until a non-SQLite database and GitHub App credentials are configured; selected online integrations are
also checked in development.

Readiness is a configuration and reachability gate.
The phase integration tests are the proof for durable writes, restart recovery, and deletion behavior.

GitHub App runtime creates short-lived App JWTs from `CODEBASEOS_GITHUB_APP_ID` and
`CODEBASEOS_GITHUB_PRIVATE_KEY`, then exchanges them for installation tokens.
The client paginates repositories, requests recursive trees, skips oversized or binary blobs, and retries bounded
transient or exhausted-rate-limit responses.
Webhook deliveries use a `(delivery_id, repository_id)` uniqueness key before indexing work is claimed.
Failed jobs are retryable, while completed jobs remain recorded for duplicate suppression.

The production readiness check must also verify database, queue, object storage,
GitHub provider, and model gateway connectivity before accepting indexing work.

API requests under `/api/` are limited by `CODEBASEOS_MAX_REQUEST_BYTES` and
`CODEBASEOS_RATE_LIMIT_PER_MINUTE`.
Rejected requests return 413 or 429 without processing their payload.
Unexpected failures return a generic 500 response with a request ID; internal exception text is not exposed.

## Backup, restore, and rollback

Create a PostgreSQL backup before migrations or retention changes:

```powershell
pg_dump --format=custom --file=backups\codebaseos-latest.dump $env:CODEBASEOS_DATABASE_URL
```

Restore only into a stopped, disposable target first, then verify repository counts and a representative evidence span:

```powershell
pg_restore --clean --if-exists --dbname=$env:CODEBASEOS_DATABASE_URL backups\codebaseos-latest.dump
uv run pytest -q tests/test_postgres_integration.py -m integration
```

The application performs additive schema initialization on startup.
Rollback disables new indexing writes, restores the last verified database backup, and removes only the reviewed
additive migration after acceptance checks pass.
Supabase snapshot objects must be retained or restored with the matching database commit records.
Never run `pg_restore --clean` against production until the backup and target URL have been independently verified.

Snapshot objects use `tenants/<tenant>/repositories/<owner>/<repo>/<commit>.snapshot` and are never exposed through
public URLs.
Hosted Supabase Storage requires a server-side storage key with object insert, select, update, and delete permissions;
never place that key in browser configuration.
In development, a missing server key selects the local snapshot adapter so the API can start without pretending hosted
storage is connected.

## Data controls

Repository deletion must remove snapshots, evidence, memories, embeddings, and audit records
according to the configured retention policy.

Logs must contain request, tenant, repository, latency, and outcome fields, but never source
snippets, secrets, or raw model prompts.

## Model providers

Set `CODEBASEOS_MODEL_PROVIDER` to `none`, `openai`, `groq`, `cerebras`, `together`, `openrouter`, `openai-compatible`,
`anthropic`, or `gemini`. Set the API key and model name for every online provider; OpenAI-compatible providers also
require `CODEBASEOS_MODEL_BASE_URL`. Readiness validates this configuration without calling the provider.
Query responses include the selected model identifier, and query audit metadata records that identifier without storing
credentials.
Provider errors or invalid structured output fall back to citation-grounded retrieval with an explicit caveat.
