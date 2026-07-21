"""Gather available visual source options for one scene (compose existing pools)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.visual_source_intelligence.intent import build_scene_intent, scene_narration
from services.visual_source_intelligence.models import SOURCE_FALLBACK_RANK

ROOT = Path(__file__).resolve().parents[2]
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".m4v"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}


def _usable_path(raw: Any) -> str | None:
    if not raw:
        return None
    p = Path(str(raw))
    if not p.is_absolute():
        p = ROOT / p
    if not p.is_file():
        return None
    if str(p).startswith(("mock://", "runtime://")):
        return None
    if p.suffix.lower() not in VIDEO_EXTS | IMAGE_EXTS:
        return None
    return str(p.resolve())


def _option(
    *,
    source_key: str,
    label: str,
    path: str | None = None,
    available: bool,
    relevance: float,
    motion: float,
    explains: float,
    reason: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rank = int(SOURCE_FALLBACK_RANK.get(source_key, 5))
    return {
        "source_key": source_key,
        "label": label,
        "rank": rank,
        "path": path,
        "available": bool(available),
        "relevance": round(relevance, 2),
        "motion_score": round(motion, 2),
        "explains_narration": round(explains, 2),
        "reason": reason,
        "meta": meta or {},
    }


def _token_overlap(a: str, b: str) -> float:
    ta = {t for t in a.lower().split() if len(t) > 2}
    tb = {t for t in b.lower().split() if len(t) > 2}
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(1, len(ta))


def _library_hits(query: str, *, kind: str = "", limit: int = 6) -> list[dict[str, Any]]:
    try:
        from services.asset_intelligence.search import semantic_search

        return list(semantic_search(query, limit=limit, kind=kind) or [])
    except Exception:  # noqa: BLE001
        return []


def _evidence_paths(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for key in ("evidence_assets", "visual_assets", "reality_assets"):
        for row in candidate.get(key) or []:
            if isinstance(row, dict):
                out.append(row)
    ep = candidate.get("evidence_package") if isinstance(candidate.get("evidence_package"), dict) else {}
    for row in ep.get("assets") or ep.get("selected_assets") or []:
        if isinstance(row, dict):
            out.append(row)
    ai = candidate.get("asset_intelligence") if isinstance(candidate.get("asset_intelligence"), dict) else {}
    for row in ai.get("selected_media") or []:
        if isinstance(row, dict):
            out.append(row)
    return out


def _world_paths(candidate: dict[str, Any]) -> list[dict[str, Any]]:
    wp = candidate.get("world_package") if isinstance(candidate.get("world_package"), dict) else {}
    rows: list[dict[str, Any]] = []
    for key in ("assets", "world_assets", "reusable_assets", "objects"):
        for row in wp.get(key) or []:
            if isinstance(row, dict):
                rows.append(row)
    return rows


def catalog_options_for_scene(
    scene: dict[str, Any],
    *,
    candidate: dict[str, Any] | None = None,
    topic: str = "",
    used_paths: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Enumerate possible sources for a scene; availability marks what can actually load."""
    candidate = candidate or {}
    used_paths = used_paths or set()
    intent = build_scene_intent(scene, topic=topic)
    narration = scene_narration(scene)
    query = " ".join(
        [
            topic,
            narration[:120],
            str(scene.get("stock_footage_query") or ""),
            str(scene.get("subject") or ""),
        ]
    ).strip()
    options: list[dict[str, Any]] = []

    # 1) Licensed / library video
    for hit in _library_hits(query, kind="video", limit=8) + _library_hits(query, limit=8):
        kind = str(hit.get("kind") or hit.get("media_type") or "").lower()
        path = _usable_path(hit.get("path") or hit.get("local_path") or hit.get("uri"))
        is_video = kind in {"video", "video_clip", "stock_footage", "animation"} or (
            path and Path(path).suffix.lower() in VIDEO_EXTS
        )
        if not is_video:
            continue
        if path and path in used_paths:
            continue
        rel = _token_overlap(query, str(hit.get("topic") or "") + " " + " ".join(hit.get("keywords") or []))
        options.append(
            _option(
                source_key="stock_video",
                label="Licensed / library stock video",
                path=path,
                available=bool(path),
                relevance=max(0.35, rel + float((hit.get("scores") or {}).get("overall_score") or 0) / 200),
                motion=0.9,
                explains=max(0.4, rel),
                reason="Existing library video matched scene query",
                meta={"asset_id": hit.get("asset_id"), "license": hit.get("license")},
            )
        )

    # Evidence / authentic stills or clips already on candidate
    for hit in _evidence_paths(candidate):
        path = _usable_path(hit.get("path") or hit.get("local_path") or hit.get("uri") or hit.get("image"))
        if not path or path in used_paths:
            continue
        is_video = Path(path).suffix.lower() in VIDEO_EXTS
        key = "stock_video" if is_video else "static_image"
        rel = _token_overlap(query, str(hit.get("title") or hit.get("topic") or hit.get("caption") or ""))
        options.append(
            _option(
                source_key=key,
                label="Evidence / catalog asset" if not is_video else "Evidence video",
                path=path,
                available=True,
                relevance=max(0.4, rel),
                motion=0.85 if is_video else 0.25,
                explains=max(0.45, rel),
                reason="Authenticated evidence or catalog media already attached",
                meta={"asset_id": hit.get("asset_id") or hit.get("image_id")},
            )
        )

    # World reusable assets
    for hit in _world_paths(candidate):
        path = _usable_path(hit.get("path") or hit.get("asset_path") or hit.get("uri"))
        if path and path not in used_paths:
            options.append(
                _option(
                    source_key="static_image",
                    label="Reusable world asset",
                    path=path,
                    available=True,
                    relevance=0.55,
                    motion=0.3,
                    explains=0.5,
                    reason="Persistent world package asset for continuity",
                    meta={"object_id": hit.get("object_id") or hit.get("id")},
                )
            )

    # 2) AI video (provider may still degrade later — available as selection intent)
    options.append(
        _option(
            source_key="ai_video",
            label="AI-generated video",
            available=True,
            relevance=0.7 if intent["prefers_motion"] else 0.55,
            motion=0.95,
            explains=0.7 if intent["prefers_motion"] else 0.55,
            reason="Motivated camera/subject motion when stock video is unavailable",
            meta={"prompt": scene.get("ai_video_prompt") or intent["ideal_visual"]},
        )
    )

    # 3) Animated diagrams / motion graphics
    if intent["prefers_diagram"] or scene_narration(scene):
        options.append(
            _option(
                source_key="animated_diagram",
                label="Animated diagram / motion graphics",
                available=True,
                relevance=0.9 if intent["prefers_diagram"] else 0.35,
                motion=0.75,
                explains=0.92 if intent["prefers_diagram"] else 0.4,
                reason="Labeled diagram or motion graphic best teaches comparison/rate/legend beats",
                meta={
                    "media_type": "motion_graphics" if intent["prefers_diagram"] else "infographic",
                    "overlay_plan": "callouts for narrated keywords",
                },
            )
        )

    # 4) AI still + meaningful motion
    options.append(
        _option(
            source_key="ai_still_motion",
            label="AI-generated still with meaningful motion",
            available=True,
            relevance=0.65,
            motion=0.6,
            explains=0.6,
            reason="Generative still with non-repeating camera move when video/diagram unavailable",
            meta={"prompt": scene.get("ai_image_prompt") or intent["ideal_visual"]},
        )
    )

    # 5) Static image last resort (existing approved path / evidence still)
    existing = _usable_path(
        scene.get("approved_asset_path")
        or scene.get("image")
        or scene.get("path")
        or scene.get("local_path")
    )
    if existing and existing not in used_paths:
        options.append(
            _option(
                source_key="static_image",
                label="Static image (last resort)",
                path=existing,
                available=True,
                relevance=0.5,
                motion=0.15,
                explains=0.45,
                reason="Existing still on the scene — only if stronger motion sources fail",
            )
        )
    else:
        options.append(
            _option(
                source_key="static_image",
                label="Static image (last resort)",
                available=True,
                relevance=0.4,
                motion=0.1,
                explains=0.35,
                reason="Static generative plate only when no stronger option can be fulfilled",
            )
        )

    # Deduplicate by source_key+path (keep highest relevance)
    best: dict[str, dict[str, Any]] = {}
    for opt in options:
        key = f"{opt['source_key']}|{opt.get('path') or opt['label']}"
        prev = best.get(key)
        if not prev or float(opt["relevance"]) > float(prev["relevance"]):
            best[key] = opt
    return list(best.values())
