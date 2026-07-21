# Local Execution — Render, Verify, Export

**Mode:** `ExecutionMode.LOCAL` (only mode)  
**Export root:** `~/Desktop/AI Start-Up/Videos/{Category}/`

---

## Local owns the full production pipeline

- Script / brief / render package preparation
- Image downloads (via local cache)
- OpenAI TTS / narration
- FFmpeg rendering
- Lip-sync performance
- QC gates
- Verified MP4 export to the media library
- Finder visibility

---

## Prerequisites (Mac)

1. Generational repo cloned locally
2. Python 3 + dependencies
3. **ffmpeg** installed (`brew install ffmpeg`)
4. `.env` with `OPENAI_API_KEY` (or use `--smoke` for offline test)
5. Reality catalog images under `data/reality/images/` when needed

---

## Recommended workflow

```bash
cd /path/to/generational

# Prepare + render a production script (local end-to-end)
python3 scripts/foundation_v2_turtles.py --smoke

# Or execute an existing render package / job
python3 scripts/run_local_render_job.py --job RENDER_PACKAGE.json

# Verify a known export
python3 scripts/verify_local_export.py
```

---

## Export standard

Finished videos land under the classified media library:

```
~/Desktop/AI Start-Up/Videos/{Category}/{Category}_{Series}_{Episode}_{Topic}.mp4
```

Example:

```
~/Desktop/AI Start-Up/Videos/Biology/Biology_001_202_Origin_of_Turtles.mp4
```

Companion folder (script, sources, metadata, captions) sits beside the MP4.

---

## Status vocabulary

| Status | Meaning |
|--------|---------|
| `ready_to_render` | Package prepared; local render authorized |
| `verified` | Destination MP4 verified |
| `SUCCESS` / `SUCCESS_WITH_WARNINGS` / `FAILED` | Final production status (`FINAL_STATUS_SPEC.md`) |

The legacy handoff status `awaiting_local_render` is retired (may appear only in historical JSON).

---

## Cloud usage policy

Cursor Cloud is **not** part of the production workflow.

It may be used manually for brainstorming or architecture **only when you explicitly request it**.  
It must never render, export, or claim a Desktop MP4 exists.
