# Render & Video Production Engine — Agent 6 (LANDED, mock render)

## Responsibility

Turning approved plans into a render-ready vertical short-form video
package: master timeline assembly, per-scene render instructions, caption
burn-in planning, narration/music/SFX mixing per the audio cue sheet,
transition and motion instructions, asset resolution through swappable
providers, validation with a production readiness score, and a **mock
render** that simulates the real render pass end-to-end. No real MP4 is
produced yet — the architecture and handoff are complete, and real
backends swap in without changing any contract.

## Modules (all under this folder, each independently testable)

| Module | Class | Does |
|---|---|---|
| `engine.py` | `RenderEngine` | ContractEngine (`key="render"`) — the unified façade; `render_ideas()` / `build_render_output()` |
| `models.py` | `RenderJob`, `TimelineSegment` | Contracts: `OUTPUT_FORMAT`, `RENDER_PACKAGE_VERSION`, `TIMELINE_SEGMENT_FIELDS`, `SCENE_RENDER_PLAN_FIELDS`, `RenderStatus`, `RenderJobStatus` |
| `timeline.py` | `TimelineBuilder` | Contiguous, gap-free segment timeline with material references |
| `scene_plans.py` | `SceneRenderer` | Per-scene render instructions (asset type, prompts, footage slots, camera, effects, overlays, sound cues) |
| `assets.py` | `AssetResolver`, `AssetFulfiller` | Resolves asset requests through swappable fulfillers; unavailable sources degrade to placeholders + `missing_assets` |
| `captions.py` | `CaptionRenderer` | Word-by-word/sentence captions, per-word timing map, emphasis, safe area, platform layouts, style presets |
| `audio_mix.py` | `AudioMixer` | Narration/music/SFX/transition tracks, ducking, silence drops, levels, -14 LUFS placeholder |
| `transitions.py` | `TransitionPlanner` | cut/fade/push/zoom/whip_pan/glitch/flash/documentary_slow_zoom/cinematic_push_in/quick_cut |
| `motion.py` | `MotionPlanner` | ken burns / slow zoom / push-in / pan instructions with numeric zoom/pan parameters |
| `packaging.py` | `OutputPackager` | Assembles the final `render_package` dict (additive over the media-production seed) |
| `validator.py` | `RenderValidator` | Pre-flight checks → SUCCESS/WARNING/FAILED/SKIPPED + 0-100 readiness score |
| `renderer.py` | `MockRenderer` | Simulated render: status, mock output path, duration, warnings, missing assets, render log |

The `image` engine (asset resolution) and `video` engine (assembly) in
`engines/image.py` / `engines/video.py` are thin ContractEngines over these
modules — they form the orchestrator's `render` stage. The `render` key is
the standalone façade doing both.

## Input contracts (consumed per idea / ContentPackage)

`script_package` / `structured_script` · `scene_breakdown` ·
`visual_package` (scenes, asset_requests, caption plan) · `audio_package` /
`voice_plan` fields (voice_style, narration_plan, scene_cues, sfx_plan,
music_direction) · `captions` · `thumbnail_plan` · `quality_score` · the
media-production `render_package` seed. Missing layers degrade gracefully:
scenes fall back to the script scene breakdown; a fully unplannable idea
gets a safe mock package (`render_status: SKIPPED`) — never a crash.

## Output contract

Writes `ContentPackage.render_package` (version `"2.0"`, fields documented
in `DATA_CONTRACTS.md` §5): `timeline`, `scene_render_plan`,
`caption_render_plan`, `audio_mix_plan`, `transition_plan`, `motion_plan`,
`asset_requirements`, `missing_assets`, `render_warnings`,
`estimated_render_duration_sec`, `output_format` (9:16 · 1080x1920 · MP4 ·
30fps), `production_readiness_score`, `validation`, `render_status`,
`mock_output_path` / `file_uri`, `render_log`, `render_job`,
`render_manifest`. Context gains `render_summary` (and
`render_assets_summary` from the image engine); matching
`unified_packages` entries get the render package merged and
`status="rendered"` when `render_manifest.ready_for_publishing` is true.
**Add fields only — never remove or rename.**

## Timeline format

`timeline.segments[]` — each segment carries `TIMELINE_SEGMENT_FIELDS`:
`scene_id`, `start_time`, `end_time`, `duration` (contiguous, recomputed
cumulatively), `narration_reference` / `visual_reference` /
`caption_reference` / `audio_reference` (stable `kind/scene_N` lookup keys
into the plan), `transition_in` / `transition_out` (normalized vocabulary),
`motion_effect`, `overlay_text`, `render_status`.

## Future real renderer providers

- **AI image/video generation** — implement `providers/image_provider.py`
  / `providers/video_provider.py` and register via `set_image_provider()`
  / `set_video_provider()`.
- **Licensed stock, user uploads, avatar footage, AI reaction footage** —
  implement an `AssetFulfiller` and `register_fulfiller()` in
  `engines/render/assets.py`. `user_asset`, `avatar`, and `reaction`
  report unavailable today and fall back to placeholders recorded in
  `missing_assets`.
- **Actual encoding** — implement `MockRenderer.render()`'s signature
  against ffmpeg or a cloud renderer; everything upstream/downstream is
  unchanged (the mock already reserves `data/renders/{job_id}/...mp4`).

## How Publishing (Agent 7) consumes this

Gate on `render_manifest.ready_for_publishing` and
`production_readiness_score`; read `file_uri` (mock URI until real
rendering), `duration_sec`, `resolution`, `aspect_ratio`, and `platforms`
to schedule per-platform posts. Treat `render_warnings` / `missing_assets`
as human-review flags. Never mutate render fields — write only to
`publishing_package` and `status`.

## Files Agent 6 may edit

- `engines/render/` (this folder) · `engines/image.py` · `engines/video.py`
- `providers/image_provider.py` · `providers/video_provider.py` · `providers/music_provider.py`
- `tests/test_render_engine.py`

## Files it must NOT touch

`app.py` · `core/workflows.py` · `engines/__init__.py` (append-only, with
review) · `engines/registry.py` · `engines/base.py` · `engines/contracts.py` ·
`services/orchestrator/` · other agents' landing zones · `ui/` layout.

Read `AGENT_WORKFLOW.md`, `ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` before
writing code. Work on `feature/render-engine`.
