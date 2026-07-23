"""Self-Optimization API — every engine queries historical knowledge here.

Examples:
  optimize.for_script(topic) → best opening hooks
  optimize.for_psychology(topic) → curiosity patterns
  optimize.for_seo(topic) → winning titles
  optimize.for_visual(topic) → pacing / thumbnail styles
  optimize.for_animation(topic) → camera movements
  optimize.for_voice(topic) → narration speed / voice styles
  optimize.for_discovery() → niche opportunity scores
"""

from __future__ import annotations

from typing import Any

from services.analytics.store import get_analytics_store
from services.learning.consult import build_learning_brief
from services.learning.patterns import mine_patterns
from services.learning.recommendations import build_recommendations, guidance_for_engine


class SelfOptimizationAPI:
    """Stable query surface for upstream engines."""

    def brief(self, topic: str, **kwargs) -> dict[str, Any]:
        return build_learning_brief(topic, **kwargs)

    def for_script(self, topic: str = "") -> dict[str, Any]:
        g = self._guidance("script_generation")
        return {
            "question": "What opening historically performs best for this topic?",
            "winning_hooks": g.get("winning_hooks") or [],
            "preferred_lengths": g.get("preferred_lengths") or [],
            "preferred_topics": g.get("preferred_topics") or [],
            "recommendations": g.get("recommendations") or [],
            "topic": topic,
        }

    def for_psychology(self, topic: str = "") -> dict[str, Any]:
        g = self._guidance("psychology")
        return {
            "question": "What curiosity pattern creates the highest retention?",
            "preferred_strategies": g.get("preferred_strategies") or [],
            "avoided_strategies": g.get("avoided_strategies") or [],
            "winning_hooks": g.get("winning_hooks") or [],
            "recommendations": g.get("recommendations") or [],
            "topic": topic,
        }

    def for_seo(self, topic: str = "") -> dict[str, Any]:
        g = self._guidance("seo_optimization")
        return {
            "question": "What titles historically generated the most search traffic?",
            "winning_titles": g.get("winning_titles") or [],
            "winning_keywords": g.get("winning_keywords") or [],
            "best_posting_hours": g.get("best_posting_hours") or [],
            "recommendations": g.get("recommendations") or [],
            "topic": topic,
        }

    def for_visual(self, topic: str = "") -> dict[str, Any]:
        g = self._guidance("visual_intelligence")
        return {
            "question": "What visual pacing maximizes completion rate?",
            "winning_thumbnail_styles": g.get("winning_thumbnail_styles") or [],
            "recommendations": g.get("recommendations") or [],
            "topic": topic,
        }

    def for_animation(self, topic: str = "") -> dict[str, Any]:
        g = self._guidance("cinematography")
        return {
            "question": "What camera movement best supports this narration?",
            "recommendations": g.get("recommendations") or [],
            "topic": topic,
        }

    def for_voice(self, topic: str = "") -> dict[str, Any]:
        g = self._guidance("voice_audio")
        return {
            "question": "What narration speed performs best for this audience?",
            "winning_voice_styles": g.get("winning_voice_styles") or [],
            "preferred_lengths": g.get("preferred_lengths") or [],
            "recommendations": g.get("recommendations") or [],
            "topic": topic,
        }

    def for_discovery(self) -> dict[str, Any]:
        g = self._guidance("trend_discovery")
        recs = g.get("recommendations") or []
        niches = [r for r in recs if r.get("dimension") in ("niche", "topic")]
        return {
            "question": "What niche currently offers the highest opportunity score?",
            "top_niches": [
                r.get("value") for r in niches if r.get("evidence", {}).get("lift", 0) > 0
            ][:10],
            "avoid_niches": [
                r.get("value") for r in niches if r.get("evidence", {}).get("lift", 0) < 0
            ][:10],
            "recommendations": niches,
        }

    def for_evidence(self, topic: str = "") -> dict[str, Any]:
        return {
            "question": "What evidence modalities historically support retention?",
            "recommendations": self._guidance("evidence_intelligence").get("recommendations") or [],
            "topic": topic,
        }

    def _guidance(self, engine_key: str) -> dict:
        records = get_analytics_store().list_records()
        recommendations = build_recommendations(mine_patterns(records))
        return guidance_for_engine(engine_key, recommendations)


_API: SelfOptimizationAPI | None = None


def get_optimization_api() -> SelfOptimizationAPI:
    global _API
    if _API is None:
        _API = SelfOptimizationAPI()
    return _API


def for_script(topic: str = "") -> dict:
    return get_optimization_api().for_script(topic)


def for_psychology(topic: str = "") -> dict:
    return get_optimization_api().for_psychology(topic)


def for_seo(topic: str = "") -> dict:
    return get_optimization_api().for_seo(topic)


def for_visual(topic: str = "") -> dict:
    return get_optimization_api().for_visual(topic)


def for_animation(topic: str = "") -> dict:
    return get_optimization_api().for_animation(topic)


def for_voice(topic: str = "") -> dict:
    return get_optimization_api().for_voice(topic)


def for_discovery() -> dict:
    return get_optimization_api().for_discovery()
