"""Analytics tab — live records from the Analytics store + session stats."""

from __future__ import annotations

import streamlit as st

from core import storage
from core.constants import ANALYTICS_COMING_SOON
from ui import components


def render() -> None:
    st.subheader("📊 Analytics")
    st.caption(
        "Performance records from the Analytics Engine. Live platform metrics require "
        "publisher credentials; demo/mock runs still produce inspectable records."
    )

    ideas_total = st.session_state.ideas_generated_total
    projects_total = storage.project_count()
    analytics = _analytics_summary()

    cols = st.columns(4)
    cols[0].metric("Ideas Generated", ideas_total)
    cols[1].metric("Projects Saved", projects_total)
    cols[2].metric("Analytics Records", analytics["record_count"])
    cols[3].metric("Total Views (stored)", analytics["total_views"])

    if analytics["record_count"]:
        st.markdown("### Recent records")
        for record in analytics["records"][:20]:
            st.caption(
                f"{record.get('platform', '?')} · "
                f"views={record.get('views', 0)} · "
                f"status={record.get('metrics_status') or record.get('status') or '—'} · "
                f"{str(record.get('collected_at') or '')[:19]} · "
                f"ref={str(record.get('analytics_ref') or '')[:16]}"
            )
    else:
        st.info("No analytics records yet. Complete a production run that publishes (or dry-runs).")

    result = st.session_state.get("current_result") or {}
    if result.get("analytics_summary") or result.get("learning_report"):
        st.markdown("### Current run")
        st.json(
            {
                "analytics_summary": result.get("analytics_summary") or {},
                "learning_report": {
                    k: (result.get("learning_report") or {}).get(k)
                    for k in ("status", "records_analyzed", "recommendations")
                },
            }
        )

    st.divider()
    st.markdown("### Still coming")
    components.coming_soon_grid(ANALYTICS_COMING_SOON)


def _analytics_summary() -> dict:
    try:
        from services.analytics.store import get_analytics_store

        store = get_analytics_store()
        records = store.list_records(limit=50)
    except Exception:  # noqa: BLE001
        records = []
    total_views = sum(int(r.get("views") or 0) for r in records)
    return {
        "record_count": len(records),
        "total_views": total_views,
        "records": records,
    }
