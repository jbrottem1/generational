"""Final Quality engine — stage 9: score every piece and apply the publish gate.

Computes, per content piece:
- Opportunity Score (from research trend/competition)
- SEO Score (from the SEO engine)
- Psychology Score (from the psychology engine)
- Retention Prediction (psychology retention x post-revision critic score)
- CTR Prediction (curiosity/surprise x packaging quality)
- Overall Publish Score (weighted blend)

Anything below the configurable publish threshold is marked unpublishable —
the future publishing engine refuses to post it.
"""

from __future__ import annotations

from core.constants import DEFAULT_PUBLISH_THRESHOLD
from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import clamp

logger = get_logger(__name__)

PUBLISH_WEIGHTS = {
    "opportunity": 0.20,
    "seo": 0.20,
    "psychology": 0.25,
    "retention": 0.20,
    "ctr": 0.15,
}


class QualityEngine(Engine):
    key = "quality"
    label = "Quality"
    icon = "✅"
    description = "Final quality scoring and the publish-threshold gate."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        threshold = context.get("threshold", DEFAULT_PUBLISH_THRESHOLD)
        opportunity = context.get("research", {}).get("opportunity_score", 60)

        publishable_count = 0
        for idea in selected:
            psychology = idea.get("psychology", {})
            psychology_score = idea.get("psychology_score", 50)
            seo = idea.get("seo_score", 50)
            critic = idea.get("critique", {}).get("score", 70)

            retention = clamp(0.55 * psychology.get("retention_potential", 50) + 0.45 * critic)
            ctr = clamp(
                0.5 * psychology.get("curiosity", 50)
                + 0.3 * psychology.get("surprise", 50)
                + 0.2 * seo
            )
            publish = clamp(
                PUBLISH_WEIGHTS["opportunity"] * opportunity
                + PUBLISH_WEIGHTS["seo"] * seo
                + PUBLISH_WEIGHTS["psychology"] * psychology_score
                + PUBLISH_WEIGHTS["retention"] * retention
                + PUBLISH_WEIGHTS["ctr"] * ctr
            )

            idea["scores"] = {
                "opportunity": opportunity,
                "seo": seo,
                "psychology": psychology_score,
                "retention": retention,
                "ctr": ctr,
                "publish": publish,
            }
            idea["publishable"] = publish >= threshold
            publishable_count += idea["publishable"]

        log_event(
            logger, "quality.gated",
            scored=len(selected), publishable=publishable_count, threshold=threshold,
        )
        return {
            "ideas": selected,
            "quality_summary": {
                "threshold": threshold,
                "publishable": publishable_count,
                "held": len(selected) - publishable_count,
            },
        }
