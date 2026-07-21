"""Audience Intelligence creative memory — searchable lessons with evidence.

Does not replace Creative Performance Lab or Publishing Intelligence libraries.
Composes their signals and stores AI-owned production lessons.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
KB_ROOT = ROOT / "data" / "audience_intelligence"
KB_PATH = KB_ROOT / "CREATIVE_MEMORY.json"
LESSONS_PATH = KB_ROOT / "PRODUCTION_LESSONS.json"
BRIEF_DIR = KB_ROOT / "briefs"
REVIEW_DIR = KB_ROOT / "reviews"

# Knowledge categories (mission vocabulary)
KNOWLEDGE_CATEGORIES = (
    "hook_patterns",
    "curiosity_gaps",
    "emotional_triggers",
    "visual_pacing",
    "camera_movement_styles",
    "narration_styles",
    "thumbnail_characteristics",
    "caption_styles",
    "scene_density",
    "transition_styles",
    "subject_best_practices",
    "platform_recommendations",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    KB_ROOT.mkdir(parents=True, exist_ok=True)
    BRIEF_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)


def _empty_kb() -> dict[str, Any]:
    return {
        "version": "2.0.0",
        "updated_at": "",
        "lessons": [],
        "by_category": {c: [] for c in KNOWLEDGE_CATEGORIES},
        "note": "Audience Intelligence creative memory — evidence-backed only",
    }


def load_knowledge() -> dict[str, Any]:
    ensure_dirs()
    if not KB_PATH.exists():
        return _empty_kb()
    try:
        data = json.loads(KB_PATH.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return _empty_kb()
        data.setdefault("lessons", [])
        data.setdefault("by_category", {c: [] for c in KNOWLEDGE_CATEGORIES})
        return data
    except (OSError, json.JSONDecodeError):
        return _empty_kb()


def save_knowledge(data: dict[str, Any]) -> Path:
    ensure_dirs()
    data["updated_at"] = _now()
    KB_PATH.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    # Mirror lean index for docs/tooling
    LESSONS_PATH.write_text(
        json.dumps(
            {
                "updated_at": data["updated_at"],
                "count": len(data.get("lessons") or []),
                "lessons": data.get("lessons") or [],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return KB_PATH


def add_lesson(
    *,
    statement: str,
    category: str,
    evidence: list[dict[str, Any]] | None = None,
    confidence: float = 0.5,
    platform: str = "youtube_shorts",
    niche: str = "",
    topic: str = "",
    production_id: str = "",
    source: str = "post_production_review",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Store one lesson with evidence + confidence (0–1)."""
    cat = category if category in KNOWLEDGE_CATEGORIES else "subject_best_practices"
    conf = max(0.0, min(1.0, float(confidence)))
    lesson = {
        "lesson_id": f"ail_{uuid.uuid4().hex[:10]}",
        "statement": statement.strip(),
        "category": cat,
        "confidence": round(conf, 3),
        "evidence": list(evidence or []),
        "platform": platform,
        "niche": niche,
        "topic": topic,
        "production_id": production_id,
        "source": source,
        "tags": list(tags or []),
        "created_at": _now(),
        "active": True,
    }
    kb = load_knowledge()
    lessons = list(kb.get("lessons") or [])
    # Dedup near-identical statements
    key = re.sub(r"\W+", " ", lesson["statement"].lower()).strip()
    for existing in lessons:
        ekey = re.sub(r"\W+", " ", str(existing.get("statement") or "").lower()).strip()
        if ekey == key:
            # Raise confidence if corroborated
            existing["confidence"] = round(min(1.0, float(existing.get("confidence") or 0) + 0.05), 3)
            existing.setdefault("evidence", []).extend(lesson["evidence"])
            existing["evidence"] = existing["evidence"][-20:]
            existing["last_corroborated_at"] = _now()
            existing["production_id"] = production_id or existing.get("production_id")
            save_knowledge(kb)
            return existing
    lessons.insert(0, lesson)
    kb["lessons"] = lessons[:1000]
    by_cat = dict(kb.get("by_category") or {})
    ids = list(by_cat.get(cat) or [])
    ids.insert(0, lesson["lesson_id"])
    by_cat[cat] = ids[:200]
    kb["by_category"] = by_cat
    save_knowledge(kb)
    return lesson


def search_lessons(
    query: str = "",
    *,
    category: str = "",
    platform: str = "",
    niche: str = "",
    min_confidence: float = 0.0,
    limit: int = 12,
) -> list[dict[str, Any]]:
    q = {t for t in re.findall(r"[a-z0-9]+", (query or "").lower()) if len(t) > 2}
    rows = []
    for lesson in load_knowledge().get("lessons") or []:
        if not lesson.get("active", True):
            continue
        if category and lesson.get("category") != category:
            continue
        if platform and lesson.get("platform") and lesson.get("platform") != platform:
            continue
        if niche and niche.lower() not in str(lesson.get("niche") or "").lower() and niche.lower() not in str(lesson.get("topic") or "").lower():
            # soft: still allow if query matches
            if not q:
                continue
        if float(lesson.get("confidence") or 0) < min_confidence:
            continue
        hay = f"{lesson.get('statement')} {lesson.get('niche')} {lesson.get('topic')} {' '.join(lesson.get('tags') or [])}".lower()
        overlap = len(q & set(re.findall(r"[a-z0-9]+", hay))) / max(1, len(q)) if q else 0.35
        if q and overlap <= 0:
            continue
        rows.append({**lesson, "relevance": round(overlap, 3)})
    rows.sort(key=lambda r: (-float(r.get("relevance") or 0), -float(r.get("confidence") or 0)))
    return rows[:limit]


def seed_bootstrap_lessons() -> dict[str, Any]:
    """Seed high-quality starter lessons (marked low-moderate confidence until corroborated)."""
    seeds = [
        ("Three-beat openings (stop / reframe / promise) consistently improve curiosity on science Shorts.", "hook_patterns", 0.62, ["biology", "science"], "youtube_shorts"),
        ("Ocean / observatory environments outperform flat blue or solid color beds for marine topics.", "visual_pacing", 0.58, ["biology", "ocean"], "youtube_shorts"),
        ("Fast push-in / zoom on the first biology hook beat lifts early retention vs static establishing.", "camera_movement_styles", 0.6, ["biology"], "youtube_shorts"),
        ("Professor / science narration profile outperforms generic default for educational science Shorts.", "narration_styles", 0.64, ["science", "biology"], "youtube_shorts"),
        ("Curiosity gaps that confront a wrong belief outperform definition openings.", "curiosity_gaps", 0.66, ["education"], "youtube_shorts"),
        ("Captions that punch the hook keywords in the first 3s outperform dense paragraph captions.", "caption_styles", 0.55, ["shorts"], "youtube_shorts"),
        ("Thumbnails with one large subject + short numeric claim beat multi-element clutter.", "thumbnail_characteristics", 0.57, ["shorts"], "youtube_shorts"),
        ("Scene density of a visual change every 2–3.5s in the open reduces early drop-off.", "scene_density", 0.59, ["shorts"], "youtube_shorts"),
    ]
    added = 0
    for statement, cat, conf, tags, platform in seeds:
        before = len(load_knowledge().get("lessons") or [])
        add_lesson(
            statement=statement,
            category=cat,
            confidence=conf,
            platform=platform,
            niche=tags[0] if tags else "",
            tags=tags,
            source="bootstrap_seed",
            evidence=[{"type": "seed", "note": "Bootstrap — raise confidence when corroborated by reviews"}],
        )
        after = len(load_knowledge().get("lessons") or [])
        if after >= before:
            added += 1
    return {"ok": True, "seeded_or_corroborated": added, "total": len(load_knowledge().get("lessons") or [])}
