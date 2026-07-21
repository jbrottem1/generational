# Generational Stage & World Simulation Engine

**Status:** Permanent studio system  
**Architecture:** Frozen — no new renderer, no image generator  
**Service:** `services/stage_world_simulation/`  
**CLI:** `scripts/stage_world_simulation.py`  
**Library:** `data/world_simulation/WORLD_LIBRARY.json`

---

## Objective

Every scene takes place inside a **persistent world**.

Characters move through the world.

They do not stand in front of photographs.

---

## WORLD_PACKAGE

Each environment contains:

geometry · floor · walls · ceilings · doors · windows · furniture · props · lighting · weather · ambient effects · **navigation mesh** · **interaction points**

Stored at:

```text
data/world_simulation/library/{WORLD_ID}/WORLD_PACKAGE.json
```

DOCTOR_001 home stage also mirrored at:

```text
data/studio_assets/DOCTOR_001/WORLD_PACKAGE/WORLD_PACKAGE.json
```

---

## Recurring locations

| World ID | Name |
|----------|------|
| WORLD-GMRI-MEDICAL-LAB | Generational Medical Lab |
| WORLD-LECTURE-HALL | Lecture Hall |
| WORLD-SCIENCE-MUSEUM | Science Museum |
| WORLD-LIBRARY | Library |
| WORLD-FOREST | Forest |
| WORLD-CITY-PARK | City Park |
| WORLD-SPACE-STATION | Space Station |
| WORLD-HOSPITAL | Hospital |
| WORLD-CLASSROOM | Classroom |
| WORLD-OCEAN-RESEARCH | Ocean Research Center |

These persist across episodes.

---

## Pipeline (frozen compose)

```
Scene Director chooses location
→ Stage & World Simulation resolves WORLD_PACKAGE
→ Character Rig places actors
→ Performance Engine chooses actions / nav paths
→ Camera follows performance
→ Renderer records
```

Soft-wired into Character & World Studio, Shot Assembly, and candidate `world_package` enrichment.

Physical contact with stage props is governed by [Physics & Interaction](PHYSICS_INTERACTION_ENGINE.md).

---

## Quality gates

Reject scenes where:

- the background is a flat image  
- actors cannot navigate naturally  
- objects cannot be interacted with  
- the environment appears static  
- the camera replaces character movement  

JSON plans are not proof — inspect the final MP4.

---

## CLI

```bash
python3 scripts/stage_world_simulation.py ensure
python3 scripts/stage_world_simulation.py build --world WORLD-GMRI-MEDICAL-LAB
python3 scripts/stage_world_simulation.py selftest
```

---

## Honest limit

Under frozen architecture this is the **persistent stage contract** (geometry, nav mesh, interactions, living channels). It composes Environment Department packages where available. Full real-time 3D collision simulation still executes through existing Animation Engine / true_motion consumers — this engine does not become a new renderer.
