# Generational Facial Performance & Environment Construction Standard

**Status:** Permanent studio standard  
**Architecture:** Frozen — no new renderer, no pipeline redesign  
**Services:** `services/character_performance/` · `services/environment_department/` · `services/shot_assembly/`  
**Related:** [Character Performance Engine](CHARACTER_PERFORMANCE_ENGINE.md) · [Character Rig Studio](CHARACTER_RIG_STUDIO.md) · [Stage & World Simulation](STAGE_WORLD_SIMULATION.md) · [Physics & Interaction](PHYSICS_INTERACTION_ENGINE.md) · [Cinematic Direction Studio](CINEMATIC_DIRECTION_STUDIO.md) · [Animation Execution Layer](ANIMATION_EXECUTION_LAYER.md)  
**CLI:** `scripts/facial_env_standard.py`

---

## Hard rule

JSON plans, test scores, and declared controls are **not** proof of quality.

The final MP4 must be inspected for:

- gaze direction and focus  
- facial emotion readability  
- blink naturalism  
- lip sync to real narration  
- world depth (foreground / midground / background)  
- material detail  
- weather response  
- lighting coherence  
- environmental continuity  

Motion alone is not realism.

---

## Part I — Facial Performance

Pipeline:

```
Scene Intent → Emotion → Attention → Facial Performance Plan
→ Eye/Head Coordination → Expression Blending → Speech/Visemes
→ Micro-Expressions → Rendered Performance Validation
```

Modules: emotion · attention · gaze · blinking · expressions · speech · face_rig · performance_plan · validation

Every speaking shot soft-attaches a `facial_performance_plan` (via Character & World Studio).

Canonical face rig: `FACE_RIG_PROFILE.json` (DOCTOR_001 and recurring hosts).

---

## Part II — Environment Construction

Pipeline:

```
Story Requirement → Environment Type → Layout → FG/MG/BG
→ Architecture → Materials → Vegetation → Props
→ Weather/Atmosphere → Lighting → Ambient Motion
→ Continuity Validation → Rendered Environment Validation
```

Modules: definition · layout · architecture · materials · vegetation · weather · atmosphere · lighting · set_dressing · continuity · package · validation

Every shot soft-attaches an `environment_package` + `complete_shot` contract.

Recurring environments (e.g. GMRI Lab A) are never regenerated from scratch.

---

## Complete shot input

`services/shot_assembly` builds:

```json
{
  "shot_id": "...",
  "character_performance": { "...": "..." },
  "environment": { "...": "..." },
  "camera": { "...": "..." },
  "validation": {
    "rendered_facial_inspection": "PENDING...",
    "rendered_environment_inspection": "PENDING..."
  }
}
```

---

## Final standard

Not: “The character moved inside a background.”

Yes: “A believable character delivered an emotionally readable performance inside a coherent, living world.”
