"""Reusable Channel Profiles — brand identity for multi-channel operations.

Templates only. Runtime profiles are configurable and persisted via the store.
Composes existing ChannelManager + Voice Studio narrator keys — no new engines.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Example templates (configurable — not hard-wired brands)
CHANNEL_TEMPLATES: dict[str, dict[str, Any]] = {
    "science_daily": {
        "brand_name": "Science Daily",
        "description": "Bite-sized science facts that reframe everyday curiosity.",
        "platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
        "target_audience": "curious generalists ages 18–35 who enjoy science shorts",
        "topic_categories": ["biology", "physics", "astronomy", "chemistry", "nature"],
        "tone": "curious, clear, wonder-led",
        "narrator_profile": "science_educator",
        "voice_profile": "science_educator",
        "visual_style": "clean educational motion with bold labels",
        "world_preferences": {"domains": ["science", "biology", "physics"], "style": "reality_first"},
        "thumbnail_style": "one subject, high contrast, max 5 claim words",
        "intro_outro_rules": {"intro_sec": 1.2, "outro_cta": "Follow for daily science"},
        "upload_schedule": {"youtube_shorts": "daily 18:00", "tiktok": "daily 12:00"},
        "hashtag_strategy": ["#science", "#facts", "#shorts", "#learnontiktok"],
        "seo_rules": {"title_pattern": "curiosity_hook", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "ai_explained": {
        "brand_name": "AI Explained",
        "description": "Plain-language explainers for AI concepts without hype.",
        "platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
        "target_audience": "tech-curious beginners and professionals learning AI",
        "topic_categories": ["artificial_intelligence", "technology", "engineering"],
        "tone": "modern, precise, demystifying",
        "narrator_profile": "technology_explainer",
        "voice_profile": "technology_explainer",
        "visual_style": "diagram-forward tech explainer with neon accents sparingly",
        "world_preferences": {"domains": ["ai", "technology"], "style": "diagram_world"},
        "thumbnail_style": "bold concept word + simple icon metaphor",
        "intro_outro_rules": {"intro_sec": 1.0, "outro_cta": "AI, explained simply"},
        "upload_schedule": {"youtube_shorts": "mon/wed/fri 17:00"},
        "hashtag_strategy": ["#ai", "#machinelearning", "#tech", "#explainers"],
        "seo_rules": {"title_pattern": "what_is_x", "max_title_chars": 65},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "space_explorer": {
        "brand_name": "Space Explorer",
        "description": "Cosmic wonder through clear astronomy storytelling.",
        "platforms": ["youtube_shorts", "instagram_reels"],
        "target_audience": "space enthusiasts and STEM learners",
        "topic_categories": ["astronomy", "physics", "engineering"],
        "tone": "awe, cinematic, documentary-adjacent",
        "narrator_profile": "documentary",
        "voice_profile": "documentary",
        "visual_style": "cinematic space imagery with soft motion pans",
        "world_preferences": {"domains": ["astronomy", "space"], "style": "cinematic_cosmos"},
        "thumbnail_style": "cosmic subject + scale cue",
        "intro_outro_rules": {"intro_sec": 1.5, "outro_cta": "Explore the cosmos with us"},
        "upload_schedule": {"youtube_shorts": "tue/thu/sat 19:00"},
        "hashtag_strategy": ["#space", "#astronomy", "#nasa", "#jwst"],
        "seo_rules": {"title_pattern": "cosmic_wonder", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "human_biology": {
        "brand_name": "Human Biology",
        "description": "How the human body works — surprising mechanisms, clear science.",
        "platforms": ["youtube_shorts", "tiktok"],
        "target_audience": "biology students and health-curious adults",
        "topic_categories": ["biology", "medicine", "psychology"],
        "tone": "clinical-clarity with everyday metaphors",
        "narrator_profile": "science_educator",
        "voice_profile": "science_educator",
        "visual_style": "anatomy-first educational graphics",
        "world_preferences": {"domains": ["biology", "medicine"], "style": "medical_illustration"},
        "thumbnail_style": "body system focus + one surprising claim",
        "intro_outro_rules": {"intro_sec": 1.0, "outro_cta": "Your body, explained"},
        "upload_schedule": {"youtube_shorts": "daily 16:00"},
        "hashtag_strategy": ["#biology", "#humanbody", "#science"],
        "seo_rules": {"title_pattern": "body_surprise", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "medical_mysteries": {
        "brand_name": "Medical Mysteries",
        "description": "Strange cases and medical mechanisms that invite careful curiosity.",
        "platforms": ["youtube_shorts", "tiktok"],
        "target_audience": "medicine-curious adults who enjoy mystery framing",
        "topic_categories": ["medicine", "biology", "psychology"],
        "tone": "investigative, careful, awe without fearmongering",
        "narrator_profile": "storyteller",
        "voice_profile": "storyteller",
        "visual_style": "case-file aesthetic with clear diagrams",
        "world_preferences": {"domains": ["medicine"], "style": "case_file"},
        "thumbnail_style": "mystery framing + clinical clarity",
        "intro_outro_rules": {"intro_sec": 1.3, "outro_cta": "Another medical mystery solved"},
        "upload_schedule": {"youtube_shorts": "mon/wed/fri 20:00"},
        "hashtag_strategy": ["#medicine", "#mysteries", "#healthscience"],
        "seo_rules": {"title_pattern": "mystery_case", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "ancient_history": {
        "brand_name": "Ancient History",
        "description": "Lost knowledge and ancient engineering made vivid and accurate.",
        "platforms": ["youtube_shorts", "instagram_reels"],
        "target_audience": "history lovers and lifelong learners",
        "topic_categories": ["history", "engineering", "archaeology"],
        "tone": "measured, storied, respectful of sources",
        "narrator_profile": "history_narrator",
        "voice_profile": "history_narrator",
        "visual_style": "archival textures with clean motion graphics",
        "world_preferences": {"domains": ["history"], "style": "archive_world"},
        "thumbnail_style": "artifact + bold historical claim",
        "intro_outro_rules": {"intro_sec": 1.4, "outro_cta": "History that still matters"},
        "upload_schedule": {"youtube_shorts": "tue/thu 18:00"},
        "hashtag_strategy": ["#history", "#ancienthistory", "#archaeology"],
        "seo_rules": {"title_pattern": "ancient_reveal", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "engineering_explained": {
        "brand_name": "Engineering Explained",
        "description": "How impossible structures and machines actually work.",
        "platforms": ["youtube_shorts", "tiktok"],
        "target_audience": "engineering students and makers",
        "topic_categories": ["engineering", "physics", "technology"],
        "tone": "practical, structural, step-by-step",
        "narrator_profile": "professor",
        "voice_profile": "professor",
        "visual_style": "blueprint + real-world process visuals",
        "world_preferences": {"domains": ["engineering"], "style": "blueprint"},
        "thumbnail_style": "structure hero shot + load/force cue",
        "intro_outro_rules": {"intro_sec": 1.1, "outro_cta": "Built to make sense"},
        "upload_schedule": {"youtube_shorts": "daily 17:30"},
        "hashtag_strategy": ["#engineering", "#howitworks", "#stem"],
        "seo_rules": {"title_pattern": "how_it_works", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "wildlife_earth": {
        "brand_name": "Wildlife Earth",
        "description": "Nature storytelling grounded in ecology and adaptation.",
        "platforms": ["youtube_shorts", "instagram_reels"],
        "target_audience": "wildlife and nature lovers",
        "topic_categories": ["nature", "biology", "environment"],
        "tone": "documentary wonder, quiet awe",
        "narrator_profile": "documentary",
        "voice_profile": "documentary",
        "visual_style": "wildlife cinema with habitat continuity",
        "world_preferences": {"domains": ["nature", "biology"], "style": "habitat_world"},
        "thumbnail_style": "animal eye contact + habitat color",
        "intro_outro_rules": {"intro_sec": 1.5, "outro_cta": "Earth's wild systems"},
        "upload_schedule": {"youtube_shorts": "wed/sat 15:00"},
        "hashtag_strategy": ["#wildlife", "#nature", "#earth"],
        "seo_rules": {"title_pattern": "wildlife_wonder", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "psychology_lab": {
        "brand_name": "Psychology Lab",
        "description": "Behavioral science that explains why minds bend and stick.",
        "platforms": ["youtube_shorts", "tiktok", "instagram_reels"],
        "target_audience": "psychology-curious adults seeking self-insight",
        "topic_categories": ["psychology", "medicine", "biology"],
        "tone": "insightful, slightly confrontational, humane",
        "narrator_profile": "storyteller",
        "voice_profile": "storyteller",
        "visual_style": "mind metaphor graphics with clean typography",
        "world_preferences": {"domains": ["psychology"], "style": "mind_lab"},
        "thumbnail_style": "face/metaphor + bias claim",
        "intro_outro_rules": {"intro_sec": 1.0, "outro_cta": "Your mind, under the microscope"},
        "upload_schedule": {"youtube_shorts": "daily 19:30"},
        "hashtag_strategy": ["#psychology", "#mindset", "#cognitivebias"],
        "seo_rules": {"title_pattern": "bias_reveal", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
    "future_technology": {
        "brand_name": "Future Technology",
        "description": "Near-future tech explained with grounded timelines.",
        "platforms": ["youtube_shorts", "tiktok"],
        "target_audience": "futurists and early adopters",
        "topic_categories": ["technology", "artificial_intelligence", "engineering"],
        "tone": "forward-looking, skeptical of hype",
        "narrator_profile": "technology_explainer",
        "voice_profile": "technology_explainer",
        "visual_style": "sleek product/diagram hybrid",
        "world_preferences": {"domains": ["technology", "ai"], "style": "future_lab"},
        "thumbnail_style": "device/concept + timeline cue",
        "intro_outro_rules": {"intro_sec": 1.0, "outro_cta": "What's next, explained"},
        "upload_schedule": {"youtube_shorts": "tue/fri 18:30"},
        "hashtag_strategy": ["#futuretech", "#innovation", "#tech"],
        "seo_rules": {"title_pattern": "future_reveal", "max_title_chars": 70},
        "monetization_status": "not_monetized",
        "publishing_status": "manual_review",
    },
}

PROFILE_FIELDS: tuple[str, ...] = (
    "channel_id",
    "brand_name",
    "description",
    "platforms",
    "target_audience",
    "topic_categories",
    "tone",
    "narrator_profile",
    "voice_profile",
    "visual_style",
    "world_preferences",
    "thumbnail_style",
    "intro_outro_rules",
    "upload_schedule",
    "hashtag_strategy",
    "seo_rules",
    "monetization_status",
    "publishing_status",
    "analytics_history",
    "status",
    "metrics",
)


def list_template_ids() -> list[str]:
    return sorted(CHANNEL_TEMPLATES.keys())


def build_profile_from_template(template_id: str, *, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Instantiate a configurable Channel Profile from a template."""
    key = template_id.strip().lower().replace(" ", "_").replace("-", "_")
    if key not in CHANNEL_TEMPLATES:
        raise ValueError(f"Unknown channel template: {template_id}")
    base = deepcopy(CHANNEL_TEMPLATES[key])
    if overrides:
        base.update(overrides)
    brand = str(base.get("brand_name") or key)
    profile = {
        "channel_id": key,
        "template_id": key,
        "brand_name": brand,
        "name": brand,  # ChannelManager compat
        "niche": ", ".join(base.get("topic_categories") or []) or key,
        "brand_voice": base.get("tone") or "",
        "description": base.get("description") or "",
        "platforms": list(base.get("platforms") or []),
        "target_audience": base.get("target_audience") or "",
        "topic_categories": list(base.get("topic_categories") or []),
        "tone": base.get("tone") or "",
        "narrator_profile": base.get("narrator_profile") or "professor",
        "voice_profile": base.get("voice_profile") or "professor",
        "visual_style": base.get("visual_style") or "",
        "world_preferences": dict(base.get("world_preferences") or {}),
        "thumbnail_style": base.get("thumbnail_style") or "",
        "intro_outro_rules": dict(base.get("intro_outro_rules") or {}),
        "upload_schedule": dict(base.get("upload_schedule") or {}),
        "posting_schedule": dict(base.get("upload_schedule") or {}),
        "hashtag_strategy": list(base.get("hashtag_strategy") or []),
        "seo_rules": dict(base.get("seo_rules") or {}),
        "monetization_status": base.get("monetization_status") or "not_monetized",
        "publishing_status": base.get("publishing_status") or "manual_review",
        "analytics_history": list(base.get("analytics_history") or []),
        "status": "active",
        "metrics": {
            "videos_published": 0,
            "videos_scheduled": 0,
            "total_views": 0,
            "followers": 0,
            "estimated_revenue": 0.0,
            "average_creative_score": None,
        },
        "credentials": {},
    }
    return profile


def normalize_profile(raw: dict[str, Any]) -> dict[str, Any]:
    """Ensure a profile dict has required Multi-Channel fields."""
    brand = str(raw.get("brand_name") or raw.get("name") or "Untitled Channel")
    channel_id = str(raw.get("channel_id") or raw.get("template_id") or brand).lower().replace(" ", "_")
    out = dict(raw)
    out.setdefault("channel_id", channel_id)
    out.setdefault("brand_name", brand)
    out.setdefault("name", brand)
    out.setdefault("description", "")
    out.setdefault("platforms", ["youtube_shorts"])
    out.setdefault("target_audience", "")
    out.setdefault("topic_categories", [])
    out.setdefault("tone", raw.get("brand_voice") or "")
    out.setdefault("narrator_profile", "professor")
    out.setdefault("voice_profile", out.get("narrator_profile") or "professor")
    out.setdefault("visual_style", "")
    out.setdefault("world_preferences", {})
    out.setdefault("thumbnail_style", "")
    out.setdefault("intro_outro_rules", {})
    out.setdefault("upload_schedule", raw.get("posting_schedule") or {})
    out.setdefault("posting_schedule", out["upload_schedule"])
    out.setdefault("hashtag_strategy", [])
    out.setdefault("seo_rules", {})
    out.setdefault("monetization_status", "not_monetized")
    out.setdefault("publishing_status", "manual_review")
    out.setdefault("analytics_history", [])
    out.setdefault("status", "active")
    out.setdefault(
        "metrics",
        {
            "videos_published": 0,
            "videos_scheduled": 0,
            "total_views": 0,
            "followers": 0,
            "estimated_revenue": 0.0,
            "average_creative_score": None,
        },
    )
    out.setdefault("niche", ", ".join(out.get("topic_categories") or []) or channel_id)
    out.setdefault("brand_voice", out.get("tone") or "")
    out.setdefault("credentials", {})
    return out
