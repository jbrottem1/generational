"""Pipeline handoff — production brief → Research + Studio Ops (no manual editing)."""

from __future__ import annotations

from typing import Any

from services.trend_opportunity.brief import to_studio_brief_kwargs


def verify_brief_ready(production_brief: dict[str, Any]) -> dict[str, Any]:
    """Assert brief is complete for automated pipeline intake."""
    required = [
        "topic",
        "objective",
        "target_audience",
        "hook",
        "research_goals",
        "world_selection",
        "narrator",
        "style",
        "visual_direction",
        "thumbnail_direction",
        "platform",
        "duration_sec",
        "command",
    ]
    missing = [k for k in required if production_brief.get(k) in (None, "", [], {})]
    return {
        "ok": not missing and production_brief.get("manual_editing_required") is False,
        "missing": missing,
        "manual_editing_required": bool(production_brief.get("manual_editing_required")),
        "command": production_brief.get("command"),
    }


def handoff_to_research(
    production_brief: dict[str, Any],
    *,
    execute_research: bool = False,
) -> dict[str, Any]:
    """Map brief → Research Engine context (command-based; no Research rewrite)."""
    check = verify_brief_ready(production_brief)
    if not check["ok"]:
        return {"ok": False, "stage": "research", "verification": check}
    command = str(production_brief.get("command") or "")
    ctx = {
        "command": command,
        "subject": production_brief.get("topic"),
        "topic": production_brief.get("topic"),
        "research_settings": {
            "goals": production_brief.get("research_goals"),
            "from_trend_opportunity": True,
        },
        "trend_opportunity_brief": production_brief,
    }
    if execute_research:
        try:
            from services.research.manager import build_research_context

            built = build_research_context(command)
            if isinstance(built, dict):
                ctx = {**built, **ctx}
        except Exception as exc:  # noqa: BLE001
            ctx["research_context_note"] = f"build_research_context soft-fail: {str(exc)[:120]}"
    return {"ok": True, "stage": "research", "context": ctx, "verification": check, "research_executed": execute_research}


def handoff_to_studio_ops(
    production_brief: dict[str, Any],
    *,
    execute: bool = False,
    production_id: str = "",
) -> dict[str, Any]:
    """
    Feed brief into Production Operations.

    execute=False → verify + build context only
    execute=True  → call run_studio_ops with auto brief (may take a while)
    """
    check = verify_brief_ready(production_brief)
    if not check["ok"]:
        return {"ok": False, "stage": "studio_ops", "verification": check, "executed": False}

    from services.production_operations.brief import brief_to_context, build_studio_brief

    kwargs = to_studio_brief_kwargs(production_brief)
    studio = build_studio_brief(**kwargs)
    ctx = brief_to_context(studio)
    ctx["trend_opportunity_brief"] = production_brief
    ctx["manual_editing_required"] = False

    result: dict[str, Any] = {
        "ok": True,
        "stage": "studio_ops",
        "verification": check,
        "studio_brief": studio.to_dict(),
        "context_keys": sorted(ctx.keys()),
        "executed": False,
        "command": studio.to_command(),
    }

    if not execute:
        return result

    try:
        from services.production_operations import run_studio_ops

        ops = run_studio_ops(
            topic=studio.topic,
            platform=studio.platform,
            length_sec=studio.length_sec,
            style=studio.style,
            narrator=studio.narrator,
            command=studio.command,
            context=ctx,
            production_id=production_id or None,
        )
        result["executed"] = True
        result["ops_result"] = {
            "production_id": ops.get("production_id") or (ops.get("status") or {}).get("production_id"),
            "success": ops.get("success") or (ops.get("status") or {}).get("success"),
            "keys": list(ops.keys())[:20] if isinstance(ops, dict) else [],
        }
    except Exception as exc:  # noqa: BLE001
        result["ok"] = False
        result["executed"] = False
        result["error"] = str(exc)[:300]
    return result


def handoff_pipeline(
    production_brief: dict[str, Any],
    *,
    execute_ops: bool = False,
    execute_research: bool = False,
    enqueue: bool = True,
    run_immediately: bool = False,
    route_channel: bool = True,
) -> dict[str, Any]:
    """Full automatic handoff: research context + ops brief (+ optional channel route / enqueue)."""
    research = handoff_to_research(production_brief, execute_research=execute_research)
    ops = handoff_to_studio_ops(production_brief, execute=execute_ops)

    # Soft Channel OS routing — inject brand identity into constraints (no engine redesign)
    channel_route = None
    if route_channel:
        try:
            from services.channel_os.routing import profile_to_ops_kwargs, route_opportunity

            opportunity = {
                "topic": production_brief.get("topic"),
                "category": production_brief.get("category")
                or production_brief.get("domain")
                or (production_brief.get("world_selection") or {}).get("domain"),
                "platform": production_brief.get("platform"),
                "target_audience": production_brief.get("target_audience"),
                "opportunity_score": production_brief.get("opportunity_score"),
                "tags": production_brief.get("research_goals") or [],
            }
            channel_route = route_opportunity(opportunity)
            if channel_route.get("ok") and channel_route.get("profile"):
                mapped = profile_to_ops_kwargs(
                    channel_route["profile"],
                    topic=str(production_brief.get("topic") or ""),
                    length_sec=int(production_brief.get("duration_sec") or 45),
                )
                # Prefer channel brand fields; keep brief topic/command
                studio_brief = ops.get("studio_brief") if isinstance(ops.get("studio_brief"), dict) else {}
                if isinstance(ops.get("context_keys"), list):
                    pass
                production_brief.setdefault("channel_id", channel_route.get("selected_channel_id"))
                production_brief.setdefault("brand_name", channel_route.get("selected_brand"))
                # Merge constraints for enqueue path below
                production_brief["_channel_ops"] = {
                    "narrator": mapped["narrator"],
                    "voice": mapped["voice"],
                    "platform": mapped["platform"],
                    "style": mapped["style"],
                    "constraints": mapped["constraints"],
                    "context": mapped["context"],
                }
                if studio_brief:
                    studio_brief["channel_id"] = channel_route.get("selected_channel_id")
        except Exception as exc:  # noqa: BLE001
            channel_route = {"ok": False, "error": str(exc)[:200]}

    queued = None
    if enqueue and research.get("ok") and ops.get("ok"):
        try:
            from services.production_operations.queue import enqueue_production

            kwargs = to_studio_brief_kwargs(production_brief)
            channel_ops = production_brief.get("_channel_ops") or {}
            constraints = dict(kwargs.get("constraints") or {})
            constraints.update(channel_ops.get("constraints") or {})
            queued = enqueue_production(
                topic=kwargs["topic"],
                platform=channel_ops.get("platform") or kwargs["platform"],
                length_sec=kwargs["length_sec"],
                style=channel_ops.get("style") or kwargs.get("style") or "educational",
                narrator=channel_ops.get("narrator") or kwargs.get("narrator") or "professor",
                command=kwargs.get("command") or "",
                constraints=constraints,
                run_immediately=run_immediately,
            )
        except Exception as exc:  # noqa: BLE001
            queued = {"error": str(exc)[:200]}

    return {
        "ok": bool(research.get("ok") and ops.get("ok")),
        "manual_editing_required": False,
        "research": research,
        "studio_ops": ops,
        "channel_route": channel_route,
        "enqueue": queued,
        "note": "Opportunity brief auto-wired into Research + Studio Ops + Channel OS routing",
    }
