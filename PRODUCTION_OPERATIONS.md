# Production Operations Layer

The command center for the Generational AI Studio.

**Does not redesign engines.** It orchestrates, monitors, recovers, validates, reports, and stores complete productions.

## Input → Output

```
INPUT:  topic, platform, style, duration, narrator, voice, quality target, constraints
OUTPUT: monitored production → export package → Production Report → history
```

Example:

```python
from services.production_operations import run_studio_ops

result = run_studio_ops(
    topic="Why Octopuses Have Three Hearts",
    platform="youtube_shorts",
    length_sec=45,
    style="educational",
    narrator="professor",
    voice="default",
    quality_target=98,
)
```

## 16 monitored stages

1. Research Engine (`research`, `ideation`)  
2. Psychology Engine (`psychology`)  
3. AI Studio Director (`ai_director`)  
4. Script Generator (`script_generation`)  
5. Scene Builder (`visual_intelligence`, `scene_planning`, `visual_planning`)  
6. Media Collection (`evidence_intelligence`, `image`, `asset_manager`)  
7. Animation / Motion Graphics (`cinematography`, `animation`)  
8. Voice Generation (`voice_audio`, `narration`, `voice`)  
9. Music & Sound Design (director / audio package apply)  
10. Captions (`subtitle`)  
11. Rendering (`timeline`, `render_package`, `studio_render`, `video`)  
12. Viewer Retention Analysis (`viewer_retention`)  
13. Optimization Lab (`optimization_lab`)  
14. Quality Assurance (`quality`, `production_qa`)  
15. SEO Package (`seo`, `seo_optimization`)  
16. Export (EO `package_export_artifacts` + `verified_export`)

Every stage records: status, start/end, duration, warnings, errors, retries, quality score, output files.

## Failure policy

**Never terminate production.** On engine failure:

1. Retry (per-stage `max_retries`)  
2. Repair / fallback (skip unavailable engines)  
3. Continue  
4. Escalate only via warnings / degraded health in the dashboard  

## Live dashboard

`data/productions/_ops/PRODUCTION_DASHBOARD.json`

Shows: current stage, progress %, elapsed time, ETA, current agent, files, quality scores, warnings, retry count, pipeline health.

Also nested under Studio `get_executive_dashboard()["production_operations"]`.

Per-run status: `data/productions/_ops/{id}/PRODUCTION_OPS_STATUS.json`

## Post-export validation

Checks (best-effort when MP4 exists):

- Video exists  
- Duration  
- Audio present with video  
- Captions/metadata/SEO/thumbnail artifacts  
- Corrupt / empty media (via `assess_export_technical_validity`)  
- Resolution / frame rate  

## Production Report

`PRODUCTION_REPORT.json` + `.md` with overall quality, hook/narration/visual/audio/caption scores, educational accuracy, retention/CTR/completion predictions, shareability, platform readiness, final recommendation.

## History + Queue

- History: `PRODUCTION_HISTORY.json` + learning `ProductionMemory`  
- Queue: façade over `core.jobs` — single, batch, scheduled, priority, failed-job recovery, resume  

```python
from services.production_operations import enqueue_production, enqueue_batch, recover_failed_jobs

enqueue_production(topic="...", platform="tiktok", priority=5)
enqueue_batch([{...}, {...}])
recover_failed_jobs()
```

## Platforms

Future-proofed aliases: YouTube Shorts, TikTok, Instagram Reels, Facebook Reels, X, LinkedIn, long-form, podcast, course, documentary.

## Entry points

| Surface | How |
|---|---|
| Python API | `run_studio_ops(...)` |
| Engine | `production_operations` |
| Workflow | `studio_ops` → `["production_operations"]` |
| Queue | `enqueue_production` / `enqueue_batch` |

## Related

- Integration map: `PIPELINE.md`  
- Executive studio: `EXECUTIVE_ORCHESTRATOR.md`  
- Director: `AI_STUDIO_DIRECTOR.md`  
