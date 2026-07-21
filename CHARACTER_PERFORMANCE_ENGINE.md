# Generational Character Performance Engine

**Status:** Permanent studio standard  
**Architecture:** Frozen — no new renderer, no pipeline redesign  
**Service:** `services/character_performance_engine/`  
**CLI:** `scripts/character_performance_engine.py`

---

## What this is

The system responsible for producing **believable animated performances before rendering begins**.

It is **not**:

- a renderer  
- an image generator  
- an animation filter  

Every scene begins with a performance. The renderer records that performance.

---

## Pipeline (frozen compose)

```
1. Build the environment
2. Place the character
3. Assign objectives
4. Simulate performance
5. Animate the performance
6. Then render
```

Soft-wired into:

- Character & World Studio (casting)  
- Shot Assembly (`complete_shot`)  
- Animation Engine V2 (`true_motion` block)  
- `true_motion` compositor (`performance_path` keyframes)  
- Character Rig Studio (actors referenced, never regenerated)

---

## Every scene package contains

| Block | Purpose |
|-------|---------|
| `objective` | Why the actor moves |
| `blocking` | Where everyone is / walks / looks / touches / ends |
| `locomotion` | Waypoints, foot plants, no float/slide/teleport |
| `body_performance` | Continuous full-body timeline |
| `interactions` | Props, doors, holograms, microscopes |
| `environment_life` | Living world channels |
| `camera_follow` | Camera records action; never replaces it |
| `simulation` | Actor path keyframes for true_motion |
| `validation` | Rejects Ken Burns / photo-pan signatures |

---

## Hard rules

- Never stationary longer than **3 seconds** unless intentionally dramatic.  
- Characters stand on floors; feet contact ground.  
- No floating, sliding, or teleporting between poses.  
- Camera follows the actor path.  
- If motion could be recreated by moving a still photograph — **reject**.

---

## Quality test

JSON plans are **not** proof of quality. Inspect the final MP4 for:

- continuous character locomotion / gesture  
- foot contact  
- world life (not a frozen plate)  
- interactions with the set  
- camera following rather than replacing action  
- “animated television show” — not “animated pictures”

---

## CLI

```bash
python scripts/character_performance_engine.py selftest
python scripts/character_performance_engine.py doctor
python scripts/character_performance_engine.py build --narration "..." --duration 4
```

---

## Honest limit

Under frozen architecture, the compositor remains layered `true_motion` (character plate on living environment). The engine upgrades that path from camera-only Ken Burns to **actor-driven blocking keyframes**. Full skeletal 3D acting would require a new renderer — explicitly out of scope until architecture is unfrozen.
