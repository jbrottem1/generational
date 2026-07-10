"""Production readiness for Studio UI."""

from __future__ import annotations


def get_production_readiness() -> dict:
    """Studio-facing wrapper around the readiness aggregator + master pipeline."""
    from services.readiness import build_readiness_report
    from services.master_pipeline import production_readiness_report, registry_summary

    base = build_readiness_report()
    master = production_readiness_report()
    summary = registry_summary()
    base["master_pipeline"] = {
        "score": master.get("score"),
        "band": master.get("band"),
        "blockers": master.get("blockers"),
        "placeholders": master.get("placeholders"),
        "next_priorities": master.get("next_priorities"),
        "estimated_time_to_first_production": master.get("estimated_time_to_first_production"),
        "estimated_time_to_first_publish": master.get("estimated_time_to_first_publish"),
        "providers_configured": master.get("providers_configured"),
        "ffmpeg_available": master.get("ffmpeg_available"),
        "first_autonomous_checklist": master.get("first_autonomous_checklist"),
        "oauth_status": master.get("oauth_status"),
        "remaining_apis": master.get("remaining_apis"),
        "recommended_next_milestone": master.get("recommended_next_milestone"),
        "registry": summary,
    }
    return base
