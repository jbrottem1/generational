"""Production pipeline UI for the asset workspace."""

from __future__ import annotations

from typing import Any

import streamlit as st

from core.script_models import (
    PIPELINE_STAGE_KEYS,
    STATUS_ICONS,
    STATUS_LABELS,
    build_pipeline_stages,
    pipeline_progress_percent,
)

_STATUS_COLORS = {
    "not_started": "#6b7280",
    "in_progress": "#f59e0b",
    "complete": "#10b981",
    "failed": "#ef4444",
    "needs_review": "#8b5cf6",
}


def render_production_pipeline(asset: dict[str, Any] | None, *, script_generating: bool = False) -> None:
    """Render the 10-stage production pipeline with honest statuses."""
    stages = build_pipeline_stages(asset, script_generating=script_generating)
    progress = pipeline_progress_percent(stages)

    st.markdown("### Production pipeline")
    st.progress(progress / 100.0, text=f"{progress}% complete ({sum(1 for s in stages if s['status'] == 'complete')}/{len(stages)} stages)")

    cols = st.columns(len(PIPELINE_STAGE_KEYS))
    for col, stage in zip(cols, stages):
        status = stage["status"]
        icon = STATUS_ICONS.get(status, "○")
        label = STATUS_LABELS.get(status, status.replace("_", " ").title())
        color = _STATUS_COLORS.get(status, "#6b7280")
        col.markdown(
            f"<div style='text-align:center;padding:6px 2px;'>"
            f"<div style='font-size:1.1rem;color:{color};'>{icon}</div>"
            f"<div style='font-size:0.72rem;font-weight:600;'>{stage['label']}</div>"
            f"<div style='font-size:0.65rem;color:{color};'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
