"""Scripts tab — a focused, copy-friendly view of the current batch of scripts."""

import streamlit as st


def render() -> None:
    result = st.session_state.current_result

    if not result:
        st.info("No ideas generated yet. Head to the **Ideas** tab and run a command first.")
        return

    st.subheader(f"📝 Scripts — {result['niche']}")
    st.caption(result["goal"])

    for index, idea in enumerate(result["ideas"], start=1):
        with st.container(border=True):
            st.markdown(f"#### {index}. {idea.get('title', f'Idea {index}')}")
            st.text_area(
                f"Script {index}",
                value=idea.get("script", ""),
                height=120,
                key=f"script_view_{index}",
                label_visibility="collapsed",
            )
            meta_cols = st.columns(2)
            meta_cols[0].markdown(f"**📣 CTA:** {idea.get('cta', '—')}")
            hashtags = idea.get("hashtags", [])
            if isinstance(hashtags, list):
                hashtags = " ".join(hashtags)
            meta_cols[1].markdown(f"**#️⃣ Hashtags:** {hashtags}")
