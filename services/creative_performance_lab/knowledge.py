"""Creative Performance Knowledge Base — evidence-backed learnings only."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from services.creative_performance_lab.store import load_experiment, load_knowledge, save_knowledge


def add_learning(
    *,
    creative_variable: str,
    winning_pattern: str,
    losing_pattern: str = "",
    topic_category: str = "",
    audience: str = "",
    platform: str = "youtube_shorts",
    supporting_experiment_ids: list[str] | None = None,
    sample_size: int = 0,
    effect_size: float = 0.0,
    confidence: float = 0.0,
    conditions_not_to_apply: list[str] | None = None,
    active: bool = True,
) -> dict[str, Any]:
    """Store a learning. Prefer calling from evaluate when evidence_sufficient."""
    kb = load_knowledge()
    learning = {
        "learning_id": f"learn_{uuid.uuid4().hex[:10]}",
        "creative_variable": creative_variable,
        "winning_pattern": winning_pattern,
        "losing_pattern": losing_pattern,
        "topic_category": topic_category,
        "audience": audience,
        "platform": platform,
        "supporting_experiment_ids": list(supporting_experiment_ids or []),
        "sample_size": int(sample_size),
        "effect_size": float(effect_size),
        "confidence": float(confidence),
        "date_learned": datetime.now(timezone.utc).isoformat(),
        "active": bool(active),
        "conditions_where_it_should_not_apply": list(conditions_not_to_apply or []),
    }
    learnings = list(kb.get("learnings") or [])
    learnings.insert(0, learning)
    kb["learnings"] = learnings[:500]
    # Bridge into publishing intelligence library when possible (non-blocking)
    try:
        from services.publishing_intelligence.creative_library import update_creative_library

        update_creative_library()
    except Exception:  # noqa: BLE001
        pass
    save_knowledge(kb)
    return learning


def promote_experiment_learning(experiment_id: str) -> dict[str, Any] | None:
    """Create a knowledge entry only when evaluation evidence is sufficient."""
    exp = load_experiment(experiment_id)
    if not exp:
        return None
    result = exp.get("final_result") or {}
    if not result.get("evidence_sufficient"):
        return {
            "ok": False,
            "error": "Evidence insufficient — not writing a global learning",
            "status": result.get("status"),
        }
    tested = (exp.get("variables_tested") or ["unknown"])[0]
    actual = result.get("actual_winner") or ""
    variants = exp.get("variants") or []
    win = next((v for v in variants if v.get("label") == actual), {})
    lose = next((v for v in variants if v.get("label") != actual), {})
    learning = add_learning(
        creative_variable=str(tested),
        winning_pattern=str(win.get("hook_style") or actual),
        losing_pattern=str(lose.get("hook_style") or ""),
        topic_category=str((exp.get("meta") or {}).get("category") or "general"),
        audience=str(exp.get("audience") or ""),
        platform=str(exp.get("platform") or "youtube_shorts"),
        supporting_experiment_ids=[experiment_id],
        sample_size=int(result.get("sample_size") or 0),
        effect_size=0.0,
        confidence=float(exp.get("confidence_level") or 0),
        conditions_not_to_apply=["insufficient_platform_match", "different_audience_without_replication"],
    )
    return {"ok": True, "learning": learning}


def search_learnings(
    *,
    topic: str = "",
    platform: str = "",
    audience: str = "",
    creative_variable: str = "",
    active_only: bool = True,
    limit: int = 20,
) -> list[dict[str, Any]]:
    rows = load_knowledge().get("learnings") or []
    out = []
    for row in rows:
        if active_only and not row.get("active", True):
            continue
        if platform and platform not in str(row.get("platform") or ""):
            continue
        if creative_variable and creative_variable != row.get("creative_variable"):
            continue
        if audience and audience.lower() not in str(row.get("audience") or "").lower():
            continue
        if topic and topic.lower() not in (
            f"{row.get('topic_category')} {row.get('winning_pattern')}".lower()
        ):
            # soft match — keep if category empty
            if row.get("topic_category"):
                continue
        out.append(row)
        if len(out) >= limit:
            break
    return out
