# Generational — Pipeline Specification (v8.1)

The complete future flow of the AI Content Operating System. Live stages run
today; future stages are wired into the orchestrator and skip cleanly until
their engines report ready. **This ordering is the contract** — changing it
requires Agent 1 review of `core/workflows.py` and
`services/orchestrator/stages.py`.

## Complete Flow

```
User Command
   ↓
Trend Discovery            LIVE      engines: trend_discovery
   ↓
Opportunity Ranking        LIVE      engines: opportunity_ranking
   ↓
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
Render Engine              FUTURE    Agent 6 — engines: image, video
   ↓
SEO Engine                 FUTURE    Agent 8 — engines: seo_optimization
   ↓
Publishing Scheduler       FUTURE    Agent 7 — engines: scheduler, publishing
   ↓
Analytics Collection       FUTURE    Agent 9 — engines: analytics
   ↓
Learning Feedback          FUTURE    Agent 9 — engines: learning
   ↓
Brand Strategy Update      FUTURE    Agent 10 — engines: brand_management
   ↓
(loops back into Trend Discovery weights for the next run)
```

## Rules

1. **One data model.** Every stage reads and writes the canonical
   `ContentPackage` / `ProductionPackage` (see `DATA_CONTRACTS.md`). During
   intelligence stages the shared `context` dict carries state; the packager
   folds it into packages at the end. Future stages receive packages.
2. **No stage calls another stage.** The orchestrator
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

## Stage → engine key → owner map

| Stage | Engine keys | Status | Owner |
|---|---|---|---|
| trend | trend_discovery, opportunity_ranking | live | Agent 1 |
| research | research, ideation | live | Agent 1 |
| psychology | psychology | live | Agent 2 |
| script | script_generation | live | Agent 3 |
| attention | attention_graph | live | Agent 5 |
| visual | visual_intelligence | live | Agent 4 |
| audio | voice_audio | live | Agent 5 |
| refinement | ranking…threat_detection | live | shared |
| quality | quality | live | shared (gate) |
| production | scene_planning…publishing_queue | live | Agent 1 |
| render | image, video | future | **Agent 6** |
| seo | seo_optimization | future | **Agent 8** |
| publish | scheduler, publishing | future | **Agent 7** |
| analytics | analytics | future | **Agent 9** |
| learning | learning | future | **Agent 9** |
| brand_management | brand_management | future | **Agent 10** |
