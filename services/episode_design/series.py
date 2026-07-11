"""SeriesDesign planner — mini-series, seasons, sequencing, callbacks,
recurring elements, and visual + educational continuity.
"""

from __future__ import annotations

import re

_DEFAULT_RECURRING = [
    "signature curiosity hook phrase",
    "visual style consistent color palette",
    "end-of-episode question card",
]

_NUMBERING_SCHEMES = {
    "mini_series": "Part {n}/{total}",
    "season": "S{season}E{n}",
    "anthology": "#{n}",
    "standalone": None,
}


def _infer_series_type(item: dict, context: dict) -> str:
    """Infer whether this item is part of a series or standalone."""
    series_hint = str(item.get("series") or item.get("series_id") or "").strip()
    if series_hint:
        return "mini_series"

    title = str(item.get("title") or item.get("topic") or "")
    # Look for numbering signals in the title
    if re.search(r"(part|ep|episode)\s*\d+", title, re.IGNORECASE):
        return "mini_series"

    # Check context for sibling items with the same topic
    unified = context.get("unified_packages") or context.get("ideas") or []
    if len(unified) >= 3:
        return "mini_series"
    if len(unified) == 1:
        return "standalone"

    return "mini_series"


def _build_episode_sequence(items: list, series_type: str) -> list:
    """Build an ordered episode sequence with connectors for sibling items."""
    sequence = []
    for i, item in enumerate(items):
        topic = str(item.get("topic") or item.get("title") or f"Episode {i + 1}")
        sequence.append({
            "position": i + 1,
            "topic": topic,
            "project_id": str(item.get("project_id", "")),
            "connector": (
                f"Builds on episode {i}: {sequence[-1]['topic']!r}" if i > 0
                else "Series opener — establishes the central question"
            ),
            "complexity_level": min(i + 1, 5),  # 1-5 ramp
        })
    return sequence


def _build_progression_arc(series_type: str, episode_count: int) -> str:
    if series_type == "standalone":
        return "Single-episode — no arc required."
    if episode_count <= 3:
        return (
            "Short-form arc: ep1 = foundational concept, "
            "ep2 = mechanism / deeper layer, ep3 = real-world implications + payoff."
        )
    if episode_count <= 6:
        return (
            "Medium arc: begin simple (ep1-2), introduce complexity (ep3-4), "
            "deliver surprising implications and synthesis (ep5-6)."
        )
    return (
        "Full season arc: establish the core curiosity (ep1-2), "
        "explore sub-topics with rising stakes (ep3-N-2), "
        "deliver series-wide payoff and open the next season question (final 2 eps)."
    )


def build_series_design(item: dict, context: dict | None = None) -> dict:
    """SeriesDesign for one item in context of its sibling items.

    If the item appears to be standalone, returns a minimal plan.
    Otherwise builds full sequencing, callbacks, recurring elements, and continuity.
    """
    context = context or {}

    # Collect sibling items from context
    unified = context.get("unified_packages") or context.get("ideas") or []
    siblings = list(unified) if unified else [item]
    if item not in siblings:
        siblings = [item] + siblings

    series_type = _infer_series_type(item, context)
    topic = str(item.get("topic") or item.get("title") or "")
    niche = str(item.get("niche") or "general")

    series_title = (
        str(item.get("series") or "")
        or (f"The {topic.title()} Series" if topic else f"Generational {niche.title()} Series")
    )

    episode_count = len(siblings)
    sequence = _build_episode_sequence(siblings, series_type)
    progression = _build_progression_arc(series_type, episode_count)
    numbering = _NUMBERING_SCHEMES.get(series_type, "#{n}")

    callbacks = [
        f"Reference the central question from ep1 when the answer is finally revealed",
        f"Call back to the opening hook visual when delivering the final takeaway",
        "Use the recurring experiment/demonstration as a through-line",
    ] if series_type != "standalone" else []

    recurring = list(_DEFAULT_RECURRING) + [
        f"'{niche.title()} fact of the episode' card at the powerful_takeaway beat",
    ]

    return {
        "series_type": series_type,
        "series_title": series_title,
        "niche": niche,
        "episode_count": episode_count,
        "episode_sequence": sequence,
        "progression_arc": progression,
        "callbacks": callbacks,
        "recurring_elements": recurring,
        "visual_continuity": {
            "color_palette": "consistent brand palette across all episodes",
            "typography": "same title card font and lower-third style",
            "transition_style": "series-consistent cut style",
            "thumbnail_family": "matching visual template with episode number overlay",
        },
        "educational_continuity": {
            "knowledge_build": "each episode assumes the viewer watched prior episodes",
            "vocabulary": "introduce series-specific terms in ep1, use freely thereafter",
            "complexity_ramp": progression,
        },
        "numbering_scheme": numbering,
        "series_diagnostics": {
            "sibling_count": len(siblings),
            "inferred_type": series_type,
        },
    }
