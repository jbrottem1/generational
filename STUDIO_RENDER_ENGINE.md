# Studio Render & Motion Graphics Engine (Version 3.0)

## Purpose

Become the **final visual authority** between completed storyboard and exported video.

Every production should look comparable to a professionally edited YouTube documentary, Kurzgesagt-style education, Vox explainer, or premium motion-graphics studio — not “AI generated.”

Quality always wins. Movement reinforces narration. No generic transitions. No random animation.

## Engine key

`studio_render` · version `3.0.0`

## Modules

| # | Module | Output |
|---|--------|--------|
| 1 | Master Timeline | Synchronized video/camera/narration/subtitles/music/SFX/VFX/graphics/color |
| 2 | Motion Graphics | Arrows, callouts, stats, diagrams, equations, kinetic reveals |
| 3 | Transitions | Context-selected cinematic dissolves, whip pans, match cuts, etc. |
| 4 | Color Grading | LUT profiles (science, tech, space, nature, medical, business, finance, historical, educational) |
| 5 | Visual Effects | Particles, grain, DOF, bloom — only when appropriate |
| 6 | Smart Text | Kinetic typography, keyword color, blur reveals |
| 7 | Diagram Animator | Domain-aware animated educational graphics |
| 8 | B-Roll Director | Prefer NASA/ESA/NOAA/USGS/NIH/LOC; rotate assets; no repeats |
| 9 | Camera Choreography | Multi-stage moves (orbit+zoom, push+rack, pan+tilt, …) |
| 10 | Export Pipeline | Shorts/TikTok/Reels/long-form/4K/60fps presets + auto bitrate/codec |
| 11 | Render Quality | Score 10 dimensions; revise until ≥ **98** |
| 12 | Media Library | `~/Desktop/AI Start-Up/AI/Media Library/{Topic}/{Project}/…` |

## Pipeline integration (backward compatible)

- After `render_package` in Executive **assembly** stage
- Before `production_qa` in `intelligence`, `full_content`, and `media_production` workflows
- Consumes `cinematography_plan` / `animation_handoff` + `viewer_retention_package`
- Additive fields only — never removes existing keys

### Context fields written

- `studio_render_package`
- `studio_render_score` / `render_quality_score`
- `studio_render_passed`
- `master_timeline_v3`
- `export_plan_v3`
- `studio_project_folder` (when library write enabled)
- Enriches `render_package.studio_render_v3`

## Production QA

New category: **`render_quality`** (weight 1.1).

Revision owners: `studio_render`, `render_package`, `timeline`, `cinematography`.

Legacy productions without a V3 package fall back to cinematography / visual scores (no hard block).

## Media Library V3 project tree

```
~/Desktop/AI Start-Up/AI/Media Library/
  {Topic}/
    {Project}/
      Scripts/ Voice/ Images/ B-Roll/ Diagrams/ Animations/
      Audio/ Assets/ Timeline/ Final/ Reports/ Archive/
```

Enable with context flag `studio_render_write_library=True` or `write_media_library=True`.

Canonical published MP4s remain under `~/Desktop/AI Start-Up/Videos/` via existing `export_verified_production`.

## Threshold

`RENDER_QUALITY_THRESHOLD = 98` · `MAX_RENDER_REVISIONS = 3`

## Tests

```bash
./venv/bin/python -m pytest tests/test_studio_render.py -q
./venv/bin/python scripts/verify_studio_render_e2e.py
```

Reports: `data/productions/_validation/studio_render/`

## Design rules

1. Never use generic hard cuts as the default transition.
2. Never apply random animation — every graphic/VFX has a narration reason.
3. Prefer authentic B-roll; rotate assets; avoid repeats.
4. Camera motion is multi-stage and smoothed — never mechanical.
5. Auto-revise until render quality ≥ 98 before export.
