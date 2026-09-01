# Release Acceptance

Run these checks from the repository root with DBngin PostgreSQL running.
Never paste secret values into logs or issue reports.

## Local environment

```powershell
uv sync --locked --extra dev
uv run pytest -q tests/test_postgres_integration.py -m integration
uv run pytest -q
uv run python -m compileall -q src
uv build --out-dir .release-dist
```

## Production-like configuration

Start with `uv run uvicorn codebase_os.main:app --env-file .env` and verify only status fields:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/ready | ConvertTo-Json
```

Expected result is `status=ready` with `database`, `github`, `model`, and `object_storage` true.
The app selects `SupabaseSnapshotStore` when the Supabase endpoint, access key, and server key are configured.

## Staging-only external checks

Use a disposable staging tenant and repository.
Index one small repository, upload one snapshot, read it back, then delete it and verify the object is gone.
Verify one signed GitHub webhook, one duplicate delivery, and one changed-commit re-index.
These checks mutate external state and must be run by an operator with staging scope.

## Release evidence matrix

| Area | Evidence | Status |
| --- | --- | --- |
| DBngin PostgreSQL | Integration persistence suite | pending operator run |
| Supabase Storage | Disposable upload/read/delete | pending operator run |
| Groq | Query response includes configured model | covered by model tests |
| GitHub | Signature, duplicate, retry, changed commit | covered by webhook tests; live check pending |
| Auth and tenancy | JWT/header boundary and repository filtering | covered by auth/API tests |
| Deletion and retention | Repository cleanup and retention tests | covered by API/retention tests |
| Browser | Static UI contract and responsive/accessibility checks | covered by UI tests |
| Recovery | Backup/restore/rollback runbook | documented; operator restore pending |

## Release decision

Do not tag production while any critical or high-severity item is open.
After all operator checks pass, record the commit, environment, timestamp, and evidence location in the release ticket.
