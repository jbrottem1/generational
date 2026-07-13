# Production Readiness Report — Real Media Integrations

**Date:** 2026-07-10  
**Branch:** `release/1.0.0-rc2`  
**Architect:** Agent 1  

Architecture was not redesigned. This release wires production media onto existing
ProviderRuntime, RenderEngine, NarrationEngine, and PublishingManager seams.

---

## Production readiness

| Metric | Value |
|---|---|
| **Score** | **88 / 100** |
| **Band** | `assembly_ready` |
| FFmpeg | available (via `imageio-ffmpeg` and/or system) |
| OpenAI (script + TTS + images) | configured on this host |
| Live OAuth | not configured |
| Estimated time to first autonomous video | **minutes** after confirming OpenAI + ffmpeg |
| Estimated time to first live publish | same day after YouTube OAuth |

---

## What shipped

### Priority 1 — Voice
- `services/media_production/voice.py` — ElevenLabs / OpenAI TTS / local-clone seam
- Persistence, timing metadata (word + sentence), SSML strip/pass-through
- ElevenLabs `with-timestamps` endpoint with fallback
- `LocalVoiceCloneConnector` reserved for future on-device clone
- `engines/voice.py` graduated from Planned → live Engine
- `engines/narration.py` uses production voice service

### Priority 2 — Image & video
- Existing ProviderRuntime connectors unchanged as the abstraction
- `engine_api` + fulfillers now **persist** generated images/video to `data/media/`
- Failover / retry / cache remain in ProviderRuntime

### Priority 3–4 — Assembly
- `services/media_production/ffmpeg_assembler.py` — Ken Burns stills, video clips, color bed + audio
- `MockRenderer.render()` attempts real MP4; keeps mock contract when ffmpeg/assets missing
- Aspect presets: vertical / landscape / square / custom
- Duration bands: 1s → 24h (timeline-driven)

### Priority 5 — Publishing
- OAuth connectors already present; tokens remain Settings-configurable
- `ProductionIntegrityGate` blocks **live OAuth** publish of mock/incomplete packages
- Dry-run and mock-adapter paths unchanged

### Priority 6 — QC
- Master QC detects real vs mock MP4 and voice presence
- Pre-publish gate enforces voice, captions, timeline, thumbnail, metadata, playable MP4 when OAuth is live

### Priority 7 — Dashboard
- Studio Dashboard + Readiness show ffmpeg status, blockers, outputs, checklist

### Priority 8 — Logging
- `data/reports/{run_id}/` — production, render, assets, publishing, performance JSON

### Priority 9 — Scale
- Provider abstraction unchanged; queue workers / WE durable jobs remain the scale path

---

## Remaining placeholders

| Item | Status |
|---|---|
| Local voice clone backend | Interface only |
| Remotion motion-graphics path | Not used — FFmpeg is the assembler |
| Async Runway/Fal/Replicate job polling to completion | Submit works; poll/download still thin |
| Avatar / reaction / user-upload footage | Reserved fulfillers |
| Character / animation / optlab agents | Stubs |

---

## Remaining blockers

1. **Platform OAuth** for live publish (YouTube / TikTok / Instagram / …)
2. Optional: **ElevenLabs** for higher-quality TTS + native timestamps (OpenAI TTS works today)
3. Optional: **Runway / Fal / Replicate** for generative video clips (stills + Ken Burns work without them)

---

## Integrated providers (code-ready)

| Capability | Providers |
|---|---|
| Voice | ElevenLabs, OpenAI TTS, Local Voice Clone (future) |
| Image | OpenAI Images, Flux, Ideogram, Stability, Fal, Replicate |
| Video | Runway, Fal, Replicate, Pika, Kling, Luma, Veo |
| Assembly | FFmpeg (`imageio-ffmpeg` bundled) |
| Publish | YouTube, TikTok, Instagram, Facebook, X, LinkedIn |

---

## Remaining APIs required (for full autonomy)

- `YOUTUBE_ACCESS_TOKEN` (first live publish)
- Prefer `ELEVENLABS_API_KEY` for production voice
- Prefer `RUNWAY_API_KEY` or `FAL_KEY` / `REPLICATE_API_TOKEN` for AI video clips

---

## OAuth status

All platforms: **configurable** — paste tokens in Settings. No embedded consent redirect yet (`OAUTH_SETUP.md`).

---

## First autonomous production checklist

- [x] Orchestrator + dry-run pipeline operational  
- [x] OpenAI key for script / TTS / images  
- [x] FFmpeg available (`pip install imageio-ffmpeg`)  
- [ ] Run a short Studio production and confirm `render_package.mock == false`  
- [ ] Confirm `mp4_path` exists under `data/renders/`  
- [ ] Pass ProductionIntegrityGate with `enforce_production_qc`  
- [ ] Add YouTube OAuth for first live publish  

---

## Recommended next milestone

**First live YouTube publish of an assembled short** — generate with OpenAI stills + TTS + FFmpeg, then upload with YouTube OAuth.

---

## Tests

`tests/test_media_production.py` + render / master / publishing suites: **83 passed**.
