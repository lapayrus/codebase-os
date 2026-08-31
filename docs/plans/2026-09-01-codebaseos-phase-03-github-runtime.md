# Phase 3: GitHub App Runtime Integration

> Execute with `superpowers-optimized:executing-plans`, `superpowers-optimized:test-driven-development`,
> and `superpowers-optimized:verification-before-completion`.

**Goal:** Make GitHub App installations usable at runtime for repository discovery, snapshot fetching,
and idempotent webhook-driven indexing.

**Base:** `master` at the merged Phase 2 commit.

**Exit gate:** A configured installation can acquire an installation token, list and snapshot a repository,
and a duplicate validated webhook produces one durable ingestion job.

## Task 1: Define GitHub transport and configuration boundaries

- [ ] Add settings for GitHub API URL, request timeout, retry count, and optional installation scope.
- [ ] Add failing tests for configuration validation and secret-safe error messages.
- [ ] Define a transport protocol for App JWT creation, installation token exchange, repository listing,
  tree lookup, and file content retrieval.
- [ ] Keep the transport provider-neutral so tests use fixtures without network access.

## Task 2: Implement GitHub App authentication and HTTP transport

- [ ] Add failing tests for JWT claims, installation token exchange, pagination, and rate-limit handling.
- [ ] Implement short-lived App JWT creation from the configured private key without logging credentials.
- [ ] Implement installation-token acquisition and authenticated GitHub API requests.
- [ ] Implement bounded retry for transient responses and rate-limit reset handling.
- [ ] Map permission and upstream failures to actionable typed errors.

## Task 3: Implement repository snapshot retrieval

- [ ] Add failing fixture tests for default branch metadata, recursive tree traversal, and text file contents.
- [ ] Fetch repository metadata and resolve the default branch.
- [ ] Fetch a commit tree and retrieve supported text files with size and binary safeguards.
- [ ] Produce the existing `RepositoryIndex` shape for the durable indexing pipeline.
- [ ] Preserve repository and installation identity in the snapshot result.

## Task 4: Make webhook deliveries durable and connect indexing jobs

- [ ] Add failing storage tests for delivery uniqueness, job status transitions, retries, and completion.
- [ ] Add additive PostgreSQL tables for webhook deliveries and ingestion jobs.
- [ ] Implement storage ports and PostgreSQL/in-memory implementations for durable job state.
- [ ] Replace process-local delivery deduplication with durable idempotency.
- [ ] Connect validated push and installation events to job creation and repository indexing.
- [ ] Keep deleted installations and inaccessible repositories from being indexed.

## Task 5: Expose runtime integration and verify the phase gate

- [ ] Add API-level tests for installation listing and repository snapshot/index dispatch.
- [x] Add API-level duplicate webhook coverage.
- [ ] Add readiness checks that distinguish missing configuration from upstream GitHub failures.
- [ ] Update operations documentation with GitHub App setup, permissions, retries, and recovery steps.
- [ ] Update `state.md`, `session-log.md`, and the full roadmap checklist.
- [ ] Run the focused suite, full suite, compile check, package build, stub scan, and diff check.

## Verification commands

```powershell
rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider
rtk uv --cache-dir .uv-cache run python -m compileall -q src
rtk uv --cache-dir .uv-cache build
rtk rg -n 'TODO|FIXME|placeholder|NotImplementedError|raise NotImplementedError' src -g '*.py'
rtk git diff --check
```
