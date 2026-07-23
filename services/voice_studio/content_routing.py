"""Map content type / niche → narrator profile (config-driven selection)."""

from __future__ import annotations

from typing import Any

from services.voice_studio.config_store import get_configured_voice_id, get_studio_default_voice_id
from services.voice_studio.profiles import NARRATOR_PROFILE_CATALOG, normalize_profile_key

# Content / niche tokens → profile (no voice IDs)
CONTENT_TYPE_ROUTES: dict[str, str] = {
    "science": "science_educator",
    "biology": "science_educator",
    "physics": "science_educator",
    "chemistry": "science_educator",
    "nature": "documentary",
    "documentary": "documentary",
    "history": "history_narrator",
    "dark_history": "history_narrator",
    "historical": "history_narrator",
    "technology": "technology_explainer",
    "tech": "technology_explainer",
    "ai": "technology_explainer",
    "software": "technology_explainer",
    "storytelling": "storyteller",
    "story": "storyteller",
    "narrative": "storyteller",
    "health": "calm_instructor",
    "wellness": "calm_instructor",
    "calm": "calm_instructor",
    "shorts": "energetic_presenter",
    "high_energy": "energetic_presenter",
    "energetic": "energetic_presenter",
    "social": "energetic_presenter",
    "educational": "professor",
    "academic": "professor",
    "professor": "professor",
}


def select_narrator_profile(
    *,
    content_type: str = "",
    niche: str = "",
    narrator: str = "",
    style: str = "",
) -> dict[str, Any]:
    """Choose a narrator profile for content without touching the production pipeline."""
    if narrator:
        key = normalize_profile_key(narrator)
    else:
        tokens = " ".join([content_type, niche, style]).lower().replace("-", "_")
        key = ""
        for token, profile in CONTENT_TYPE_ROUTES.items():
            if token in tokens.replace(" ", "_") or token in tokens:
                key = profile
                break
        if not key and style:
            key = normalize_profile_key(style)
        if not key:
            key = "professor"

    meta = NARRATOR_PROFILE_CATALOG.get(key) or NARRATOR_PROFILE_CATALOG["professor"]
    voice_id = get_configured_voice_id(key) or get_studio_default_voice_id()
    return {
        "profile_key": key,
        "label": meta["label"],
        "description": meta["description"],
        "voice_id": voice_id,
        "env_key": meta["env_key"],
        "content_type_input": content_type,
        "niche_input": niche,
        "selection_source": "narrator" if narrator else ("content_route" if content_type or niche else "default"),
    }
