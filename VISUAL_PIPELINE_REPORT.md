# VISUAL PIPELINE REPORT

- Generated: 2026-07-22T05:16:37.069192+00:00
- Title: Why Octopuses Have Three Hearts
- Overall: **PASS**
- Scenes passed: **3 / 3**
- Final MP4: `data/renders/0e2a22a585be/why-octopuses-have-three-hearts_1080x1920.mp4` (3,578,940 bytes)
- Assembly: `visual_count=3`, Ken Burns per scene, **no color bed**

## 1. Root cause of blank screens

Demo/mock image generation returned `success=True` with fake URIs (`runtime://image/demo`) and **no bytes on disk**. Persistence silently skipped those URIs. The FFmpeg assembler then found `visuals=[]` and substituted:

```text
lavfi color=c=0x101820  →  solid navy blank MP4
```

Historical census on this branch: ~627/637 assemblies logged `color_bed→mp4`.

**Break point:** MEDIA GENERATION → MEDIA DOWNLOAD/STORAGE  
Assets stopped existing as real files immediately after ProviderRuntime demo adapters “succeeded.”

## 2. Scene audit

| Scene | Narration | Expected Visual | Actual Visual | Provider | Generation Prompt | Storage Path | Resolution | File Size | Timeline Ref | Renderer Ref | Result |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | This animal has three hearts. | Photorealistic octopus underwater | `scene_1_octopus_*.jpg` | wikimedia_curated | Photorealistic octopus underwater… | `data/media/images/…` | 1080x1920 | 394234 | yes | yes | **PASS** |
| 2 | Two pump blood through the gills… | Educational circulatory still | `scene_2_octopus_*.jpg` | wikimedia_curated | Realistic octopus anatomy… | `data/media/images/…` | 1080x1920 | 394234 | yes | yes | **PASS** |
| 3 | When an octopus swims… | Octopus crawl/swim documentary | `scene_3_octopus_*.jpg` | wikimedia_curated | Photorealistic octopus crawling… | `data/media/images/…` | 1080x1920 | 394234 | yes | yes | **PASS** |

## Failures

- none

## 3. Repaired subsystems / modified files

| Subsystem | File | Repair |
| --- | --- | --- |
| Image runtime contract | `services/provider_runtime/engine_api.py` | Reject demo/mock “success”; require persisted bytes |
| OpenAI Images | `services/provider_runtime/connectors/image.py` | Prefer `b64_json` for durable persistence |
| Persistence | `services/media_production/persistence.py` | Clear fake URIs; require ≥1KB files |
| Asset resolver | `engines/render/assets.py` | AI → photographic fallback → fail closed |
| Image engine | `engines/image.py` | Attach validated assets onto scenes |
| Scene plans | `engines/render/scene_plans.py` | Prefer scene `resolved_asset` |
| Validator | `engines/render/validator.py` | Blocking `scenes_have_validated_media` |
| Renderer | `engines/render/renderer.py` | QA gate before assemble; no fake COMPLETE |
| Assembler | `services/media_production/ffmpeg_assembler.py` | Color bed rejected unless explicit test flag |
| Asset production | `services/asset_production/executor.py` | Photographic fallback; cinematic gradients off by default |
| Visual QA (new) | `services/media_production/visual_qa.py` | Fail-closed audit + report writer |
| Photo fallback (new) | `services/media_production/photographic_fallback.py` | Wikimedia / Reality catalog approved stills |
| E2E harness (new) | `scripts/octopus_visual_pipeline_e2e.py` | Octopus production proof |
| Tests | `tests/test_visual_pipeline_repair.py`, updated render/media tests | Contract coverage |

## 4. Visual pipeline architecture (repaired)

```text
SCRIPT / SCENES
    ↓
VISUAL REQUIREMENTS + IMAGE PROMPTS
    ↓
IMAGE GENERATION (ProviderRuntime — real connectors only)
    ↓ (if no bytes)
APPROVED PHOTOGRAPHIC FALLBACK (Reality catalog / Wikimedia)
    ↓
PERSIST → data/media/images/*.jpg|png   (≥1KB, real file)
    ↓
ASSET RESOLVER / IMAGE ENGINE  → scene.resolved_asset
    ↓
VISUAL QA (fail closed if any scene invalid)
    ↓
TIMELINE + MOTION (Ken Burns / pan)
    ↓
FFMPEG ASSEMBLER  (refuses color beds)
    ↓
FINAL MP4 with continuous photographic storytelling
```

## 5. Remaining known issues

1. Without `OPENAI_API_KEY` / image provider keys, scenes use **approved photographic fallback** (real photos), not unique AI-generated art per beat.
2. Curated Wikimedia matching can reuse the same octopus photograph across scenes when keywords collide — visual continuity exists, but shot diversity is limited.
3. Character/Doctor animation systems are separate (`animation` engine still not ready) and were out of scope for this visual-media repair.
4. Legacy productions under `data/productions/*` that already color-bedded are not rewritten; new renders are gated.

## 6. Phase 2 recommendations

1. Require OpenAI Images (or Flux/Ideogram) credentials in production profiles and assert non-fallback rate ≥ 80%.
2. Diversify photographic fallback queries per scene (heart/gills/swim keywords) and cache unique Commons results.
3. Add perceptual “not-near-solid-color” QA using frame sampling before publish.
4. Wire Doctor/character animation assets into `resolved_asset` once the animation engine is production-ready.
5. Backfill a one-shot re-render job for historical color-bed MP4s that still lack validated media.

## Extra diagnostics

- **render_status**: SUCCESS
- **mp4_path**: data/renders/0e2a22a585be/why-octopuses-have-three-hearts_1080x1920.mp4
- **image_resolved**: 3
- **image_missing**: 0
- **frame_sample_entropy**: high (not a solid color; extracted frame ~4.4MB)
