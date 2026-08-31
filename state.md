# Current Goal

Create durable planning and memory artifacts for the CodebaseOS production implementation.

## Decisions

- Modular FastAPI monolith with provider-neutral interfaces.
- `uv` is the only Python workflow and `uv.lock` is committed.
- Read-only answers require versioned evidence, confidence, freshness, and abstention.
- GitHub is the first provider; PostgreSQL is the planned durable store.

## Plan Status

- Design approved and saved to `docs/specs/2026-08-31-codebaseos-design.md`.
- Implementation plan saved to `docs/plans/2026-08-31-codebaseos-implementation.md`.
- Tasks 1, 3, 5, 6, 7, 8, and 9 have working slices in the current workspace.
- Tasks 2 and 4 have interfaces and security primitives; durable deployment and live GitHub wiring remain.

## Evidence

- `uv sync --locked --extra dev` is the target CI setup.
- `uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp` passes 3 tests.
- Existing HTTP smoke flow indexes a repository and returns cited evidence.
- `uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp` passes 24 tests.
- Supabase project `pcxrntpgplvdbvpqycfv` exists in `ap-south-1` on the confirmed $0/month path.
- Supabase schema tables have RLS enabled and `repository-snapshots` is a private storage bucket.

## Open Issues

- No git commit exists, so project-map staleness uses timestamps.
- Supabase service-role/database credentials and model-provider credentials are not configured.
- GitHub App values are present in local `.env`; webhook signature verification and incremental queueing now have
  an API route, while OAuth and provider HTTP transport remain unimplemented.

## Current execution checkpoint

- Plan: `docs/plans/2026-08-31-codebaseos-implementation.md`.
- Last completed task: Task 2 persistence ports and tenant isolation proof.
- Verification: `uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .test-tmp` → 29 passed;
  `compileall` succeeded; app route count is 13; `git diff --check` reported no diff errors.
- New facts: `tests/test_storage_ports.py` uses a deterministic fake cursor to exercise `PostgresStore` tenant-bound
  queries without requiring a live database; same repository IDs remain isolated by tenant.
- Next state: address remaining release-gate gaps, starting with production readiness and durable deletion checks.
