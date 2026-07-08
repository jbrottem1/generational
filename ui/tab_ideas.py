"""Ideas tab — the original AI Command Center flow, now powered by real AI."""

import streamlit as st

from core import ai, parsing, state
from core.constants import EXAMPLE_COMMANDS, PIPELINE_STEPS
from ui import notify


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
        _render_idea_cards(result)
        _render_pipeline()
        st.divider()
        st.caption("💾 Want to keep this? Head to the **Projects** tab to save it.")


def _handle_run(command: str) -> None:
    if not command.strip():
        st.warning("Please enter a command before running it.")
        return

    niche = parsing.detect_niche(command)
    video_count = parsing.detect_video_count(command)
    subject = parsing.detect_subject(command, fallback=niche.lower())
    goal = parsing.build_goal(subject)

    with st.spinner("✨ Generational is thinking... generating your content..."):
        result = ai.generate_content(command, niche, subject, 10, st.session_state.selected_model)

    ideas = result["ideas"]
    demo_mode = result["demo_mode"]

    st.session_state.current_result = {
        "command": command,
        "niche": niche,
        "video_count": video_count,
        "goal": goal,
        "ideas": ideas,
        "demo_mode": demo_mode,
        "model": st.session_state.selected_model,
    }
    state.record_ideas_generated(len(ideas))
    state.add_token_usage(result.get("tokens_used", 0))

    if not st.session_state.current_project_name:
        st.session_state.project_name_input = niche

    if demo_mode:
        if result.get("error"):
            st.warning(f"⚠️ Demo Mode fallback — AI generation failed: {result['error']}")
            notify.error("AI generation failed, showing demo ideas.")
        else:
            st.info("🟡 Demo Mode — add an OpenAI API key in **Settings** to generate real AI content.")
            notify.success("Generated 10 demo ideas!")
    else:
        notify.success("Generated 10 AI-powered ideas!")


def _render_breakdown(result: dict) -> None:
    st.subheader("📋 Command Breakdown")
    cols = st.columns(3)
    cols[0].metric("Detected Niche", result["niche"])
    cols[1].metric("Videos Requested", result["video_count"])
    cols[2].metric("Mode", "Demo" if result["demo_mode"] else "Live AI")
    st.info(f"**Content Goal:** {result['goal']}")


def _render_idea_cards(result: dict) -> None:
    st.subheader("💡 Generated Ideas")
    for index, idea in enumerate(result["ideas"], start=1):
        title = idea.get("title", f"Idea #{index}")
        with st.expander(f"{index}. {title}"):
            st.markdown(f"**🎣 Hook:** {idea.get('hook', '—')}")
            st.markdown("**📝 Script (15-30s):**")
            st.write(idea.get("script", "—"))
            st.markdown(f"**📣 CTA:** {idea.get('cta', '—')}")
            hashtags = idea.get("hashtags", [])
            if isinstance(hashtags, list):
                hashtags = " ".join(hashtags)
            st.markdown(f"**#️⃣ Hashtags:** {hashtags}")
            st.markdown(f"**🖼️ Thumbnail Concept:** {idea.get('thumbnail_concept', '—')}")


def _render_pipeline() -> None:
    st.subheader("⚙️ Next Pipeline Steps")
    cols = st.columns(len(PIPELINE_STEPS) * 2 - 1)
    for index, (icon, step) in enumerate(PIPELINE_STEPS):
        cols[index * 2].markdown(f"<div class='pipeline-step'>{icon}<br>{step}</div>", unsafe_allow_html=True)
        if index < len(PIPELINE_STEPS) - 1:
            cols[index * 2 + 1].markdown("<div class='pipeline-arrow'>→</div>", unsafe_allow_html=True)
