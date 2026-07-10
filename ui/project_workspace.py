"""Project Workspace — project list + full-screen Asset Workspace.

Does not regenerate or delete generated content. Opens assets into a dedicated
viewer at the top of the page with clear pre-production labeling.
"""

from __future__ import annotations

import copy
import json
from datetime import datetime, timezone
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from core import storage
from core.log import get_logger
from core.models import normalize_idea_asset, normalize_project_for_workspace
from core.script_models import apply_script_to_asset, asset_has_video_script
from services.asset_production import run_asset_production
from services.script_generator import generate_video_script
from ui import notify
from ui.production_pipeline import render_production_pipeline
from ui.script_tab import render_script_tab

logger = get_logger(__name__)


def _active_project() -> dict | None:
    project = st.session_state.get("opened_project_data")
    if isinstance(project, dict) and project.get("ideas") is not None:
        return normalize_project_for_workspace(project)

    project_id = st.session_state.get("selected_project_id") or ""
    name = st.session_state.get("current_project_name") or ""
    loaded = None
    if project_id:
        loaded = storage.load_project_by_id(project_id)
    if loaded is None and name:
        loaded = storage.load_project(name)
    if loaded is None and st.session_state.get("current_result"):
        result = dict(st.session_state.current_result)
        result.setdefault("name", name or "Opened project")
        loaded = result
    if loaded is None:
        return None
    normalized = normalize_project_for_workspace(loaded)
    st.session_state.opened_project_data = normalized
    return normalized


def _pending_script_key(asset_id: str) -> str:
    return f"script_gen_pending_{asset_id}"


def _script_generating_key(asset_id: str) -> str:
    return f"script_gen_active_{asset_id}"


def _production_running_key(asset_id: str) -> str:
    return f"asset_production_active_{asset_id}"


def _pending_production_key(asset_id: str) -> str:
    return f"asset_production_pending_{asset_id}"


def _run_script_generation(project: dict, asset: dict, index: int) -> bool:
    """Generate a structured video script with visible progress. Returns success."""
    asset_id = str(asset.get("asset_id") or f"asset_{index}")
    st.session_state[_script_generating_key(asset_id)] = True
    progress_messages: list[str] = []

    def on_progress(message: str) -> None:
        progress_messages.append(message)
        logger.info("workspace.script_progress | asset_id=%s step=%s", asset_id, message)

    try:
        with st.status("Script generation in progress", expanded=True) as status:
            result = generate_video_script(
                asset,
                project,
                model=str(project.get("model") or ""),
                on_progress=lambda msg: (on_progress(msg), status.update(label=msg)),
            )
            if result.ok and result.script:
                status.update(label="Saving project", state="running")
                updated = apply_script_to_asset(asset, result.script)
                ideas = list(project.get("ideas") or [])
                ideas[index] = updated
                project["ideas"] = ideas
                if result.tokens_used:
                    project["token_usage"] = int(project.get("token_usage") or 0) + result.tokens_used
                _persist_project(project)
                status.update(label="Script saved", state="complete")
                if result.error:
                    notify.warning(result.error)
                else:
                    notify.success("Structured video script generated and saved.")
                logger.info(
                    "workspace.script_generated | asset_id=%s segments=%s demo=%s",
                    asset_id,
                    len(result.script.segments),
                    result.demo_mode,
                )
                return True

            status.update(label="Script generation failed", state="error")
            notify.error(result.error or "Script generation failed. Please try again.")
            logger.error("workspace.script_failed | asset_id=%s error=%s", asset_id, result.error)
            return False
    finally:
        st.session_state[_script_generating_key(asset_id)] = False
        st.session_state[_pending_script_key(asset_id)] = False


def _run_full_asset_production(project: dict, asset: dict, index: int) -> bool:
    """Run Idea→…→Export MP4 automatically with live pipeline progress."""
    asset_id = str(asset.get("asset_id") or f"asset_{index}")
    st.session_state[_production_running_key(asset_id)] = True
    live_placeholder = st.empty()

    def on_progress(event: dict) -> None:
        updated = event.get("asset") or asset
        ideas = list(project.get("ideas") or [])
        ideas[index] = updated
        project["ideas"] = ideas
        st.session_state.selected_asset = updated
        st.session_state.opened_project_data = project
        with live_placeholder.container():
            render_production_pipeline(updated, script_generating=False)
            st.caption(
                f"{event.get('label')}: {event.get('status')} — {event.get('message')} "
                f"(retries={event.get('retry_count', 0)}, {event.get('execution_time_sec', 0)}s)"
            )
        logger.info(
            "workspace.production_progress | asset_id=%s stage=%s status=%s",
            asset_id,
            event.get("stage"),
            event.get("status"),
        )

    try:
        with st.status("Building video from this asset…", expanded=True) as status:
            status.update(label="Starting production pipeline", state="running")
            result_asset = run_asset_production(
                asset,
                project,
                on_progress=lambda event: (
                    on_progress(event),
                    status.update(label=f"{event.get('label')}: {event.get('message')}", state="running"),
                ),
            )
            ideas = list(project.get("ideas") or [])
            ideas[index] = result_asset
            project["ideas"] = ideas
            _persist_project(project)
            st.session_state.selected_asset = result_asset

            if result_asset.get("production_ok"):
                mp4 = (result_asset.get("render_package") or {}).get("mp4_path") or ""
                status.update(label="Production complete", state="complete")
                notify.success(
                    f"Video package ready{f' — {mp4}' if mp4 else ''}. "
                    + (
                        "Publish prep awaiting OAuth."
                        if (result_asset.get("publish_package") or {}).get("status") == "awaiting_oauth"
                        else "Ready for publishing."
                    )
                )
                logger.info(
                    "workspace.production_complete | asset_id=%s mp4=%s",
                    asset_id,
                    mp4,
                )
                return True

            status.update(label="Production failed", state="error")
            notify.error(result_asset.get("production_error") or "Production failed")
            logger.error(
                "workspace.production_failed | asset_id=%s error=%s",
                asset_id,
                result_asset.get("production_error"),
            )
            return False
    finally:
        st.session_state[_production_running_key(asset_id)] = False
        st.session_state[_pending_production_key(asset_id)] = False


def _persist_asset_at_index(project: dict, updated_asset: dict, index: int) -> None:
    ideas = list(project.get("ideas") or [])
    ideas[index] = updated_asset
    project["ideas"] = ideas
    _persist_project(project)
    st.session_state.selected_asset = updated_asset


def _persist_project(project: dict) -> None:
    normalized = normalize_project_for_workspace(project)
    storage.save_project(normalized)
    st.session_state.opened_project_data = normalized
    from core.models import result_from_project

    st.session_state.current_result = result_from_project(normalized)


def _clamp_index(index: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(int(index), total - 1))


def _scroll_workspace_to_top() -> None:
    """Force the Streamlit main pane to the top so Asset Workspace is visible."""
    components.html(
        """
        <div id="generational-asset-anchor"></div>
        <script>
        (function () {
          try {
            const doc = window.parent.document;
            const main = doc.querySelector('section.main')
              || doc.querySelector('[data-testid="stAppViewContainer"]')
              || doc.documentElement;
            if (main && main.scrollTo) { main.scrollTo({ top: 0, behavior: 'instant' }); }
            window.parent.scrollTo(0, 0);
          } catch (e) {}
        })();
        </script>
        """,
        height=0,
    )


def _open_asset(index: int, ideas: list[dict], *, source: str = "open_button") -> None:
    """Load the selected asset into session state and open the Asset Workspace."""
    total = len(ideas)
    index = _clamp_index(index, total)
    asset = normalize_idea_asset(ideas[index] if total else {}, index=index)
    asset_id = str(asset.get("asset_id") or f"asset_{index + 1}")

    st.session_state.project_asset_index = index
    st.session_state.active_asset_id = asset_id
    st.session_state.asset_detail_visible = True
    st.session_state.asset_workspace_open = True
    st.session_state.show_build_video_checklist = False
    st.session_state.selected_asset = asset
    st.session_state._scroll_asset_workspace = True
    st.session_state._asset_open_notice = {
        "index": index,
        "title": asset.get("title") or f"Asset {index + 1}",
        "asset_id": asset_id,
        "source": source,
    }

    logger.info(
        "workspace.asset_open_clicked | source=%s index=%s asset_id=%s title=%s",
        source,
        index,
        asset_id,
        (asset.get("title") or "")[:80],
    )


def _export_asset(asset: dict, project: dict) -> str:
    payload = {
        "title": asset.get("title"),
        "hook": asset.get("hook"),
        "script": asset.get("script"),
        "video_script": asset.get("video_script"),
        "production_pipeline": asset.get("production_pipeline"),
        "description": asset.get("description"),
        "cta": asset.get("cta"),
        "keywords": asset.get("keywords") or asset.get("suggested_seo_keywords"),
        "hashtags": asset.get("hashtags"),
        "thumbnail_concept": asset.get("thumbnail_concept"),
        "visual_prompts": asset.get("visual_prompts"),
        "workspace_status": asset.get("workspace_status"),
        "platform": project.get("platform") or (project.get("studio_settings") or {}).get("platform"),
        "provider": project.get("provider"),
        "model": project.get("model"),
        "token_usage": project.get("token_usage"),
        "created_at": project.get("created_at"),
        "asset_id": asset.get("asset_id"),
        "content_type": "pre_production_package",
        "video_rendered": False,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def _scene_plan(asset: dict) -> list[dict[str, Any]]:
    """Build a readable scene list from structured script / visual package (read-only)."""
    scenes: list[dict[str, Any]] = []
    video_script = asset.get("video_script") if isinstance(asset.get("video_script"), dict) else {}
    vs_segments = video_script.get("segments") if isinstance(video_script, dict) else None
    if isinstance(vs_segments, list) and vs_segments:
        for i, segment in enumerate(vs_segments):
            if not isinstance(segment, dict):
                continue
            start = segment.get("start_time", 0)
            end = segment.get("end_time", "")
            scenes.append(
                {
                    "index": i + 1,
                    "title": segment.get("segment_type") or f"Segment {i + 1}",
                    "narration": segment.get("voiceover") or "",
                    "visual": segment.get("delivery") or segment.get("retention_device") or "",
                    "duration": round(float(end) - float(start), 1) if end != "" else "",
                }
            )
        if scenes:
            return scenes

    structured = asset.get("structured_script") if isinstance(asset.get("structured_script"), dict) else {}
    breakdown = structured.get("scene_breakdown") if isinstance(structured, dict) else None
    if isinstance(breakdown, list) and breakdown:
        for i, scene in enumerate(breakdown):
            if isinstance(scene, dict):
                scenes.append(
                    {
                        "index": i + 1,
                        "title": scene.get("title") or scene.get("label") or f"Scene {i + 1}",
                        "narration": scene.get("narration") or scene.get("voiceover") or scene.get("text") or "",
                        "visual": scene.get("visual") or scene.get("visual_intent") or scene.get("description") or "",
                        "duration": scene.get("estimated_duration_sec") or scene.get("duration_sec") or "",
                    }
                )
            else:
                scenes.append({"index": i + 1, "title": f"Scene {i + 1}", "narration": str(scene), "visual": "", "duration": ""})
        return scenes

    sections = asset.get("script_sections") or structured.get("sections") or []
    if isinstance(sections, list) and sections:
        for i, section in enumerate(sections):
            if not isinstance(section, dict):
                continue
            scenes.append(
                {
                    "index": i + 1,
                    "title": section.get("label") or section.get("key") or f"Scene {i + 1}",
                    "narration": section.get("narration") or section.get("text") or "",
                    "visual": section.get("visual_intent") or section.get("broll_type") or "",
                    "duration": section.get("estimated_duration_sec") or "",
                }
            )
        if scenes:
            return scenes

    visual_pkg = asset.get("visual_package") if isinstance(asset.get("visual_package"), dict) else {}
    vp_scenes = visual_pkg.get("scenes") or visual_pkg.get("storyboard") or []
    if isinstance(vp_scenes, list):
        for i, scene in enumerate(vp_scenes):
            if isinstance(scene, dict):
                scenes.append(
                    {
                        "index": i + 1,
                        "title": scene.get("title") or f"Scene {i + 1}",
                        "narration": scene.get("narration") or "",
                        "visual": scene.get("description") or scene.get("visual") or str(scene.get("prompt") or ""),
                        "duration": scene.get("duration_sec") or "",
                    }
                )
    return scenes


def _has_rendered_video(asset: dict, project: dict) -> bool:
    """Honest check — only true when a real (non-mock) MP4 path exists."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]

    def _exists(path: str) -> bool:
        if not path or str(path).startswith(("mock://", "runtime://")):
            return False
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = root / path
        return candidate.exists() and candidate.stat().st_size > 100

    for key in ("mp4_path", "video_path", "output_mp4", "rendered_video_path"):
        if _exists(str(asset.get(key) or project.get(key) or "")):
            return True
    render = asset.get("render_package") if isinstance(asset.get("render_package"), dict) else {}
    if render.get("mock"):
        return False
    if _exists(str(render.get("mp4_path") or render.get("output_file") or render.get("file_uri") or "")):
        return True
    return False


def _provider_connected(env_var: str) -> bool:
    try:
        from services.provider_runtime.config import has_credential

        return bool(has_credential(env_var))
    except Exception:  # noqa: BLE001
        return False


def render_workspace() -> None:
    """Render the Project Workspace for the currently opened project."""
    logger.info(
        "workspace.render_called | asset_index=%s workspace_open=%s",
        st.session_state.get("project_asset_index"),
        st.session_state.get("asset_workspace_open"),
    )

    for key, default in (
        ("asset_detail_visible", True),
        ("asset_workspace_open", True),
        ("active_asset_id", ""),
        ("selected_asset", None),
        ("show_build_video_checklist", False),
        ("_scroll_asset_workspace", False),
    ):
        if key not in st.session_state:
            st.session_state[key] = default

    project = _active_project()
    if not project:
        st.warning("No project is open. Returning to the project list.")
        st.session_state.projects_view = "list"
        st.rerun()
        return

    ideas = list(project.get("ideas") or [])
    total = len(ideas)
    index = _clamp_index(int(st.session_state.get("project_asset_index") or 0), total)
    st.session_state.project_asset_index = index

    notice = st.session_state.pop("_projects_open_notice", None)
    if notice:
        notify.success(f"Opened project '{notice}'")

    # --- Top navigation (always first) ---
    _render_top_nav(project, index, total)

    if total == 0:
        st.info("This project has no generated ideas/scripts yet.")
        return

    asset = normalize_idea_asset(ideas[index], index=index)
    st.session_state.active_asset_id = str(asset.get("asset_id") or f"asset_{index + 1}")
    st.session_state.selected_asset = asset
    st.session_state.asset_workspace_open = True
    st.session_state.asset_detail_visible = True

    if st.session_state.pop("_scroll_asset_workspace", False) or st.session_state.pop("_asset_open_notice", None):
        _scroll_workspace_to_top()

    # --- Asset Workspace (top of page) ---
    _render_asset_workspace(project, asset, index, total)

    st.divider()
    st.markdown(f"### Project assets ({total})")
    st.caption("Click **Open** to load an asset into the workspace above.")
    _render_asset_picker(project, ideas, index)
    _render_highlighted_asset_list(project, ideas, index)


def _render_top_nav(project: dict, index: int, total: int) -> None:
    cols = st.columns([1.3, 1, 1, 1.3, 1.5])
    if cols[0].button("← Back to Projects", key="ws_back_projects", use_container_width=True):
        st.session_state.projects_view = "list"
        st.session_state.asset_workspace_open = False
        st.session_state.show_build_video_checklist = False
        st.rerun()
    ideas = list(project.get("ideas") or [])
    if cols[1].button("◀ Previous Asset", key="ws_prev_asset", disabled=total <= 0 or index <= 0, use_container_width=True):
        _open_asset(index - 1, ideas, source="previous")
        st.rerun()
    if cols[2].button("Next Asset ▶", key="ws_next_asset", disabled=total <= 0 or index >= total - 1, use_container_width=True):
        _open_asset(index + 1, ideas, source="next")
        st.rerun()
    if cols[3].button("🎬 Return to Studio", key="ws_return_studio", use_container_width=True):
        st.session_state.projects_view = "list"
        st.session_state._projects_studio_hint = True
        notify.success("Project stays loaded — open the Studio tab to continue production.")
        st.rerun()
    cols[4].caption(f"{project.get('name', 'Project')[:40]} · Asset {index + 1}/{total}" if total else "No assets")


def _render_asset_workspace(project: dict, asset: dict, index: int, total: int) -> None:
    title = asset.get("title") or f"Asset {index + 1}"
    created = (project.get("created_at") or "")[:19].replace("T", " ") or "—"
    platform = (
        project.get("platform")
        or (project.get("studio_settings") or {}).get("platform")
        or asset.get("script_platform")
        or "—"
    )
    video_ready = _has_rendered_video(asset, project)

    st.markdown(f"# Now Viewing: {title}")
    if video_ready:
        st.success("Finished production package — MP4 exported.")
    else:
        st.info("Pre-production content package — press **Build Video From This Asset** to produce the MP4 automatically.")
    if not video_ready:
        st.caption("Script, scenes, and prompts may already exist. The full pipeline generates voice, visuals, captions, and the final render.")
    else:
        st.caption(f"Output: `{(asset.get('render_package') or {}).get('mp4_path') or '—'}`")

    meta = st.columns(5)
    meta[0].metric("Status", str(asset.get("workspace_status") or "draft"))
    meta[1].metric("Provider", str(project.get("provider") or "—"))
    meta[2].metric("Model", str(project.get("model") or "—"))
    meta[3].metric("Token usage", project.get("token_usage") or 0)
    meta[4].metric("Asset", f"{index + 1}/{total}")
    st.caption(f"Platform: {platform} · Created: {created} · id: `{asset.get('asset_id')}`")

    asset_id = str(asset.get("asset_id") or f"asset_{index}")
    script_generating = bool(st.session_state.get(_script_generating_key(asset_id)))
    production_running = bool(st.session_state.get(_production_running_key(asset_id)))

    render_production_pipeline(asset, script_generating=script_generating or production_running)

    # Process a queued generation request (set by Regenerate or cross-tab trigger).
    if st.session_state.pop(_pending_script_key(asset_id), False) and not script_generating and not production_running:
        _run_script_generation(project, asset, index)
        st.rerun()

    if st.session_state.pop(_pending_production_key(asset_id), False) and not production_running:
        _run_full_asset_production(project, asset, index)
        st.rerun()

    build_cols = st.columns([2, 1, 1])
    if build_cols[0].button(
        "🎬 Build Video From This Asset",
        key="ws_build_video",
        type="primary",
        use_container_width=True,
        disabled=production_running or script_generating,
    ):
        st.session_state.show_build_video_checklist = False
        st.session_state._scroll_asset_workspace = True
        st.session_state[_pending_production_key(asset_id)] = True
        logger.info("workspace.build_video_clicked | asset_id=%s", asset.get("asset_id"))
        st.rerun()
    if build_cols[1].button("◀ Previous Asset", key="ws_prev_inline", disabled=index <= 0, use_container_width=True):
        _open_asset(index - 1, list(project.get("ideas") or []), source="inline_prev")
        st.rerun()
    if build_cols[2].button("Next Asset ▶", key="ws_next_inline", disabled=index >= total - 1, use_container_width=True):
        _open_asset(index + 1, list(project.get("ideas") or []), source="inline_next")
        st.rerun()

    if st.session_state.get("show_build_video_checklist"):
        _render_build_video_checklist(project, asset)

    if asset_has_video_script(asset) and not (asset.get("render_package") or {}).get("mp4_path"):
        st.caption("Structured script ready — press **Build Video From This Asset** to run the full automatic pipeline.")
        if st.button("Show pre-render provider checklist", key="ws_show_checklist"):
            st.session_state.show_build_video_checklist = True
            st.rerun()
    elif (asset.get("render_package") or {}).get("mp4_path") and not (asset.get("render_package") or {}).get("mock"):
        st.success(f"Finished MP4: `{(asset.get('render_package') or {}).get('mp4_path')}`")

    overview, script_tab, scenes_tab, visuals_tab, audio_tab, render_tab, export_tab = st.tabs(
        ["Overview", "Script", "Scenes", "Visuals", "Audio", "Render", "Export"]
    )

    def _request_script_generation(force: bool = True) -> None:
        st.session_state[_pending_script_key(asset_id)] = True
        if force:
            logger.info("workspace.script_regenerate_requested | asset_id=%s", asset_id)
        st.rerun()

    with overview:
        _tab_overview(project, asset, platform, created)
        _render_asset_actions(project, asset, index, total)

    with script_tab:
        render_script_tab(
            project,
            asset,
            index,
            generating=script_generating,
            on_persist=lambda updated, idx: _persist_asset_at_index(project, updated, idx),
            on_generate=_request_script_generation,
            on_overview=lambda: st.info("Select the **Overview** tab above to return."),
        )

    with scenes_tab:
        _tab_scenes(asset)

    with visuals_tab:
        _tab_visuals(asset)

    with audio_tab:
        _tab_audio(asset)

    with render_tab:
        _tab_render(project, asset, video_ready)

    with export_tab:
        st.markdown("#### Export this pre-production package")
        st.caption("Exports JSON metadata + script package. This is not an MP4 download.")
        st.download_button(
            "📤 Download package JSON",
            data=_export_asset(asset, project),
            file_name=f"{(title).replace(' ', '_')[:40]}.json",
            mime="application/json",
            key=f"ws_export_tab_{index}",
            use_container_width=True,
        )
        export_script = asset.get("script") or ""
        if isinstance(asset.get("video_script"), dict):
            export_script = asset["video_script"].get("full_voiceover") or export_script
        st.code(export_script, language=None)


def _tab_overview(project: dict, asset: dict, platform: str, created: str) -> None:
    st.markdown("#### Title")
    st.write(asset.get("title") or "—")
    st.markdown("#### Hook")
    st.write(asset.get("hook") or "—")
    st.markdown("#### Description")
    st.write(asset.get("description") or "—")
    kw = asset.get("suggested_seo_keywords") or asset.get("keywords") or []
    tags = asset.get("hashtags") or []
    c1, c2 = st.columns(2)
    c1.markdown("#### SEO keywords")
    c1.write(", ".join(str(k) for k in kw) if kw else "—")
    c2.markdown("#### Hashtags & CTA")
    c2.write(", ".join(str(t) for t in tags) if tags else "—")
    c2.caption(f"CTA: {asset.get('cta') or '—'}")
    st.markdown("#### Thumbnail prompt")
    st.write(asset.get("thumbnail_concept") or "—")
    st.markdown("#### Meta")
    st.write(
        {
            "platform": platform,
            "provider": project.get("provider"),
            "model": project.get("model"),
            "status": asset.get("workspace_status") or "draft",
            "token_usage": project.get("token_usage") or 0,
            "created": created,
        }
    )


def _tab_scenes(asset: dict) -> None:
    st.markdown("#### Scene-by-scene visual plan")
    scenes = _scene_plan(asset)
    if not scenes:
        st.info("No scene breakdown stored. Visual prompts are available under the Visuals tab.")
        return
    for scene in scenes:
        with st.container(border=True):
            dur = f" · ~{scene['duration']}s" if scene.get("duration") else ""
            st.markdown(f"**Scene {scene['index']}: {scene['title']}**{dur}")
            if scene.get("narration"):
                st.markdown("*Voiceover*")
                st.write(scene["narration"])
            if scene.get("visual"):
                st.markdown("*Visual*")
                st.write(scene["visual"])


def _tab_visuals(asset: dict) -> None:
    st.markdown("#### Thumbnail prompt")
    st.write(asset.get("thumbnail_concept") or "—")
    st.markdown("#### Visual prompts")
    visuals = asset.get("visual_prompts") or []
    if visuals:
        for vp in visuals:
            st.markdown(f"- {vp}")
    else:
        st.write("—")
    broll = asset.get("broll_suggestions") or []
    if broll:
        st.markdown("#### B-roll suggestions")
        for item in broll:
            st.markdown(f"- {item}")
    visual_pkg = asset.get("visual_package") if isinstance(asset.get("visual_package"), dict) else {}
    if visual_pkg.get("summary"):
        st.markdown("#### Visual package summary")
        st.write(visual_pkg.get("summary"))
    if visual_pkg.get("aspect_ratio"):
        st.caption(f"Planned aspect ratio: {visual_pkg.get('aspect_ratio')}")


def _tab_audio(asset: dict) -> None:
    audio = asset.get("audio_package") if isinstance(asset.get("audio_package"), dict) else {}
    st.markdown("#### Audio plan (pre-production)")
    st.caption("Voice/music plans may exist as metadata. No finished audio file is implied.")
    if not audio:
        st.info("No audio package metadata on this asset yet.")
        st.write(f"Music style hint: {asset.get('music_style') or '—'}")
        return
    st.write(
        {
            "voice_style": audio.get("voice_style"),
            "audio_mood": audio.get("audio_mood"),
            "music_direction": audio.get("music_direction"),
            "summary": audio.get("summary"),
        }
    )
    if audio.get("narration_plan"):
        st.markdown("#### Narration plan")
        st.write(audio.get("narration_plan"))


def _tab_render(project: dict, asset: dict, video_ready: bool) -> None:
    st.markdown("#### Render status")
    if video_ready:
        st.success("Rendered video artifact detected.")
        mp4 = (asset.get("render_package") or {}).get("mp4_path") or asset.get("mp4_path")
        if mp4:
            st.code(mp4, language=None)
    else:
        st.warning("**Not rendered yet.** Press **Build Video From This Asset** to run the automatic pipeline.")
    render = asset.get("render_package") if isinstance(asset.get("render_package"), dict) else {}
    if render:
        st.markdown("#### Render package")
        st.write(
            {
                "mock": render.get("mock"),
                "mp4_path": render.get("mp4_path"),
                "aspect_ratio": render.get("aspect_ratio"),
                "duration_sec": render.get("duration_sec") or asset.get("estimated_runtime_sec"),
                "resolution": render.get("resolution"),
                "render_status": render.get("render_status"),
            }
        )
    arts = (asset.get("production_artifacts") or {}).get("files") or []
    if arts:
        st.markdown("#### Production artifacts")
        for path in arts[:30]:
            st.markdown(f"- `{path}`")
    else:
        st.caption(f"Estimated runtime: {asset.get('estimated_runtime_sec') or '—'} sec")


def _render_build_video_checklist(project: dict, asset: dict) -> None:
    with st.container(border=True):
        st.markdown("### Build Video — production checklist")
        st.caption("Connect providers and confirm settings before a real render can run. No video file is created by opening this checklist.")

        render = asset.get("render_package") if isinstance(asset.get("render_package"), dict) else {}
        visual_pkg = asset.get("visual_package") if isinstance(asset.get("visual_package"), dict) else {}
        audio = asset.get("audio_package") if isinstance(asset.get("audio_package"), dict) else {}
        settings = project.get("studio_settings") if isinstance(project.get("studio_settings"), dict) else {}

        voice_ok = _provider_connected("ELEVENLABS_API_KEY") or _provider_connected("OPENAI_API_KEY")
        image_ok = (
            _provider_connected("BFL_API_KEY")
            or _provider_connected("IDEOGRAM_API_KEY")
            or _provider_connected("OPENAI_API_KEY")
            or _provider_connected("REPLICATE_API_TOKEN")
            or _provider_connected("FAL_KEY")
        )
        video_ok = (
            _provider_connected("RUNWAY_API_KEY")
            or _provider_connected("PIKA_API_KEY")
            or _provider_connected("KLING_API_KEY")
            or _provider_connected("LUMA_API_KEY")
            or _provider_connected("GOOGLE_API_KEY")
        )

        rows = [
            ("Voice provider connection", "Connected" if voice_ok else "Not connected", voice_ok),
            ("Image / video provider connection", "Connected" if (image_ok or video_ok) else "Not connected", image_ok or video_ok),
            (
                "Music source",
                str(audio.get("music_direction") or asset.get("music_style") or settings.get("music") or "Not configured"),
                bool(audio.get("music_direction") or asset.get("music_style")),
            ),
            (
                "Captions",
                "Plan present" if (asset.get("structured_script") or {}).get("caption_plan") or render.get("caption_render_plan") else "Not configured",
                bool((asset.get("structured_script") or {}).get("caption_plan") or render.get("caption_render_plan")),
            ),
            (
                "Aspect ratio",
                str(render.get("aspect_ratio") or visual_pkg.get("aspect_ratio") or settings.get("aspect_ratio") or "Not set"),
                bool(render.get("aspect_ratio") or visual_pkg.get("aspect_ratio") or settings.get("aspect_ratio")),
            ),
            (
                "Duration",
                f"{render.get('duration_sec') or asset.get('estimated_runtime_sec') or '—'} sec",
                bool(render.get("duration_sec") or asset.get("estimated_runtime_sec")),
            ),
            (
                "Render status",
                "Rendered" if _has_rendered_video(asset, project) else "Not rendered (script package only)",
                _has_rendered_video(asset, project),
            ),
        ]

        for label, value, ok in rows:
            mark = "✓" if ok else "✗"
            st.markdown(f"- **{mark} {label}:** {value}")

        st.warning(
            "Building a finished MP4 requires connected media providers and a render pipeline run. "
            "This checklist does not create a video by itself."
        )
        if st.button("Close checklist", key="ws_close_checklist"):
            st.session_state.show_build_video_checklist = False
            st.rerun()


def _render_asset_picker(project: dict, ideas: list[dict], active_index: int) -> None:
    labels = []
    for i, idea in enumerate(ideas):
        asset = normalize_idea_asset(idea, index=i)
        prefix = "▶ " if i == active_index else ""
        labels.append(f"{prefix}{i + 1}. {asset.get('title') or f'Idea {i + 1}'}")

    selected_label = st.selectbox(
        "Jump to asset",
        options=labels,
        index=active_index,
        key=f"ws_asset_select_{project.get('project_id')}",
    )
    # Strip highlight prefix for index resolution
    clean_labels = [f"{i + 1}. {normalize_idea_asset(idea, index=i).get('title') or f'Idea {i + 1}'}" for i, idea in enumerate(ideas)]
    # selected_label may include ▶ prefix
    selected_index = active_index
    for i, label in enumerate(labels):
        if label == selected_label:
            selected_index = i
            break
    jump_cols = st.columns([1, 3])
    if jump_cols[0].button("Open selected", key="ws_open_selected", type="primary", use_container_width=True):
        _open_asset(selected_index, ideas, source="selectbox_open")
        st.rerun()
    _ = clean_labels  # reserved for future label normalization


def _render_highlighted_asset_list(project: dict, ideas: list[dict], active_index: int) -> None:
    for i, idea in enumerate(ideas):
        asset = normalize_idea_asset(idea, index=i)
        status = asset.get("workspace_status") or "draft"
        selected = i == active_index
        label = f"{'✅ SELECTED · ' if selected else ''}{i + 1}. {asset.get('title') or f'Idea {i + 1}'} · {status}"
        cols = st.columns([4, 1])
        if selected:
            cols[0].success(label)
        else:
            cols[0].markdown(label)
        open_key = f"ws_open_{project.get('project_id')}_{asset.get('asset_id')}_{i}"
        if cols[1].button("Open", key=open_key, use_container_width=True, type="primary" if selected else "secondary"):
            _open_asset(i, ideas, source="list_open")
            st.rerun()


def _render_asset_actions(project: dict, asset: dict, index: int, total: int) -> None:
    st.markdown("##### Asset actions")
    ideas = list(project.get("ideas") or [])

    with st.expander("✏️ Edit asset", expanded=False):
        title = st.text_input("Title", value=asset.get("title") or "", key=f"ws_edit_title_{index}")
        hook = st.text_area("Hook", value=asset.get("hook") or "", key=f"ws_edit_hook_{index}", height=80)
        script = st.text_area("Script", value=asset.get("script") or "", key=f"ws_edit_script_{index}", height=160)
        description = st.text_area(
            "Description",
            value=asset.get("description") or "",
            key=f"ws_edit_desc_{index}",
            height=80,
        )
        thumb = st.text_area(
            "Thumbnail prompt",
            value=asset.get("thumbnail_concept") or "",
            key=f"ws_edit_thumb_{index}",
            height=80,
        )
        if st.button("💾 Save", key=f"ws_save_edits_{index}", type="primary"):
            updated = {
                **asset,
                "title": title.strip() or asset.get("title"),
                "hook": hook,
                "script": script,
                "description": description,
                "thumbnail_concept": thumb,
                "workspace_status": "edited",
            }
            ideas[index] = updated
            project["ideas"] = ideas
            _persist_project(project)
            _open_asset(index, ideas, source="save")
            notify.success("Asset saved.")
            st.rerun()

    a1, a2, a3, a4 = st.columns(4)
    if a1.button("🔁 Regenerate", key=f"ws_regen_{index}", use_container_width=True):
        ideas[index] = {**asset, "workspace_status": "draft", "regenerate_requested": True}
        project["ideas"] = ideas
        _persist_project(project)
        notify.success("Marked for regeneration (no new generation from this view).")
        st.rerun()
    if a2.button("📄 Duplicate", key=f"ws_dup_{index}", use_container_width=True):
        clone = copy.deepcopy(asset)
        clone["asset_id"] = f"asset_{len(ideas) + 1}_{datetime.now(timezone.utc).strftime('%H%M%S')}"
        clone["title"] = f"{asset.get('title') or 'Asset'} (copy)"
        clone["workspace_status"] = "draft"
        ideas.append(clone)
        project["ideas"] = ideas
        project["video_count"] = len(ideas)
        _persist_project(project)
        _open_asset(len(ideas) - 1, ideas, source="duplicate")
        notify.success("Asset duplicated.")
        st.rerun()
    if a3.button("🗑️ Delete", key=f"ws_del_{index}", use_container_width=True):
        if total <= 1:
            notify.error("Cannot delete the last asset.")
        else:
            ideas.pop(index)
            ideas = [normalize_idea_asset(item, index=i) for i, item in enumerate(ideas)]
            project["ideas"] = ideas
            project["video_count"] = len(ideas)
            _persist_project(project)
            _open_asset(_clamp_index(index, len(ideas)), ideas, source="delete")
            notify.success("Asset deleted.")
            st.rerun()
    a4.download_button(
        "📤 Export",
        data=_export_asset(asset, project),
        file_name=f"{(asset.get('title') or f'asset_{index + 1}').replace(' ', '_')[:40]}.json",
        mime="application/json",
        key=f"ws_export_action_{index}",
        use_container_width=True,
    )

    b1, b2, _ = st.columns([1, 1, 4])
    if b1.button("✅ Approve", key=f"ws_approve_{index}", use_container_width=True):
        ideas[index] = {**asset, "workspace_status": "approved"}
        project["ideas"] = ideas
        _persist_project(project)
        notify.success("Asset approved.")
        st.rerun()
    if b2.button("⛔ Reject", key=f"ws_reject_{index}", use_container_width=True):
        ideas[index] = {**asset, "workspace_status": "rejected"}
        project["ideas"] = ideas
        _persist_project(project)
        notify.success("Asset rejected.")
        st.rerun()
