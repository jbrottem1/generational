"""
Generational — AI Content Operating System (v1.0)

Main Streamlit entry point. Wires together the sidebar (AI Command Center
status) and the six workspace tabs: Ideas, Scripts, Projects, Publishing,
Analytics, and Settings. All actual logic lives in the modular `core/` and
`ui/` packages — this file only orchestrates them.
"""

from dotenv import load_dotenv

load_dotenv()

import streamlit as st

from core.constants import APP_VERSION
from core.state import init_session_state
from ui import sidebar, styles
from ui import tab_analytics, tab_ideas, tab_projects, tab_publishing, tab_scripts, tab_settings

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
    tab_ideas.render()

with scripts_tab:
    tab_scripts.render()

with projects_tab:
    tab_projects.render()

with publishing_tab:
    tab_publishing.render()

with analytics_tab:
    tab_analytics.render()

with settings_tab:
    tab_settings.render()

# Rendered last (but still appears in the sidebar) so stats reflect any
# updates made by the tab logic above during this same script run.
with st.sidebar:
    sidebar.render()
