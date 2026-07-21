# Generational Character Rig Studio

**Status:** Permanent studio system  
**Architecture:** Frozen — no new renderer, image generator, or video generator  
**Service:** `services/character_rig_studio/`  
**CLI:** `scripts/character_rig_studio.py`  
**Library:** `data/character_rig_studio/CHARACTER_LIBRARY.json`

---

## Goal

Characters are no longer regenerated for every scene.

Characters become **permanent digital actors**.

Every actor owns:

identity · proportions · skeleton · facial rig · performance rig · clothing · materials · animation library · personality

Scenes **reference** the actor. Scenes **never recreate** the actor.

---

## Pipeline (frozen compose)

```
Scene Director chooses actors
→ Performance Engine chooses actions
→ Character Rig Studio executes movement (rig + clips)
→ Renderer records the performance
```

Soft-wired into Character & World Studio casting, Shot Assembly, and host profiles (`character_rig_ref`).

Stages come from [Stage & World Simulation](STAGE_WORLD_SIMULATION.md) — actors perform inside persistent worlds, not photo backdrops.

---

## CHARACTER_RIG_PACKAGE

Stored at:

```text
data/studio_assets/{CHARACTER_ID}/CHARACTER_RIG/
```

Includes: IDENTITY · BODY_RIG · FACIAL_RIG · EYE_SYSTEM · HAND_SYSTEM · BODY_MECHANICS · WARDROBE · MATERIALS · PERFORMANCE_SYSTEM · PERSONALITY · VALIDATION

---

## Character Library

| ID | Role |
|----|------|
| DOCTOR_001 | Canonical medical educator (gold standard) |
| FOUNDER_001 | Inspiration traveler host |
| TEACHER_001 | Classroom educator (reserved) |
| HISTORIAN_001 | History storyteller (reserved) |
| ENGINEER_001 | Systems / invention host (reserved) |
| NURSE_001 | Care partner educator (reserved) |
| PATIENT_CHILD_001 | Pediatric patient presence (reserved) |

---

## Quality gates

Reject actors that:

- change appearance between scenes  
- have inconsistent proportions  
- cannot walk naturally  
- cannot perform expressive facial acting  
- cannot interact with objects  
- cannot maintain eye contact  
- cannot support reusable animation clips  

---

## CLI

```bash
python3 scripts/character_rig_studio.py ensure
python3 scripts/character_rig_studio.py build --character DOCTOR_001
python3 scripts/character_rig_studio.py selftest
```

---

## Honest limit

This is the **permanent actor contract and library** under frozen architecture. It composes existing studio assets (skeleton, face, wardrobe, animation index) into a reusable rig package. Full skeletal mesh deformation still depends on downstream execution systems (Animation Engine / true_motion) — the Rig Studio does not become a new renderer.
