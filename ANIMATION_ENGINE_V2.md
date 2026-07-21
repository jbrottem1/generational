# Cinematic Animation Engine V2

**Status:** Production (quality evolution of V1)  
**Service:** `services/animation_engine/`  
**Engine:** `engines/animation.py` (`is_ready=True`, version `2.0.0`)  
**CLI:** `scripts/animation_engine_v2.py` (V1 CLI still routes to the same package builder)

Architecture remains frozen. This is **not** a new renderer and **not** a pipeline redesign.

V2 upgrades planning quality from “make it move” → **cinematic storytelling**.

---

## The problem V2 solves

V1 ensured every scene has motion. V2 ensures every motion has **purpose**.

Rejected patterns:

- purposeless camera drift  
- floating abstract shapes pretending to be worlds  
- mannequin characters  
- empty / flat backdrops  
- PowerPoint / slideshow energy  

---

## Pipeline position (unchanged)

```
Visual Asset Director
      ↓
Cinematography (live)
      ↓
Cinematic Animation Engine V2   ← intent · camera · world depth · performance · immersion · gate
      ↓
Voice → Renderer (MotionPlanner / true_motion / ffmpeg assembler)
```

---

## What V2 adds

| Layer | V2 behavior |
|-------|-------------|
| **Cinematic intent** | Before each scene: audience understanding, emotion, lighting mood, shot size, visual moment, reject list |
| **Motivated camera** | Dolly / crane / orbit / tracking / reveal / hero low-angle / vulnerability high-angle — each with `narrative_purpose` |
| **World depth** | FG / MG / BG life tokens; living env continues without narration; `allow_abstract_geometry=false` |
| **Character performance** | Micro-performance (breathe, blink, weight shift, gaze) + forbid mannequin |
| **Lighting color** | Golden hour, soft daylight, storm, moonlight, firelight, volumetric sunlight, cinematic contrast |
| **Transitions** | Motives: emotion/lighting continuity, match cuts, focus racks — still avoid default crossfades |
| **Immersion test** | Checklist per scene; failures produce `re_render_scenes` targets |
| **true_motion execution** | Mood grading, grounded grass/cloud/bird layers, emotion-scaled camera amplitude, story props only when narratively earned |

---

## Animation Excellence (V2 dimensions)

V1 dimensions plus:

- intentionality  
- environmental_believability  
- performance_life  

Soft target: **≥ 78**.

## Quality gate

Still rejects:

- \>10% static runtime  
- frozen backgrounds  
- locked cameras  
- lifeless planned characters  
- empty motion  

V2 also rejects / warns on:

- purposeless camera movement  
- abstract-geometry worlds  
- immersion pass ratio below **0.85**  

Failed scenes are listed in `quality_gate.re_render_scenes` for selective re-render.

---

## Outputs

`data/animation_engine/packages/*_ANIMATION_PACKAGE.json` (+ `.md`)

Package version: **`2.0.0`**

Candidate soft-attach:

- `ANIMATION_PACKAGE` / `animation_engine`  
- Per-scene `cinematic_intent`, `true_motion` (`cinematic_v2`, lighting, emotion, shot_size, depth_layers)  
- `animation_handoff.animation_engine_v2 = true` (v1 flag retained for compatibility)  
- `cinematic_animation_v2 = true`  

---

## CLI

```bash
./venv/bin/python scripts/animation_engine_v2.py selftest
./venv/bin/python scripts/animation_engine_v2.py plan --topic "Your Topic"
```

---

## Compose only

| System | Role |
|--------|------|
| Cinematography | Upstream camera plan / handoff |
| Visual Source Intelligence | Source selection + motion preference |
| `true_motion` | Layered env/character/camera compositor (V2 mood/depth) |
| MotionPlanner / ffmpeg assembler | Execute motion effects |
| Renderer / Ops stages | Unchanged order |

**Final goal:** cinematic educational short films — not AI slideshow with motion.
