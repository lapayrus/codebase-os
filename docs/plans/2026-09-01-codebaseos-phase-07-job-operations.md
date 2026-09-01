# Phase 7: Background Jobs and Operations

**Goal:** Make ingestion jobs restart-safe and operationally visible with leases, bounded retries, dead-letter state,
and protected status reporting.

**Exit gate:** Webhook jobs survive restarts, retry safely, and expose actionable failure status.

## Tasks

- [ ] Add lease, retry, backoff, and dead-letter fields to durable jobs.
- [ ] Recover expired running leases and prevent concurrent claims.
- [ ] Add protected job status endpoint and structured correlation fields.
- [ ] Add worker startup documentation and operational tests.
- [ ] Update state and roadmap tracking.
- [ ] Run focused tests, full suite, compileall, package build, stub scan, and diff check.
