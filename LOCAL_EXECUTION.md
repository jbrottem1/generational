# Local Execution — Render, Verify, Export

**Mode:** `ExecutionMode.LOCAL`  
**Detection:** macOS with `~/Desktop/AI Start-up/` present, or `GENERATIONAL_EXECUTION_MODE=local`

---

## Local is responsible for

- Image downloads (via cache)
- OpenAI TTS / ElevenLabs narration
- FFmpeg rendering
- Lip-sync performance (`render_lip_sync_performance`)
- Local asset caching
- Video assembly and QC gates
- **Final MP4** on Desktop
- Finder visibility

---

## Prerequisites (Mac)

1. Generational repo cloned locally
2. Python 3 + dependencies (`pip install -r requirements.txt` or project venv)
3. **ffmpeg** installed (`brew install ffmpeg`)
4. `.env` with `OPENAI_API_KEY` (or use `--smoke` for offline test)
5. Reality catalog images present under `data/reality/images/` (or run `python3 scripts/fetch_reality_images.py`)

---

## Render from job package (recommended)

After a cloud agent prepares the job:

```bash
cd /path/to/generational
python3 scripts/run_local_render_job.py --job LOCAL_RENDER_JOB.json
```

With real TTS (requires OpenAI key in `.env`):

```bash
python3 scripts/run_local_render_job.py --job LOCAL_RENDER_JOB.json
```

Offline smoke test:

```bash
python3 scripts/run_local_render_job.py --job LOCAL_RENDER_JOB.json --smoke
```

On success the script:

1. Warms **local asset cache** (`data/local_cache/`)
2. Builds narration
3. Renders episode
4. Copies to `~/Desktop/AI Start-up/videos/Test run 2 generational/`
5. Runs ffprobe verification
6. Reveals file in **Finder** (`open -R`)

---

## Render from flagship script (direct)

When already on Mac in local mode, scripts render directly:

```bash
python3 scripts/foundation_v2_turtles.py
```

Gate detects local mode → full pipeline runs → verified Desktop export.

---

## Asset cache

Location: `data/local_cache/`

| Kind | Reuse |
|------|-------|
| `reality_image` | Catalog JPEGs by `image_id` |
| `image` | Remote URL downloads by URL hash |

Identical assets are not re-downloaded across renders.

API: `services/media_production/local_cache.py`

---

## Export verification (required for SUCCESS)

All checks must pass (`verified_export.verify_canonical_export`):

| Check | Requirement |
|-------|-------------|
| `file_exists` | Path is a file |
| `size_gt_zero` | Bytes > 0 |
| `video_stream` | h264 (typical) |
| `audio_stream` | aac (typical) |
| `playable` | ffprobe OK |
| `duration` | > 0.5s |
| `resolution` | width × height set |
| `under_canonical_dir` | Under Test run 2 generational |
| `local_execution` | Not cloud mode |

Only then may status be `"export_verified"`.

---

## Canonical destination

```
~/Desktop/AI Start-up/videos/Test run 2 generational/
```

Never overwrite — version suffix `_v2`, `_v3`, … when filename exists.

---

## Open export folder

```bash
open ~/Desktop/AI\ Start-up/videos/Test\ run\ 2\ generational/
```

Or rely on `run_local_render_job.py` which calls Finder reveal automatically.
