"""Visual Intelligence Engine — the Cinematic AI Director of the pipeline.

Runs after Script Generation and the Attention Graph: every scripted
candidate receives a complete **Visual Production Package** before ranking,
so downstream stages weigh visual craft — not just concept psychology and
script quality — and every future renderer (voice, audio, image, video)
consumes one canonical, directed visual plan.

Inputs consumed per candidate (all structured, none re-derived):

- **Trend Discovery / Research** — niche + subject context
- **Psychology Engine** — concept-level psychology signals
- **Script Engine** — the canonical `structured_script` handoff
- **Attention Graph** — hook/retention scores feeding retention prediction

Each package contains:

- Directed scene list — purpose, emotion, attention level, professional
  shot type with lens + depth of field, composition, subject placement,
  lighting, style-preset palette, transitions, motion recommendation,
  recommended asset source, base AI image/video prompts, stock footage
  query, overlays, caption placement + timing, SFX timing, B-roll, and a
  thumbnail-candidate flag
- 12-trigger visual psychology scores per scene (curiosity, pattern
  interrupt, contrast, novelty, human faces, eye contact, motion, scale,
  speed, emotional color, negative space, visual hierarchy) plus a
  **predicted retention** per scene and a retention curve
- Professional shot list and provider-agnostic asset requests (adapters —
  never a hardcoded provider)
- Model-ready AI image prompts (Midjourney, Flux, Stable Diffusion, DALL-E,
  OpenAI Images) and AI video prompts (Runway, Veo, Pika, Luma, Kling, Sora)
- Five thumbnail concepts with title overlay, emotion, color strategy,
  focal subject, eye direction, contrast score, and click probability
- The five-frame first-3-second hook sequence with a scroll-stop rationale
- Caption plan, pacing / camera / transition / motion reports
- A machine-consumable **Render Package** for the future Render Engine
- One weighted **Overall Visual Score (0-100)**

Style presets (`register_style`) and asset sources (`register_source`) are
runtime-extensible — future engines add both without changing this engine.
All planning is deterministic — Demo Mode carries the full Director, and
swapping in vision-model scoring later never changes the package contract.
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
        "Direct every scripted candidate like an AI film director — directed "
        "shot list, style presets, per-scene retention prediction, AI image/video "
        "prompts, asset sourcing, scored thumbnails, and a render-ready package."
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
        style_key = context.get("visual_style", "")  # optional operator/brand override

        for candidate in candidates:
            package = build_visual_package(
                candidate,
                niche=niche,
                subject=subject,
                aspect_ratio=spec.aspect_ratio,
                style_key=style_key,
                attention=candidate.get("attention_graph"),
            )
            candidate["visual_package"] = package
            candidate["visual_score"] = package["visual_score"]
            # Best thumbnail direction feeds packaging; SEO's later concept
            # text is never overwritten — this is the art-directed complement.
            candidate["thumbnail_concepts"] = package["thumbnails"]

        scores = [candidate["visual_score"] for candidate in candidates]
        avg_score = round(sum(scores) / len(scores), 1)
        total_scenes = sum(len(c["visual_package"]["scenes"]) for c in candidates)
        avg_retention = round(
            sum(c["visual_package"]["retention_curve"]["average_retention"] for c in candidates)
            / len(candidates),
            1,
        )

        log_event(
            logger,
            "visual_intelligence.planned",
            candidates=len(candidates),
            scenes=total_scenes,
            avg_visual_score=avg_score,
            avg_predicted_retention=avg_retention,
        )
        return {
            "candidates": candidates,
            "visual_intelligence_summary": {
                "planned": len(candidates),
                "total_scenes": total_scenes,
                "average_visual_score": avg_score,
                "average_predicted_retention": avg_retention,
                "style": candidates[0]["visual_package"]["visual_style"],
                "aspect_ratio": spec.aspect_ratio,
                "platform": spec.key,
            },
        }
