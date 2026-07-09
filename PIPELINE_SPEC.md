# Generational — Pipeline Specification (v9.9)

The complete flow of the AI Content Operating System. Every live stage runs
inside **one integrated `run_full_pipeline()` call**. Future stages are
wired and skip cleanly until their engines report ready. **This ordering
is the contract** — changing it requires Agent 1 review of
`core/workflows.py` and `services/orchestrator/stages.py`.

## Complete Flow

```
User Command
   ↓
Trend Discovery            LIVE      engines: trend_discovery
   ↓
Opportunity Ranking        LIVE      engines: opportunity_ranking
   ↓
Trend Forecasting          LIVE      Agent 11 — trend_forecasting
   ↓
Market Intelligence        LIVE      Agent 11 — market_intelligence
   ↓
Research + Ideation        LIVE      research, ideation
   ↓
Psychology & Virality      LIVE      psychology
   ↓
Script Generation          LIVE      script_generation
   ↓
Attention Graph            LIVE      attention_graph
   ↓
Visual Intelligence        LIVE      visual_intelligence
   ↓
Voice & Audio (planning)   LIVE      voice_audio
   ↓
Refinement                 LIVE      ranking → script → critic → revision →
   ↓                                 citation → seo → threat_detection
Quality Gate               LIVE      quality
   ↓
Media Production           LIVE      scene_planning → … → publishing_queue
   ↓
Packaging                  LIVE      ContentPackage assembly
   ↓
────────────────────────────────────────────────────────────
  DISTRIBUTION STAGES (services/orchestrator/stages.py)
────────────────────────────────────────────────────────────
   ↓
AI Director                LIVE      Agent 18 — ai_director
   ↓                                 → director_package
Creative Studio            LIVE      Agent 12 — creative_studio
   ↓                                 → creative_package
Character / Universe / IP  STUB      Agent 15 — character_universe
   ↓                                 → character_universe_package
Asset Generation           LIVE      Agent 14 — asset_generation
   ↓                                 → asset_package
Animation & Cinematics     STUB      Agent 16 — animation
   ↓                                 → animation_package
Render Engine              LIVE      Agent 6 — image, video (render façade)
   ↓                                 → render_package
Post-Production            LIVE      Agent 17 — post_production
   ↓                                 → post_production_package
SEO Optimization           LIVE      Agent 8 — seo_optimization
   ↓                                 → seo_package (enriched)
Optimization Laboratory    STUB      Agent 13 — optimization_lab
   ↓                                 → optimization_package
Publishing & Distribution  LIVE      Agent 7 — scheduler, publishing
   ↓                                 → publishing_package
Analytics Collection       LIVE      Agent 10 — analytics
   ↓
Learning Feedback          LIVE      Agent 10 — learning
   ↓
Brand Strategy Update      STUB      brand_management
   ↓
(feedback loop → Trend Discovery / Market Intelligence weights)
```

Voice *planning* stays in the intelligence pipeline. Real TTS (`voice`
stub) graduates later as an audio-stage upgrade — not a distribution stage.

## Rules

1. **One data model.** Every stage reads/writes the canonical
   `ContentPackage` / `ProductionPackage` (`DATA_CONTRACTS.md`).
2. **No stage calls another stage.** Architecture Directive #1 —
   orchestrator-only communication (`ARCHITECTURE_DIRECTIVES.md`).
3. **Statuses.** SUCCESS / WARNING / FAILED / SKIPPED + diagnostics.
   FAILED stops gracefully; not-ready engines yield WARNING/SKIPPED.
4. **Quality Gate is the safety boundary.** Distribution stages only
   receive packages that passed (or were explicitly overridden).
5. **Additive evolution.** New stages via `register_stage()` /
   `DISTRIBUTION_STAGES`; new fields append to ContentPackage only.

## Stage → engine key → owner map

| Stage | Engine keys | Status | Owner |
|---|---|---|---|
| trend | trend_discovery, opportunity_ranking, trend_forecasting, market_intelligence | live | Agents 1, 11 |
| research | research, ideation | live | Agent 1 |
| psychology | psychology | live | Agent 2 |
| script | script_generation | live | Agent 3 |
| attention | attention_graph | live | Agent 2 |
| visual | visual_intelligence | live | Agent 4 |
| audio | voice_audio | live | Agent 5 |
| refinement | ranking…threat_detection | live | shared |
| quality | quality | live | shared (gate) |
| production | scene_planning…publishing_queue | live | Agent 9 |
| ai_director | ai_director | live | **Agent 18** |
| creative | creative_studio | live | **Agent 12** |
| character_universe | character_universe | stub | **Agent 15** |
| asset_generation | asset_generation | live | **Agent 14** |
| animation | animation | stub | **Agent 16** |
| render | image, video | live | **Agent 6** |
| post_production | post_production | live | **Agent 17** |
| seo | seo_optimization | live | **Agent 8** |
| optimization | optimization_lab | stub | **Agent 13** |
| publish | scheduler, publishing | live | **Agent 7** |
| analytics | analytics | live | **Agent 10** |
| learning | learning | live | **Agent 10** |
| brand_management | brand_management | stub | Brand OS |
| executive | autonomous_executive | live | **Agent 24** — manual/hook only |

---

## Provider Runtime Layer (Agent 19) + Connectors (Agent 22)

`services/provider_runtime/` is the **single gateway** for external AI and
platform publishing. Agent 22 production connectors implement real HTTP
`execute()` paths for OpenAI, Anthropic, Gemini, OpenAI Images, Flux,
Ideogram, Stability, Veo, Runway, Kling, Pika, Luma, ElevenLabs, OpenAI TTS,
and YouTube/TikTok/Instagram/Facebook/X. Selection, fallback, retries, rate
limits, caching, cost, and health stay inside ProviderRuntime. See
`PROVIDER_INTEGRATION.md` and `PROVIDER_CONNECTORS.md`.

---

## Studio UI Layer (Agent 20)

The Creative Studio (`ui/tabs/studio.py`, `services/studio/`) is the primary
user interface. It does not run pipeline stages directly — it calls:

- `services/studio/run_studio_production()` → **Workflow Executor** → Orchestrator
- `services/studio/get_provider_dashboard()` → `ProviderRuntime`
- `services/studio/submit_longform_job()` → job queue + `RuntimeExecutionEngine`

Pipeline visualization maps orchestrator `StageReport` objects to the 12-stage
Studio view. See `STUDIO_UI.md`.

## Workflow Executor Layer (Agent 21)

One-prompt production runs are managed by
`services/workflow_executor/` (`WorkflowExecutor.execute()`). The executor
creates a durable `ProjectRun`, resolves production type/template, drives
Orchestrator stages in order, checkpoints after each stage, retries/degrades
failures, and exposes Studio UI status (`get_status`). It does not redefine
stage order — it filters/annotates the canonical plan above. See
`WORKFLOW_EXECUTOR.md`.
