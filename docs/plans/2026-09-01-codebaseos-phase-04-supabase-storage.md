# Phase 4: Supabase Storage Snapshots

**Goal:** Store repository snapshots in private Supabase Storage with tenant-safe paths, authenticated access,
and deletion aligned with repository lifecycle.

**Exit gate:** A snapshot uploads privately, can be read by indexing, obeys retention metadata, and is deleted with
its repository.

## Tasks

- [x] Define a snapshot storage protocol and canonical tenant/repository/commit object path.
- [x] Add failing tests for path traversal rejection, metadata, upload, download, and delete.
- [x] Implement a fixture-testable Supabase Storage REST client using server-side credentials only.
- [x] Add a local in-memory adapter for development and tests.
- [x] Connect snapshot upload and retrieval to ingestion/indexing jobs.
- [x] Connect repository deletion to snapshot deletion.
- [ ] Add retention listing/deletion primitives without exposing public URLs.
- [ ] Update readiness, operations docs, state, and roadmap tracking.
- [ ] Run focused tests, full suite, compileall, package build, stub scan, and diff check.

## Verification commands

```powershell
rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .phase4-test-tmp
rtk uv --cache-dir .uv-cache run python -m compileall -q src
rtk uv --cache-dir .uv-cache build
rtk git diff --check
```
