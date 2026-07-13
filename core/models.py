"""Canonical data shapes shared across the app.

Results and projects are plain dicts (they round-trip through JSON and
Streamlit session state), but their shape is defined here in one place
instead of being rebuilt ad hoc in each tab.

Idea dict keys: title, hook, script, cta, hashtags, thumbnail_concept.
"""

from __future__ import annotations

import uuid

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
    "project_id",
)


def ensure_project_id(project: dict, *, file_stem: str = "") -> str:
    """Assign a stable project_id if missing (never derived from display name alone)."""
    pid = (
        project.get("project_id")
        or project.get("id")
        or project.get("workflow_run_id")
    )
    if not pid and file_stem:
        pid = f"legacy_{file_stem}"
    if not pid:
        pid = uuid.uuid4().hex[:12]
    project["project_id"] = pid
    return pid


def project_widget_key(project: dict, action: str, index: int) -> str:
    """Globally unique Streamlit widget key for one project row."""
    pid = project.get("project_id") or ensure_project_id(
        project, file_stem=project.get("_storage_stem", "")
    )
    return f"{action}_project_{pid}_{index}"


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
    ensure_project_id(project)
    return project


def normalize_idea_asset(idea: dict | None, *, index: int = 0) -> dict:
    """Normalize one generated idea/script asset for workspace display.

    Older projects may omit fields or nest scripts differently; this keeps the
    Project Workspace resilient without regenerating content.
    """
    raw = dict(idea or {})
    script = raw.get("script") or ""
    video_script = raw.get("video_script") if isinstance(raw.get("video_script"), dict) else {}
    if isinstance(video_script, dict) and video_script.get("full_voiceover"):
        script = str(video_script.get("full_voiceover") or script)
    if not script and isinstance(raw.get("structured_script"), dict):
        script = (
            raw["structured_script"].get("full_script")
            or raw["structured_script"].get("script")
            or ""
        )
    if not script and isinstance(raw.get("script_sections"), list):
        script = "\n\n".join(
            str(section.get("text") or section.get("content") or "")
            for section in raw["script_sections"]
            if isinstance(section, dict)
        ).strip()

    keywords = raw.get("keywords") or raw.get("suggested_seo_keywords") or []
    if isinstance(keywords, str):
        keywords = [part.strip() for part in keywords.split(",") if part.strip()]

    visual_prompts = raw.get("visual_prompts") or []
    if isinstance(visual_prompts, str):
        visual_prompts = [visual_prompts] if visual_prompts.strip() else []
    if not visual_prompts and raw.get("broll_suggestions"):
        visual_prompts = list(raw.get("broll_suggestions") or [])

    thumbnail = (
        raw.get("thumbnail_concept")
        or raw.get("thumbnail_prompt")
        or ""
    )
    if not thumbnail and isinstance(raw.get("thumbnail_concepts"), list) and raw["thumbnail_concepts"]:
        first = raw["thumbnail_concepts"][0]
        thumbnail = first if isinstance(first, str) else str((first or {}).get("concept") or first)

    status = str(raw.get("workspace_status") or raw.get("status") or "draft").lower()
    if status not in {"draft", "approved", "rejected", "edited"}:
        status = "draft"

    asset_id = str(raw.get("asset_id") or raw.get("id") or f"asset_{index + 1}")
    return {
        **raw,
        "asset_id": asset_id,
        "title": str(raw.get("title") or f"Idea {index + 1}"),
        "hook": str(raw.get("hook") or ""),
        "script": str(script or ""),
        "description": str(raw.get("description") or raw.get("cta") or ""),
        "cta": str(raw.get("cta") or ""),
        "keywords": list(keywords),
        "suggested_seo_keywords": list(raw.get("suggested_seo_keywords") or keywords),
        "hashtags": list(raw.get("hashtags") or []),
        "thumbnail_concept": str(thumbnail or ""),
        "visual_prompts": list(visual_prompts),
        "workspace_status": status,
    }


def normalize_project_for_workspace(project: dict | None) -> dict:
    """Return a display-ready project dict with normalized idea assets."""
    project = dict(project or {})
    ensure_project_id(project)
    ideas = project.get("ideas") or project.get("generated_ideas") or project.get("assets") or []
    if not isinstance(ideas, list):
        ideas = []
    normalized = [normalize_idea_asset(idea if isinstance(idea, dict) else {"title": str(idea)}, index=i) for i, idea in enumerate(ideas)]
    project["ideas"] = normalized
    project["video_count"] = project.get("video_count") or len(normalized)
    project["command"] = project.get("command") or project.get("production_command") or project.get("goal") or ""
    project["created_at"] = project.get("created_at") or project.get("updated_at") or ""
    project["updated_at"] = project.get("updated_at") or project.get("created_at") or ""
    project["model"] = project.get("model") or "—"
    project["provider"] = (
        project.get("provider")
        or (next(iter((project.get("provider_usage") or {}).keys()), None) if project.get("provider_usage") else None)
        or ("demo" if project.get("demo_mode") else "openai")
    )
    usage = project.get("provider_usage") or {}
    token_usage = project.get("token_usage")
    if token_usage in (None, "", 0):
        # Best-effort: sum call counts when explicit tokens were not stored.
        token_usage = sum(int((entry or {}).get("calls") or 0) for entry in usage.values() if isinstance(entry, dict))
    project["token_usage"] = token_usage
    return project


def result_from_project(project: dict) -> dict:
    """Rehydrate a session result from a stored project (tolerates old formats).

    Preserves stored idea payloads verbatim for round-trip fidelity. UI layers
    should call ``normalize_project_for_workspace`` when display normalization
    is required.
    """
    project = dict(project or {})
    ensure_project_id(project)
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
    result["provider"] = project.get("provider", "—")
    result["token_usage"] = project.get("token_usage", 0)
    result["created_at"] = project.get("created_at", "")
    result["updated_at"] = project.get("updated_at", "")
    result["name"] = project.get("name", "")
    for key in _PROJECT_OPTIONAL_FIELDS:
        if key in project and project.get(key) not in (None,):
            result[key] = project[key]
    return result
