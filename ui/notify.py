"""Small helper for consistent success/error notifications (toast + inline)."""

import streamlit as st


def success(message: str) -> None:
    if hasattr(st, "toast"):
        st.toast(message, icon="✅")
    else:
        st.success(message)


def error(message: str) -> None:
    if hasattr(st, "toast"):
        st.toast(message, icon="❌")
    else:
        st.error(message)
