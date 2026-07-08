"""Global CSS injection for Generational's polished dark theme."""

import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

div[data-testid="stTextArea"] textarea {
    font-size: 1.05rem;
    border-radius: 12px;
}

div.stButton > button {
    border-radius: 10px;
    font-weight: 600;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}
div.stButton > button:hover:not(:disabled) {
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(124, 92, 255, 0.35);
}

div[data-testid="stMetric"] {
    background: #181b24;
    border: 1px solid #262a36;
    border-radius: 14px;
    padding: 14px 12px;
    transition: transform 0.15s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
}

div[data-testid="stExpander"] {
    border-radius: 12px !important;
    border: 1px solid #262a36 !important;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
}

.pipeline-step {
    text-align: center;
    background: linear-gradient(180deg, #262a36, #1c1f29);
    color: #fafafa;
    padding: 12px 6px;
    border-radius: 12px;
    font-size: 0.85rem;
    font-weight: 600;
    border: 1px solid #333748;
}
.pipeline-arrow {
    text-align: center;
    font-size: 1.2rem;
    padding-top: 14px;
    color: #7c5cff;
}

.status-card {
    text-align: center;
    background: #181b24;
    border: 1px solid #262a36;
    border-radius: 14px;
    padding: 16px 8px;
    margin-bottom: 8px;
}

.badge-muted {
    display: inline-block;
    margin-top: 6px;
    font-size: 0.75rem;
    color: #9aa0ab;
    background: #262a36;
    padding: 2px 10px;
    border-radius: 999px;
}

section[data-testid="stSidebar"] div[data-testid="stMetric"] {
    padding: 10px 8px;
}
</style>
"""


def inject() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
