# Phase 6: Authentication and Tenancy

**Goal:** Require verified hosted sessions and enforce tenant/repository boundaries across every protected operation.

**Exit gate:** Production requests require valid sessions and cannot cross tenant or repository boundaries.

## Tasks

- [x] Add Supabase JWT/session verification with injectable key and issuer checks.
- [x] Restrict header-based development authentication to non-production environments.
- [x] Link verified user, tenant, installation, and repository context.
- [x] Enforce authentication and authorization on retrieval, snippets, memories, and snapshot access.
- [x] Add session expiry, denied-access audit, and cross-tenant tests.
- [x] Update readiness, docs, state, and roadmap tracking.
- [ ] Run focused tests, full suite, compileall, package build, stub scan, and diff check.
