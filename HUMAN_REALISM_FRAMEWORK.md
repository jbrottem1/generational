# Human Realism Framework V1

**Status:** Permanent studio infrastructure  
**Style target:** Feature-film cinematic realism  
**Gold standard:** `DOCTOR_001` The Doctor (legacy alias `CHAR-0001`)  
**Service:** `services/human_realism/`  
**Data:** `data/human_realism/`

Architecture remains frozen. This is **not** a new renderer and **not** a pipeline redesign.

---

## Mission

No Generational character should feel robotic or procedurally empty.

Every humanoid host inherits one shared Human Realism Framework. Characters override only:

- visual identity  
- personality  
- voice  
- clothing  
- role  
- gait personality  
- signature gestures / biography  

Anatomy, locomotion, face, eyes, blink, breath, cloth/hair *intent*, emotion, idle life, object interaction, camera awareness, and QC dimensions come from the base.

---

## Inheritance

```
BASE_HUMAN_REALISM  (services/human_realism/base.py)
        ↓
character identity overrides  (services/human_realism/characters.py)
        ↓
resolved package + profile views  (data/human_realism/characters/<ID>/)
```

The Doctor is the richest reference implementation. Atlas, Nova, Orion, Piper, Luna — and every future host — resolve through the same path.

---

## PerformancePlan (every scene)

Character & World Studio attaches a `performance_plan` on each scene binding:

- emotional state  
- gaze target  
- body language  
- gesture cadence  
- walking style  
- breathing intensity  
- facial performance  
- interaction targets  
- camera awareness  
- environmental reactions  

Soft-wired into visual package scenes via `attach_character_world_studio`.

---

## CLI

```bash
./venv/bin/python scripts/human_realism_framework.py ensure
./venv/bin/python scripts/human_realism_framework.py show CHAR-0001
./venv/bin/python scripts/human_realism_framework.py selftest
```

## Companions

- `GENERATIONAL_VISUAL_FOUNDATION_V1.md`  
- `data/visual_foundation/HUMAN_CHARACTER_REALISM_V1.md`  
- `STUDIO_ASSET_0001_THE_DOCTOR.md`  
- `CHARACTER_WORLD_STUDIO.md`  
