# CodebaseOS Design

**Status:** Approved on 2026-08-31.

## Goal

CodebaseOS gives engineering teams concise repository answers with versioned evidence,
confidence, freshness, and durable project memory.

## Scope

- GitHub is the first repository provider.
- The platform is organization-aware and read-only for code.
- Answers support architecture, behavior, impact, ownership, history, and documentation questions.
- Every material claim links to repository, commit, path, line range, and source snippet.
- Human memories support decisions, conventions, gotchas, ownership, and open questions.

## Non-goals

- No autocomplete or general coding-agent replacement.
- No automatic code edits, merges, or deployment actions.
- No runtime telemetry ingestion in the first implementation plan.
- No microservice split before measured scaling pressure.

## Architecture

Use a modular monolith managed with `uv`.

FastAPI exposes repository, query, memory, health, and administrative endpoints.

The ingestion boundary accepts provider-neutral repository snapshots and commit metadata.

Indexing extracts files, symbols, imports, relationships, summaries, and evidence records.

Retrieval combines lexical, structural, semantic, history, and memory signals.

The answer layer produces structured claims, validates claim-to-evidence mappings,
and abstains when support is insufficient.

PostgreSQL stores tenant, permission, repository, evidence, and memory metadata.

Object storage stores immutable snapshots and generated artifacts.

The vector index is an optional retrieval signal, never the authority for source claims.

## Contracts

`QueryRequest` contains `question`, optional `repository`, and bounded `top_k`.

`Answer` contains `answer`, `claims`, `evidence`, `caveats`, `repository`, `commit`,
and `tokens_estimate`.

`Claim` contains text, confidence, and evidence IDs.

`Evidence` contains repository, commit, path, start line, end line, snippet, kind,
and relevance.

All identifiers crossing API boundaries are opaque strings.

## Failure handling

- Missing repositories return a typed 404 or 409 response.
- Unindexed repositories cannot receive memories or queries.
- Unsupported or unreadable files are skipped and counted in indexing diagnostics.
- Unsupported claims are removed before rendering an answer.
- Stale evidence is visible and never silently presented as current.
- Permission checks execute before retrieval and before source snippet access.

## Adversarial risks

- Parser gaps can create incomplete graphs; expose parser coverage and static-analysis caveats.
- LLM confidence can exceed evidence; require deterministic evidence validation and abstention.
- Cross-tenant leakage is critical; enforce tenant and repository authorization in the service layer.
- Product scope can drift into coding assistance; preserve the read-only evidence boundary.

## Acceptance measures

Track citation correctness, supported-claim rate, abstention quality, freshness after commits,
retrieval latency, model tokens, cost per question, and engineer verification time.

The primary product metric is verified useful answers per engineer-minute.

