# Visual Education Engine V2 — Production Rules Lock

**Date:** 2026-07-12  
**Mission:** Permanent fix for missing real photographs + random annotations  
**Status:** COMPLETE — engine-level rules; QC hard-fails on violation

---

## Permanent production rules

### 1. Real photographs are mandatory

Visual priority ladder (always):

1. Authentic photographs (NASA, satellite, wildlife, fossils, lab, etc.)
2. Authentic scientific diagrams
3. Public-domain educational illustrations
4. Museum-quality reconstructions
5. AI-generated imagery **only** when no suitable real-world visual exists

AI supplements authentic material — it must never replace it when a photo exists.

### 2. Every annotation must teach

- Semantic **target** required (`keyword:…`, `panel:…`, `shell:N`)
- **narration_cue** (teaching purpose) required
- Fade in → teach → fade out
- Max one arrow, one circle, one highlight, one label at a time
- No decorative circles, random arrows, or scribbles
- Unsupported kinds are never drawn

### 3. Text quality (unchanged, reinforced)

- No overlapping / duplicated / clipped labels
- Presenter never covers content
- Readability ≥ 95

---

## Engine upgrades

| Module | Change |
|--------|--------|
| `services/quality/visual_priority.py` | Priority ladder + `select_visual_source()` |
| `services/knowledge_atlas/search.py` | Photos rank above AI/diagrams |
| `services/knowledge_atlas/evaluator.py` | Priority boost in asset score |
| `services/animation/annotation_engine.py` | Purpose gate + per-family clutter cap |
| `services/quality/visual_education_qc.py` | Authentic-media + annotation policy QC |
| `services/quality/visual_layout_qc.py` | Merges education policy into demo QC |
| `services/animation/foundation_gate.py` | Education policy hard-fails block export |
| `services/generational_os/final_status.py` | New hard-fail taxonomy keys |
| `services/reality/annotate.py` | Decorative marks skipped without purpose |
| `services/animation/seasons_demos.py` | NASA Earth + real season photos (not drawings) |
| `services/reality/planner.py` | `SEASONS_001_PANELS` authentic evidence |

---

## New QC hard-fails (export blocked)

- `no_reality_images`
- `real_photos_available_but_unused`
- `ai_imagery_used_when_real_photos_available`
- `synthetic_visuals_preferred_over_authentic`
- `annotations_missing_teaching_purpose`
- `annotations_missing_semantic_targets`
- `annotation_clutter_*` (identical double-booked marks)

---

## Validation

| Check | Result |
|-------|--------|
| `tests/test_visual_engine.py` | **15 passed** |
| Turtle visual QC | **100/100** |
| Seasons visual QC | **97/100** (passed) |
| Seasons reality images | NASA Apollo 17 + 4 seasonal photographs |

---

## Eye-path storytelling (enforced)

Camera / presenter gesture → arrow → circle → narration → remove annotation → next beat.

These standards apply to every future Generational video.
