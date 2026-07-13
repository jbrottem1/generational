# Cinematography Engine

**Status:** Production  
**Engine key:** `cinematography`  
**Service:** `services/cinematography/`

Every educational video is professionally directed. Movement always reinforces narration — never random.

---

## Pipeline position

```
evidence_intelligence → visual_intelligence → cinematography → (Animation Engine) → voice_audio
```

Receives completed scenes from Evidence & Visual Intelligence.  
Outputs `cinematography_plan` + `animation_handoff` for Animation / Render.

---

## Narration → movement examples

| Narration | Movement |
|-----------|----------|
| "The Earth tilts…" | `orbit` |
| "Notice this fossil…" | `slow_push_in` |
| "This tiny transistor…" | `macro_push_in` |
| "The factory…" | `establishing_wide` |
| reveal / hidden | `reveal` |
| depth / layers | `parallax` |
| follow / travels | `tracking` |

---

## Per-scene output

- camera angle · framing  
- zoom direction · pan direction  
- parallax depth · camera speed · easing  
- focus point / coordinates  
- transition · duration  
- movement + reason  
- **camera plan**  
- **timeline**  
- **motion graph** (keyframes)  
- scene pacing  
- attention score  
- `animation_effect` / `animation_camera` for Animation Engine  

### Available movements
Slow push-in · Slow pull-out · Horizontal pan · Vertical pan · Parallax · 3D camera move · Orbit · Rack focus · Tracking · Reveal · Macro push-in · Establishing wide · Static hold  

### Transitions
Whip · Match cut · Cross dissolve · Fade · L-cut · J-cut · Hard cut  

---

## Animation Engine handoff

```python
from services.cinematography import get_animation_handoff, cinematography_to_true_motion_cameras

handoff = candidate["animation_handoff"]
# handoff["scenes"][i]["camera"] → composite_true_motion_scene(..., camera=...)
# handoff["scenes"][i]["effect"] → MotionPlanner / ffmpeg effect vocabulary
```

---

## Usage

```python
from services.cinematography import build_cinematography_plan

plan = build_cinematography_plan(candidate)  # uses evidence_package / visual_package scenes
print(plan.to_dict()["animation_handoff"])
```

```bash
./venv/bin/python -m pytest tests/test_cinematography.py -q
./venv/bin/python scripts/verify_cinematography.py
```

---

## Files

| Path | Role |
|------|------|
| `services/cinematography/models.py` | Contracts + animation payload |
| `services/cinematography/director.py` | Narration → movement + graphs |
| `services/cinematography/animation_adapter.py` | MotionPlanner / true_motion bridge |
| `engines/cinematography.py` | Pipeline adapter |
