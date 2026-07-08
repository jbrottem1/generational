"""
Generational - The AI Content Operating System

MVP Streamlit application. Lets a user pick a content category and a topic,
then generates placeholder content ideas. Real AI-powered generation and the
features listed under "Coming Soon" will be wired up in future iterations.
"""

import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CATEGORIES = [
    "Psychology",
    "AI & Future Tech",
    "History",
    "Space",
    "Finance",
    "Health",
]

COMING_SOON_FEATURES = [
    ("✍️", "AI Script Writer"),
    ("🎙️", "AI Voice Generation"),
    ("🎬", "AI Video Creation"),
    ("🔍", "SEO Optimizer"),
    ("📤", "Auto Posting"),
    ("📊", "Analytics Dashboard"),
]

st.set_page_config(
    page_title="Generational | AI Content Operating System",
    page_icon="🚀",
    layout="centered",
)

st.title("🚀 Generational")
st.subheader("The AI Content Operating System")

st.divider()

category = st.selectbox("Choose a content category", CATEGORIES)
topic = st.text_input("Enter a topic")

generate_clicked = st.button("Generate Ideas", type="primary")

if generate_clicked:
    if not topic.strip():
        st.warning("Please enter a topic before generating ideas.")
    else:
        st.subheader(f"💡 10 Content Ideas: {category} — {topic}")
        for i in range(1, 11):
            st.write(f"{i}. [Placeholder idea #{i} about {topic} in {category}]")

st.divider()

st.subheader("🔮 Coming Soon")

cols = st.columns(3)
for index, (icon, feature) in enumerate(COMING_SOON_FEATURES):
    with cols[index % 3]:
        st.info(f"{icon}  **{feature}**")
