# Generational — Agent Registry (v9.6)

The canonical roster of development agents, the department each belongs to,
what they own, and the expansion slots reserved for the future. Maintained
by Agent 1; a new agent starts by adding its row here **before** writing
code (see `INTEGRATION_CHECKLIST.md`).

Companion views: `ENGINE_REGISTRY.md` (engine keys), `SYSTEM_DEPENDENCY_MAP.md`
(who depends on whom), `AGENT_WORKFLOW.md` (merge safety + file ownership).

---

## 1. Active & Completed Agents

### Foundation Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **1** | Master Architecture & Orchestrator | — (owns `services/orchestrator/`, registry, contracts, `trend_discovery`, `opportunity_ranking`) | active, permanent |
| **2** | Psychology & Behavioral Intelligence | `psychology`, `attention_graph`, `threat_detection` | shipped |
| **3** | Script Generation | `script_generation`, `script`, `critic`, `revision` | shipped |
| **4** | Visual Intelligence | `visual_intelligence` | shipped |
| **5** | Voice & Audio | `voice_audio` (+ planned `voice` TTS) | shipped (planning) |

### Production Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **6** | Render Engine | `render`, `image`, `video` | shipped (mock renderer, provider-swappable) |
| **7** | Publishing & Distribution | `publishing`, `scheduler`, `publishing_queue` | shipped (mock platforms) |
| **8** | Global Content Optimization | `seo_optimization` | shipped |
| **9** | Production Pipeline | media-production chain (`scene_planning` … `render_package`) + `services/pipeline.py` | shipped |

### Intelligence Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **10** | Analytics & Continuous Learning | `analytics`, `learning` | shipped (simulated metrics) |
| **11** | Market Intelligence & Forecasting | `market_intelligence`, `trend_forecasting` | shipped |
| **12** | Creative Studio | `creative_studio` | built on `feature/creative-studio` — merge + register pending |
| **13** | Optimization Laboratory | reserved key: `optimization_lab` | planned |

### Media Generation Department

| Agent | Subsystem | Engine keys | Status |
|---|---|---|---|
| **14** | Universal Asset Generation | key: `asset_generation` (`services/asset_generation/` + `providers/asset_generation/`) | **live** |
| **15** | Character, Universe & IP | reserved key: `ip_management` | planned |

---

## 2. Planned Agents (16-20)

| Agent | Subsystem | Reserved engine key | Integrates via |
|---|---|---|---|
| **16** | Animation & Cinematics | `animation` | `creative_package` → animated assets in `render_package` |
| **17** | Video Editing & Post Production | `post_production` | `render_package` enrichment after `render` stage |
| **18** | AI Director | `ai_director` | cross-stage creative direction notes in `creative_package` / diagnostics |
| **19** | Business Intelligence & Monetization | `business_intelligence` | `analytics_package` → revenue/ROI fields (additive) |
| **20** | Autonomous Executive | `autonomous_executive` | `OrchestratorHook` + job queue (`ORCHESTRATOR_JOB_TYPE`) — the first agent that *initiates* runs |

Reserved keys are names only — do not register stubs until the agent is
scheduled (Agent 1 adds the `FutureEngine` stub in `engines/future_stubs.py`
when work begins).

---

## 3. Department Registry

Departments are organizational, not architectural: every department's
engines integrate identically (ContractEngine → registry → orchestrator
stage → ContentPackage slot). Adding a department requires **zero**
platform changes.

| Department | Charter | Active agents |
|---|---|---|
| Foundation | Contracts, orchestration, core intelligence pipeline | 1-5 |
| Production | Plans → finished, published media | 6-9 |
| Intelligence | Measure, forecast, learn, decide | 10-13 |
| Media Generation | Assets, characters, universes, IP | 14-15 |
| Direction (planned) | Animation, editing, AI direction | 16-18 |
| Executive (planned) | Monetization, autonomous operation | 19-20 |

---

## 4. Future Expansion Registry

Divisions under consideration — each maps onto the same integration
pattern. Column three is the architectural seam it will plug into; none
require redesign.

| Future division | Plugs into |
|---|---|
| Brand Management | `brand_management` stage (stub already wired) + `services/channels.py` |
| Community Management | new engine key + `analytics_package` (comments/engagement) |
| Marketing / Sales / Customer Support | new stages after `publish`; `publishing_package` + hooks |
| Research / Knowledge Graph | `services/knowledge.py` + research providers |
| Mobile Apps / SaaS / API Platform | consume `Orchestrator` + `PipelineResult.to_dict()` (already serializable) |
| Game Development / Interactive Media | new package slots (additive fields on ContentPackage) |
| Education / Translation / Localization | extend `seo_optimization` localization + new engine keys |
| Infrastructure / Security / Compute Scheduling | job queue + future distributed orchestrator backends |
| Provider Marketplace / Plugin Ecosystem | `providers/` interfaces + `register_stage()` / registry replacement |

**Rule:** a new division claims (1) an agent number here, (2) engine keys in
`ENGINE_REGISTRY.md`, (3) an ownership row in `AGENT_WORKFLOW.md`, and
(4) any new ContentPackage slots in `DATA_CONTRACTS.md` — all four before code.
