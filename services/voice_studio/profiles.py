"""Narrator profile catalog — metadata only; voice IDs live in config/env."""

from __future__ import annotations

from typing import Any

# Profiles describe delivery intent. Voice IDs are never hardcoded here.
NARRATOR_PROFILE_CATALOG: dict[str, dict[str, Any]] = {
    "founder": {
        "label": "Founder Voice",
        "description": "Permanent default Generational narrator — cloned ElevenLabs Founder Voice",
        "env_key": "ELEVENLABS_VOICE_FOUNDER",
        "stability": 0.52,
        "similarity_boost": 0.8,
        "content_types": ("default", "founder", "educational", "general"),
        "score_weights": {
            "clarity": 1.3,
            "educational_tone": 1.3,
            "energy": 0.9,
            "professionalism": 1.3,
            "long_form_comfort": 1.2,
        },
        "studio_asset_id": "VOICE-0001",
        "permanent_default": True,
    },
    "professor": {
        "label": "Professor",
        "description": "Authoritative educational delivery for explainers",
        "env_key": "ELEVENLABS_VOICE_PROFESSOR",
        "stability": 0.55,
        "similarity_boost": 0.8,
        "content_types": ("educational", "science", "professor", "academic"),
        "score_weights": {
            "clarity": 1.2,
            "educational_tone": 1.4,
            "energy": 0.7,
            "professionalism": 1.3,
            "long_form_comfort": 1.0,
        },
    },
    "documentary": {
        "label": "Documentary",
        "description": "Calm cinematic documentary narration",
        "env_key": "ELEVENLABS_VOICE_DOCUMENTARY",
        "stability": 0.6,
        "similarity_boost": 0.75,
        "content_types": ("documentary", "nature", "cinema"),
        "score_weights": {
            "clarity": 1.1,
            "educational_tone": 1.0,
            "energy": 0.5,
            "professionalism": 1.2,
            "long_form_comfort": 1.5,
        },
    },
    "storyteller": {
        "label": "Storyteller",
        "description": "Narrative storytelling cadence",
        "env_key": "ELEVENLABS_VOICE_STORYTELLER",
        "stability": 0.45,
        "similarity_boost": 0.7,
        "content_types": ("storytelling", "storyteller", "narrative"),
        "score_weights": {
            "clarity": 1.0,
            "educational_tone": 0.8,
            "energy": 0.9,
            "professionalism": 0.9,
            "long_form_comfort": 1.3,
        },
    },
    "science_educator": {
        "label": "Science Educator",
        "description": "Clear science classroom style",
        "env_key": "ELEVENLABS_VOICE_SCIENCE",
        "stability": 0.58,
        "similarity_boost": 0.78,
        "content_types": ("science", "biology", "physics", "chemistry"),
        "score_weights": {
            "clarity": 1.4,
            "educational_tone": 1.5,
            "energy": 0.8,
            "professionalism": 1.2,
            "long_form_comfort": 1.1,
        },
    },
    "technology_explainer": {
        "label": "Technology Explainer",
        "description": "Modern tech explainers and AI topics",
        "env_key": "ELEVENLABS_VOICE_TECH",
        "stability": 0.5,
        "similarity_boost": 0.75,
        "content_types": ("technology", "tech", "ai", "software"),
        "score_weights": {
            "clarity": 1.3,
            "educational_tone": 1.2,
            "energy": 1.0,
            "professionalism": 1.1,
            "long_form_comfort": 0.9,
        },
    },
    "history_narrator": {
        "label": "History Narrator",
        "description": "Measured historical narration",
        "env_key": "ELEVENLABS_VOICE_HISTORY",
        "stability": 0.62,
        "similarity_boost": 0.75,
        "content_types": ("history", "historical", "dark_history"),
        "score_weights": {
            "clarity": 1.1,
            "educational_tone": 1.1,
            "energy": 0.6,
            "professionalism": 1.3,
            "long_form_comfort": 1.4,
        },
    },
    "calm_instructor": {
        "label": "Calm Instructor",
        "description": "Soft, clear classroom instructor",
        "env_key": "ELEVENLABS_VOICE_CALM",
        "stability": 0.65,
        "similarity_boost": 0.75,
        "content_types": ("calm", "health", "wellness", "instruction"),
        "score_weights": {
            "clarity": 1.2,
            "educational_tone": 1.3,
            "energy": 0.4,
            "professionalism": 1.1,
            "long_form_comfort": 1.5,
        },
    },
    "energetic_presenter": {
        "label": "Energetic Presenter",
        "description": "High-energy short-form presenter",
        "env_key": "ELEVENLABS_VOICE_ENERGETIC",
        "stability": 0.35,
        "similarity_boost": 0.7,
        "content_types": ("high_energy", "energetic", "shorts", "social"),
        "score_weights": {
            "clarity": 1.1,
            "educational_tone": 0.9,
            "energy": 1.6,
            "professionalism": 0.8,
            "long_form_comfort": 0.5,
        },
    },
    # Legacy keys (same settings / env) so older narrator strings still resolve
    "energetic_explainer": {
        "label": "Energetic Explainer",
        "description": "Legacy alias of Energetic Presenter",
        "env_key": "ELEVENLABS_VOICE_ENERGETIC",
        "stability": 0.35,
        "similarity_boost": 0.7,
        "content_types": ("high_energy", "energetic", "energetic_explainer"),
        "score_weights": {
            "clarity": 1.1,
            "educational_tone": 0.9,
            "energy": 1.6,
            "professionalism": 0.8,
            "long_form_comfort": 0.5,
        },
    },
    "calm_educator": {
        "label": "Calm Educator",
        "description": "Legacy alias of Calm Instructor",
        "env_key": "ELEVENLABS_VOICE_CALM",
        "stability": 0.65,
        "similarity_boost": 0.75,
        "content_types": ("calm", "calm_educator", "health"),
        "score_weights": {
            "clarity": 1.2,
            "educational_tone": 1.3,
            "energy": 0.4,
            "professionalism": 1.1,
            "long_form_comfort": 1.5,
        },
    },
}

# Compatibility aliases → canonical Voice Studio keys
PROFILE_ALIASES: dict[str, str] = {
    "professor": "professor",
    "educator": "professor",
    "educational": "professor",
    "documentary": "documentary",
    "storyteller": "storyteller",
    "storytelling": "storyteller",
    "science_educator": "science_educator",
    "science": "science_educator",
    "technology_explainer": "technology_explainer",
    "tech": "technology_explainer",
    "technology": "technology_explainer",
    "ai": "technology_explainer",
    "history_narrator": "history_narrator",
    "history": "history_narrator",
    "historical": "history_narrator",
    "calm_instructor": "calm_instructor",
    "calm": "calm_instructor",
    "calm_educator": "calm_educator",
    "energetic_presenter": "energetic_presenter",
    "energetic": "energetic_presenter",
    "energetic_explainer": "energetic_explainer",
    "high_energy": "energetic_presenter",
    "default": "founder",
    "founder": "founder",
    "founder_voice": "founder",
    "voice_0001": "founder",
    "voice-0001": "founder",
    "doctor": "founder",
}


def normalize_profile_key(value: str) -> str:
    raw = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    return PROFILE_ALIASES.get(raw, raw if raw in NARRATOR_PROFILE_CATALOG else "founder")


def list_profile_catalog() -> list[dict[str, Any]]:
    rows = []
    for key, meta in NARRATOR_PROFILE_CATALOG.items():
        rows.append(
            {
                "profile_key": key,
                "label": meta["label"],
                "description": meta["description"],
                "env_key": meta["env_key"],
                "content_types": list(meta["content_types"]),
            }
        )
    return rows
