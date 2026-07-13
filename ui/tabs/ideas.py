"""Ideas tab — the AI Command Center flow. Rendering only; logic lives in services.ideation."""

from __future__ import annotations

import streamlit as st

from core import state
from core.constants import CANDIDATE_IDEAS, EXAMPLE_COMMANDS, IDEAS_PER_BATCH
from services import ideation, pipeline
from ui import components, notify
from ui.project_state import queue_project_name_update


def _fill_example(example: str) -> None:
    st.session_state.command_text = example


def render() -> None:
    command = st.text_area(
        "Command",
        key="command_text",
        placeholder="Tell Generational what to create...",
        height=110,
        label_visibility="collapsed",
    )

    st.caption("Try an example:")
    example_cols = st.columns(2)
    for index, example in enumerate(EXAMPLE_COMMANDS):
        example_cols[index % 2].button(
            example,
            key=f"example_{index}",
            on_click=_fill_example,
            args=(example,),
            use_container_width=True,
        )

    run_clicked = st.button("🚀 Run Command", type="primary", use_container_width=True)

    if run_clicked:
        _handle_run(command)

    result = st.session_state.current_result
    if result:
        st.divider()
        _render_breakdown(result)

        st.subheader("💡 Generated Ideas")
        if result.get("pipeline_steps"):
            st.caption(
                f"Top {len(result['ideas'])} of {CANDIDATE_IDEAS} candidates — "
                "selected by the Psychology & Virality Engine (18-dimension ViralScore) and weighted "
                "ranking, scripted, critiqued, auto-revised, SEO-packaged, and screened for "
                "production risk (Threat Detection)."
            )
        for index, idea in enumerate(result["ideas"], start=1):
            components.idea_card(index, idea)

        st.subheader("⚙️ Next Pipeline Steps")
        components.pipeline_flow(pipeline.next_stages())

        st.divider()
        st.caption("💾 Want to keep this? Head to the **Projects** tab to save it.")


def _handle_run(command: str) -> None:
    if not command.strip():
        st.warning("Please enter a command before running it.")
        return

    with st.spinner("🔬 Knowledge Engine → 🧠 Intelligence pipeline → 🎬 Media production..."):
        result = ideation.run_command(
            command,
            count=IDEAS_PER_BATCH,
            model=st.session_state.selected_model,
            threshold=st.session_state.publish_threshold,
            voice_mode=st.session_state.voice_mode,
            research_settings={
                "enabled_providers": st.session_state.research_enabled_providers,
                "cache_ttl_hours": st.session_state.research_cache_hours,
                "max_sources": st.session_state.research_max_sources,
                "min_confidence": st.session_state.research_min_confidence,
                "research_depth": st.session_state.research_depth,
                "science_medical_strict": st.session_state.science_medical_strict,
                "citation_required": st.session_state.citation_required,
                "research_confidence_threshold": st.session_state.research_confidence_threshold,
                "max_unsupported_claims": st.session_state.max_unsupported_claims,
                "min_claim_confidence": st.session_state.min_claim_confidence,
            },
            project_name=st.session_state.current_project_name,
        )

    error = result.pop("error", None)
    tokens_used = result.pop("tokens_used", 0)

    st.session_state.current_result = result
    state.record_ideas_generated(len(result["ideas"]))
    state.add_token_usage(tokens_used)

    if not st.session_state.current_project_name:
        queue_project_name_update(result["niche"])

    idea_count = len(result["ideas"])
    publishable = result.get("quality_summary", {}).get("publishable", idea_count)
    produced = len(result.get("production_packages", []))
    if result["demo_mode"]:
        st.info(
            "🟡 Demo Mode — set `OPENAI_API_KEY` in the project `.env` "
            "(or **Settings → API Keys**), then restart Streamlit."
        )
    if error:
        st.warning(f"⚠️ One or more AI calls failed and used heuristic fallbacks: {error}")
    if result.get("production_error"):
        st.warning(f"⚠️ Media production issue: {result['production_error']}")
    msg = f"Pipeline complete — {idea_count} scripts, {publishable} publish-ready"
    if produced:
        msg += f", {produced} production package(s) built"
    notify.success(msg)


def _render_breakdown(result: dict) -> None:
    st.subheader("📋 Command Breakdown")
    cols = st.columns(3)
    cols[0].metric("Detected Niche", result["niche"])
    cols[1].metric("Videos Requested", result["video_count"])
    cols[2].metric("Mode", "Demo" if result["demo_mode"] else "Live AI")

    opportunities = result.get("trend_opportunities")
    if opportunities:
        st.markdown("**📡 Trend Discovery**")
        components.trend_dashboard(result.get("trend_dashboard", {}), opportunities)

    research = result.get("research")
    if research:
        cols = st.columns(3)
        cols[0].metric("Audience", research.get("audience", "—"))
        cols[1].metric("Search Intent", research.get("search_intent", "—"))
        cols[2].metric("Trend Strength", f"{research.get('trend_strength', '—')}/100")
        if research.get("summary"):
            st.info(f"**🔍 Research Summary:** {research['summary']}")
        source_count = research.get("source_count", 0)
        if source_count:
            providers = research.get("providers_used", [])
            conf = research.get("research_confidence")
            st.caption(
                f"📚 {source_count} vetted source(s)"
                + (f" · confidence {conf:.0%}" if conf else "")
                + (f" · cached" if research.get("cached") else "")
                + (f" · {len(providers)} provider(s)" if providers else "")
            )
        facts = research.get("important_facts", [])
        if facts:
            with st.expander("📊 Key Research Facts"):
                for fact in facts[:5]:
                    st.markdown(f"- {fact}")

    st.info(f"**Content Goal:** {result['goal']}")

    steps = result.get("pipeline_steps")
    if steps:
        marks = {"succeeded": "✓", "skipped": "·", "failed": "✗"}
        flow = " → ".join(f"{step['engine']} {marks.get(step['status'], '?')}" for step in steps)
        st.caption(f"🧠 Intelligence pipeline: {flow}")

    summary = result.get("quality_summary")
    if summary:
        held = summary.get("held", 0)
        message = (
            f"**Quality gate (threshold {summary.get('threshold')}):** "
            f"{summary.get('publishable', 0)} publish-ready"
        )
        message += f" · {held} held back" if held else " · none held back"
        st.markdown(message)

    dashboard = result.get("production_dashboard")
    if dashboard:
        st.markdown("**🎬 Production Pipeline**")
        components.production_dashboard(dashboard)
        queued = result.get("queued_count", 0)
        if queued:
            st.caption(f"📤 {queued} render package(s) queued for publishing.")
