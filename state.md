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

## Open Issues

- No git commit exists, so project-map staleness uses timestamps.
- PostgreSQL, live GitHub App credentials, and model-provider credentials are not configured.
