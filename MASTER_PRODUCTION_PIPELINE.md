# Master Production Pipeline — Agent 1 Status (RC)

**Date:** 2026-07-10  
**Branch target:** `release/1.0.0-rc2`  
**Canonical path:** Studio → Workflow Executor → Orchestrator → Engines → ProviderRuntime  

No stage bypasses the Orchestrator. This release adds a live registry, contract
normalization, QC, and a master-pipeline façade over existing systems.

---

## Live registry snapshot

| Metric | Value |
|---|---|
| Agents (1–23) | 23 |
| Agents ready / service-complete | 16 |
| Agents partial | 5 |
| Agents stub / reserved / worktree | 5 |
| Engines registered | 44 |
| Engines ready | 39 |

---

## Master stage map → Orchestrator

User Prompt → Executive Intelligence (trend) → Topic Research → Creative Planning
(psychology) → Script → Storyboard (attention) → Scene/Visual → Audio plan →
Refinement → Quality → Production packaging → Content packaging → AI Director →
Creative Studio → Character/IP (optional stub) → Asset Generation → Animation
(optional stub) → Render → Post → SEO/Captions/Thumb/Meta → Optimization
(optional stub) → Publish → Analytics → Learning → Executive Review.

---

## Dry-run verification (2026-07-10)

Prompt: *Create one 20 second educational short about bioluminescence for YouTube Shorts*

| Check | Result |
|---|---|
| Workflow status | `completed` |
| Stages reported | 23 |
| Failed stages | 0 |
| Ideas | 20 |
| Unified packages | 20 |
| Demo Mode | False (OpenAI live) |
| QC | passed, score 100 |
| Render | **mock** (honest — no MP4 claimed) |
| Publish mode | dry_run |

---

## Provider connections

| Provider | Status |
|---|---|
| OpenAI | connected |
| Anthropic | connected (model routing fixed) |
| Gemini / ElevenLabs / Runway / Flux / Fal / Replicate / Ideogram | configurable (missing keys) |
| YouTube / TikTok / Instagram / Facebook / LinkedIn / X | configurable (OAuth missing) |

---

## Production readiness

**Score: 72 / 100 — `architecture_ready`**

### Blockers for finished MP4 / live publish
1. Real TTS (ElevenLabs or OpenAI TTS wiring)
2. Real video/image provider (Runway / Fal / Replicate / BFL)
3. OAuth for live publish (dry-run available)

### Estimates
- **First production (dry-run / mock render):** immediate  
- **First live publish:** same day after media keys + OAuth  

### Next priorities
1. Wire ElevenLabs / OpenAI TTS into voice fulfillers  
2. Wire Runway/Fal/Replicate into `engines/render/assets.py`  
3. YouTube OAuth for first live publish  
4. Merge character / animation / optlab stubs only when product needs them  

---

## Short-form / long-form

| Mode | Durations / platforms | Status |
|---|---|---|
| Short-form | 15 / 30 / 60 / 90s · Shorts / TikTok / Reels | Executable via WE (`youtube_short`) |
| Long-form | 5–60 min · documentary / podcast / course | WE templates + durable jobs; render still short-form oriented |

---

## API

```python
from services.master_pipeline import (
    run_master_production,
    production_readiness_report,
    live_agent_registry,
    registry_summary,
)

result = run_master_production(
    "Create a 30 second Short about …",
    platform="youtube_shorts",
    duration_sec=30,
    publish_mode="dry_run",
)
```

Studio → **Readiness** tab shows the Master Pipeline score and blockers.
