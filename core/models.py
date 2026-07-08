"""Canonical data shapes shared across the app.

Results and projects are plain dicts (they round-trip through JSON and
Streamlit session state), but their shape is defined here in one place
instead of being rebuilt ad hoc in each tab.

Idea dict keys: title, hook, script, cta, hashtags, thumbnail_concept.
"""

from __future__ import annotations


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
    if result.get("research"):
        project["research"] = result["research"]
    if result.get("quality_summary"):
        project["quality_summary"] = result["quality_summary"]
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
    if project.get("research"):
        result["research"] = project["research"]
    if project.get("quality_summary"):
        result["quality_summary"] = project["quality_summary"]
    return result
