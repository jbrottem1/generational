# Production Readiness Report

**Version:** 9.15.0  
**Branch:** `feature/real-provider-connectors`  
**Owner:** Agent 1 — Chief Systems Architect  
**Date:** 2026-07-09

## Overall production readiness: **84 / 100**

Generational is ready for controlled real-provider pilots and end-to-end
demo/mock production. Remaining blockers are mostly credentialed vendor
validation, engine migration completeness for media backends, and
operational hardening (rate limits under load, observability).

---

## Scorecard

| Area | Score | Why |
|---|---|---|
| Architecture | **90** | Orchestrator-only engine communication enforced; Studio → Workflow Executor → Orchestrator wired; engines no longer import `core.ai`. |
| Execution | **86** | Full pipeline + distribution stages run; stubs degrade with WARNING; analytics/learning on Executor path. |
| Provider Runtime | **88** | Selection, fallback, health, cost, cache, connectors live; `engine_api` is the engine gateway; vendor `execute()` implemented for major providers (keys required). |
| Studio UI | **85** | Production routes through Workflow Executor; long-form via `workflow_run`; provider dashboard via runtime. |
| Workflow Executor | **90** | Durable `ProjectRun`, checkpoints, retries, resume, **pause**, cancel, Studio status projection. |
| Analytics | **78** | Stage wired; mock/heuristic ingestion; real platform analytics adapters still thin. |
| Learning | **76** | Stage wired; weight updates bounded by directive; continuous learning hooks exist but lightly used. |
| Publishing | **80** | Mock adapters + runtime publish path; real YouTube/etc. need live credentials and QA. |
| Long-form readiness | **87** | Checkpoint/resume on WE + RuntimeExecutionEngine; pause/cancel added; multi-hour via stage checkpoints. |
| API readiness | **72** | Internal Python APIs solid; no public HTTP/SaaS API surface yet. |

**Previous estimate:** ~72/100 (pre–engine_api / Studio–WE / pause).  
**Delta:** +12 from ProviderRuntime enforcement, Studio–WE integration, pause/cancel, regression tests.

---

## What was fixed in this readiness pass

1. **Direct AI calls removed from engines** — ideation, script, script_generation, seo use `services.provider_runtime.engine_api.runtime_generate_json`.
2. **`providers.get_llm_provider()`** now returns a ProviderRuntime-backed adapter (no `core.ai`).
3. **Studio → Workflow Executor** production path ported onto this branch.
4. **Pause / cancel** added to Workflow Executor and long-form `RuntimeExecutionEngine`.
5. **Architecture tests** forbid `core.ai` and vendor SDK imports in engines; assert Studio→WE and pause/cancel APIs.
6. **`engine_api` exported** from `services.provider_runtime`.

---

## Remaining blockers (before first live content generation)

| Priority | Blocker | Mitigation |
|---|---|---|
| P0 | Valid API keys + spend limits for chosen vendors | Configure env secrets; start with OpenAI + one image/video vendor |
| P0 | End-to-end smoke with real keys (short + long-form) | Run Studio short → verify packages; documentary with pause/resume |
| P1 | Media engines still may use legacy generation bridges | Prefer `runtime_generate_image/video/voice` everywhere |
| P1 | Publishing to real platforms | Enable one platform adapter; keep others mock |
| P2 | Public API / multi-tenant auth | Out of scope until Agent 22+ API platform |
| P2 | Observability (metrics, tracing) | Add structured provider usage dashboards |

---

## Risk assessment

| Risk | Level | Notes |
|---|---|---|
| Dual long-form controllers (WE vs RuntimeExecutionEngine) | Medium | Studio defaults to WE; longform engine kept for Agent 19 tooling |
| `core.ai` still exists as legacy bridge adapter | Low | Registered in runtime only; engines banned from importing it |
| Demo/heuristic fallbacks mask missing keys | Low | By design for offline; surface `provider_used` / demo flags in UI |
| Concurrent feature branches (Agents 22/23) | Medium | Rebase carefully; do not drop ProviderRuntime connectors |

---

## Recommended next milestones

1. **Live short-form pilot** — one niche, OpenAI + one image provider, publish mock.
2. **Live long-form pilot** — 10–20 min documentary; exercise pause/resume/cancel.
3. **Cost guardrails** — hard budget_usd abort in WorkflowConfig under load.
4. **Deprecate direct `core.ai` callers** outside tests/diagnostics.
5. **Public API sketch** — serialize `PipelineResult` / `ProjectRun` for SaaS.

---

## Success criteria checklist

- [x] Engines do not call AI providers directly
- [x] ProviderRuntime is the generation gateway
- [x] Studio → Workflow Executor → Orchestrator
- [x] Long-form checkpoint / resume / pause / cancel
- [x] Architecture regression tests for bypasses
- [ ] First credentialed end-to-end generation (operator step)
- [ ] First real platform publish (operator step)
