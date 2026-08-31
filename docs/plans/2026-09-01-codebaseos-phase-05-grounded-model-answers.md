# Phase 5: Grounded Model Answers

**Goal:** Connect configured model providers to repository retrieval while preserving citation validity,
deterministic fallback behavior, and audit-safe model identity.

**Exit gate:** Generated answers expose only citation-valid claims, reject unsupported claims, identify the selected model,
and safely fall back when a provider fails.

## Tasks

- [x] Connect the service query path to the model gateway.
- [x] Validate model claims against retrieved evidence before response delivery.
- [x] Preserve deterministic no-model mode and safe provider/invalid-response fallback.
- [x] Record selected provider and model in audit data without storing secrets.
- [x] Add API tests for configured provider responses and failure behavior.
- [ ] Add live Groq smoke verification using `.env` without exposing credentials.
- [x] Update operations docs, state, and roadmap tracking.
- [ ] Run focused tests, full suite, compileall, package build, stub scan, and diff check.

## Verification commands

```powershell
rtk uv --cache-dir .uv-cache run pytest -q -p no:cacheprovider --basetemp .phase5-test-tmp
rtk uv --cache-dir .uv-cache run python -m compileall -q src
rtk uv --cache-dir .uv-cache build
rtk git diff --check
```
