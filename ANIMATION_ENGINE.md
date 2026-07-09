# Animation & Cinematic Production Engine (Agent 16)

The motion department of Generational. Transforms static creative assets into
fully planned animated productions — **without rendering final video**.

**Engine key:** `animation`  
**Pipeline stage:** `animation` (distribution — after asset generation, before render)  
**ContentPackage slot:** `animation_package`  
**Context keys:** `animation_summary`, `animation_packages`

---

## Architecture

```
Creative Studio / Asset Generation / Visual / Voice / Script / Psychology / OptLab
                                    ↓
                         Animation Engine (planning only)
                                    ↓
              animation_package → Render / Post-Production
```

| Layer | Path | Role |
|---|---|---|
| Engine | `engines/animation.py` | Thin pipeline adapter (`run(context) → dict`) |
| Service | `services/animation/` | Timeline, camera, motion, lip sync, VFX, QC |
| Providers | `providers/animation_provider.py` + `providers/animation/` | Future video backends (stubs + mock) |

The engine **reads** upstream slots and **writes only** `animation_package`
(+ summary context keys). It never mutates script, visual, audio, creative,
asset, render, seo, publishing, or analytics slots.

---

## Timeline system

`services/animation/timeline.py` builds a master multi-track timeline:

| Track | Contents |
|---|---|
| scene | Absolute scene windows |
| shot | Camera shot clips |
| animation | Character / facial / lip-sync clips |
| audio / music | Voice + underscore sync |
| subtitle | Caption cues |
| effects | VFX windows |
| transition | Transition clips |

Duration is unbounded (15s shorts → multi-hour). FPS, aspect ratio, and
target duration are configurable.

---

## Camera system

`services/animation/camera.py` supports:

**Framings:** wide, medium, close-up, extreme close-up, drone, orbit,
tracking, dolly, crane, handheld, first-person, over-the-shoulder,
top-down, establishing, custom.

**Movements:** pan, tilt, zoom, push, pull, orbit, truck, pedestal, crane,
dolly, smooth follow, static, custom — with keyframes and bezier
interpolation curves.

---

## Motion engine

| Module | Plans |
|---|---|
| `character.py` | Walking, running, talking, gestures, blinking, breathing, idle, blocking, multi-character coordination |
| `character.py` (facial) | Smile, fear, surprise, anger, confusion, curiosity, blends, eye/head |
| `lip_sync.py` | Phonemes, words, sentences, pauses, breaths (provider-independent) |
| `effects.py` | Transitions, VFX, particles, lighting, motion graphics, audio sync, subtitles |

---

## Provider interfaces

```python
from providers.animation import register_animation_provider, get_animation_provider
from providers.animation_provider import AnimationProvider

class MyVeo(AnimationProvider):
    name = "google_veo"
    provider_id = "google_veo"
    capabilities = ("video", "camera", "motion")
    def is_available(self): return True
    def plan(self, brief): return {"provider": "google_veo", ...}

register_animation_provider("google_veo", MyVeo())
```

Reserved adapter stubs (unavailable until API keys are set): OpenAI,
Runway, Google Veo, Kling, Pika, Luma, PixVerse, Stable Video. Demo Mode
uses `MockAnimationProvider`.

The engine emits **provider instructions** (briefs) — it does not call
vendor render APIs.

---

## Configuration

`data/animation/config.json` or runtime:

```python
from services.animation import configure

configure(
    fps=24,
    camera_style="cinematic",
    animation_style="anime",
    motion_intensity="high",
    target_aspect_ratio="9:16",
    motion_smoothing=0.7,
)
```

Knobs: animation quality, motion intensity, camera/animation style, FPS,
target platform / duration / aspect ratio, motion smoothing, feature flags
(lip sync, facial, VFX, motion graphics), parallel planning, provider
priority.

---

## Quality engine

`services/animation/quality.py` detects:

- Timeline overlaps
- Missing assets (when creative requirements exist without assets)
- Camera collisions
- Animation conflicts (walk + run)
- Continuity framing jumps
- Lip sync mismatches
- Invalid transitions
- Motion errors (missing keyframes / zero duration)

Findings are warnings/blockers — QC never raises.

---

## Batch / series

```python
from services.animation import batch_plan, plan_series, prepare_render_batch

batch_plan(items)                 # parallel campaign planning
plan_series(episodes, "saga_1")   # stamps series_id / episode_index
prepare_render_batch(packages)    # render-prep manifest (no pixels)
```

---

## Extension guide

1. **New camera move / shot type** — append to `CameraMovement` /
   `CameraShotType` and the language maps in `camera.py`.
2. **New VFX family** — append to `EffectType` and `_EFFECT_HINTS`.
3. **New provider** — subclass `AnimationProvider` in
   `providers/animation/adapters.py`, register in
   `providers/animation/__init__.py`.
4. **New package field** — append to `ANIMATION_PACKAGE_FIELDS` (additive
   only) and document in `DATA_CONTRACTS.md`.

---

## Tests

`tests/test_animation_engine.py` covers timeline, camera, animation, lip
sync, providers, quality, pipeline integration, configuration, and failure
handling.

```bash
python3 -m pytest tests/test_animation_engine.py -v
```

---

## Roadmap

1. Wire real provider `plan()` / future `render()` calls behind adapters.
2. Consume Character/IP engine packages when Agent 15 merges.
3. Deeper Creative Studio stage ordering (creative → assets → animation).
4. Hand off richer briefs to Post-Production (Agent 17) and AI Director
   (Agent 18).
5. Phoneme accuracy from real TTS word timings instead of estimates.
