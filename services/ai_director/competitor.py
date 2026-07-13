"""V5 Competitor Analysis — differentiate while staying original."""

from __future__ import annotations


_NICHE_COMPETITORS = {
    "artificial intelligence": {
        "top_creators": ["Two Minute Papers", "ColdFusion", "AI Explained"],
        "avg_views": 420_000,
        "avg_length_sec": 55,
        "avg_pacing": "fast_cuts_2_3s",
        "thumbnail_styles": ["face_plus_bold_text", "before_after_ai"],
        "hook_styles": ["shock_statistic", "open_loop"],
        "editing_styles": ["kinetic_type", "macro_tech_broll"],
        "narration_styles": ["conversational", "engineer"],
        "publishing_frequency": "2-4x weekly",
    },
    "science": {
        "top_creators": ["Kurzgesagt", "Veritasium", "SciShow"],
        "avg_views": 1_200_000,
        "avg_length_sec": 60,
        "avg_pacing": "medium_with_pauses",
        "thumbnail_styles": ["bold_illustration", "question_overlay"],
        "hook_styles": ["impossible_statement", "visual_mystery"],
        "editing_styles": ["infographic_dense", "orbit_macro"],
        "narration_styles": ["storyteller", "scientist"],
        "publishing_frequency": "1-2x weekly",
    },
    "default": {
        "top_creators": ["Category leaders"],
        "avg_views": 180_000,
        "avg_length_sec": 50,
        "avg_pacing": "fast_educational",
        "thumbnail_styles": ["centered_subject_bold_title", "question_overlay"],
        "hook_styles": ["open_loop", "contradiction"],
        "editing_styles": ["cross_dissolve", "caption_pop"],
        "narration_styles": ["documentary_host", "teacher"],
        "publishing_frequency": "3x weekly",
    },
}


def analyze_competitors(candidate: dict) -> dict:
    topic = str(candidate.get("topic") or candidate.get("title") or "").lower()
    niche = "default"
    if any(w in topic for w in ("ai", "artificial intelligence", "machine learning", "robot")):
        niche = "artificial intelligence"
    elif any(w in topic for w in ("science", "physics", "space", "biology", "chemistry")):
        niche = "science"

    base = dict(_NICHE_COMPETITORS[niche])
    differentiation = [
        "Open with a sharper curiosity gap than category average hooks",
        "Use authentic government/NASA imagery where competitors lean stock",
        "Vary camera compounds (orbit+zoom) to avoid mechanical sameness",
        "Keep educational clarity while increasing kinetic caption emphasis",
        "Differentiate thumbnail with one surprising visual + one short claim",
    ]
    return {
        "niche": niche,
        **base,
        "differentiation_recommendations": differentiation,
        "originality_guardrails": [
            "Do not copy competitor scripts or thumbnail layouts verbatim",
            "Borrow pacing patterns, invent original visual metaphors",
        ],
    }
