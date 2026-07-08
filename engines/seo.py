"""SEO engine — stage 8: optimized metadata for every finished script.

Produces an optimized title, hashtags, keywords, description, and thumbnail
concept per content piece, plus an SEO score. Provider-backed when
available, deterministic heuristics otherwise.
"""

from __future__ import annotations

from core.ai import get_provider
from core.log import get_logger, log_event
from engines.base import Engine
from engines.heuristics import CURIOSITY_WORDS, clamp, content_words, count_hits, stable_jitter

logger = get_logger(__name__)


def seo_score(title: str, keywords: list, hashtags: list, description: str) -> int:
    score = 48
    if 20 <= len(title) <= 60:
        score += 15
    if len(keywords) >= 5:
        score += 10
    if 3 <= len(hashtags) <= 6:
        score += 10
    if 80 <= len(description) <= 320:
        score += 10
    return clamp(score + stable_jitter(title))


class SeoEngine(Engine):
    key = "seo"
    label = "SEO"
    icon = "🔑"
    description = "Optimized titles, hashtags, keywords, descriptions, thumbnails."

    def is_ready(self) -> bool:
        return True

    def run(self, context: dict) -> dict:
        selected = context.get("selected_ideas", [])
        if not selected:
            return {}

        seo_items = self._provider_seo(context, selected)
        if seo_items is None:
            seo_items = [self._heuristic_seo(context, idea) for idea in selected]

        all_keywords = []
        for idea, seo in zip(selected, seo_items):
            idea["title"] = seo["title"]
            idea["hashtags"] = seo["hashtags"]
            idea["keywords"] = seo["keywords"]
            idea["description"] = seo["description"]
            idea["thumbnail_concept"] = seo["thumbnail_concept"]
            idea["seo_score"] = seo_score(seo["title"], seo["keywords"], seo["hashtags"], seo["description"])
            all_keywords.extend(seo["keywords"])

        log_event(logger, "seo.optimized", items=len(selected))
        return {"selected_ideas": selected, "seo_keywords": sorted(set(all_keywords))}

    def _provider_seo(self, context: dict, selected: list) -> "list | None":
        provider = get_provider()
        items = "\n".join(f'{i}. "{idea["title"]}" — {idea["hook"]}' for i, idea in enumerate(selected, 1))
        system = "You are a short-form SEO and packaging expert. Respond with valid minified JSON only."
        user = (
            f"Niche: {context.get('niche', '')}\nSubject: {context.get('subject', '')}\n\n"
            f"Optimize packaging for each video, in order:\n{items}\n\n"
            'Respond with JSON: {"items": [{"title": "optimized <=60 char title", '
            '"hashtags": ["#a", "#b"], "keywords": ["k1", "k2", "k3", "k4", "k5"], '
            '"description": "1-2 sentence description", '
            '"thumbnail_concept": "one sentence thumbnail concept"}]}'
        )
        data, tokens = provider.generate_json(system, user, context.get("model", ""))
        if data is None:
            if provider.name != "demo":
                context["error"] = "AI SEO call failed; used heuristic fallback."
            return None
        context["tokens_used"] = context.get("tokens_used", 0) + tokens
        items_out = data.get("items", [])
        if len(items_out) < len(selected):
            return None
        return items_out

    def _heuristic_seo(self, context: dict, idea: dict) -> dict:
        subject = context.get("subject", "content")
        niche = context.get("niche", "General Content")
        title = idea["title"]
        if len(title) > 60:
            title = title[:57].rstrip() + "..."
        if count_hits(title, CURIOSITY_WORDS) == 0 and "?" not in title:
            suffix = " — The Truth"
            title = (title[: 60 - len(suffix)].rstrip() + suffix) if len(title) + len(suffix) > 60 else title + suffix

        keywords = list(dict.fromkeys(
            [word for word in subject.lower().split() if len(word) > 2]
            + content_words(idea["hook"])[:3]
            + [niche.lower(), "shorts", "viral"]
        ))[:8]

        niche_tag = "#" + niche.replace(" ", "").replace("&", "")
        subject_tag = "#" + "".join(part.title() for part in subject.split()[:2])
        hashtags = [niche_tag, subject_tag, "#Shorts", f"#{keywords[0].title()}" if keywords else "#Viral"]
        hashtags = list(dict.fromkeys(hashtags))[:5]

        description = (
            f"{idea['hook']} We break down {subject} in under 30 seconds — "
            f"the {niche.lower()} insight most people never hear. Watch to the end for the payoff."
        )
        thumbnail = (
            f"3-word bold text '{(idea.get('angle') or subject).upper()}' beside a high-contrast "
            f"close-up reaction face, {niche} color palette."
        )
        return {
            "title": title,
            "hashtags": hashtags,
            "keywords": keywords,
            "description": description,
            "thumbnail_concept": thumbnail,
        }
