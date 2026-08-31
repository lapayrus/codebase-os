# CodebaseOS Production Roadmap Design

## Status

Approved on 2026-09-01 by the project owner.

## Goal

Move CodebaseOS from a tested modular prototype to a production-ready application with durable data,
provider integrations, secure tenancy, background processing, usable UI, and operational release controls.

## Scope

- Durable PostgreSQL runtime using one active database selected by `DATABASE_URL`.
- DBngin PostgreSQL for local development and Supabase PostgreSQL for hosted environments.
- Supabase Storage for private repository snapshots and retention-managed objects.
- GitHub App authentication, repository access, webhooks, and incremental indexing.
- Provider-neutral model gateway with Groq as the current live provider.
- Grounded answers with citation validation, confidence, caveats, and abstention.
- Production authentication, tenant isolation, auditability, background jobs, UI, deployment, and release controls.

## Non-goals

- Dual-writing application data to local PostgreSQL and Supabase PostgreSQL in one environment.
- Treating model output as authoritative without evidence validation.
- Exposing private repository snapshots directly to browsers.
- Replacing provider-neutral interfaces with provider-specific business logic.

## Architecture

`DATABASE_URL` selects the sole durable application database for each environment.
DBngin is the local PostgreSQL target, while Supabase PostgreSQL is the hosted target.

Supabase Storage is an independent object-storage service used for private snapshots.
Supabase Auth may provide hosted sessions, while GitHub remains the repository provider and identity link.

PostgreSQL is the source of truth for repository metadata, evidence, memories, jobs, and audit events.
In-memory structures may remain as bounded query caches, but a process restart must not lose durable data.

The model gateway receives only authorized, bounded retrieval context.
Returned claims are validated against evidence before they are shown to users.

## Phase sequence

1. Existing foundation baseline.
2. Durable PostgreSQL runtime.
3. Durable indexing pipeline.
4. GitHub App runtime integration.
5. Supabase Storage snapshots.
6. Model-grounded answer generation.
7. Authentication and authorization.
8. Background jobs and operations.
9. Production UI.
10. Security, reliability, deployment, and release acceptance.

Each phase has a separate implementation plan, tests before production changes, a verification gate, and a state
checkpoint that names the next phase or blocker.

## Failure-mode check

- Runtime persistence could silently remain in memory; restart persistence tests prevent this.
- Local and hosted schemas could diverge; one migration path and schema readiness checks prevent this.
- Model responses could introduce unsupported claims; claim validation and abstention prevent this.
- Webhook retries could duplicate indexing; durable idempotency keys and job state prevent this.
- Tenant boundaries could be bypassed through snippets or storage objects; authorization occurs before retrieval,
  source access, and object access.

These are critical acceptance requirements, not deferred limitations.

## Environment policy

| Environment | Database | Object storage | Model |
| --- | --- | --- | --- |
| Local | DBngin PostgreSQL | Supabase Storage or local adapter | Groq or another configured adapter |
| Staging | Supabase PostgreSQL | Supabase Storage | Groq or another configured adapter |
| Production | Supabase PostgreSQL | Supabase Storage | Explicitly configured adapter |

Only one database is active per process.
Credentials remain in ignored environment files or secret managers and never enter tracked documents.
