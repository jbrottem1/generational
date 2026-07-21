# Virtual Film Director (VFD)

**Status:** Production (direction layer)  
**Service:** `services/virtual_film_director/`  
**Soft-wire:** inside `engines/cinematography.py` (after cine plan) + ops ensure on `animation` stage  
**CLI:** `scripts/virtual_film_director.py`

Architecture remains frozen.

This is **not** a renderer.  
This is **not** another animation engine.  
This is **not** a pipeline redesign.

The Virtual Film Director sits **above** the Animation Engine.

> Animation executes. The Virtual Film Director decides.

---

## The problem

Movement ≠ direction.

Without a director, productions get purposeless camera drift, flat emotion, and procedural-feeling scenes. VFD forces every scene to answer professional questions before Animation Engine V2 plans motion.

---

## Studio position

```
Executive Producer (GenOS)
          │
Virtual Film Director ⭐
          │
Cinematography / Cinematic Director (composed, not replaced)
          │
Animation Engine V2 (executes SHOT_PLAN seeds)
          │
true_motion / MotionPlanner / assembler
```

---

## Director's questions (per scene)

- Why does this scene exist?  
- What should the viewer learn?  
- What emotion should they feel?  
- What should they notice first?  
- What should move / remain still?  
- Where does the camera begin / end?  
- What is the cinematic payoff?  

If any answer is unclear → scene is not ready.

---

## Mandatory outputs

Written under `data/virtual_film_director/packages/<topic>_<stamp>/`:

| Artifact | Role |
|----------|------|
| `SHOT_PLAN.json` | Full per-scene shot plan |
| `DIRECTOR_NOTES.md` | Creative brief + review |
| `CAMERA_SCRIPT.md` | Begin→end camera motivation |
| `EMOTIONAL_TIMELINE.json` | Curiosity→payoff rhythm |
| `VISUAL_STORYBOARD.md` | Muted-viewer storyboard |
| `VIRTUAL_FILM_DIRECTOR_PACKAGE.json` | Master package |

Each shot includes: objective, subject, angle, lens, shot size, movement, blocking, environment motion, lighting, palette, transition, emotional beat, educational goal, duration, animation priority.

---

## Soft-attach → Animation Engine

Scenes receive:

- `vfd_seed` (`true_motion_camera`, `ae_camera_move`, `narrative_purpose`, emotion, lighting)  
- `shot_language`, `emotional_beat`, `transition_style`  

Animation Engine V2 **honors** these seeds when choosing cameras (source=`virtual_film_director`) instead of inventing purposeless motion.

---

## Director review

Approves only when:

- every scene has purpose  
- every camera communicates  
- emotional pacing is not flat  
- muted-story test passes  

Failures produce `rewrite_scenes` and a one-pass rewrite **before** animation begins.

---

## CLI

```bash
./venv/bin/python scripts/virtual_film_director.py selftest
./venv/bin/python scripts/virtual_film_director.py direct --topic "Your Topic"
```

---

## Compose only

| System | Role |
|--------|------|
| `cinematic_director` | Existing intensity / palette façade |
| `cinematography` | Classic documentary camera plan |
| **Virtual Film Director** | Shot plan + emotional timeline + review |
| Animation Engine V2 | Executes directed seeds |
| true_motion | Pixel execution |

**Success criteria:** Generational behaves like a studio where scenes are directed before they are animated — not like an AI video assembler.
