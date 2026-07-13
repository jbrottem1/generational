# Permanent Generational Media Library

**Owner:** Agent 0 · Executive Office  
**Status:** LOCKED · Default export architecture  
**Module:** `services/generational_os/media_library.py`

---

## Mission

Every completed production is automatically exported to the user's **local Mac** as the permanent single source of truth. Cloud agents prepare packages only — they never claim a finished MP4 exists on Desktop.

---

## Root directory

```
~/Desktop/AI Start-Up/Videos/
```

Final production MP4s live **only** under this tree. Temporary renders stay in cache or production work folders.

---

## Category structure

Forty-five standard category folders are created automatically on first export (Biology, Chemistry, Physics, … Miscellaneous). If no standard folder fits, a new category folder is created automatically — the user never creates folders manually.

Classifier: `classify_production()` in `media_library.py`

---

## File naming

```
<Category>_<Series>_<Episode>_<Topic>.mp4
```

Examples:

| Production | Filename |
|------------|----------|
| Origin of Turtles | `Biology_001_202_Origin_of_Turtles.mp4` |
| Black Holes | `Astronomy_001_008_Black_Holes.mp4` |
| Newton's Laws | `Physics_001_014_FequalsMA.mp4` |

Builder: `build_library_filename()`

---

## Multi-category support

Some productions span multiple subjects (e.g. *Artificial Intelligence in Medicine*).

- **Primary category** → export folder
- **Secondary categories** → recorded in manifest + `VIDEO_LIBRARY.json`

---

## Companion folder

For every MP4, a sibling folder is created:

```
Biology_001_202_Origin_of_Turtles/
├── script.md
├── sources.json
├── captions.srt
├── thumbnail.png
├── metadata.json
├── production_report.md
└── render_manifest.json
```

Writer: `write_companion_files()`

---

## Library index

**Repo mirror:** `data/generational_os/VIDEO_LIBRARY.json`  
**Mac mirror:** `~/Desktop/AI Start-Up/Videos/VIDEO_LIBRARY.json` (when Desktop is reachable)

Each entry includes: title, category, series, episode, duration, keywords, scientific sources, creation date, file path, thumbnail, QC score, publishing status.

Search API: `search_library(query=..., category=..., series=..., character=..., platform=..., date_from=...)`

---

## Export verification

A production is **not complete** until all checks pass:

- MP4 exists and is playable
- Audio and video streams present
- Correct category folder
- Companion files created
- `PRODUCTION_MANIFEST.json` updated
- `VIDEO_LIBRARY.json` updated

Pipeline: `export_verified_production()` in `services/generational_os/export.py`

---

## Deduplication

Before export, SHA-256 hash is computed. If an identical file already exists in the library, the existing export is reused — no duplicate MP4 is created. If filename collides with different content, intelligent `_v2`, `_v3`, … versioning applies.

---

## Local render (Mac)

```bash
python3 scripts/run_render_package.py --package RENDER_PACKAGE.json
python3 scripts/foundation_v2_turtles.py --smoke   # benchmark
```

Cloud agents return `"Production package prepared. Awaiting local render."` — never `"Video exported."`

---

## Related docs

- [GENERATIONAL_OS_V2_5.md](./GENERATIONAL_OS_V2_5.md)
- [EXECUTION_MODE.md](./EXECUTION_MODE.md)
- [LOCAL_EXECUTION.md](./LOCAL_EXECUTION.md)
