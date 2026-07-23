"""Publishing tab — live queue/history from the Publishing Engine."""

from __future__ import annotations

import streamlit as st

from core.constants import PUBLISHING_COMING_SOON, PUBLISHING_PLATFORMS
from ui import components


def render() -> None:
    st.subheader("📤 Publishing")
    st.caption(
        "Publishing queue and history from the Publishing Engine. "
        "Platform Connect buttons stay disabled until OAuth credentials are configured."
    )

    summary = _publishing_summary()
    cols = st.columns(4)
    cols[0].metric("Queued / Scheduled", summary["queued"])
    cols[1].metric("Published", summary["published"])
    cols[2].metric("Failed", summary["failed"])
    cols[3].metric("History entries", summary["history_count"])

    cols = st.columns(len(PUBLISHING_PLATFORMS))
    for col, (icon, platform) in zip(cols, PUBLISHING_PLATFORMS):
        with col:
            components.status_card(icon, platform, "Credentials required")
            st.button("Connect", key=f"connect_{platform}", disabled=True, use_container_width=True)

    jobs = summary["jobs"]
    if jobs:
        st.markdown("### Queue")
        for job in jobs[:25]:
            st.caption(
                f"`{job.get('status', '?')}` · {job.get('platform', '')} · "
                f"{job.get('job_id', '')} · scheduled {str(job.get('scheduled_time', ''))[:19]}"
            )
    else:
        st.info("No publish jobs yet. Run a Studio production with publish_mode scheduled or dry_run.")

    history = summary["history"]
    if history:
        st.markdown("### Recent attempts")
        for entry in history[:20]:
            st.caption(
                f"`{entry.get('status', '?')}` · {entry.get('platform', '')} · "
                f"post={entry.get('post_id') or '—'} · "
                f"{'dry-run' if entry.get('dry_run') else 'live'} · "
                f"{str(entry.get('published_at') or entry.get('started_at') or '')[:19]}"
            )

    result = st.session_state.get("current_result") or {}
    publishing_result = result.get("publishing_result") or {}
    if publishing_result:
        st.markdown("### Current run")
        st.json(
            {
                "status": publishing_result.get("status"),
                "jobs_created": publishing_result.get("jobs_created"),
                "published": publishing_result.get("published"),
                "scheduled": publishing_result.get("scheduled"),
                "failed": publishing_result.get("failed"),
                "publish_mode": publishing_result.get("publish_mode"),
            }
        )

    st.divider()
    st.markdown("### Still coming")
    components.coming_soon_grid(PUBLISHING_COMING_SOON)


def _publishing_summary() -> dict:
    try:
        from services.publishing.queue import PublishingHistory, PublishingQueue

        queue = PublishingQueue()
        history = PublishingHistory()
        jobs = queue.list_jobs()
        entries = history.all()
    except Exception:  # noqa: BLE001 — UI must never crash on store issues
        jobs, entries = [], []

    queued = [j for j in jobs if j.get("status") in ("queued", "scheduled", "pending")]
    published = [j for j in jobs if j.get("status") in ("published", "succeeded", "completed")]
    failed = [j for j in jobs if j.get("status") in ("failed", "error")]
    return {
        "queued": len(queued),
        "published": len(published),
        "failed": len(failed),
        "jobs": list(reversed(jobs))[:50],
        "history": list(reversed(entries))[:50],
        "history_count": len(entries),
    }
