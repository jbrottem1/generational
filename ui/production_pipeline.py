"""Production pipeline UI for the asset workspace — live stage progress."""

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
    "started": "#3b82f6",
    "running": "#f59e0b",
    "in_progress": "#f59e0b",
    "completed": "#10b981",
    "complete": "#10b981",
    "failed": "#ef4444",
    "skipped": "#94a3b8",
    "needs_review": "#8b5cf6",
}


def render_production_pipeline(asset: dict[str, Any] | None, *, script_generating: bool = False) -> None:
    """Render the production pipeline with status, retries, and timing."""
    stages = build_pipeline_stages(asset, script_generating=script_generating)
    progress = pipeline_progress_percent(stages)
    done = sum(1 for s in stages if s["status"] in {"completed", "complete", "skipped"})

    st.markdown("### Production pipeline")
    st.progress(progress / 100.0, text=f"{progress}% complete ({done}/{len(stages)} stages)")

    # Compact icon row (wrap in chunks of 5 for readability)
    chunk = 5
    for start in range(0, len(PIPELINE_STAGE_KEYS), chunk):
        group = stages[start : start + chunk]
        cols = st.columns(len(group))
        for col, stage in zip(cols, group):
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

    with st.expander("Stage details (status · retries · time · artifacts)", expanded=True):
        rows = []
        for stage in stages:
            retries = stage.get("retry_count") or 0
            timing = stage.get("execution_time_sec") or 0
            arts = stage.get("artifacts") or []
            err = stage.get("error") or ""
            rows.append(
                {
                    "Stage": stage["label"],
                    "Status": STATUS_LABELS.get(stage["status"], stage["status"]),
                    "Retries": retries,
                    "Seconds": round(float(timing), 2),
                    "Artifacts": ", ".join(str(a).split("/")[-1] for a in arts[:4]) or "—",
                    "Error": err[:80] if err else "—",
                }
            )
        st.dataframe(rows, use_container_width=True, hide_index=True)

    current = (asset or {}).get("production_pipeline") or {}
    if current.get("current_stage"):
        st.caption(f"Current stage: `{current.get('current_stage')}` · updated {current.get('updated_at') or '—'}")
