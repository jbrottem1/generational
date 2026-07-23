"""Cost dashboard aggregation over ProviderRuntime usage."""

from __future__ import annotations


def get_cost_dashboard() -> dict:
    from services.provider_runtime import get_provider_runtime
    from services.studio.providers import get_provider_dashboard

    runtime = get_provider_runtime()
    usage = runtime.usage_summary() if hasattr(runtime, "usage_summary") else {}
    dash = get_provider_dashboard()

    per_provider = []
    tokens = images = video_min = voice_min = music = publish_calls = 0
    for name, info in (usage or {}).items():
        if not isinstance(info, dict):
            continue
        cost = float(info.get("total_cost_usd") or 0)
        calls = int(info.get("calls") or 0)
        per_provider.append(
            {
                "provider": name,
                "calls": calls,
                "successes": int(info.get("successes") or 0),
                "failures": int(info.get("failures") or 0),
                "cost_usd": round(cost, 4),
                "tokens": int(info.get("tokens") or info.get("total_tokens") or 0),
                "images": int(info.get("images") or 0),
                "video_minutes": float(info.get("video_minutes") or 0),
                "voice_minutes": float(info.get("voice_minutes") or 0),
                "music": int(info.get("music") or 0),
                "publish_calls": int(info.get("publish_calls") or 0),
            }
        )
        tokens += int(info.get("tokens") or info.get("total_tokens") or 0)
        images += int(info.get("images") or 0)
        video_min += float(info.get("video_minutes") or 0)
        voice_min += float(info.get("voice_minutes") or 0)
        music += int(info.get("music") or 0)
        publish_calls += int(info.get("publish_calls") or 0)

    per_provider.sort(key=lambda r: -r["cost_usd"])
    return {
        "total_cost_usd": dash.get("total_cost_usd", 0),
        "total_calls": dash.get("total_calls", 0),
        "tokens": tokens,
        "images": images,
        "video_minutes": round(video_min, 2),
        "voice_minutes": round(voice_min, 2),
        "music": music,
        "publishing_calls": publish_calls,
        "per_provider": per_provider,
        "per_project": [],  # filled when project-scoped usage lands
        "per_campaign": [],
        "period": "session",
        "note": "Costs are session/runtime estimates until durable billing export is enabled.",
    }
