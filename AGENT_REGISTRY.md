# Generational — Agent Registry (v9.7)

Canonical roster of development agents, departments, and expansion slots.
Maintained by Agent 1. New agents add a row here **before** writing code
(`INTEGRATION_CHECKLIST.md`).

Companions: `ENGINE_REGISTRY.md` · `SYSTEM_DEPENDENCY_MAP.md` ·
`AGENT_WORKFLOW.md` · `ARCHITECTURE_REVIEW.md`.

---

## 1. Active & Completed Agents

### Foundation Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **1** | Master Architecture & Orchestrator | orchestrator, registry, contracts, trend_discovery, opportunity_ranking | active, permanent |
| **2** | Psychology & Behavioral Intelligence | psychology, attention_graph, threat_detection | shipped |
| **3** | Script Generation | script_generation, script, critic, revision | shipped |
| **4** | Visual Intelligence | visual_intelligence | shipped |
| **5** | Voice & Audio | voice_audio (+ planned `voice` TTS) | shipped (planning) |

### Production Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **6** | Render Engine | render, image, video | shipped (mock renderer) |
| **7** | Publishing & Distribution | publishing, scheduler, publishing_queue | shipped (mock platforms) |
| **8** | Global Content Optimization | seo_optimization | shipped |
| **9** | Production Pipeline | scene_planning … render_package + services/pipeline.py | shipped |

### Intelligence Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **10** | Analytics & Continuous Learning | analytics, learning | shipped (simulated metrics) |
| **11** | Market Intelligence & Forecasting | market_intelligence, trend_forecasting | shipped |
| **12** | Creative Studio | creative_studio | **LIVE** |
| **13** | Optimization Laboratory | optimization_lab | stub (worktree ready — merge pending) |

### Media Generation Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **14** | Universal Asset Generation | asset_generation | **LIVE** |
| **15** | Character, Universe & IP | character_universe | stub (worktree ready — merge pending) |
| **16** | Animation & Cinematics | animation | stub (worktree ready — merge pending) |
| **17** | Post-Production & Intelligent Editing | post_production | **LIVE** |

---

## 2. Active & Completed Agents (continued)

### Infrastructure & Interface Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **19** | Provider Integration & Runtime | `services/provider_runtime/` | **LIVE** |
| **20** | Studio UI & Creative Workspace | `services/studio/` + `ui/tabs/studio.py` | **LIVE** |
| **21** | End-to-End Workflow Executor | `services/workflow_executor/` | **LIVE** |

---

## 3. Planned Agents (22+)

| Agent | Subsystem | Reserved key | Integrates via |
|---|---|---|---|
| **22** | Real Provider Integrations / Autonomous Executive prep | vendor `execute()` on ProviderRuntime adapters | `ProviderRuntime` only — no Orchestrator/Studio changes |

### Agent 20 — Studio UI & Creative Workspace (LIVE)

| Agent | Subsystem | Key | Integrates via |
|---|---|---|---|
| **20** | Studio UI & Creative Workspace | `studio` (service + UI) | `services/studio/` → **Workflow Executor** → Orchestrator; ProviderRuntime for health/cost |

Primary user interface: project workspace, creative prompt panel, pipeline
visualization, live previews, settings, provider status, output library,
executive dashboard. See `STUDIO_UI.md`.

### Agent 21 — End-to-End Workflow Executor (LIVE)

| Agent | Subsystem | Key | Integrates via |
|---|---|---|---|
| **21** | End-to-End Workflow Executor | `workflow_executor` (service) | `ProjectRun` + Orchestrator stages + job queue `workflow_run` |

Durable run controller: one prompt → `ProjectRun` with checkpoints, retries,
resume, and Studio UI status. Does not replace the Orchestrator or call
provider APIs directly. See `WORKFLOW_EXECUTOR.md`.

### Agent 19 — Provider Integration & Runtime (LIVE)

| Agent | Subsystem | Key | Integrates via |
|---|---|---|---|
| **19** | Provider Integration & Runtime | `provider_runtime` (service) | `ProviderRuntime.generate_*()` + job queue `longform_pipeline` |

Reserved for future BI: `business_intelligence` engine key.

### Agent 18 — AI Director (LIVE)

| Agent | Subsystem | Key | Integrates via |
|---|---|---|---|
| **18** | AI Director | `ai_director` | `director_package` slot + orchestration notes for Agents 12–17 |

---

## 3. Department Registry

| Department | Charter | Agents |
|---|---|---|
| Foundation | Contracts, orchestration, core intelligence | 1–5 |
| Production | Plans → finished, published media | 6–9 |
| Intelligence | Measure, forecast, learn, experiment | 10–13 |
| Media Generation | Assets, characters, universes, motion, edit | 14–17 |
| Direction | AI direction, executive creative strategy | **18** |
| Interface | Studio UI, creative workspace | **20** |
| Infrastructure | Provider integration, runtime, workflow execution | **19**, **21** |
| Providers / Executive (planned) | Real vendor APIs + autonomous operation | **22** |

---

## 4. Future Expansion Registry (22–30+)

| Future division | Plugs into |
|---|---|
| Brand Management | `brand_management` stage (stub wired) + channels |
| Community / Marketing / Sales / Support | stages after `publish`; hooks |
| Research / Knowledge Graph | `services/knowledge.py` + research providers |
| Translation / Localization / Education | SEO localization + new keys |
| Mobile / SaaS / API Platform | `Orchestrator` + serializable `PipelineResult` |
| Game / Interactive Media | additive ContentPackage slots |
| Infrastructure / Security / Compute | job queue + distributed backends |
| Provider Marketplace / Plugin Ecosystem | `providers/` + `register_stage()` |

**Rule:** claim (1) agent number here, (2) engine keys in `ENGINE_REGISTRY.md`,
(3) ownership in `AGENT_WORKFLOW.md`, (4) package slots in `DATA_CONTRACTS.md`
— all four before code.
