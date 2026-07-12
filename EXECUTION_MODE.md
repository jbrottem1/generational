# Execution Mode — Local-First Production Architecture V2

**Owner:** Agent 0 · Executive Operating System  
**Status:** LOCKED effective 2026-07-12

Generational separates **thinking** (cloud) from **rendering** (local Mac).

---

## Two modes

| Mode | Runtime | Media production |
|------|---------|------------------|
| **CLOUD** | Cursor cloud agents, CI, remote Linux VMs | Plans only — writes `LOCAL_RENDER_JOB.json` |
| **LOCAL** | User's Mac (`Darwin` + Desktop path) | Full render, verify, Desktop export |

Detection: `services/media_production/execution_mode.py` → `detect_execution_mode()`

Override env vars:

| Variable | Effect |
|----------|--------|
| `GENERATIONAL_EXECUTION_MODE=cloud` | Force cloud (plan only) |
| `GENERATIONAL_EXECUTION_MODE=local` | Force local render |
| `GENERATIONAL_FORCE_LOCAL=1` | Treat Linux as local (dev only) |
| `GENERATIONAL_CLOUD_MODE=1` | Treat as cloud |

---

## Execution gate

Before any flagship render script runs FFmpeg/TTS:

```python
from services.media_production.local_first import gate_production

gate = gate_production(job_id=..., title=..., demo_id=..., ...)
if not gate.get("proceed"):
    # Cloud: job written — return awaiting_local_render
    return gate
# Local: continue render pipeline
```

**Cloud agents must never report:** `"Video exported."`  
**Cloud agents must report:** `"Production package prepared. Awaiting local render."`

**Local SUCCESS requires:** verified MP4 at  
`~/Desktop/AI Start-up/videos/Test run 2 generational/`

---

## Deliverables map

| File | Purpose |
|------|---------|
| [EXECUTION_MODE.md](./EXECUTION_MODE.md) | This document |
| [CLOUD_EXECUTION.md](./CLOUD_EXECUTION.md) | Cloud agent responsibilities |
| [LOCAL_EXECUTION.md](./LOCAL_EXECUTION.md) | Mac workstation workflow |
| [LOCAL_RENDER_JOB.json](./LOCAL_RENDER_JOB.json) | Portable render package |
| `scripts/run_local_render_job.py` | Execute job on Mac |
| `services/media_production/local_cache.py` | Reuse downloaded assets |

---

## Export standard (V2.5 update)

**Primary path (classified):**

```
~/Desktop/AI Start-up/Generational/Videos/{Domain}/{filename}.mp4
```

See [GENERATIONAL_OS_V2_5.md](./GENERATIONAL_OS_V2_5.md) for domain folders and manifest requirements.

**Legacy path** (migration in progress):

```
~/Desktop/AI Start-up/videos/Test run 2 generational/
```

Verification checklist (all must pass for SUCCESS):

- File exists
- Size > 0
- Video stream present
- Audio stream present
- Playable (ffprobe)
- Duration recorded
- Resolution recorded
- Path under canonical Desktop folder
- Local execution mode

Implementation: `services/media_production/verified_export.py`

---

## Agent compliance

All production agents and scripts that create MP4s must:

1. Call `gate_production()` before render
2. Respect `proceed=False` in cloud mode
3. Use `export_verified_mp4()` for final copy
4. Never treat cloud VM `Path.home()/Desktop` as the user's Mac

See [data/knowledge_standards/PRODUCTION_STANDARDS.md](./data/knowledge_standards/PRODUCTION_STANDARDS.md) § Local-First.
