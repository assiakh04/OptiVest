"""Registre des pages (rempli par app.py) pour permettre les liens inter-pages."""
PAGES = {}


def link(key, label=None, icon=None):
    import streamlit as st
    if key in PAGES:
        st.page_link(PAGES[key], label=label, icon=icon)
