# Post-Production & Intelligent Editing Engine (Agent 17)

Agent 17 transforms completed animation/render packages into polished,
publication-ready productions. It does **not** generate new content — it
intelligently edits, refines, enhances, synchronizes, packages, and prepares
completed productions for final rendering and publishing.

**Engine key:** `post_production`  
**Version:** 1.0.0  
**Pipeline position:** Render Engine → **Post-Production** → Global Content Optimization → Publishing

---

## Architecture

```
ContentPackage (unified_packages)
    │
    ├── render_package          (read — Agent 6)
    ├── audio_package           (read — Agent 5)
    ├── creative_package        (read — Agent 12)
    ├── asset_package           (read — Agent 14)
    └── animation_package       (read — Agent 16, when present)
            │
            ▼
    PostProductionEngine (engines/post_production.py)
            │
            ├── editing.py          — pacing, jump cuts, dead space
            ├── timeline.py         — master edit timeline (tracks/layers/clips)
            ├── audio_finalize.py   — dialogue leveling, ducking, normalization
            ├── captions_finalize.py — animated captions, themes, exports
            ├── color.py            — correction, grading, brand LUTs
            ├── effects.py          — transitions, VFX planning
            ├── motion_graphics.py  — intros, outros, CTAs, watermarks
            ├── platform.py         — per-platform safe zones and exports
            ├── export.py           — resolution presets (1080p–4K, HDR, proxy)
            └── quality.py          — QC validation and readiness scoring
            │
            ▼
    post_production_package (ContentPackage slot — Agent 17 write zone)
```

### Design principles

1. **Consume, don't duplicate.** Reads `render_package` plans (timeline,
   `caption_render_plan`, `audio_mix_plan`, `transition_plan`, `motion_plan`)
   and *finalizes* them — never rebuilds Agent 6's work from scratch.
2. **Never crash the pipeline.** Per-item failures degrade to incomplete
   packages with diagnostics; empty context returns SKIPPED.
3. **Provider-driven.** All real editing backends (FFmpeg, Premiere,
   DaVinci Resolve, CapCut, Runway) swap in via
   `PostProductionProvider` — no vendor logic in the engine.
4. **Fully configurable.** Editing style, pacing, captions, transitions,
   color, audio targets, and platform defaults are all tunable via
   `PostProductionConfig`.

---

## Timeline model

The master editing timeline (`EDIT_TIMELINE_FIELDS`) supports:

| Component | Fields |
|---|---|
| Timeline | `timeline_id`, `total_duration_sec`, `fps`, `tracks`, `markers`, `metadata` |
| Track | `track_id`, `track_type` (video/audio/caption/effect/transition/graphics), `layer`, `clips` |
| Clip | `clip_id`, `asset_ref`, `start_time`, `end_time`, `duration`, transitions, effects |
| Marker | `marker_id`, `time`, `label`, `marker_type` (cut/beat/cta/chapter/note) |

Seven default tracks: video_main, audio_dialogue, audio_music, audio_sfx,
captions, effects, graphics.

---

## Audio pipeline

Reads `render_package.audio_mix_plan` and produces a finalized mix plan
(`AUDIO_MIX_FINAL_FIELDS`):

- Dialogue leveling and normalization to platform LUFS targets
- Music ducking during speech (configurable)
- Compression, EQ, limiter, noise reduction effects
- Fade in/out
- Per-platform loudness targets (YouTube -14 LUFS, Facebook -16 LUFS, etc.)

---

## Caption system

Reads `render_package.caption_render_plan` and produces:

- **Caption timeline** — word-by-word or sentence mode with highlight words and emoji support
- **Subtitle styling** — theme presets (bold_pop, clean_minimal, karaoke_highlight, documentary_lower_third)
- **Export formats** — SRT, VTT, ASS, burned-in
- **Multi-language** — configurable via `PostProductionConfig.multi_language`

---

## Color engine

Plans color correction and grading (`COLOR_GRADING_FIELDS`):

- Presets: neutral, vibrant, cinematic_warm, documentary_cool, brand
- Per-scene corrections from creative blueprint color palette
- Brand LUT support
- HDR preparation placeholder

---

## Visual effects & motion graphics

**Effects** (`EFFECT_PLAN_FIELDS`): motion blur, glow, lens flare, particles,
speed ramps, freeze frames, zoom emphasis — planned from render motion_plan
and intelligent editing cut decisions.

**Motion graphics** (`MOTION_GRAPHIC_FIELDS`): intro sequences, outro/end
screens, subscribe/like CTAs, channel branding watermarks — timed from
configurable intro/outro/CTA lengths.

---

## Platform optimization

Per-platform export configurations (`PLATFORM_EXPORT_FIELDS`):

| Platform | Aspect | Safe zones | Caption anchor |
|---|---|---|---|
| YouTube Shorts | 9:16 | top 12%, bottom 20% | 68% |
| TikTok | 9:16 | top 10%, bottom 18% | 64% |
| Instagram Reels | 9:16 | top 10%, bottom 16% | 66% |
| YouTube | 16:9 | standard | 85% |
| LinkedIn | 16:9 | standard | 88% |
| Facebook | 9:16 | standard | 65% |
| X | 16:9 | standard | 85% |

---

## Export system

Eight built-in export presets (`EXPORT_PRESET_FIELDS`):

- 1080p vertical / horizontal / square
- 1440p vertical
- 4K horizontal / vertical
- Archive master (4K HDR)
- Proxy 720p

---

## Quality control

Automatic detection (`QUALITY_REPORT_FIELDS`):

- Broken cuts (edited_end ≤ edited_start)
- Missing assets (from render validation)
- Caption overlap
- Audio clipping / missing loudness target
- Sync errors (duration mismatch)
- Duplicate clips
- Zero-duration (black frame) clips

Readiness scoring maps to `ready` / `needs_review` / `incomplete`.

---

## Provider abstraction

```python
from providers.post_production import default_post_production_provider, provider_catalog

provider = default_post_production_provider()  # MockPostProductionProvider (Demo Mode)
provider.assemble(package)   # timeline → project
provider.export(package, "1080p_vertical")
provider.validate(package)
provider_catalog()           # [{name, label, capabilities, ...}]
```

Future adapters register via `register_post_production_provider()`:
FFmpeg, Adobe Premiere, DaVinci Resolve, CapCut, Runway.

---

## Configuration

```python
from services.post_production import configure, get_post_production_config

configure(
    editing_style="retention",       # fast_paced | documentary | educational | comedy | cinematic | retention
    pacing_profile="balanced",       # aggressive | balanced | conservative
    caption_theme="bold_pop",
    transition_style="dynamic",
    color_preset="vibrant",
    target_platforms=["youtube_shorts", "tiktok"],
    enable_jump_cuts=True,
    enable_dead_space_removal=True,
    intro_length_sec=1.5,
    outro_length_sec=3.0,
)
```

---

## Pipeline integration

```python
from services.orchestrator import Orchestrator

orch = Orchestrator()
report = orch.run_post_production_stage(context)
# context["post_production_summary"] — aggregate diagnostics
# context["post_production_packages"] — list of PostProductionPackage dicts
# context["unified_packages"][i]["post_production_package"] — per-item slot
```

Distribution order in `run_full_pipeline()`:

```
asset_generation → render → post_production → seo → publish
```

---

## Extension guide

1. Implement `PostProductionProvider` in `providers/post_production/`.
2. Register via `register_post_production_provider()` or add to `ADAPTER_CLASSES`.
3. The engine's `provider_instructions` field tells downstream executors
   which provider handles each operation.
4. Add new export presets in `services/post_production/config.py` `EXPORT_PRESETS`.
5. Add new caption themes in `captions_finalize.py` `_STYLE_PRESETS`.
6. Append fields to `POST_PRODUCTION_PACKAGE_FIELDS` (additive only).

---

## Long-term vision

The Post-Production Engine will eventually edit:

- Shorts and long-form YouTube videos
- Podcasts and educational courses
- Cartoons and animated series
- Feature-length documentaries
- Commercial advertisements and brand campaigns

Productions ranging from seconds to hours, all through the same timeline
model and provider abstraction.

---

## Files

| Path | Role |
|---|---|
| `engines/post_production.py` | ContractEngine façade |
| `services/post_production/models.py` | Field tuples and version pins |
| `services/post_production/config.py` | Tunable behavior |
| `services/post_production/package.py` | PostProductionPackage assembly |
| `services/post_production/editing.py` | Intelligent editing decisions |
| `services/post_production/timeline.py` | Master edit timeline |
| `services/post_production/audio_finalize.py` | Audio mix finalization |
| `services/post_production/captions_finalize.py` | Caption styling |
| `services/post_production/color.py` | Color grading |
| `services/post_production/effects.py` | Transitions and VFX |
| `services/post_production/motion_graphics.py` | Intros, outros, CTAs |
| `services/post_production/platform.py` | Platform optimization |
| `services/post_production/export.py` | Export presets |
| `services/post_production/quality.py` | QC validation |
| `providers/post_production_provider.py` | Provider interface |
| `providers/post_production/mock.py` | Demo Mode provider |
| `tests/test_post_production_engine.py` | Comprehensive test suite |
