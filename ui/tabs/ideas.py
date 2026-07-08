"""Ideas tab — the AI Command Center flow. Rendering only; logic lives in services.ideation."""

from __future__ import annotations

import streamlit as st

from core import state
from core.constants import EXAMPLE_COMMANDS, IDEAS_PER_BATCH
from services import ideation, pipeline
from ui import components, notify


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

    with st.spinner("✨ Generational is thinking... generating your content..."):
        result = ideation.run_command(command, count=IDEAS_PER_BATCH, model=st.session_state.selected_model)

    error = result.pop("error", None)
    tokens_used = result.pop("tokens_used", 0)

    st.session_state.current_result = result
    state.record_ideas_generated(len(result["ideas"]))
    state.add_token_usage(tokens_used)

    if not st.session_state.current_project_name:
        st.session_state.project_name_input = result["niche"]

    idea_count = len(result["ideas"])
    if result["demo_mode"]:
        if error:
            st.warning(f"⚠️ Demo Mode fallback — AI generation failed: {error}")
            notify.error("AI generation failed, showing demo ideas.")
        else:
            st.info("🟡 Demo Mode — add an OpenAI API key in **Settings** to generate real AI content.")
            notify.success(f"Generated {idea_count} demo ideas!")
    else:
        notify.success(f"Generated {idea_count} AI-powered ideas!")


def _render_breakdown(result: dict) -> None:
    st.subheader("📋 Command Breakdown")
    cols = st.columns(3)
    cols[0].metric("Detected Niche", result["niche"])
    cols[1].metric("Videos Requested", result["video_count"])
    cols[2].metric("Mode", "Demo" if result["demo_mode"] else "Live AI")
    st.info(f"**Content Goal:** {result['goal']}")
