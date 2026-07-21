# Production Pipeline Integration

Connects every completed production agent into one executable workflow.

This layer does **not** redesign architecture or rewrite agents. It orders existing engines, standardizes handoffs, logs every step, and writes live `PIPELINE_STATUS.json`.

## Workflow

```
Research
  → Psychology
  → Studio Director
  → Script Generator
  → Scene Builder
  → Media Generation
  → Voice Generation
  → Video Assembly
  → Quality Control
  → Export
```

## Stage → Engine map

| Stage | Existing engine keys | Primary context inputs | Primary context outputs |
|---|---|---|---|
| Research | `research`, `ideation` | `command` | `research`, `niche`, `subject`, `candidates` |
| Psychology | `psychology` | `candidates` | `candidates` (+ scores), `psychology_summary` |
| Studio Director | `ai_director` | `candidates` / `unified_packages` | `director_package`, `production_blueprint`, `ai_director_summary` |
| Script Generator | `script_generation` | `candidates` | `candidates` (+ scripts), `script_generation_summary` |
| Scene Builder | `visual_intelligence`, `scene_planning`, `visual_planning` | `candidates`, `approved_content` | `production_packages`, visual packages |
| Media Generation | `image`, `asset_manager` | `ideas`, `production_packages` | assets / `render_assets_summary` |
| Voice Generation | `voice_audio`, `narration`, `voice` | `candidates`, `production_packages` | `audio_package`, voice tracks |
| Video Assembly | `subtitle`, `timeline`, `render_package`, `studio_render`, `video` | `production_packages`, `ideas` | render / studio packages |
| Quality Control | `quality`, `production_qa` | `selected_ideas`, `candidates` | `quality_summary`, `pqa_summary` |
| Export | `optimization_lab` | `candidates` | `optimization_summary`, export prep |

Ideation is grouped under Research because Psychology requires a candidate pool (existing OS pattern). Bridges seed a candidate from `subject`/`command` if ideation is skipped.

## How to run

```python
from services.production_pipeline import run_production_pipeline, verify_agents

verify_agents()  # I/O + readiness check

result = run_production_pipeline(
    "Explain how popsicles are made in 60 seconds",
    platform="youtube_shorts",
)
# result["status_path"] → data/productions/{id}/PIPELINE_STATUS.json
```

Engine entry (registry key `production_pipeline`):

```python
from engines import registry
registry.get_engine("production_pipeline").run({"command": "..."})
```

Named workflow (flattened engines, no status writer — use the engine for status):

```python
from core.workflows import WorkflowEngine
WorkflowEngine().execute("production_pipeline", {"command": "..."})
```

## Data contracts

Handoffs stay on the shared context dict (see `DATA_CONTRACTS.md`). The integration layer only:

1. Declares expected inputs/outputs per stage (`services/production_pipeline/stages.py`)
2. Applies **additive bridges** before each stage (`bridges.py`):
   - ensure candidates after research
   - sync `candidates` ↔ `ideas` ↔ `selected_ideas` ↔ `unified_packages`
   - build `approved_content` for scene planning
   - prepare media inputs for image/voice/assembly
3. Never strips `research`, `script_package`, `director_package`, or other package slots

## Structured logging

Every run emits `log_event` records:

- `production_pipeline.started`
- `production_pipeline.stage_started`
- `production_pipeline.stage_finished` (success, elapsed_ms, validation_score)
- `production_pipeline.stage_skipped`
- `production_pipeline.finished`

Plus each underlying engine’s own events via `WorkflowEngine` (`workflow.step_*`).

## PIPELINE_STATUS.json

Written continuously to:

```
data/productions/{production_id}/PIPELINE_STATUS.json
```

Fields:

| Field | Meaning |
|---|---|
| `current_stage` | Stage key running or last completed |
| `elapsed_ms` | Total and per-stage timings |
| `overall_status` / `success` | Run outcome |
| `output_location` | Production folder path |
| `validation_score` | Roll-up completeness score (0–100) |
| `stages[]` | Per-stage status, success/failure, output location, validation score, engine results |

## Backward compatibility

- Existing workflows (`intelligence`, `full_content`, `media_production`, `executive`) are unchanged in behavior beyond additive registration
- Agents are invoked through the same `Engine.run(context)` contract
- New keys are additive: `production_pipeline_summary`, `pipeline_status`, `production_pipeline_result`

## Validation

```bash
python -m pytest tests/test_production_pipeline_integration.py -q
python scripts/verify_production_pipeline_e2e.py
```

## Package layout

```
services/production_pipeline/
  stages.py         # stage map + contracts
  bridges.py        # context adapters
  status.py         # PIPELINE_STATUS.json
  orchestrator.py   # run_production_pipeline / verify_agents
engines/production_pipeline.py
PIPELINE.md         # this file
```
