# Studio Character — DOCTOR_001 (The Doctor)

**Status:** Permanent Generational Studio Character  
**Character ID:** `DOCTOR_001`  
**Legacy alias:** `CHAR-0001`  
**Version:** `1.1.0`  
**Path:** `data/studio_assets/DOCTOR_001/`  
**Service:** `services/studio_assets/doctor_001/`  
**CLI:** `scripts/studio_character_doctor_001.py`

This is **not** an episode character sheet.

This is the canonical medical educator for the entire Generational Universe — a complete reusable studio asset package so The Doctor remains visually identical across every future video.

## Master Concept Art (permanent visual identity)

Path: `MASTER_CONCEPT_ART/`

Official 20-plate concept library (hero, orthographic, expressions, poses, materials, palette, reference sheet).  
Recognition keys: hero portrait + official character reference sheet.

See `MASTER_CONCEPT_ART/MASTER_CONCEPT_BIBLE.md`.

Architecture remains frozen (no new renderer / no pipeline redesign).

---

## Package contents

| Library / Spec | Location |
|----------------|----------|
| Orthographic front / side / back / 3⁄4 | `ORTHOGRAPHIC/` |
| Facial topology | `FACIAL_TOPOLOGY.json` |
| Expression library (50+) | `EXPRESSIONS/` |
| Eye / blink / breath models | `EYE_MOVEMENT_MODEL.json` · `BLINKING_MODEL.json` · `BREATHING_PROFILE.json` |
| Personality / emotion | `PERSONALITY_PROFILE.json` · `EMOTIONAL_PROFILE.json` |
| Gestures / hands | `GESTURE_LIBRARY.json` · `HAND_POSES/` |
| Walk / run / idle / talk / teach / listen / reactions | `ANIMATION/` |
| Clothing / materials / palette / silhouette | `CLOTHING_SIMULATION.json` · `MATERIALS.json` · `COLOR_PALETTE.json` · `SILHOUETTE_RULES.json` |
| Lighting / close-up / full-body / scale refs | `LIGHTING_REFERENCE/` · `CLOSEUP_REFERENCE/` · `FULLBODY_REFERENCE/` · `SCALE_REFERENCE/` |
| Proportions / skeleton / muscle / skin / hair | `PROPORTIONS.json` · `SKELETAL_PROPORTIONS.json` · `MUSCLE_DEFINITION.json` · `SKIN_MATERIAL.json` · `HAIR_PROFILE.json` |
| Rig + animation constraints | `RIG_SPECIFICATION.json` · `ANIMATION_CONSTRAINTS.json` |
| Continuity / voice / catch phrases / bio | `CONTINUITY_RULES.md` · `VOICE_IDENTITY.json` · `CATCH_PHRASES.json` · `BIOGRAPHY.md` |
| Strengths / flaws / teaching style | `STRENGTHS_FLAWS.json` · `TEACHING_STYLE.md` |
| Camera tests / environment interactions | `CAMERA_TESTS/` · `ENVIRONMENT_INTERACTIONS/` |

---

## Continuity law

1. Always cast `DOCTOR_001` from this package.  
2. Never regenerate The Doctor from scratch for an episode.  
3. Palette, silhouette, proportions, and materials are locked.  
4. Expressions and animations come from these libraries only.  
5. Recognition test: viewers must know The Doctor next episode — even in silhouette.

---

## CLI

```bash
./venv/bin/python scripts/studio_character_doctor_001.py ensure
./venv/bin/python scripts/studio_character_doctor_001.py status
./venv/bin/python scripts/studio_character_doctor_001.py selftest
```

Use `--force` only for intentional plate rebuilds during a version upgrade.
