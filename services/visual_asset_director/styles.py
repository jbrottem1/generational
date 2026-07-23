"""Style profile selection for a production."""

from __future__ import annotations

from typing import Any

from services.visual_asset_director.models import DEFAULT_STYLE, STYLE_LIBRARY


def list_styles() -> list[dict[str, Any]]:
    return [{"key": k, **v} for k, v in STYLE_LIBRARY.items()]


def resolve_style_profile(
    style: str | None = None,
    *,
    niche: str = "",
    topic: str = "",
    world_type: str = "",
) -> dict[str, Any]:
    """Pick a style profile before generation / review."""
    key = (style or "").strip().lower().replace(" ", "_").replace("-", "_")
    if key in ("pixar", "3d", "pixar3d"):
        key = "pixar_inspired_3d"
    if key in ("cine", "film", "cinematic"):
        key = "cinematic_film"
    if key in ("science", "illustration", "scientific"):
        key = "scientific_illustration"
    if key in ("edu", "animated", "explainer"):
        key = "animated_educational"
    if key in ("museum",):
        key = "museum_display"
    if key in ("medical", "anatomy"):
        key = "medical_visualization"
    if key not in STYLE_LIBRARY:
        key = _infer_style(niche=niche, topic=topic, world_type=world_type)
    profile = dict(STYLE_LIBRARY[key])
    return {
        "style_key": key,
        **profile,
        "inferred": not bool((style or "").strip()),
        "niche": niche,
        "topic": topic,
        "world_type": world_type,
    }


def _infer_style(*, niche: str, topic: str, world_type: str) -> str:
    blob = f"{niche} {topic} {world_type}".lower()
    # World / niche first — biology oceans beat organ-word medical defaults
    if any(w in blob for w in ("ocean", "observatory", "marine", "biology", "nature", "wildlife")):
        return "documentary"
    if any(w in blob for w in ("museum", "artifact", "exhibit")):
        return "museum_display"
    if any(w in blob for w in ("history", "ancient", "historical")):
        return "historical_recreation"
    if any(w in blob for w in ("future", "ai lab", "cyber", "space station")):
        return "futuristic"
    if any(w in blob for w in ("pixar", "cartoon", "3d character")):
        return "pixar_inspired_3d"
    if any(w in blob for w in ("diagram", "illustration", "cross-section")):
        return "scientific_illustration"
    if any(w in blob for w in ("medical", "anatomy", "surgical", "organ anatomy")):
        return "medical_visualization"
    if any(w in blob for w in ("science",)):
        return "documentary"
    return DEFAULT_STYLE

def style_compatibility(asset_meta: dict[str, Any], profile: dict[str, Any]) -> float:
    """0–100 compatibility heuristic from tags / kind / path hints."""
    key = profile.get("style_key") or DEFAULT_STYLE
    hay = " ".join(
        [
            str(asset_meta.get("topic") or ""),
            str(asset_meta.get("kind") or ""),
            str(asset_meta.get("collection") or ""),
            str(asset_meta.get("style") or ""),
            str(asset_meta.get("uri") or asset_meta.get("path") or ""),
            " ".join(str(t) for t in (asset_meta.get("tags") or [])),
        ]
    ).lower()
    score = 70.0
    if key == "documentary" and any(w in hay for w in ("photo", "observatory", "nature", "ocean", "reality")):
        score += 12
    if key == "scientific_illustration" and any(w in hay for w in ("diagram", "illustrat", "chart", "cutaway")):
        score += 15
    if key == "medical_visualization" and any(w in hay for w in ("anatomy", "organ", "medical", "heart")):
        score += 15
    if key == "cinematic_film" and any(w in hay for w in ("cinematic", "film", "grade")):
        score += 10
    if "stock" in hay or "shutterstock" in hay or "getty" in hay:
        score -= 20
    if "mock" in hay or "placeholder" in hay:
        score -= 25
    return max(0.0, min(100.0, score))
