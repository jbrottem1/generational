"""
Generational — AI Content Operating System

Main Streamlit entry point. Wires together the sidebar (AI Command Center
status) and the six workspace tabs. All logic lives in the layered packages:
`core/` (config, models, AI providers, storage, state), `services/`
(pipeline stages), and `ui/` (components, tabs) — this file only
orchestrates them.
"""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from core.constants import APP_VERSION
from core.state import init_session_state
from ui import sidebar, styles
from ui.tabs import analytics, ideas, projects, publishing, scripts, settings

st.set_page_config(
    page_title="Generational | AI Content Operating System",
    page_icon="🚀",
    layout="wide",
)

init_session_state()
styles.inject()

st.title("🚀 Generational")
st.subheader("AI Content Operating System")
st.caption(f"v{APP_VERSION} · Build faceless content at scale")

tab_labels = ["💡 Ideas", "📝 Scripts", "📁 Projects", "📤 Publishing", "📊 Analytics", "⚙️ Settings"]
ideas_tab, scripts_tab, projects_tab, publishing_tab, analytics_tab, settings_tab = st.tabs(tab_labels)

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
