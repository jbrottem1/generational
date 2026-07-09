# Generational — Pipeline Specification (v9.0)

The complete flow of the AI Content Operating System. As of v9.0 every live
stage — through Render, Global Content Optimization, and Publishing — runs
inside **one integrated `run_full_pipeline()` call** which returns one
Production Report; future stages are wired into the orchestrator and skip
cleanly until their engines report ready. **This ordering is the contract**
— changing it requires Agent 1 review of `core/workflows.py` and
`services/orchestrator/stages.py`.

## Complete Flow

```
User Command
   ↓
Trend Discovery            LIVE      engines: trend_discovery
   ↓
Opportunity Ranking        LIVE      engines: opportunity_ranking
   ↓
Trend Forecasting          LIVE      Agent 11 — engines: trend_forecasting
   ↓                                 (quality control, forecasts,
   ↓                                  classifications, structured
   ↓                                  recommendations — see
   ↓                                  TREND_INTELLIGENCE.md)
Research + Ideation        LIVE      engines: research, ideation
   ↓
Psychology & Virality      LIVE      engines: psychology
   ↓
Script Generation          LIVE      engines: script_generation
   ↓
Attention Graph            LIVE      engines: attention_graph
   ↓
Visual Intelligence        LIVE      engines: visual_intelligence
   ↓
Voice & Audio              LIVE      engines: voice_audio
   ↓
Refinement                 LIVE      engines: ranking, script, critic,
   ↓                                 revision, citation, seo, threat_detection
Quality Gate               LIVE      engines: quality
   ↓
Media Production           LIVE      scene planning → narration → visual
   ↓                                 planning → assets → subtitles →
   ↓                                 timeline → render package → queue
Render Engine              LIVE      Agent 6 — engines: image, video, render
   ↓                                 (mock render: full plan + simulated
   ↓                                  output; real providers swap in later)
SEO Engine                 LIVE      Agent 8 — engines: seo_optimization
   ↓                                 (Global Content Optimization: titles,
   ↓                                  keywords, hashtags, descriptions,
   ↓                                  thumbnails, localization, windows,
   ↓                                  Optimization Report, PublishingPackage)
Publishing & Distribution  LIVE      Agent 7 — engines: scheduler, publishing
   ↓                                 (mock providers: platform packages,
   ↓                                  timezone-aware scheduling, retry queue;
   ↓                                  real platform APIs swap in later)
Analytics Collection       LIVE      Agent 9 — engines: analytics
   ↓                                 (structured analytics record per
   ↓                                  published item × platform; mock
   ↓                                  metrics provider; append-only store)
Learning Feedback          LIVE      Agent 9 — engines: learning
   ↓                                 (pattern mining, confidence-scored
   ↓                                  recommendations per engine, cumulative
   ↓                                  memory, experiments, reports)

Brand Strategy Update      FUTURE    Agent 10 — engines: brand_management
   ↓
(loops back into Trend Discovery weights for the next run)
```

## Rules

1. **One data model.** Every stage reads and writes the canonical
   `ContentPackage` / `ProductionPackage` (see `DATA_CONTRACTS.md`). During
   intelligence stages the shared `context` dict carries state; the packager
   folds it into packages at the end. Future stages receive packages.
2. **No stage calls another stage.** This is Architecture Directive #1 —
   Orchestrator-Only Communication (`ARCHITECTURE_DIRECTIVES.md`), enforced
   by `tests/test_architecture.py`. The orchestrator
   (`services/orchestrator/`) sequences everything; engines communicate only
   through context/package fields declared in their contracts.
3. **Statuses.** Every stage returns SUCCESS, WARNING, FAILED, or SKIPPED
   plus diagnostics (`StageReport`). A FAILED stage stops the pipeline
   gracefully; a not-ready future stage yields WARNING/SKIPPED and the run
   continues.
4. **Quality Gate is the safety boundary.** Nothing reaches Render or
   Publishing with `publish_ready=False` unless a human explicitly overrides.
5. **Additive evolution.** New stages are added via
   `register_stage()` / `WORKFLOWS`; new fields are appended to the
   ContentPackage; nothing existing is removed or renamed.
6. **Render stage.** Runs automatically after packaging inside
   `run_full_pipeline()` (and remains runnable on demand via
   `run_render_stage(context)`). It renders every idea in the context
   (mock render today), writes each `render_package`, and mirrors the
   results into `context["unified_packages"]` (status → `rendered`). With
   nothing to render it returns a safe SKIPPED summary — never a failure.
7. **SEO stage.** Runs automatically after render inside
   `run_full_pipeline()` (and on demand via `run_seo_stage(context)`). It
   optimizes every publish-ready item (preferring `unified_packages`,
   falling back to `ideas`), enriches each `seo_package` additively (base
   refinement metadata is never overwritten), and emits
   `seo_optimization_report` + `publishing_packages` (standardized
   PublishingPackage v1.0 per item — the handover to Agent 7; the
   ContentPackage `publishing_package` slot stays Agent 7's to write).
   With nothing to optimize it reports zero items — never a failure.
8. **Publish stage.** Runs automatically after seo inside
   `run_full_pipeline()` (and on demand via `run_publish_stage(context)`).
   The `scheduler` engine emits `publish_schedule` (timezone-aware slots
   from the Optimization Engine's ranked windows); the `publishing` engine
   builds one platform publish package per item × platform through the
   provider adapters, queues retry-capable PublishingJobs, executes due
   jobs when `publish_mode="immediate"` (the full pipeline defaults to
   `"scheduled"` — nothing posts without an explicit immediate request),
   writes each ContentPackage `publishing_package` slot (status →
   `scheduled` / `published`), and returns a standardized PublishingResult
   on `publishing_result`. With nothing to publish it reports SKIPPED —
   never a failure.
9. **Distribution degradation.** A FAILED render/seo/publish stage
   degrades the run to WARNING (errors preserved in the report) instead of
   discarding finished content; unavailable engines skip with warnings.
10. **Analytics stage.** Live (`run_analytics_stage(context)`). Runs after
    publishing — either on demand, or automatically after every full run
    once `enable_continuous_learning()` has attached the analytics
    `OrchestratorHook`. One structured analytics record per published item
    × platform (metrics via `AnalyticsProvider`, deterministic mock today),
    each ContentPackage `analytics_package` slot filled, records appended
    (deduplicated on `analytics_ref`) to the cumulative store. With nothing
    to measure it reports zero items — never a failure.
11. **Learning stage.** Live (`run_learning_stage(context)`). Mines the
    cumulative store for winners/losers across eleven attribution
    dimensions, emits `learning_report` + `learning_recommendations`
    (confidence-scored, routed per target engine), fills each
    `learning_metadata` slot, and grows the append-only long-term memory.
    Historical knowledge is never overwritten. With no history it reports
    `insufficient_data` — never a failure.
12. **One Production Report.** Every full run attaches one unified report
    (`services/orchestrator/report.py`) to
    `PipelineResult.production_report` /
    `context["production_report"]`: the eight production areas resolved
    to outcomes, per-stage diagnostics, an engine availability inventory,
    content/publishing summaries, and the full warning/error rollup.

## Stage → engine key → owner map

| Stage | Engine keys | Status | Owner |
|---|---|---|---|
| trend | trend_discovery, opportunity_ranking, trend_forecasting | live | Agent 1 · **Agent 11** (trend_forecasting) |
| research | research, ideation | live | Agent 1 |
| psychology | psychology | live | Agent 2 |
| script | script_generation | live | Agent 3 |
| attention | attention_graph | live | Agent 5 |
| visual | visual_intelligence | live | Agent 4 |
| audio | voice_audio | live | Agent 5 |
| refinement | ranking…threat_detection | live | shared |
| quality | quality | live | shared (gate) |
| production | scene_planning…publishing_queue | live | Agent 1 |
| render | image, video (+ `render` façade) | live (mock render) | **Agent 6** |
| seo | seo_optimization | live | **Agent 8** |
| publish | scheduler, publishing | live (mock providers) | **Agent 7** |
| analytics | analytics | live (mock metrics providers) | **Agent 9** |
| learning | learning | live | **Agent 9** |
| brand_management | brand_management | future | **Agent 10** |
