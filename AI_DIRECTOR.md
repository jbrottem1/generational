# AI Director — Agent 18 (Executive Creative Decision Engine)

> **V5.0 Studio Director:** see [`AI_STUDIO_DIRECTOR.md`](AI_STUDIO_DIRECTOR.md)
> for the Production Blueprint, style library, competitor analysis, and
> early-pipeline wiring. This document covers the `DirectorPackage` contract.

The AI Director is Generational's executive creative department. It receives
ideas and intelligence from every upstream engine and determines the optimal
production strategy **before assets are generated**. It orchestrates Agents
12–17 by emitting structured `DirectorPackage` briefs — it never generates
media or duplicates downstream logic.

## Pipeline position

```
Audience Intelligence → AI Studio Director (Production Blueprint)
  → Script → Visuals → … → Studio Render → Optimization Lab → QA

Legacy distribution path:
Packaging → AI Director → Creative Studio → Character Universe →
Asset Generation → Animation → Render → Post-Production → …
```

Engine key: `ai_director`  
Executive stage: `direction`  
Orchestrator stage: `ai_director`  
Slot written: `director_package` (includes `production_blueprint` in v5)  
Context keys: `ai_director_summary`, `ai_director_packages`
Version: `5.0.0`

```python
from services.orchestrator import Orchestrator

orch = Orchestrator()
report = orch.run_ai_director_stage(context)
# context["ai_director_packages"] — one per item
# context["unified_packages"][i]["director_package"]
```

## Three "Director" concepts (do not conflate)

| Concept | Agent | Scope |
|---|---|---|
| **AI Director** (this doc) | 18 | Cross-stage executive strategy — format, platform, style, pacing, orchestration |
| **Creative Director** | 12 | Pre-production blueprint inside `creative_package` — storyboard execution |
| **Cinematic AI Director** | 4 | Intelligence-phase visual psychology — retention-optimized shots on candidates |

The AI Director sets strategy; Creative Studio executes visual design; Visual
Intelligence scores retention during ideation. Each owns its slot — the
Director reads upstream packages but **never mutates** them.

## Decision architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Upstream intelligence                      │
│  psychology · script · visual · audio · trend · market ·     │
│  analytics · creative (optional, for reconciliation)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Configurable policies (policies.py)               │
│  format weights · platform defaults · quality tiers ·        │
│  learning feedback weights · graceful-degradation fallbacks    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Decision engine (decisions.py)                    │
│  format · orientation · platforms · strategy · style ·         │
│  animation · camera · pacing · shots · characters · music ·    │
│  narration · editing · optimization hints · runtime · QC       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              Quality validation (quality.py)                   │
│  conflict detection · graceful degradation · provider checks   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    DirectorPackage
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   Creative Studio   Asset Generation   Post-Production
   (Agent 12)         (Agent 14)         (Agent 17)
```

Deterministic by design: identical input → identical direction, so tests,
diagnostics, and the learning loop can reason about creative decisions.

## DirectorPackage

Field tuple: `DIRECTOR_PACKAGE_FIELDS` in `services/ai_director/models.py`.

| Field | Purpose |
|---|---|
| `production_strategy` | Format, orientation, content class, emotional intensity, caption/thumbnail/publishing strategy |
| `target_platforms` | Platform targets with aspect ratio, duration limits, caption requirements |
| `creative_style` | Tone, mood, color/typography direction |
| `visual_style` | Lighting, texture, reference mood |
| `animation_style` | Technique (2D/3D/motion graphics), motion language, transitions |
| `camera_plan` | Camera grammar, dominant shot types, movement profile |
| `pacing` | Tempo, scene targets, cuts per minute, retention curve |
| `shot_plan` | Beat structure, key shots — high-level, not scene storyboard |
| `character_plan` | Cast strategy, selected characters, consistency rules |
| `music_plan` | Direction, tempo range, instrumentation, beat sync |
| `narration_plan` | Voice selection, delivery style, pacing WPM |
| `editing_plan` | Edit style, transitions, color grade, caption style |
| `optimization_hints` | Trend/market/analytics hints for downstream optimization |
| `asset_requirements` | High-level asset categories — Agent 14 expands into generation specs |
| `expected_runtime` | Target/min/max seconds, chapter marker flag |
| `quality_targets` | Production tier, minimum score, QC gates |
| `production_priority` | urgent / high / standard / low |
| `orchestration_notes` | Per-agent guidance for Agents 12–17 |
| `upstream_alignment` | Packages consumed, conflicts detected/resolved, degradations |
| `validation` | QC status, confidence, warnings, blockers |

## Orchestration flow

1. **Collect items** from `unified_packages` (fallback: `ideas`, `candidates`).
2. **Read upstream** — script, visual, audio, psychology, trend, market, analytics.
3. **Apply policies** — configurable weights + optional learning feedback.
4. **Decide** — format, platform, style, pacing, camera, characters, music, editing.
5. **Validate** — detect conflicts with existing packages; cap impossible durations.
6. **Degrade gracefully** — missing upstream → policy fallbacks, never crash.
7. **Write** — `director_package` slot + context summary keys only.

Downstream agents **should read** `director_package` when present:

| Agent | Reads | Uses |
|---|---|---|
| 12 Creative Studio | `production_strategy`, `visual_style`, `pacing` | Blueprint alignment |
| 14 Asset Generation | `asset_requirements`, `quality_targets` | Generation scope |
| 15 Character Universe | `character_plan` | Cast selection |
| 16 Animation | `animation_style`, `camera_plan` | Motion direction |
| 6 Render | `expected_runtime`, `camera_plan` | Render parameters |
| 17 Post-Production | `editing_plan`, `music_plan`, `narration_plan` | Edit/mix direction |

## Configurable policies

```python
from services.ai_director import configure_policies, apply_learning_feedback, get_policies

# Override platform defaults
configure_policies({"default_platforms": ["tiktok"]})

# Future RL hook — analytics feedback adjusts weights
apply_learning_feedback({"format": {"short_form": 0.3}, "platform": {"tiktok": 0.2}})

policies = get_policies()
```

Policy bundle is versioned (`DEFAULT_POLICY_VERSION`) and recorded in
`director_diagnostics.policy_version` for attribution.

## Extension guide

### Add a new format

1. Add keyword signals to `_FORMAT_SIGNALS` in `decisions.py`.
2. Add a weight entry in `DEFAULT_POLICIES["format_weights"]`.
3. Add orientation mapping in `_ORIENTATION_BY_FORMAT` if needed.
4. Extend `build_production_strategy()` for format-specific defaults.

### Add a new platform

1. Add entries to `platform_orientation` and `platform_max_duration` in policies.
2. No engine changes required.

### Wire reinforcement learning

1. Analytics/Learning emits feedback dicts `{dimension: {choice: delta}}`.
2. Call `apply_learning_feedback(feedback)` before directing.
3. Decision functions call `learning_boost(dimension, choice)` — already wired.

### Add a new decision dimension

1. Append field to `DIRECTOR_PACKAGE_FIELDS` (additive only).
2. Add builder function in `decisions.py`.
3. Wire into `build_director_package()` in `package.py`.
4. Add validation rules in `quality.py` if conflicts possible.
5. Update tests and this document.

## File map

| File | Role |
|---|---|
| `engines/ai_director.py` | ContractEngine façade |
| `services/ai_director/models.py` | Field tuples, status enums |
| `services/ai_director/policies.py` | Configurable decision policies + RL hook |
| `services/ai_director/decisions.py` | All creative decision logic |
| `services/ai_director/quality.py` | Validation, conflicts, degradation |
| `services/ai_director/package.py` | DirectorPackage assembly |
| `tests/test_ai_director.py` | Service-layer tests |
| `tests/test_ai_director_engine.py` | Engine contract + integration tests |

## Failure policy

- Empty context → `"no_items"` summary, empty packages list.
- Per-item exception → incomplete package with blocker diagnostic.
- Missing upstream packages → degraded direction with policy fallbacks.
- Conflicting upstream choices → detected, resolved where possible, warned otherwise.
- **Never crashes the pipeline.**
