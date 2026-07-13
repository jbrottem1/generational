"""
Generational — AI Content Operating System

Main Streamlit entry point. Wires together the sidebar (AI Command Center
status) and the six workspace tabs. All logic lives in the layered packages:
`core/` (config, models, AI providers, storage, state), `services/`
(pipeline stages), and `ui/` (components, tabs) — this file only
orchestrates them.
"""

# Load project-root `.env` before any provider / AI imports resolve credentials.
from core.env import load_application_env, startup_credential_report

_env_boot = load_application_env(create_if_missing=True)
_credential_report = startup_credential_report()

import streamlit as st

from core import storage
from core.constants import APP_VERSION
from core.log import get_logger
from core.state import init_session_state
from ui import sidebar, styles
from ui.project_state import apply_pending_streamlit_state
from ui.tabs import analytics, ideas, projects, publishing, scripts, settings, studio

_log = get_logger(__name__)
for _line in _credential_report.get("lines") or []:
    _log.info("startup credentials: %s", _line)
if _credential_report.get("demo_mode"):
    _log.warning(
        "OPENAI_API_KEY missing — Demo Mode active. Set the key in %s and restart.",
        _credential_report.get("env_path"),
    )
else:
    _log.info("OPENAI_API_KEY loaded — Demo Mode disabled.")

st.set_page_config(
    page_title="Generational | AI Content Operating System",
    page_icon="🚀",
    layout="wide",
)

init_session_state()
apply_pending_streamlit_state(storage=storage)
styles.inject()

# Arm analytics → learning closed loop for Studio and CLI (idempotent).
try:
    from services.analytics.integration import enable_continuous_learning

    enable_continuous_learning()
except Exception:  # noqa: BLE001 — boot must never fail on optional hooks
    pass

st.title("🚀 Generational")
st.subheader("AI Content Operating System")
st.caption(f"v{APP_VERSION} · Build faceless content at scale")

# Visible startup credential status (never prints secret values).
if _credential_report.get("demo_mode"):
    st.warning(
        "**Demo Mode** — `OPENAI_API_KEY` is missing. "
        f"Add it to `{_credential_report.get('env_path')}` (or Settings → API Keys), "
        "then restart the app."
    )
    with st.expander("Credential status at startup", expanded=False):
        for _line in _credential_report.get("lines") or []:
            st.text(_line)
else:
    st.success("OpenAI API key loaded — live generation enabled.")

tab_labels = ["🎬 Studio", "💡 Ideas", "📝 Scripts", "📁 Projects", "📤 Publishing", "📊 Analytics", "⚙️ Settings"]
studio_tab, ideas_tab, scripts_tab, projects_tab, publishing_tab, analytics_tab, settings_tab = st.tabs(tab_labels)

with studio_tab:
    studio.render()

with ideas_tab:
    ideas.render()

with scripts_tab:
    scripts.render()

with projects_tab:
    projects.render()

with publishing_tab:
    publishing.render()

with analytics_tab:
    analytics.render()

with settings_tab:
    settings.render()

# Rendered last (but still appears in the sidebar) so stats reflect any
# updates made by the tab logic above during this same script run.
with st.sidebar:
    sidebar.render()
