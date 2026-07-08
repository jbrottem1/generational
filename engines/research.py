"""Research engine — stage 1 of the intelligence pipeline.

Parses the command, then builds a research brief: topic context, target
audience, search intent, trend strength, and a summary. Uses the AI provider
when available; otherwise deterministic heuristics keyed to the niche and
subject.
"""

from __future__ import annotations

from core import parsing
from core.ai import get_provider, is_demo_mode
from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import clamp, stable_jitter

logger = get_logger(__name__)

AUDIENCES = {
    "Psychology": "Self-improvement viewers, 18-34",
    "AI & Future Tech": "Tech-curious early adopters, 18-40",
    "Dark History": "History and mystery fans, 20-45",
    "Space": "Science and space enthusiasts, 16-40",
    "Finance": "Aspiring investors and savers, 20-40",
    "Health": "Wellness-focused viewers, 20-45",
    "Science": "Curious science lovers, 16-40",
    "General Content": "Curious short-form viewers, 16-40",
}


def _detect_search_intent(command: str) -> str:
    lower = command.lower()
    if "how" in lower:
        return "Instructional (how-to)"
    if "why" in lower or "what" in lower:
        return "Informational curiosity"
    if "story" in lower or "history" in lower:
        return "Narrative discovery"
    return "Entertainment discovery"


class ResearchEngine(Engine):
    key = "research"
    label = "Research"
    icon = "🔍"
    description = "Topic context, audience, search intent, and trend strength."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        command = context["command"]
        niche = parsing.detect_niche(command)
        video_count = parsing.detect_video_count(command)
        subject = parsing.detect_subject(command, fallback=niche.lower())
        goal = parsing.build_goal(subject)

        research = self._provider_research(context, command, niche, subject)
        if research is None:
            research = self._heuristic_research(command, niche, subject)

        log_event(
            logger, "research.completed",
            niche=niche, subject=subject, trend=research["trend_strength"],
            opportunity=research["opportunity_score"],
        )
        return {
            "niche": niche,
            "video_count": video_count,
            "subject": subject,
            "goal": goal,
            "demo_mode": is_demo_mode(),
            "research": research,
        }

    def _provider_research(self, context: dict, command: str, niche: str, subject: str) -> "dict | None":
        provider = get_provider()
        system = (
            "You are a short-form content research analyst. "
            "Respond with valid minified JSON only."
        )
        user = (
            f'Command: "{command}"\nNiche: "{niche}"\nSubject: "{subject}"\n\n'
            "Build a research brief. Respond with JSON exactly like:\n"
            '{"topic_context": "2-3 sentences of essential context",'
            ' "audience": "short audience description",'
            ' "search_intent": "primary search intent",'
            ' "trend_strength": 0-100 integer,'
            ' "summary": "3-4 sentence research summary"}'
        )
        data, tokens = provider.generate_json(system, user, context.get("model", ""))
        if data is None:
            if provider.name != "demo":
                context["error"] = "AI research call failed; used heuristic fallback."
            return None
        context["tokens_used"] = context.get("tokens_used", 0) + tokens
        trend = clamp(int(data.get("trend_strength", 60)), 5, 98)
        return {
            "topic_context": data.get("topic_context", ""),
            "audience": data.get("audience", AUDIENCES.get(niche, AUDIENCES["General Content"])),
            "search_intent": data.get("search_intent", _detect_search_intent(command)),
            "trend_strength": trend,
            "summary": data.get("summary", ""),
            "opportunity_score": self._opportunity(trend, niche),
        }

    def _heuristic_research(self, command: str, niche: str, subject: str) -> dict:
        trend = clamp(58 + stable_jitter(subject, 38), 5, 98)
        audience = AUDIENCES.get(niche, AUDIENCES["General Content"])
        intent = _detect_search_intent(command)
        context_text = (
            f"{subject.title()} sits in the {niche} niche, where short, punchy explainers "
            f"consistently outperform generic takes. The strongest angle is a specific, "
            f"counterintuitive claim delivered in the first 3 seconds."
        )
        summary = (
            f"Audience: {audience}. Intent: {intent}. Trend strength for '{subject}' "
            f"scores {trend}/100 right now. Recommended approach: lead with a "
            f"curiosity-gap hook, keep each video to one concrete insight, and end "
            f"with a payoff that rewards watching to the end."
        )
        return {
            "topic_context": context_text,
            "audience": audience,
            "search_intent": intent,
            "trend_strength": trend,
            "summary": summary,
            "opportunity_score": self._opportunity(trend, niche),
        }

    @staticmethod
    def _opportunity(trend: int, niche: str) -> int:
        competition = 35 + stable_jitter(niche, 30)
        return clamp(0.7 * trend + 0.3 * (100 - competition), 5, 98)
