# Execution Mode — Local-First Production

**Owner:** Agent 0 · Executive Operating System  
**Status:** LOCKED — Local-First (cloud production execution removed 2026-07-12)

Generational renders, verifies, and exports **only on the user's local Mac**.

Cursor Cloud may still be used manually for brainstorming or architecture when explicitly requested — **never** for rendering, exporting, or production execution.

---

## Single mode

| Mode | Runtime | Media production |
|------|---------|------------------|
| **LOCAL** | User's Mac — local Python, FFmpeg, filesystem | Full pipeline: plan → render → verify → Desktop export |

Detection: `services/media_production/execution_mode.py` → always `ExecutionMode.LOCAL`

There is no `ExecutionMode.CLOUD` and no automatic “Run in Cloud” path.

---

## Production gate

```python
from services.media_production.local_first import gate_production

gate = gate_production(job_id=..., title=..., demo_id=..., ...)
# Always proceeds locally — writes brief + RENDER_PACKAGE, then authorizes render
assert gate["proceed"] is True
assert gate["status"] == "ready_to_render"
```

**SUCCESS requires:** verified MP4 under:

```
~/Desktop/AI Start-Up/Videos/{Category}/
```

via the media library classifier (`MEDIA_LIBRARY.md`).

---

## Assumptions for all future development

- Local Python
- Local FFmpeg
- Local filesystem
- Local render pipeline
- Local testing
- Local exports to `~/Desktop/AI Start-Up/Videos/`

---

## Deliverables map

| File | Purpose |
|------|---------|
| [EXECUTION_MODE.md](./EXECUTION_MODE.md) | This document |
| [LOCAL_EXECUTION.md](./LOCAL_EXECUTION.md) | Mac workstation workflow |
| [MEDIA_LIBRARY.md](./MEDIA_LIBRARY.md) | Classified Desktop library |
| `scripts/run_local_render_job.py` | Execute render package on Mac |
| `services/media_production/execution_mode.py` | Local-only context helpers |

---

## Safety

Remote VM paths (`/home/ubuntu/`, `/workspace/`) are rejected as `stale_cloud_path` so a non-Mac filesystem can never be reported as a successful user Desktop export.

---

## Agent compliance (locked)

1. Call `gate_production()` / `prepare_production()` before render (local prep).
2. Never claim Desktop SUCCESS without a verified local MP4 under the media library.
3. Never introduce a Cursor Cloud / remote render or export execution path.
4. Do not add `GENERATIONAL_CLOUD_*` / `CURSOR_CLOUD_*` production gates.
