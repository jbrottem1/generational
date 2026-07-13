"""Script tab for the asset workspace — Phase 1B."""

from __future__ import annotations

import copy
import json
from typing import Any, Callable

import streamlit as st

from core.script_models import (
    ScriptSegment,
    VideoScript,
    asset_has_video_script,
    estimated_duration_from_segments,
    load_video_script,
)

PersistFn = Callable[[dict[str, Any], int], None]
GenerateFn = Callable[[bool], None]


def _draft_key(asset_id: str) -> str:
    return f"script_draft_{asset_id}"


def _status_label(asset: dict[str, Any], *, generating: bool) -> str:
    if generating:
        return "Generating…"
    if asset_has_video_script(asset):
        return "Complete"
    if asset.get("script"):
        return "Legacy script only (no structured segments)"
    return "Not generated"


def _ensure_draft(asset: dict[str, Any]) -> dict[str, Any] | None:
    script = load_video_script(asset)
    if script is None:
        return None
    asset_id = str(asset.get("asset_id") or "asset")
    key = _draft_key(asset_id)
    if key not in st.session_state:
        st.session_state[key] = script.to_dict()
    return st.session_state[key]


def _save_draft_to_asset(asset: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    """Apply draft edits back onto the asset (caller persists)."""
    from core.script_models import apply_script_to_asset, validate_script_payload

    draft = copy.deepcopy(draft)
    draft["source"] = "edited"
    segments = []
    for raw in draft.get("segments") or []:
        if isinstance(raw, dict):
            segments.append(ScriptSegment.from_dict(raw))
    draft["full_voiceover"] = " ".join(
        segment.voiceover.strip() for segment in segments if segment.voiceover.strip()
    )
    draft["estimated_word_count"] = len(draft["full_voiceover"].split())
    script, errors = validate_script_payload(draft)
    if script is None:
        raise ValueError("; ".join(errors))
    return apply_script_to_asset(asset, script)


def render_script_tab(
    project: dict[str, Any],
    asset: dict[str, Any],
    index: int,
    *,
    generating: bool = False,
    on_persist: PersistFn,
    on_generate: GenerateFn,
    on_overview: Callable[[], None] | None = None,
) -> None:
    """Render the Script tab with view/edit/save/regenerate/copy."""
    asset_id = str(asset.get("asset_id") or f"asset_{index}")
    script = load_video_script(asset)
    draft = _ensure_draft(asset) if script else None

    st.markdown("#### Script production")
    status = _status_label(asset, generating=generating)
    if status == "Complete":
        st.success(f"**Status:** {status}")
    elif generating:
        st.warning(f"**Status:** {status}")
    elif status.startswith("Legacy"):
        st.info(f"**Status:** {status}")
    else:
        st.info(f"**Status:** {status}")

    if not script and not generating:
        st.warning(
            "No structured video script yet. Click **Build Video From This Asset** on the workspace "
            "header, or use **Regenerate Script** below once a script exists."
        )
        legacy = asset.get("script") or ""
        if legacy:
            st.markdown("##### Legacy voiceover (read-only)")
            st.text_area("Legacy script", value=legacy, height=200, disabled=True, key=f"legacy_script_{asset_id}")
        if st.button("🎬 Generate Script Now", key=f"script_gen_now_{asset_id}", type="primary"):
            on_generate(force=True)
        return

    if generating:
        st.spinner("Script generation in progress…")
        return

    assert draft is not None and script is not None

    target = int(draft.get("target_duration_seconds") or script.target_duration_seconds)
    estimated = int(round(estimated_duration_from_segments(script.segments)))
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Target duration", f"{target}s")
    m2.metric("Estimated duration", f"{estimated}s")
    m3.metric("Tone", str(draft.get("tone") or "—"))
    m4.metric("Primary emotion", str(draft.get("primary_emotion") or "—"))
    st.caption(
        f"Words: {draft.get('estimated_word_count', 0)} · "
        f"Segments: {len(draft.get('segments') or [])} · "
        f"Source: {draft.get('source', 'ai')}"
    )
    if draft.get("script_summary"):
        st.markdown("**Summary**")
        st.write(draft["script_summary"])

    st.markdown("##### Full voiceover")
    full_key = f"full_voiceover_{asset_id}"
    full_value = st.text_area(
        "Full voiceover",
        value=draft.get("full_voiceover") or "",
        height=180,
        key=full_key,
        label_visibility="collapsed",
    )
    draft["full_voiceover"] = full_value
    draft["estimated_word_count"] = len(full_value.split())

    st.markdown("##### Timed segments")
    segments = list(draft.get("segments") or [])
    for seg_index, segment in enumerate(segments):
        if not isinstance(segment, dict):
            continue
        with st.expander(
            f"Segment {segment.get('segment_number', seg_index + 1)} · "
            f"{segment.get('start_time', 0)}–{segment.get('end_time', 0)}s · "
            f"{segment.get('segment_type', 'beat')}",
            expanded=seg_index < 2,
        ):
            c1, c2, c3 = st.columns(3)
            segment["segment_type"] = c1.text_input(
                "Type",
                value=str(segment.get("segment_type") or ""),
                key=f"seg_type_{asset_id}_{seg_index}",
            )
            segment["emotion"] = c2.text_input(
                "Emotion",
                value=str(segment.get("emotion") or ""),
                key=f"seg_emotion_{asset_id}_{seg_index}",
            )
            segment["delivery"] = c3.text_input(
                "Delivery",
                value=str(segment.get("delivery") or ""),
                key=f"seg_delivery_{asset_id}_{seg_index}",
            )
            segment["retention_device"] = st.text_input(
                "Retention device",
                value=str(segment.get("retention_device") or ""),
                key=f"seg_retention_{asset_id}_{seg_index}",
            )
            segment["voiceover"] = st.text_area(
                "Voiceover",
                value=str(segment.get("voiceover") or ""),
                height=100,
                key=f"seg_voice_{asset_id}_{seg_index}",
            )
    draft["segments"] = segments

    st.markdown("##### Call to action")
    draft["call_to_action"] = st.text_input(
        "CTA",
        value=str(draft.get("call_to_action") or ""),
        key=f"cta_{asset_id}",
    )

    btn1, btn2, btn3, btn4 = st.columns(4)
    if btn1.button("💾 Save edits", key=f"save_script_{asset_id}", type="primary", use_container_width=True):
        try:
            updated_asset = _save_draft_to_asset(asset, draft)
            on_persist(updated_asset, index)
            st.session_state[_draft_key(asset_id)] = updated_asset["video_script"]
            st.success("Script saved.")
        except ValueError as exc:
            st.error(f"Could not save script: {exc}")

    if btn2.button("🔁 Regenerate Script", key=f"regen_script_{asset_id}", use_container_width=True):
        st.session_state.pop(_draft_key(asset_id), None)
        on_generate(force=True)

    copy_text = draft.get("full_voiceover") or ""
    btn3.download_button(
        "📋 Copy / download",
        data=copy_text,
        file_name=f"{(draft.get('title') or 'script').replace(' ', '_')[:40]}.txt",
        mime="text/plain",
        key=f"copy_script_{asset_id}",
        use_container_width=True,
    )

    if btn4.button("↩ Overview", key=f"script_to_overview_{asset_id}", use_container_width=True):
        if on_overview:
            on_overview()

    with st.expander("Raw script JSON", expanded=False):
        st.code(json.dumps(draft, indent=2), language="json")
