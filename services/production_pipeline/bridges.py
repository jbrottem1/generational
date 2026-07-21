"""Context bridges between production pipeline stages.

Standardizes handoffs without mutating engine internals. Additive only —
never strips existing packages or research slots.
"""

from __future__ import annotations

from typing import Any


def _as_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    return []


def _best_script(item: dict) -> str:
    script = str(item.get("script") or "").strip()
    if script:
        return script
    sp = item.get("script_package") if isinstance(item.get("script_package"), dict) else {}
    return str(
        sp.get("full_script")
        or sp.get("script")
        or sp.get("narration")
        or item.get("hook")
        or ""
    ).strip()


def ensure_seed_candidate(context: dict) -> dict:
    """If Research produced no candidates yet, seed one from subject/command."""
    ctx = dict(context)
    candidates = _as_list(ctx.get("candidates"))
    if candidates:
        return ctx
    subject = str(ctx.get("subject") or ctx.get("niche") or ctx.get("command") or "Topic").strip()
    seed = {
        "project_id": str(ctx.get("project_id") or "pipeline_seed"),
        "title": subject[:120],
        "topic": subject,
        "niche": ctx.get("niche") or "General Content",
        "hook": f"What if everything you know about {subject} is wrong?",
        "script": "",
        "platform": ctx.get("platform") or "youtube_shorts",
        "quality_score": 70,
    }
    if isinstance(ctx.get("research"), dict):
        seed["research"] = ctx["research"]
    ctx["candidates"] = [seed]
    ctx.setdefault("ideas", list(ctx["candidates"]))
    return ctx


def sync_candidate_aliases(context: dict) -> dict:
    """Keep candidates / ideas / selected_ideas / unified_packages aligned."""
    ctx = dict(context)
    candidates = _as_list(ctx.get("candidates"))
    ideas = _as_list(ctx.get("ideas"))
    selected = _as_list(ctx.get("selected_ideas"))

    if not candidates and ideas:
        candidates = ideas
    if not candidates and selected:
        candidates = selected
    if not candidates:
        return ensure_seed_candidate(ctx)

    # Prefer scored/scripted candidates as selected for QC
    ranked = sorted(
        candidates,
        key=lambda c: float(
            (c.get("psychology") or {}).get("viral_score")
            or c.get("viral_score")
            or c.get("quality_score")
            or 0
        ),
        reverse=True,
    )
    ctx["candidates"] = candidates
    ctx["ideas"] = list(candidates)
    ctx["selected_ideas"] = list(ranked[: max(1, min(5, len(ranked)))])
    ctx["unified_packages"] = list(candidates)
    return ctx


def prepare_approved_content(context: dict) -> dict:
    """Scene Planning reads approved_content — bridge from scripted candidates."""
    ctx = sync_candidate_aliases(context)
    approved = []
    for item in _as_list(ctx.get("candidates")):
        script = _best_script(item)
        if not script:
            continue
        row = dict(item)
        row["script"] = script
        row.setdefault("title", row.get("topic") or "Untitled")
        approved.append(row)
    if not approved and _as_list(ctx.get("candidates")):
        # Still build scenes from hook when script generator skipped
        for item in ctx["candidates"]:
            row = dict(item)
            row["script"] = str(row.get("hook") or row.get("title") or "Scene.")
            approved.append(row)
    ctx["approved_content"] = approved
    return ctx


def prepare_media_inputs(context: dict) -> dict:
    """Image/video engines prefer ideas; keep production_packages in sync."""
    ctx = sync_candidate_aliases(context)
    packages = _as_list(ctx.get("production_packages"))
    if not packages and ctx.get("approved_content"):
        # Soft package shells if scene builder skipped
        packages = [
            {
                "title": a.get("title"),
                "script": a.get("script"),
                "scenes": [],
                "source_idea": a,
            }
            for a in ctx["approved_content"]
        ]
        ctx["production_packages"] = packages
    return ctx


def validation_score(context: dict, stage_key: str) -> float:
    """Heuristic 0–100 completeness score for PIPELINE_STATUS."""
    score = 40.0
    candidates = _as_list(context.get("candidates"))
    if candidates:
        score += 15
    if context.get("research"):
        score += 15
    psych = sum(
        1 for c in candidates if c.get("psychology") or c.get("viral_score") is not None
    )
    if psych:
        score += min(15, psych * 5)
    directed = sum(
        1 for c in candidates if c.get("director_package") or c.get("production_blueprint")
    )
    if directed:
        score += min(15, directed * 5)
    scripted = sum(1 for c in candidates if _best_script(c))
    if scripted:
        score += min(15, scripted * 5)
    if context.get("production_packages"):
        score += 10
    if context.get("quality_summary") or context.get("pqa_summary"):
        score += 10
    if context.get("studio_render_summary") or context.get("optimization_summary"):
        score += 5
    bumps = {
        "research": 10 if context.get("research") else 0,
        "psychology": 10 if context.get("psychology_summary") else 0,
        "studio_director": 10 if context.get("ai_director_summary") else 0,
        "script_generator": 10 if context.get("script_generation_summary") else 0,
        "scene_builder": 10 if context.get("production_packages") else 0,
        "media_generation": 5 if context.get("render_assets_summary") else 0,
        "voice_generation": 5 if context.get("voice_audio_summary") or context.get("voice_packages") else 0,
        "video_assembly": 10 if context.get("studio_render_summary") or context.get("render_summary") else 0,
        "quality_control": 10 if context.get("pqa_summary") or context.get("quality_summary") else 0,
        "export": 10 if context.get("optimization_summary") else 0,
    }
    score += bumps.get(stage_key, 0)
    return round(min(100.0, score), 1)


def bridge_before_stage(stage_key: str, context: dict) -> dict:
    """Apply the right adapter immediately before a stage runs."""
    if stage_key == "research":
        return context
    if stage_key == "psychology":
        return ensure_seed_candidate(sync_candidate_aliases(context))
    if stage_key == "studio_director":
        return sync_candidate_aliases(context)
    if stage_key == "script_generator":
        return sync_candidate_aliases(context)
    if stage_key == "scene_builder":
        return prepare_approved_content(context)
    if stage_key in ("media_generation", "voice_generation", "video_assembly"):
        return prepare_media_inputs(context)
    if stage_key in ("quality_control", "export"):
        return sync_candidate_aliases(context)
    return sync_candidate_aliases(context)


def verify_stage_io(stage: dict, context: dict) -> dict[str, Any]:
    """Check declared inputs/outputs against current context (non-fatal)."""
    missing_inputs = [k for k in stage.get("inputs") or [] if k not in context]
    present_outputs = [k for k in stage.get("outputs") or [] if context.get(k) not in (None, "", [], {})]
    missing_outputs = [k for k in stage.get("outputs") or [] if k not in present_outputs]
    return {
        "missing_inputs": missing_inputs,
        "present_outputs": present_outputs,
        "missing_outputs": missing_outputs,
        "ok": len(missing_inputs) == 0 or stage["key"] != "research",
    }
