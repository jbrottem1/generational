"""Recommend voices for each narrator profile from scored samples."""

from __future__ import annotations

from typing import Any

from services.voice_studio.config_store import set_profile_voice_id
from services.voice_studio.profiles import NARRATOR_PROFILE_CATALOG
from services.voice_studio.scoring import educational_shorts_score, rank_voices_for_profile


def recommend_voices_for_profiles(scored: list[dict[str, Any]], *, top_n: int = 3) -> dict[str, Any]:
    """Return best-fit voices per profile plus top educational Shorts picks."""
    by_profile: dict[str, list[dict[str, Any]]] = {}
    for key in NARRATOR_PROFILE_CATALOG:
        ranked = rank_voices_for_profile(scored, key)
        by_profile[key] = [
            {
                "rank": i + 1,
                "voice_id": r.get("voice_id"),
                "name": r.get("name"),
                "profile_fit": r.get("profile_fit"),
                "overall": r.get("overall"),
                "dimensions": r.get("dimensions"),
            }
            for i, r in enumerate(ranked[:top_n])
        ]

    shorts = sorted(
        [
            {
                **row,
                "shorts_score": educational_shorts_score(row),
            }
            for row in scored
        ],
        key=lambda r: (-float(r.get("shorts_score") or 0), -float(r.get("overall") or 0)),
    )
    top_shorts = [
        {
            "rank": i + 1,
            "voice_id": r.get("voice_id"),
            "name": r.get("name"),
            "shorts_score": r.get("shorts_score"),
            "overall": r.get("overall"),
            "dimensions": r.get("dimensions"),
        }
        for i, r in enumerate(shorts[:3])
    ]

    return {
        "by_profile": by_profile,
        "educational_youtube_shorts_top3": top_shorts,
        "recommended_default": (top_shorts[0] if top_shorts else {}),
    }


def apply_recommendations_to_config(
    recommendations: dict[str, Any],
    *,
    write_default: bool = False,
) -> dict[str, Any]:
    """Persist best voice per profile into PROFILE_VOICES.json (configuration only)."""
    applied = []
    by_profile = recommendations.get("by_profile") or {}
    for key, rows in by_profile.items():
        if not rows:
            continue
        best = rows[0]
        vid = str(best.get("voice_id") or "")
        if not vid:
            continue
        also_default = bool(write_default and key == "professor")
        applied.append(set_profile_voice_id(key, vid, also_default=also_default))
    return {"ok": True, "applied": applied, "count": len(applied)}
