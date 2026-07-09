"""Visual Intelligence Engine — the visual brain of the pipeline.

Runs immediately after Script Generation and before the Attention Graph:
every scripted candidate receives a complete **Visual Production Package**
before ranking happens, so downstream stages weigh visual craft — not just
concept psychology and script quality — and every future renderer (voice,
audio, image, video) consumes one canonical visual plan.

Each package contains:

- Scene-by-scene storyboard with full visual grammar per scene (purpose,
  emotion, length, camera angle + motion, shot composition, subject
  placement, lighting, environment, palette, transitions, motion intensity,
  zoom, background, overlays, caption timing, SFX, music style, B-roll)
- 12-dimension visual psychology scores per scene (curiosity, mystery,
  wonder, fear, beauty, novelty, scale, contrast, motion, satisfaction,
  humor, identity) blended into a Scene Visual Score
- Model-ready AI image prompts (Midjourney, Flux, Stable Diffusion, DALL-E,
  OpenAI Images) and AI video prompts (Runway, Veo, Pika, Luma, Kling, Sora)
- Five scored thumbnail concepts with expected CTR
- The strongest five-frame first-3-second hook sequence with a scroll-stop
  rationale
- Caption plan, visual pacing report, camera plan, transitions, and motion
  report
- One weighted **Overall Visual Score (0-100)**

Planning is delegated to the modular `services/visual` package, which is
equally usable standalone to re-plan visuals for any approved idea. All
planning is deterministic — Demo Mode carries the full engine, and swapping
in vision-model scoring later never changes the package contract.
"""

from __future__ import annotations

from core.log import get_logger, log_event
from engines.base import Engine
from services.visual import build_visual_package
from services.scripts import DEFAULT_PLATFORM, get_platform_spec

logger = get_logger(__name__)


class VisualIntelligenceEngine(Engine):
    key = "visual_intelligence"
    label = "Visual Intelligence"
    icon = "🎥"
    description = (
        "Transform every scripted candidate into a complete Visual Production "
        "Package — storyboard, per-scene visual psychology scores, AI image/video "
        "prompts, scored thumbnails, hook sequence, and an Overall Visual Score (0-100)."
    )

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        candidates = context.get("candidates", [])
        if not candidates:
            return {}

        spec = get_platform_spec(context.get("target_platform", DEFAULT_PLATFORM))
        niche = context.get("niche", "")
        subject = context.get("subject", "")

        for candidate in candidates:
            package = build_visual_package(
                candidate,
                niche=niche,
                subject=subject,
                aspect_ratio=spec.aspect_ratio,
            )
            candidate["visual_package"] = package
            candidate["visual_score"] = package["visual_score"]
            # Best thumbnail direction feeds packaging; SEO's later concept
            # text is never overwritten — this is the art-directed complement.
            candidate["thumbnail_concepts"] = package["thumbnails"]

        scores = [candidate["visual_score"] for candidate in candidates]
        avg_score = round(sum(scores) / len(scores), 1)
        total_scenes = sum(len(c["visual_package"]["scenes"]) for c in candidates)

        log_event(
            logger,
            "visual_intelligence.planned",
            candidates=len(candidates),
            scenes=total_scenes,
            avg_visual_score=avg_score,
        )
        return {
            "candidates": candidates,
            "visual_intelligence_summary": {
                "planned": len(candidates),
                "total_scenes": total_scenes,
                "average_visual_score": avg_score,
                "aspect_ratio": spec.aspect_ratio,
                "platform": spec.key,
            },
        }
