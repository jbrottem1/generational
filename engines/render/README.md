# Landing Zone — Agent 6: Render & Video Production

## What this engine owns
Turning approved plans into pixels: asset generation/collection, timeline
assembly, narration/music/SFX mixing per the audio cue sheet, subtitle
burn-in, and the final rendered video per platform spec.

## Files Agent 6 may edit
- `engines/render/` (this folder — implementation modules live here)
- `engines/image.py`, `engines/video.py` (upgrade the planned stubs)
- `services/rendering/` (create if needed for heavy logic)
- `providers/image_provider.py`, `providers/video_provider.py`, `providers/music_provider.py`
- `tests/test_render_engine.py` (create)

## Contracts it must use
- Subclass `engines.contracts.ContractEngine`; keep engine keys `image` / `video`.
- Input: `ContentPackage.visual_package`, `.audio_package`, `.script_package`,
  `.captions`, and the media-production `render_package` seed.
- Output: write results into `ContentPackage.render_package`
  (file URI, duration, resolution, aspect ratio, render manifest) and set
  `status="rendered"`. **Add fields only — never remove or rename.**
- Vendor SDKs (ffmpeg wrappers, cloud renderers) go behind provider
  interfaces in `providers/` — never imported by engine logic directly.

## Outputs it must return
A populated `render_package` dict per approved ContentPackage plus a
`StageReport`-compatible engine result (the orchestrator handles status).

## Files it must NOT touch
`app.py` · `core/workflows.py` · `engines/__init__.py` (append-only, with
review) · `engines/registry.py` · `engines/base.py` · `engines/contracts.py` ·
`services/orchestrator/` · other agents' landing zones · `ui/` layout.

Read `AGENT_WORKFLOW.md`, `ORCHESTRATOR.md`, and `DATA_CONTRACTS.md` before
writing code. Work on `feature/render-engine`.
