# RENDER FAILURE ANALYSIS

Generated: `2026-07-14T12:45:03.547591+00:00`

## Pre-fix root cause (pilot 0% MP4)

Every launch pilot reached Rendering in ~3ms with scenes present, but `AssetResolver` left `runtime://` / `mock://` placeholders. `assemble_mp4` correctly refused color-bed encodes → `mp4_path` empty → export warned `mp4_not_yet_materialized`.

## Post-fix failures

Failed MP4s in this batch: **0 / 10**

None — all validation productions produced a playable MP4.

## Renderer path

`engines/video` → `engines/render/engine.build_render_output` → `MockRenderer.render` → `services.media_production.ffmpeg_assembler.assemble_mp4`

