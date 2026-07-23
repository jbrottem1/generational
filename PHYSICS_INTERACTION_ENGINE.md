# Generational Physics & Interaction Engine

**Status:** Permanent studio system  
**Architecture:** Frozen — not a renderer, image generator, or world builder  
**Service:** `services/physics_interaction/`  
**CLI:** `scripts/physics_interaction.py`  
**Library:** `data/physics_interaction/PHYSICS_LIBRARY.json`

---

## Mission

Everything has physical behavior.

Actors obey physics. Objects obey physics. Interactions feel believable.

**Nothing floats. Nothing clips. Nothing teleports.**

---

## INTERACTION_PACKAGE

Every interaction contains:

`interaction_id` · `actor` · `target` · `interaction_type` · `contact_points` · `physics_state` · `constraints` · `animation_requirements` · `completion_state`

Supported types include walking, doors, pick/place, typing, pointing, medical exams, microscopes, tools, reading, and more (see `SUPPORTED_INTERACTIONS`).

---

## PHYSICS_PROFILE

Per actor:

- hand physics (fingers, grasp, dual-hand)  
- foot physics (plant, heel-toe, stairs, friction)  
- body physics (CoG, weight transfer, momentum, balance)  
- object physics (mass, collision, friction, zones)  
- collision system  
- clothing physics  
- hair physics  
- environmental physics (wind / rain)

Stored at:

```text
data/physics_interaction/profiles/{CHARACTER_ID}/PHYSICS_PROFILE.json
```

DOCTOR_001 also mirrored at `data/studio_assets/DOCTOR_001/PHYSICS/`.

---

## Pipeline (frozen compose)

```
Stage resolves WORLD_PACKAGE
→ Rig places actor
→ Physics & Interaction plans INTERACTION_PACKAGEs
→ Performance Engine executes blocking against constraints
→ Renderer records
```

Soft-wired into Character & World Studio casting/package and Shot Assembly.

---

## Quality gates

Reject: floating actors · sliding feet · object clipping · broken collisions · weightless movement · hands missing targets · unrealistic balance

JSON plans are not proof — inspect the final MP4.

---

## CLI

```bash
python3 scripts/physics_interaction.py ensure
python3 scripts/physics_interaction.py interact --type opening_doors --target door_main
python3 scripts/physics_interaction.py selftest
```

---

## Honest limit

Under frozen architecture this is the **physical behavior contract**. It composes Character Rig mechanics, Stage interaction points, and Performance Engine events. Real-time rigid-body solving still depends on downstream execution — this engine does not become a new physics renderer.
