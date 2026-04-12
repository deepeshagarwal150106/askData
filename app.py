"""DataPulse AI — Application Entrypoint.

This file is intentionally slim.  It wires together all modules:

    config/         ← page config, Groq client, model list
    styles/         ← global CSS
    components/     ← header, sidebar, navigation, empty_state
    pages/          ← clean_data, insights, chat
    services/       ← llm, database
    utils/          ← charts, session
"""

import streamlit as st
import pandas as pd

from config.settings import PAGE_CONFIG
from styles.main_css import GLOBAL_CSS
from utils.session import init_session_state
from components.header import render_header
from components.sidebar import render_sidebar
from components.navigation import render_navigation
from components.empty_state import render_empty_state
from pages.clean_data import render_clean_page
from pages.insights import render_insights_page
from pages.chat import render_chat_page

# ── Page config (must be the very first Streamlit call) ───────────────────────
st.set_page_config(**PAGE_CONFIG)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
render_header()

# ── Sidebar (returns Groq client, selected model, uploaded files) ─────────────
client, model_name, uploaded_files = render_sidebar()

# ── Session state defaults ────────────────────────────────────────────────────
init_session_state()

# ── Data loading (new uploaded files → pending queue) ────────────────────────
if uploaded_files:
    for uploaded_file in uploaded_files:
        already_loaded  = uploaded_file.name in st.session_state.data_loaded_files
        already_pending = uploaded_file.name in st.session_state.pending_files
        if not already_loaded and not already_pending:
            try:
                if uploaded_file.name.lower().endswith(".xlsx"):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)
                st.session_state.pending_files[uploaded_file.name] = df
                st.session_state.active_page = "clean"
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")
                st.stop()

# ── Navigation state logic ────────────────────────────────────────────────────
has_data    = bool(st.session_state.data_loaded_files)
has_pending = bool(st.session_state.pending_files)

# Auto-redirect to the most appropriate page
if has_pending:
    st.session_state.active_page = "clean"
elif has_data and st.session_state.active_page == "clean":
    st.session_state.active_page = "insights"

# ── Navigation bar ────────────────────────────────────────────────────────────
render_navigation(has_data, has_pending)

# ── Landing page (no data yet) ────────────────────────────────────────────────
if not has_data and not has_pending:
    render_empty_state()  # calls st.stop() internally

# ── Page routing ──────────────────────────────────────────────────────────────
active_page = st.session_state.active_page

if active_page == "clean":
    render_clean_page(client, model_name)
elif active_page == "insights":
    render_insights_page(client, model_name)
elif active_page == "chat":
    render_chat_page(client, model_name)
