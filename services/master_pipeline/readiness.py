"""Production readiness scoring for the master pipeline."""

from __future__ import annotations

from typing import Any

from services.master_pipeline.registry import registry_summary


PROVIDER_ENVS = [
    ("openai", "OPENAI_API_KEY", True),  # script + TTS + images
    ("anthropic", "ANTHROPIC_API_KEY", False),
    ("gemini", "GOOGLE_API_KEY", False),
    ("elevenlabs", "ELEVENLABS_API_KEY", False),  # preferred TTS; OpenAI TTS also works
    ("runway", "RUNWAY_API_KEY", False),
    ("flux", "BFL_API_KEY", False),
    ("fal", "FAL_KEY", False),
    ("replicate", "REPLICATE_API_TOKEN", False),
    ("ideogram", "IDEOGRAM_API_KEY", False),
    ("youtube", "YOUTUBE_ACCESS_TOKEN", False),
    ("tiktok", "TIKTOK_ACCESS_TOKEN", False),
    ("instagram", "INSTAGRAM_ACCESS_TOKEN", False),
    ("facebook", "FACEBOOK_ACCESS_TOKEN", False),
    ("linkedin", "LINKEDIN_ACCESS_TOKEN", False),
    ("x", "X_ACCESS_TOKEN", False),
]


def provider_integration_status() -> list[dict[str, Any]]:
    from services.provider_runtime.config import has_credential

    rows = []
    for name, env, required_for_real_video in PROVIDER_ENVS:
        present = bool(has_credential(env))
        rows.append(
            {
                "provider": name,
                "env_var": env,
                "configured": present,
                "status": "connected" if present else "configurable",
                "required_for_real_mp4": required_for_real_video,
            }
        )
    return rows


def production_readiness_report() -> dict[str, Any]:
    """Evidence-based readiness score for end-to-end video production."""
    summary = registry_summary()
    providers = provider_integration_status()
    configured = [p for p in providers if p["configured"]]

    try:
        from services.media_production.readiness import media_production_readiness

        media = media_production_readiness()
    except Exception:  # noqa: BLE001
        media = {}

    if media.get("score") is not None:
        return {
            "score": int(media["score"]),
            "band": str(media.get("band") or "architecture_ready"),
            "notes": list(media.get("notes") or []),
            "blockers": list(media.get("blockers") or []),
            "placeholders": list(media.get("placeholders") or []),
            "registry": {
                "agent_count": summary["agent_count"],
                "agents_ready": summary["agents_ready"],
                "agents_partial": summary["agents_partial"],
                "agents_stub": summary["agents_stub"],
                "engine_count": summary["engine_count"],
                "engines_ready": summary["engines_ready"],
            },
            "providers": providers,
            "providers_configured": len(configured),
            "media_production": media,
            "oauth_status": media.get("oauth_status") or {},
            "ffmpeg_available": media.get("ffmpeg_available"),
            "estimated_time_to_first_production": media.get(
                "estimated_time_to_first_autonomous_video", "1–2 days"
            ),
            "estimated_time_to_first_publish": (
                "immediate dry-run; live after OAuth"
                if media.get("oauth_status") and any((media.get("oauth_status") or {}).values())
                else "dry-run now; live publish after OAuth tokens"
            ),
            "first_autonomous_checklist": media.get("first_autonomous_checklist") or [],
            "remaining_apis": media.get("remaining_apis") or [],
            "integrated_providers": media.get("integrated_providers") or {},
            "next_priorities": [
                media.get("recommended_next_milestone") or "First real MP4 assembly",
                "Confirm ProductionIntegrityGate passes with real media",
                "Add YouTube OAuth for first live publish",
                "Wire Runway/Fal async job polling when video APIs are keyed",
            ],
            "recommended_next_milestone": media.get("recommended_next_milestone"),
        }

    return {
        "score": 50,
        "band": "architecture_ready",
        "notes": ["Orchestrator path live"],
        "blockers": ["Media production readiness module unavailable"],
        "registry": summary,
        "providers": providers,
        "providers_configured": len(configured),
        "estimated_time_to_first_production": "unknown",
        "estimated_time_to_first_publish": "unknown",
        "next_priorities": ["Restore media_production readiness module"],
    }
