"""Canonical data shapes shared across the app.

Results and projects are plain dicts (they round-trip through JSON and
Streamlit session state), but their shape is defined here in one place
instead of being rebuilt ad hoc in each tab.

Idea dict keys: title, hook, script, cta, hashtags, thumbnail_concept.
"""

from __future__ import annotations

# Fields persisted on projects so Successful runs leave inspectable artifacts
# after reload (RC1 output-visibility requirement).
_PROJECT_OPTIONAL_FIELDS = (
    "research",
    "research_bundle",
    "quality_summary",
    "production_dashboard",
    "production_packages",
    "unified_packages",
    "stage_reports",
    "studio_settings",
    "platform",
    "production_report",
    "render_summary",
    "seo_optimization_report",
    "publishing_result",
    "publish_schedule",
    "analytics_summary",
    "analytics_package",
    "learning_report",
    "learning_metadata",
    "learning_recommendations",
    "provider_usage",
    "estimated_cost_usd",
    "workflow_run_id",
    "workflow_status",
    "pipeline_steps",
    "pipeline_state",
    "trend_opportunities",
    "trend_dashboard",
    "top_opportunity",
    "settings_preview",
    "longform_job_id",
)


def build_result(
    command: str,
    niche: str,
    video_count: int,
    goal: str,
    ideas: list,
    demo_mode: bool,
    model: str,
) -> dict:
    """The in-session result of running a command (st.session_state.current_result)."""
    return {
        "command": command,
        "niche": niche,
        "video_count": video_count,
        "goal": goal,
        "ideas": ideas,
        "demo_mode": demo_mode,
        "model": model,
    }


def project_from_result(name: str, result: dict) -> dict:
    """A persistable project payload derived from a session result."""
    project = {
        "name": name.strip(),
        "command": result["command"],
        "niche": result["niche"],
        "video_count": result["video_count"],
        "goal": result["goal"],
        "ideas": result["ideas"],
        "demo_mode": result["demo_mode"],
        "model": result["model"],
    }
    for key in _PROJECT_OPTIONAL_FIELDS:
        if result.get(key) not in (None, "", [], {}):
            project[key] = result[key]
    return project


def result_from_project(project: dict) -> dict:
    """Rehydrate a session result from a stored project (tolerates old formats)."""
    ideas = project.get("ideas", [])
    result = build_result(
        command=project.get("command", ""),
        niche=project.get("niche", "General Content"),
        video_count=project.get("video_count", len(ideas)),
        goal=project.get("goal", ""),
        ideas=ideas,
        demo_mode=project.get("demo_mode", True),
        model=project.get("model", "—"),
    )
    for key in _PROJECT_OPTIONAL_FIELDS:
        if key in project and project.get(key) not in (None,):
            result[key] = project[key]
    return result
