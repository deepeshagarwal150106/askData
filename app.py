import streamlit as st
import pandas as pd
import duckdb
from groq import Groq
import os
import re
import numpy as np
import json
from dotenv import load_dotenv
import plotly.express as px
from cleaner import clean_dataframe
from streamlit_mic_recorder import speech_to_text

load_dotenv()

st.set_page_config(page_title="DataPulse AI", page_icon="⚡", layout="wide",initial_sidebar_state="expanded")

# ── GLOBAL CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Outfit:wght@300;400;500;600;700;800&display=swap');

/* ── Root palette ── */
:root {
    --bg:        #080B14;
    --surface:   #0E1220;
    --surface2:  #161B2E;
    --border:    #1F2847;
    --violet:    #7C3AED;
    --violet-lt: #9D5FF5;
    --cyan:      #06B6D4;
    --cyan-lt:   #22D3EE;
    --emerald:   #10B981;
    --amber:     #F59E0B;
    --rose:      #F43F5E;
    --text:      #E2E8F0;
    --muted:     #64748B;
    --white:     #FFFFFF;
}

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Main container ── */
.block-container {
    padding: 1.5rem 2.5rem 3rem !important;
    max-width: 1400px !important;
}

/* ── App header ── */
.app-header {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 1.4rem 0 0.2rem;
    border-bottom: 1px solid var(--border);
    margin-bottom: 0.5rem;
}
.app-logo {
    width: 44px; height: 44px;
    background: linear-gradient(135deg, var(--violet), var(--cyan));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
    box-shadow: 0 0 24px rgba(124,58,237,0.45);
}
.app-title {
    font-size: 1.7rem;
    font-weight: 800;
    background: linear-gradient(90deg, var(--violet-lt), var(--cyan-lt));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.5px;
}
.app-sub {
    font-size: 0.82rem;
    color: var(--muted);
    margin-top: 1px;
    font-weight: 400;
}

/* ── Page nav pills ── */
.nav-bar {
    display: flex;
    gap: 8px;
    padding: 1rem 0 1.2rem;
}
.nav-pill {
    padding: 8px 20px;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    border: 1.5px solid var(--border);
    background: var(--surface);
    color: var(--muted);
    transition: all 0.18s ease;
    display: inline-flex; align-items: center; gap: 6px;
}
.nav-pill:hover { border-color: var(--violet); color: var(--text); }
.nav-pill.active {
    background: linear-gradient(135deg, var(--violet), #5B21B6);
    border-color: var(--violet);
    color: var(--white);
    box-shadow: 0 0 18px rgba(124,58,237,0.4);
}
.nav-pill.locked { opacity: 0.35; cursor: not-allowed; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0B0F1E 0%, #0E1220 40%, #0A0E1B 100%) !important;
    border-right: 1px solid transparent !important;
    background-clip: padding-box !important;
    position: relative !important;
}
[data-testid="stSidebar"]::after {
    content: '';
    position: absolute;
    top: 0; right: 0; bottom: 0;
    width: 1px;
    background: linear-gradient(180deg, var(--violet) 0%, var(--cyan) 50%, var(--violet) 100%);
    opacity: 0.35;
}
[data-testid="stSidebar"] * { color: var(--text) !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] .stTextInput input:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.15) !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] .stSelectbox > div > div:hover {
    border-color: rgba(124,58,237,0.4) !important;
}

/* ── Sidebar custom components ── */
.sidebar-brand {
    display: flex; align-items: center; gap: 12px;
    padding: 0.3rem 0.5rem 1rem;
    margin-bottom: 0.2rem;
}
.sidebar-brand-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, var(--violet), var(--cyan));
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    font-size: 20px;
    box-shadow: 0 0 20px rgba(124,58,237,0.4), 0 0 40px rgba(6,182,212,0.15);
    flex-shrink: 0;
    animation: pulse-glow 3s ease-in-out infinite;
}
@keyframes pulse-glow {
    0%, 100% { box-shadow: 0 0 20px rgba(124,58,237,0.4), 0 0 40px rgba(6,182,212,0.15); }
    50%      { box-shadow: 0 0 28px rgba(124,58,237,0.6), 0 0 50px rgba(6,182,212,0.25); }
}
.sidebar-brand-text {
    font-size: 1.15rem;
    font-weight: 800;
    background: linear-gradient(135deg, var(--violet-lt), var(--cyan-lt));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.3px;
    line-height: 1.2;
}
.sidebar-brand-sub {
    font-size: 0.68rem;
    color: var(--muted) !important;
    font-weight: 400;
    letter-spacing: 0.3px;
    margin-top: 1px;
}
.sidebar-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--border), transparent);
    margin: 0.8rem 0;
    position: relative;
}
.sidebar-divider.glow {
    background: linear-gradient(90deg, transparent, rgba(124,58,237,0.3), rgba(6,182,212,0.3), transparent);
}
.sidebar-section {
    background: rgba(14,18,32,0.6);
    border: 1px solid rgba(31,40,71,0.5);
    border-radius: 14px;
    padding: 1rem 1rem;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    transition: border-color 0.25s ease;
}
.sidebar-section:hover {
    border-color: rgba(124,58,237,0.25);
}
.sidebar-section-label {
    font-size: 0.68rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: var(--muted) !important;
    margin-bottom: 0.7rem;
    display: flex; align-items: center; gap: 6px;
}
.sidebar-section-label .dot {
    width: 6px; height: 6px;
    border-radius: 50%;
    display: inline-block;
}
.sidebar-section-label .dot-violet { background: var(--violet); box-shadow: 0 0 6px var(--violet); }
.sidebar-section-label .dot-cyan   { background: var(--cyan);   box-shadow: 0 0 6px var(--cyan); }
.sidebar-section-label .dot-emerald { background: var(--emerald); box-shadow: 0 0 6px var(--emerald); }

.sidebar-status {
    display: flex; align-items: center; gap: 8px;
    padding: 8px 12px;
    border-radius: 10px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 0.6rem;
}
.sidebar-status.success {
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.25);
    color: #34D399 !important;
}
.sidebar-status.success .status-dot {
    width: 8px; height: 8px;
    background: var(--emerald);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--emerald);
    animation: status-pulse 2s ease-in-out infinite;
}
@keyframes status-pulse {
    0%, 100% { opacity: 1; transform: scale(1); }
    50%      { opacity: 0.6; transform: scale(0.85); }
}
.sidebar-status.error {
    background: rgba(244,63,94,0.1);
    border: 1px solid rgba(244,63,94,0.25);
    color: #F87171 !important;
}

/* ── Sidebar table card ── */
.sidebar-table-card {
    background: rgba(14,18,32,0.7);
    border: 1px solid rgba(31,40,71,0.5);
    border-radius: 12px;
    padding: 10px 12px;
    margin-bottom: 8px;
    transition: all 0.25s ease;
}
.sidebar-table-card:hover {
    border-color: rgba(124,58,237,0.35);
    background: rgba(124,58,237,0.04);
}
.sidebar-table-header {
    display: flex; align-items: center; gap: 10px;
}
.sidebar-table-header .tbl-icon {
    width: 32px; height: 32px;
    border-radius: 9px;
    background: linear-gradient(135deg, rgba(124,58,237,0.25), rgba(6,182,212,0.25));
    display: flex; align-items: center; justify-content: center;
    font-size: 0.85rem;
    flex-shrink: 0;
    box-shadow: 0 0 12px rgba(124,58,237,0.15);
}
.sidebar-table-header .tbl-info {
    flex: 1; min-width: 0;
}
.sidebar-table-header .tbl-name {
    font-size: 0.82rem;
    font-weight: 700;
    font-family: 'Space Mono', monospace;
    color: var(--text) !important;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    line-height: 1.3;
}
.sidebar-table-header .tbl-meta {
    font-size: 0.65rem;
    color: var(--muted) !important;
    font-weight: 500;
    margin-top: 1px;
    display: flex; align-items: center; gap: 6px;
}
.sidebar-table-header .tbl-meta .meta-dot {
    width: 3px; height: 3px;
    background: var(--muted);
    border-radius: 50%;
    display: inline-block;
}

/* ── Schema display ── */
.schema-columns-grid {
    display: flex; flex-wrap: wrap; gap: 5px;
    padding: 8px 0 4px;
}
.schema-col-pill {
    display: inline-flex; align-items: center; gap: 4px;
    padding: 4px 8px;
    border-radius: 6px;
    font-size: 0.68rem;
    font-weight: 500;
    background: rgba(22,27,46,0.9);
    border: 1px solid rgba(31,40,71,0.5);
    transition: all 0.15s ease;
    line-height: 1.3;
}
.schema-col-pill:hover {
    border-color: rgba(124,58,237,0.3);
    background: rgba(124,58,237,0.06);
}
.schema-col-pill .col-name {
    color: var(--text) !important;
    font-family: 'Space Mono', monospace;
    font-weight: 600;
    font-size: 0.66rem;
}
.schema-col-pill .col-type {
    color: var(--cyan-lt) !important;
    font-size: 0.58rem;
    font-weight: 600;
    padding: 1px 5px;
    background: rgba(6,182,212,0.12);
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
}
.schema-col-pill .col-type.type-int     { color: var(--violet-lt) !important; background: rgba(124,58,237,0.12); }
.schema-col-pill .col-type.type-float   { color: #FCD34D !important; background: rgba(245,158,11,0.12); }
.schema-col-pill .col-type.type-date    { color: #34D399 !important; background: rgba(16,185,129,0.12); }
.schema-col-pill .col-type.type-varchar { color: var(--cyan-lt) !important; background: rgba(6,182,212,0.12); }

/* ── Schema sample table ── */
.schema-sample-label {
    font-size: 0.62rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    color: var(--muted) !important;
    margin: 8px 0 5px;
    display: flex; align-items: center; gap: 5px;
}
.schema-sample-label::after {
    content: ''; flex: 1; height: 1px;
    background: linear-gradient(90deg, var(--border), transparent);
}
.schema-sample-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.63rem;
    font-family: 'Space Mono', monospace;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(31,40,71,0.4);
}
.schema-sample-table thead th {
    background: rgba(124,58,237,0.12);
    color: var(--violet-lt) !important;
    padding: 5px 6px;
    text-align: left;
    font-weight: 700;
    font-size: 0.6rem;
    letter-spacing: 0.3px;
    white-space: nowrap;
    border-bottom: 1px solid rgba(124,58,237,0.2);
}
.schema-sample-table tbody td {
    padding: 4px 6px;
    color: var(--text) !important;
    border-bottom: 1px solid rgba(31,40,71,0.25);
    white-space: nowrap;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
}
.schema-sample-table tbody tr:nth-child(even) {
    background: rgba(14,18,32,0.5);
}
.schema-sample-table tbody tr:nth-child(odd) {
    background: rgba(22,27,46,0.4);
}
.schema-sample-table tbody tr:hover {
    background: rgba(124,58,237,0.06);
}
.schema-sample-table tbody tr:last-child td {
    border-bottom: none;
}

/* ── Sidebar footer ── */
.sidebar-footer {
    padding: 0.6rem 0.5rem 0.4rem;
    text-align: center;
    margin-top: 0.5rem;
}
.sidebar-footer-text {
    font-size: 0.65rem;
    color: var(--muted) !important;
    letter-spacing: 0.4px;
}
.sidebar-footer-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 0.6rem;
    font-weight: 700;
    background: linear-gradient(135deg, rgba(124,58,237,0.15), rgba(6,182,212,0.15));
    border: 1px solid rgba(124,58,237,0.2);
    color: var(--violet-lt) !important;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* ── Sidebar file uploader override ── */
[data-testid="stSidebar"] [data-testid="stFileUploader"] {
    background: rgba(22,27,46,0.5) !important;
    border: 1.5px dashed rgba(124,58,237,0.3) !important;
    border-radius: 12px !important;
    transition: all 0.25s ease !important;
    padding: 12px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {
    border-color: rgba(124,58,237,0.5) !important;
    background: rgba(124,58,237,0.04) !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] small {
    color: var(--muted) !important;
    font-size: 0.68rem !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, var(--violet), #5B21B6) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.75rem !important;
    padding: 5px 14px !important;
    box-shadow: 0 2px 10px rgba(124,58,237,0.3) !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 16px rgba(124,58,237,0.45) !important;
}

/* ── Uploaded file chip in sidebar ── */
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] {
    background: rgba(16,185,129,0.06) !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    border-radius: 10px !important;
    padding: 6px 10px !important;
    margin-top: 6px !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] small {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.7rem !important;
}
[data-testid="stSidebar"] [data-testid="stFileUploaderFile"] button {
    background: rgba(244,63,94,0.15) !important;
    color: #F87171 !important;
    border: 1px solid rgba(244,63,94,0.2) !important;
    box-shadow: none !important;
    padding: 2px 6px !important;
    font-size: 0.65rem !important;
    border-radius: 6px !important;
}

/* ── Sidebar expander override ── */
[data-testid="stSidebar"] .streamlit-expanderHeader {
    background: rgba(22,27,46,0.6) !important;
    border: 1px solid rgba(31,40,71,0.4) !important;
    border-radius: 10px !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    padding: 7px 12px !important;
    transition: all 0.2s ease !important;
    color: var(--muted) !important;
}
[data-testid="stSidebar"] .streamlit-expanderHeader:hover {
    border-color: rgba(124,58,237,0.35) !important;
    color: var(--text) !important;
}
[data-testid="stSidebar"] .streamlit-expanderContent {
    background: rgba(10,14,27,0.7) !important;
    border: 1px solid rgba(31,40,71,0.3) !important;
    border-top: none !important;
    border-radius: 0 0 10px 10px !important;
    padding: 8px 10px !important;
    max-height: 350px !important;
    overflow-y: auto !important;
}

/* ── Sidebar success/error alert override ── */
[data-testid="stSidebar"] [data-testid="stAlert"] {
    display: none !important;
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1rem;
}
.card-violet { border-color: rgba(124,58,237,0.4); background: rgba(124,58,237,0.06); }
.card-cyan   { border-color: rgba(6,182,212,0.4);  background: rgba(6,182,212,0.06); }
.card-emerald{ border-color: rgba(16,185,129,0.35); background: rgba(16,185,129,0.06);}

/* ── Stat chips ── */
.stat-row { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1.2rem; }
.stat-chip {
    padding: 10px 18px;
    border-radius: 12px;
    font-size: 0.82rem;
    font-weight: 600;
    display: flex; align-items: center; gap: 7px;
}
.stat-chip.violet { background: rgba(124,58,237,0.18); color: var(--violet-lt); border: 1px solid rgba(124,58,237,0.3); }
.stat-chip.cyan   { background: rgba(6,182,212,0.15);  color: var(--cyan-lt);   border: 1px solid rgba(6,182,212,0.3); }
.stat-chip.emerald{ background: rgba(16,185,129,0.15); color: #34D399;           border: 1px solid rgba(16,185,129,0.3); }
.stat-chip.amber  { background: rgba(245,158,11,0.15); color: #FCD34D;           border: 1px solid rgba(245,158,11,0.3); }

/* ── Section headings ── */
.section-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 0.5rem;
    display: flex; align-items: center; gap: 8px;
}
.section-title .accent { color: var(--cyan-lt); }
.section-badge {
    font-size: 0.7rem; font-weight: 700;
    padding: 2px 8px; border-radius: 999px;
    background: rgba(6,182,212,0.2); color: var(--cyan-lt);
    letter-spacing: 0.5px; text-transform: uppercase;
}

/* ── Inputs & buttons ── */
.stTextInput input, .stTextArea textarea {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-family: 'Outfit', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--violet), #5B21B6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-family: 'Outfit', sans-serif !important;
    padding: 0.5rem 1.3rem !important;
    transition: all 0.18s ease !important;
    box-shadow: 0 4px 14px rgba(124,58,237,0.3) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124,58,237,0.45) !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    color: var(--text) !important;
    font-weight: 600 !important;
}
.streamlit-expanderContent {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
}

/* ── Data table ── */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; }
.stDataFrame iframe { border-radius: 12px !important; }

/* ── Code block ── */
.stCodeBlock pre {
    background: #0D1117 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    font-family: 'Space Mono', monospace !important;
}

/* ── Chat messages ── */
[data-testid="stChatMessage"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    margin-bottom: 10px !important;
    padding: 4px !important;
}
[data-testid="stChatMessage"][data-testid*="user"] {
    border-color: rgba(124,58,237,0.35) !important;
    background: rgba(124,58,237,0.06) !important;
}

/* ── Chat input ── */
.stChatInput textarea, [data-testid="stChatInputTextArea"] {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--text) !important;
}
[data-testid="stChatInputContainer"] {
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    background: var(--surface2) !important;
}

/* ── Alerts ── */
.stAlert { border-radius: 10px !important; }
[data-testid="stNotification"] { border-radius: 10px !important; }

/* ── Spinner text ── */
.stSpinner p { color: var(--violet-lt) !important; }

/* ── Tabs (for insights cards) ── */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface2) !important;
    border-radius: 10px !important;
    gap: 4px !important;
    padding: 4px !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 8px !important;
    color: var(--muted) !important;
    font-weight: 600 !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--violet), #5B21B6) !important;
    color: white !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 4rem 2rem;
    color: var(--muted);
}
.empty-state .icon { font-size: 3.5rem; margin-bottom: 1rem; }
.empty-state h3 { font-size: 1.2rem; font-weight: 700; color: var(--text); margin-bottom: 0.5rem; }
.empty-state p { font-size: 0.88rem; max-width: 380px; margin: 0 auto; }

/* ── Progress / steps ── */
.step-row { display: flex; gap: 0; margin-bottom: 1.5rem; }
.step {
    flex: 1; text-align: center; padding: 10px 6px;
    font-size: 0.78rem; font-weight: 600; color: var(--muted);
    border-bottom: 2px solid var(--border);
    transition: all 0.2s;
}
.step.done  { color: var(--emerald); border-color: var(--emerald); }
.step.active{ color: var(--violet-lt); border-color: var(--violet); }

/* ── Insight card ── */
.insight-header {
    display: flex; align-items: center; gap: 10px;
    margin-bottom: 0.4rem;
}
.insight-num {
    width: 28px; height: 28px; border-radius: 8px;
    background: linear-gradient(135deg, var(--violet), var(--cyan));
    display: flex; align-items: center; justify-content: center;
    font-size: 0.78rem; font-weight: 800; color: white;
    flex-shrink: 0;
}

/* ── Suggested question chips ── */
.q-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 0.8rem; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--violet); }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface2) !important;
    border: 1.5px dashed var(--border) !important;
    border-radius: 12px !important;
}

/* ── Success / warning pills in sidebar ── */
.stSuccess { background: rgba(16,185,129,0.15) !important; border-color: rgba(16,185,129,0.3) !important; }
.stWarning { background: rgba(245,158,11,0.12) !important;  border-color: rgba(245,158,11,0.3)  !important; }

/* ── Popover ── */
[data-testid="stPopover"] button {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    color: var(--muted) !important;
    font-size: 0.8rem !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
    padding: 4px 12px !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--surface2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)

# ── APP HEADER ───────────────────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <div class="app-logo">⚡</div>
  <div>
    <div class="app-title">DataPulse AI</div>
    <div class="app-sub">Natural language analytics · Powered by Groq</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<script>
setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
}, 50);
</script>
""", unsafe_allow_html=True)

# ── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Brand header ──
    st.markdown("""
    <div class="sidebar-brand">
      <div class="sidebar-brand-icon">⚡</div>
      <div>
        <div class="sidebar-brand-text">DataPulse AI</div>
        <div class="sidebar-brand-sub">Intelligent Data Analytics</div>
      </div>
    </div>
    <div class="sidebar-divider glow"></div>
    """, unsafe_allow_html=True)

    # ── Configuration section ──
    st.markdown("""
    <div class="sidebar-section-label"><span class="dot dot-violet"></span> CONFIGURATION</div>
    """, unsafe_allow_html=True)

    api_key_input = os.environ.get("GROQ_API_KEY")

    if api_key_input:
        client = Groq(api_key=api_key_input)
        st.markdown("""
        <div class="sidebar-status success">
          <div class="status-dot"></div>
          <span>API Connected</span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="sidebar-status error">
          <span>⚠ API key missing — set GROQ_API_KEY</span>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    model_name = st.selectbox("Model", [
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "mixtral-8x7b-32768"
    ], index=0, label_visibility="collapsed")

    st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

    # ── Upload section ──
    st.markdown("""
    <div class="sidebar-section-label"><span class="dot dot-cyan"></span> DATA SOURCE</div>
    """, unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Drop CSV files here", type=["csv"], accept_multiple_files=True, label_visibility="collapsed")

    # ── Loaded tables section ──
    if "data_loaded_files" in st.session_state and st.session_state.data_loaded_files:
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        n_tables = len(st.session_state.get("table_schemas", {}))
        st.markdown(f"""
        <div class="sidebar-section-label">
          <span class="dot dot-emerald"></span> LOADED TABLES
          <span style="margin-left:auto;font-size:0.58rem;padding:2px 7px;
                        background:rgba(16,185,129,0.15);border:1px solid rgba(16,185,129,0.25);
                        border-radius:999px;color:#34D399;font-weight:700;">{n_tables}</span>
        </div>
        """, unsafe_allow_html=True)
        for t_name, t_schema in st.session_state.get("table_schemas", {}).items():
            # Parse column info from schema
            try:
                schema_df = st.session_state.duckdb_conn.execute(f"DESCRIBE {t_name}").df()
                col_count = len(schema_df)
                row_count = st.session_state.duckdb_conn.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
                sample_df = st.session_state.duckdb_conn.execute(f"SELECT * FROM {t_name} LIMIT 3").df()
            except Exception:
                col_count = 0
                row_count = 0
                schema_df = None
                sample_df = None

            # Build column pills HTML
            col_pills_html = ""
            if schema_df is not None:
                for _, row in schema_df.iterrows():
                    c_name = row['column_name']
                    c_type = row['column_type']
                    type_class = "type-varchar"
                    if 'INT' in c_type.upper() or 'BIGINT' in c_type.upper():
                        type_class = "type-int"
                    elif 'DOUBLE' in c_type.upper() or 'FLOAT' in c_type.upper() or 'DECIMAL' in c_type.upper():
                        type_class = "type-float"
                    elif 'DATE' in c_type.upper() or 'TIME' in c_type.upper() or 'TIMESTAMP' in c_type.upper():
                        type_class = "type-date"
                    col_pills_html += f'<span class="schema-col-pill"><span class="col-name">{c_name}</span><span class="col-type {type_class}">{c_type}</span></span>'

            # Build sample table HTML
            sample_html = ""
            if sample_df is not None and not sample_df.empty:
                headers = "".join(f"<th>{c}</th>" for c in sample_df.columns)
                rows = ""
                for _, srow in sample_df.iterrows():
                    cells = "".join(f"<td>{v}</td>" for v in srow.values)
                    rows += f"<tr>{cells}</tr>"
                sample_html = f"""
                <div class="schema-sample-label">Sample Data</div>
                <div style="overflow-x:auto;">
                  <table class="schema-sample-table">
                    <thead><tr>{headers}</tr></thead>
                    <tbody>{rows}</tbody>
                  </table>
                </div>
                """

            # Table card
            st.markdown(f"""
            <div class="sidebar-table-card">
              <div class="sidebar-table-header">
                <div class="tbl-icon">📊</div>
                <div class="tbl-info">
                  <div class="tbl-name">{t_name}</div>
                  <div class="tbl-meta">
                    <span>{col_count} cols</span>
                    <span class="meta-dot"></span>
                    <span>{row_count:,} rows</span>
                  </div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📋 View Schema", expanded=False):
                st.markdown(f"""
                <div class="schema-columns-grid">
                  {col_pills_html}
                </div>
                {sample_html}
                """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown('<div class="sidebar-divider glow" style="margin-top:auto;"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sidebar-footer">
      <div class="sidebar-footer-text">Powered by Groq & DuckDB</div>
      <div class="sidebar-footer-badge">v2.0 · Pro</div>
    </div>
    """, unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
if "messages"          not in st.session_state: st.session_state.messages = []
if "duckdb_conn"       not in st.session_state: st.session_state.duckdb_conn = duckdb.connect(database=':memory:', read_only=False)
if "table_schemas"     not in st.session_state: st.session_state.table_schemas = {}
if "data_loaded_files" not in st.session_state: st.session_state.data_loaded_files = set()
if "pending_files"     not in st.session_state: st.session_state.pending_files = {}
if "cleaning_questions"not in st.session_state: st.session_state.cleaning_questions = {}
if "insights_data"     not in st.session_state: st.session_state.insights_data = None
if "trigger_prompt"    not in st.session_state: st.session_state.trigger_prompt = None
if "active_page"       not in st.session_state: st.session_state.active_page = "clean"

# ── HELPERS ──────────────────────────────────────────────────────────────────
def get_schema(conn, table_name):
    try:
        schema_df = conn.execute(f"DESCRIBE {table_name}").df()
        schema_str = "Columns and Data Types:\n"
        for _, row in schema_df.iterrows():
            schema_str += f"- {row['column_name']} ({row['column_type']})\n"
        sample_df = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").df()
        schema_str += "\nSample Data (Top 5 rows):\n"
        schema_str += sample_df.to_string(index=False) + "\n"
        return schema_str
    except Exception as e:
        return str(e)

def render_chart(chart_type, df, x_col, y_col, color_arg=None):
    if chart_type == "bar":
        st.bar_chart(df, x=x_col, y=y_col, color=color_arg)
    elif chart_type == "line":
        st.line_chart(df, x=x_col, y=y_col, color=color_arg)
    elif chart_type == "scatter":
        st.scatter_chart(df, x=x_col, y=y_col, color=color_arg)
    elif chart_type in ["pie", "histogram", "heatmap"]:
        y_val = y_col[0] if isinstance(y_col, list) and y_col else y_col
        if chart_type == "pie":
            fig = px.pie(df, names=x_col, values=y_val, color=color_arg,
                         color_discrete_sequence=px.colors.sequential.Purples_r)
        elif chart_type == "histogram":
            fig = px.histogram(df, x=x_col, y=y_val, color=color_arg,
                               color_discrete_sequence=["#7C3AED"])
        elif chart_type == "heatmap":
            fig = px.density_heatmap(df, x=x_col, y=y_val, z=color_arg,
                                     color_continuous_scale="Viridis")
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            font_color="#E2E8F0", margin=dict(t=20, b=20, l=10, r=10)
        )
        st.plotly_chart(fig, width='stretch')

# ── DATA LOADING ──────────────────────────────────────────────────────────────
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.data_loaded_files and uploaded_file.name not in st.session_state.pending_files:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.pending_files[uploaded_file.name] = df
                st.session_state.active_page = "clean"
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")
                st.stop()

# ── NAVIGATION ───────────────────────────────────────────────────────────────
has_data    = bool(st.session_state.data_loaded_files)
has_pending = bool(st.session_state.pending_files)

# Determine locked states
clean_locked   = not has_pending
insights_locked = not has_data
chat_locked     = not has_data

# Auto-redirect logic
if has_pending:
    st.session_state.active_page = "clean"
elif has_data and st.session_state.active_page == "clean":
    st.session_state.active_page = "insights"

# Progress steps
step_clean    = "active" if st.session_state.active_page == "clean"    else ("done" if has_data else "")
step_insights = "active" if st.session_state.active_page == "insights" else ("done" if has_data and st.session_state.active_page == "chat" else "")
step_chat     = "active" if st.session_state.active_page == "chat"     else ""

st.markdown(f"""
<div class="step-row">
  <div class="step {step_clean}">① Clean Data</div>
  <div class="step {step_insights}">② Insights</div>
  <div class="step {step_chat}">③ Ask Questions</div>
</div>
""", unsafe_allow_html=True)

# Nav pills (only show navigable ones)
nav_cols = st.columns([1, 1, 1, 4])
with nav_cols[0]:
    if has_pending:
        st.button("🧹 Clean Data", key="nav_clean", width='stretch',
                  on_click=lambda: st.session_state.update({"active_page": "clean"}))
    elif has_data:
        if st.button("🧹 Clean Data", key="nav_clean", width='stretch'):
            st.session_state.active_page = "clean"
with nav_cols[1]:
    if has_data:
        if st.button("📊 Insights", key="nav_insights", width='stretch'):
            st.session_state.active_page = "insights"
with nav_cols[2]:
    if has_data:
        if st.button("💬 Ask AI", key="nav_chat", width='stretch'):
            st.session_state.active_page = "chat"

st.markdown("<hr/>", unsafe_allow_html=True)

# ── NO DATA LANDING ───────────────────────────────────────────────────────────
if not has_data and not has_pending:
    st.markdown("""
    <div class="empty-state">
      <div class="icon">📂</div>
      <h3>No data loaded yet</h3>
      <p>Upload one or more CSV files from the sidebar to get started. DataPulse will auto-clean, analyze, and let you chat with your data.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="stat-row" style="justify-content:center;margin-top:2rem;">
      <div class="stat-chip violet">⚡ Lightning fast via Groq</div>
      <div class="stat-chip cyan">🧠 Auto SQL generation</div>
      <div class="stat-chip emerald">📈 Smart visualizations</div>
      <div class="stat-chip amber">🎙️ Voice input</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: CLEAN DATA
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.active_page == "clean":
    if not has_pending:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">✅</div>
          <h3>All files are clean</h3>
          <p>No pending files to clean. Navigate to Insights or Ask AI to explore your data.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="section-title">
          🧹 Data Cleaning Studio <span class="section-badge">Required</span>
        </div>
        <p style="color:var(--muted);font-size:0.88rem;margin-bottom:1.2rem;">
          Review each file below, tell the AI how to handle anomalies, then load it into the query engine.
        </p>
        """, unsafe_allow_html=True)

        for filename, df in list(st.session_state.pending_files.items()):
            st.markdown(f"""
            <div class="card card-violet">
              <div class="insight-header">
                <div class="insight-num">📄</div>
                <strong>{filename}</strong>
                <span class="stat-chip amber" style="margin-left:auto;font-size:0.73rem;padding:4px 10px;">
                  {len(df):,} rows · {len(df.columns)} cols
                </span>
              </div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"Preview & Clean — {filename}", expanded=True):
                # Quick preview
                col_prev, col_stats = st.columns([3, 1])
                with col_prev:
                    st.dataframe(df.head(5), width='stretch')
                with col_stats:
                    null_count = df.isnull().sum().sum()
                    st.markdown(f"""
                    <div class="stat-chip emerald" style="margin-bottom:6px;">✓ {len(df.columns)} columns</div>
                    <div class="stat-chip {'rose' if null_count else 'emerald'}" style="margin-bottom:6px;">
                      {'⚠' if null_count else '✓'} {null_count} nulls
                    </div>
                    <div class="stat-chip cyan">{df.dtypes.value_counts().to_dict()}</div>
                    """, unsafe_allow_html=True)

                # AI cleaning analysis
                if filename not in st.session_state.cleaning_questions:
                    with st.spinner(f"🧠 Analyzing {filename}…"):
                        schema_str = "Columns and Data Types:\n" + str(df.dtypes) + "\n\nSample Data:\n" + df.head(10).to_string()
                        system_prompt = "You are a Data Cleaning Expert. Analyze the dataframe schema and sample data. Identify anomalies like missing values (NaN, null strings), incorrect data types, currency formatting strings (e.g. '$123' instead of numeric), or date strings that need conversion. also check if null values are there in form of '.' or '?' . Give me a concise summary of the problems found and ask the user how they want to handle them (e.g. drop nulls or fill with mean? Strip '$'?). Be conversational and brief."
                        try:
                            response = client.chat.completions.create(
                                model=model_name,
                                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": schema_str}],
                                temperature=0.3
                            )
                            st.session_state.cleaning_questions[filename] = response.choices[0].message.content
                        except Exception as e:
                            st.session_state.cleaning_questions[filename] = f"Could not analyze data: {e}"

                st.markdown(f"""
                <div class="card card-cyan" style="margin-top:0.8rem;">
                  <div style="font-size:0.82rem;color:var(--cyan-lt);font-weight:600;margin-bottom:6px;">🤖 AI Analysis</div>
                  <div style="font-size:0.88rem;">{st.session_state.cleaning_questions.get(filename, '')}</div>
                </div>
                """, unsafe_allow_html=True)

                user_instruction = st.text_area(
                    "Your cleaning instructions",
                    key=f"clean_input_{filename}",
                    placeholder="e.g. Drop rows with nulls, strip $ from revenue column, convert date to datetime…"
                )

                if st.button("⚡ Apply & Load Table", key=f"clean_btn_{filename}"):
                    if user_instruction:
                        with st.spinner("Executing cleaning pipeline…"):
                            schema_for_cleaning = "Columns and Data Types:\n" + str(df.dtypes) + "\n\nSample Data:\n" + df.head(10).to_string()
                            cleaning_prompt = f"""
You are a strict code generator. Generate a python function named `custom_clean` that takes a pandas DataFrame `df` as input and returns the cleaned DataFrame.
Apply the user's instructions to clean the data.
User Instructions: "{user_instruction}"
if user says do as you like then do as you think is best for the data and you can use your insights:{st.session_state.cleaning_questions.get(filename, '')}

Data Schema & Sample:
{schema_for_cleaning}

Rules:
1. You MUST use only Pandas and standard Python libraries (re, numpy). `import pandas as pd`, `import numpy as pd`, `import re` inside the function.
2. Return the function strictly inside ```python ... ``` block. No other text.
3. Be robust and handle missing columns gracefully if requested.
"""
                            max_retries = 3
                            attempt = 0
                            success = False
                            error_msg = ""
                            python_code = ""
                            code_str = ""

                            while attempt < max_retries and not success:
                                prompt_to_send = cleaning_prompt
                                if error_msg:
                                    prompt_to_send += f"\n\nPrevious attempt failed with error: {error_msg}. Please fix the python code."
                                try:
                                    code_response = client.chat.completions.create(
                                        model=model_name,
                                        messages=[{"role": "user", "content": prompt_to_send}],
                                        temperature=0.1
                                    )
                                    code_str = code_response.choices[0].message.content
                                    code_match = re.search(r"```python(.*?)```", code_str, re.DOTALL | re.IGNORECASE)
                                    if code_match:
                                        python_code = code_match.group(1).strip()
                                        local_vars = {}
                                        exec(python_code, globals(), local_vars)
                                        custom_clean = local_vars['custom_clean']
                                        cleaned_df = custom_clean(df.copy())
                                        cleaned_df = clean_dataframe(cleaned_df)

                                        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', filename.split('.')[0]).lower()
                                        original_table_name = table_name
                                        counter = 1
                                        while table_name in st.session_state.table_schemas:
                                            table_name = f"{original_table_name}_{counter}"
                                            counter += 1

                                        st.session_state.duckdb_conn.register(table_name, cleaned_df)
                                        st.session_state.table_schemas[table_name] = get_schema(st.session_state.duckdb_conn, table_name)
                                        st.session_state.data_loaded_files.add(filename)
                                        del st.session_state.pending_files[filename]
                                        st.session_state.insights_data = None  # reset insights for new data
                                        st.session_state.messages.append({
                                            "role": "assistant",
                                            "content": f"✅ `{filename}` cleaned and loaded as table **`{table_name}`**. Ready to analyze!"
                                        })
                                        st.session_state.active_page = "insights"
                                        st.rerun()
                                        success = True
                                    else:
                                        error_msg = "No python code block found."
                                        attempt += 1
                                except Exception as e:
                                    error_msg = str(e)
                                    attempt += 1

                            if not success:
                                # Friendly error — no raw stack trace shown
                                st.markdown("""
                                <div class="card" style="border-color:rgba(244,63,94,0.4);background:rgba(244,63,94,0.06);">
                                  <strong style="color:#F87171;">⚠️ Cleaning could not be applied</strong><br/>
                                  <span style="font-size:0.85rem;color:var(--muted);">
                                    Try rephrasing your instructions with more specific column names and actions.
                                  </span>
                                </div>
                                """, unsafe_allow_html=True)
                    else:
                        st.warning("Please describe how you'd like to clean this data.")

        if has_pending:
            st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: INSIGHTS
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "insights":

    # ── LLM functions (defined here so they're in scope for both pages) ──────
    def generate_insight_plan(schemas_dict, error_msg=None):
        schema_text = ""
        for t_name, t_schema in schemas_dict.items():
            schema_text += f"Table: {t_name}\n{t_schema}\n\n"

        system_instruction = f"""
        You are an expert Senior Data Analyst.
        The user has uploaded the following tables with their schemas and sample data:

        {schema_text}

        Your goal is to provide a comprehensive executive summary, some questions he can ask and analytical plan based on this data.
        You MUST output valid JSON only, using the exact structure below. Do not wrap the JSON in markdown blocks unless it is ```json ... ```.

        JSON Structure:
        {{
          "summary": "A high-level natural language summary of what the data represents overall. Be professional and concise.",
          "insights": [
            {{
              "title": "Insight Title (e.g., Highest Revenue by Category)",
              "description": "Short explanation of what this insight tells us.",
              "sql_query": "DuckDB SQL query to fetch the exact numbers for this insight.",
              "is_graph": true,
              "chart_type": "bar",
              "x_axis": "column_name",
              "y_axis": "column_name",
              "color_col": "column_name"
            }}
          ],
          "suggested_questions": [
            "What is the overall trend in sales?"
          ]
        }}

        IMPORTANT RULES FOR SQL:
        - Queries must be valid DuckDB SQL matching the provided schemas.
        - Limit results to sensible numbers (e.g., top 10) for graphs.
        """

        if error_msg:
            system_instruction += f"\n\nPREVIOUS ERROR: {error_msg}"

        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_instruction}],
            temperature=0.3
        )
        return response.choices[0].message.content

    def fix_insight_sql(failed_sql, error_msg, schemas_dict):
        schema_text = "".join(f"Table: {t}\n{s}\n\n" for t, s in schemas_dict.items())
        system_instruction = f"""
        You are a DuckDB SQL expert.
        The following SQL query failed with the error below:
        ERROR: {error_msg}
        FAILED SQL: {failed_sql}
        Schemas: {schema_text}
        Return ONLY the corrected SQL query inside a ```sql ... ``` block.
        """
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_instruction}],
            temperature=0.1
        )
        reply = response.choices[0].message.content
        sql_match = re.search(r"```sql(.*?)```", reply, re.DOTALL | re.IGNORECASE)
        if sql_match:
            return sql_match.group(1).strip()
        clean_sql = re.sub(r'```.*?\n', '', reply, flags=re.IGNORECASE)
        return re.sub(r'\n```', '', clean_sql).strip()

    def build_and_execute_insights(schemas_dict, duckdb_conn):
        plan_json_str = generate_insight_plan(schemas_dict)
        try:
            if plan_json_str.strip().startswith("```json"):
                plan_json_str = re.sub(r"^```json\s*", "", plan_json_str.strip(), flags=re.IGNORECASE)
                plan_json_str = re.sub(r"\s*```$", "", plan_json_str)
            plan = json.loads(plan_json_str.strip())
        except Exception as e:
            return {"summary": f"Failed to parse analyst plan: {e}", "insights": [], "suggested_questions": []}

        evaluated_insights = []
        for insight in plan.get("insights", []):
            sql = insight.get("sql_query")
            if not sql:
                continue
            success = False
            df_res = None
            current_sql = sql
            for attempt in range(3):
                try:
                    df_res = duckdb_conn.execute(current_sql).df()
                    success = True
                    break
                except Exception as e:
                    try:
                        current_sql = fix_insight_sql(current_sql, str(e), schemas_dict)
                    except:
                        break
            if success:
                insight["sql_query"] = current_sql
                insight["data"] = df_res
                evaluated_insights.append(insight)

        plan["insights"] = evaluated_insights
        return plan

    # ── Build insights ────────────────────────────────────────────────────────
    if not st.session_state.insights_data:
        with st.spinner("🧠 Generating executive insights…"):
            st.session_state.insights_data = build_and_execute_insights(
                st.session_state.table_schemas, st.session_state.duckdb_conn
            )

    insights_data = st.session_state.insights_data

    if insights_data and insights_data.get("summary"):
        # Header
        st.markdown("""
        <div class="section-title">📊 Executive Insights <span class="section-badge">Auto-Generated</span></div>
        """, unsafe_allow_html=True)

        # Summary card
        st.markdown(f"""
        <div class="card card-violet">
          <div style="font-size:0.78rem;color:var(--violet-lt);font-weight:700;
                      letter-spacing:0.5px;text-transform:uppercase;margin-bottom:8px;">
            Executive Summary
          </div>
          <div style="font-size:0.95rem;line-height:1.65;">{insights_data['summary']}</div>
        </div>
        """, unsafe_allow_html=True)

        # Stats row
        n_tables   = len(st.session_state.table_schemas)
        n_insights = len(insights_data.get("insights", []))
        n_q        = len(insights_data.get("suggested_questions", []))
        st.markdown(f"""
        <div class="stat-row">
          <div class="stat-chip violet">📋 {n_tables} table{'s' if n_tables!=1 else ''}</div>
          <div class="stat-chip cyan">✨ {n_insights} insight{'s' if n_insights!=1 else ''}</div>
          <div class="stat-chip emerald">💡 {n_q} suggested question{'s' if n_q!=1 else ''}</div>
        </div>
        """, unsafe_allow_html=True)

        # Key findings
        insights = insights_data.get("insights", [])
        if insights:
            st.markdown('<div class="section-title">🔍 Key Findings</div>', unsafe_allow_html=True)
            for i, ins in enumerate(insights):
                with st.expander(f"{'①②③④⑤⑥⑦⑧⑨⑩'[i] if i<10 else str(i+1)}  {ins.get('title', f'Insight {i+1}')}", expanded=(i==0)):
                    st.markdown(f"""
                    <div class="card card-cyan" style="margin-bottom:0.8rem;">
                      <span style="font-size:0.88rem;">{ins.get('description', '')}</span>
                    </div>
                    """, unsafe_allow_html=True)

                    df = ins.get("data")
                    if df is not None:
                        if ins.get("is_graph") and ins.get("chart_type"):
                            chart_type = ins.get("chart_type")
                            x_col = ins.get("x_axis")
                            y_col = ins.get("y_axis")
                            color_col = ins.get("color_col")
                            color_arg = color_col if color_col and str(color_col).lower() != "none" else None
                            try:
                                render_chart(chart_type, df, x_col, y_col, color_arg)
                            except Exception:
                                st.dataframe(df, width='stretch')
                        else:
                            st.dataframe(df, width='stretch')

                    with st.popover("🔎 View SQL"):
                        st.code(ins.get("sql_query", ""), language="sql")

        # Suggested questions
        suggested = insights_data.get("suggested_questions", [])
        if suggested:
            st.markdown('<div class="section-title" style="margin-top:1.2rem;">💡 Suggested Questions</div>', unsafe_allow_html=True)
            st.markdown('<p style="color:var(--muted);font-size:0.85rem;margin-bottom:0.8rem;">Click any question to instantly ask the AI on the chat page.</p>', unsafe_allow_html=True)

            cols = st.columns(min(len(suggested), 3))
            for i, q in enumerate(suggested):
                with cols[i % 3]:
                    if st.button(q, key=f"sugg_q_{i}", width='stretch'):
                        st.session_state.trigger_prompt = q
                        st.session_state.active_page = "chat"
                        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# PAGE: ASK AI (CHAT)
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.active_page == "chat":
    st.markdown("<div style='display:none'>force-repaint</div>", unsafe_allow_html=True)

    # ── LLM functions ─────────────────────────────────────────────────────────
    def generate_sql(user_prompt, schemas_dict, history, error_msg=None):
        schema_text = "".join(f"Table: {t}\n{s}\n\n" for t, s in schemas_dict.items())
        system_instruction = f"""
    You are an expert DuckDB Data Analyst.
    The user has uploaded the following tables with their schemas:

    {schema_text}

    Your goal is to generate a DuckDB SQL query to answer the user's question.
    Please carefully infer primary and foreign keys across these tables by analyzing column names
    and use them to construct correct JOIN operations when needed.

    You MUST provide:
    1. The SQL query inside a ```sql ... ``` block.
    2. A brief explanation inside <explanation>...</explanation> tags.
    3. Your confidence (0–100) inside <confidence>...</confidence> tags.

    If conversational (no SQL needed), reply in natural language only — no SQL/explanation/confidence tags.
    Make meaningful aliases for derived columns.
    """
        if error_msg:
            system_instruction += f"\n\nWARNING: Previous query failed: {error_msg}\nPlease fix the SQL."

        messages_payload = [{"role": "system", "content": system_instruction}]
        for m in history:
            messages_payload.append({"role": m["role"], "content": m["content"]})

        response = client.chat.completions.create(model=model_name, messages=messages_payload, temperature=0.1)
        reply = response.choices[0].message.content

        sql_match         = re.search(r"```sql(.*?)```",             reply, re.DOTALL | re.IGNORECASE)
        explanation_match = re.search(r"<explanation>(.*?)</explanation>", reply, re.DOTALL | re.IGNORECASE)
        confidence_match  = re.search(r"<confidence>(.*?)</confidence>",   reply, re.DOTALL | re.IGNORECASE)

        explanation = explanation_match.group(1).strip() if explanation_match else None
        confidence  = confidence_match.group(1).strip()  if confidence_match  else None

        if sql_match:
            sql = sql_match.group(1).strip()
            clean_fallback = re.sub(r"```sql.*?```",             "", reply, flags=re.DOTALL|re.IGNORECASE)
            clean_fallback = re.sub(r"<explanation>.*?</explanation>", "", clean_fallback, flags=re.DOTALL|re.IGNORECASE)
            clean_fallback = re.sub(r"<confidence>.*?</confidence>",   "", clean_fallback, flags=re.DOTALL|re.IGNORECASE)
            return sql, clean_fallback.strip(), explanation, confidence
        return None, reply, None, None

    def generate_summary(user_prompt, data_str, history, schemas_dict, error_msg=None):
        schema_text = "".join(f"Table: {t}\n{s}\n\n" for t, s in schemas_dict.items())
        system_instruction = f"""
    You are an AI Data Assistant. Provide a concise natural language summary of query results.

    Additionally evaluate whether a chart makes sense. If it does, write a SEPARATE DuckDB SQL
    query for visualization and choose the best chart type.

    Database Schemas:
    {schema_text}

    IMPORTANT FOR GRAPH SQL:
    - Only use columns that exist in schemas or are explicitly computed.
    - Handle '$123'→123, '1,234'→1234, '12.34%'→0.1234, date strings appropriately.
    - Use REGEXP_REPLACE for symbols, CAST for types, STRPTIME for date strings.

    A graph makes sense ONLY for comparisons, trends, distributions — NOT single scalars.

    If graph makes sense, append:
    <chart_type>bar|line|scatter|pie|histogram|heatmap</chart_type>
    <graph_sql>sql here</graph_sql>
    <x_axis>col</x_axis>
    <y_axis>col</y_axis>
    <color_col>col or NONE</color_col>
    """
        if error_msg:
            system_instruction += f"\n\nWARNING: Previous graph query failed: {error_msg}"

        messages_payload = [
            {"role": "system", "content": system_instruction},
            {"role": "user",   "content": f"User Question: {user_prompt}\n\nQuery Results:\n{data_str}"}
        ]
        response = client.chat.completions.create(model=model_name, messages=messages_payload, temperature=0.3)
        reply = response.choices[0].message.content

        ct_m  = re.search(r"<chart_type>(.*?)</chart_type>", reply, re.IGNORECASE|re.DOTALL)
        gs_m  = re.search(r"<graph_sql>(.*?)</graph_sql>",   reply, re.IGNORECASE|re.DOTALL)
        xa_m  = re.search(r"<x_axis>(.*?)</x_axis>",         reply, re.IGNORECASE|re.DOTALL)
        ya_m  = re.search(r"<y_axis>(.*?)</y_axis>",         reply, re.IGNORECASE|re.DOTALL)
        cc_m  = re.search(r"<color_col>(.*?)</color_col>",   reply, re.IGNORECASE|re.DOTALL)

        chart_type = ct_m.group(1).strip().lower() if ct_m else None
        graph_sql  = gs_m.group(1).strip()          if gs_m else None
        x_axis     = xa_m.group(1).strip()          if xa_m else None
        y_axis     = [y.strip() for y in ya_m.group(1).split(',')] if ya_m else None
        color_col  = cc_m.group(1).strip()          if cc_m else None

        text = re.sub(r"<chart_type>.*?</chart_type>", "", reply, flags=re.IGNORECASE|re.DOTALL)
        text = re.sub(r"<graph_sql>.*?</graph_sql>",   "", text,  flags=re.IGNORECASE|re.DOTALL)
        text = re.sub(r"<x_axis>.*?</x_axis>",         "", text,  flags=re.IGNORECASE|re.DOTALL)
        text = re.sub(r"<y_axis>.*?</y_axis>",         "", text,  flags=re.IGNORECASE|re.DOTALL)
        text = re.sub(r"<color_col>.*?</color_col>",   "", text,  flags=re.IGNORECASE|re.DOTALL).strip()

        return text, chart_type, graph_sql, x_axis, y_axis, color_col

    # ── Page header ───────────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-title">💬 Ask AI <span class="section-badge">Natural Language</span></div>
    <p style="color:var(--muted);font-size:0.88rem;margin-bottom:1rem;">
      Ask anything about your data — the AI writes the SQL, runs it, and explains the results.
    </p>
    """, unsafe_allow_html=True)

# ── Chat history ──────────────────────────────────────────────────────────
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if "sql" in message and message["sql"]:
                with st.expander("🔎 Query Details"):
                    st.code(message["sql"], language="sql")
                    if message.get("explanation"):
                        st.markdown(f"**Explanation:** {message['explanation']}")
                    if message.get("confidence"):
                        conf = int(message["confidence"]) if str(message["confidence"]).isdigit() else 0
                        color = "emerald" if conf >= 80 else "amber" if conf >= 60 else "rose"
                        st.markdown(f'<span class="stat-chip {color}">Confidence: {message["confidence"]}%</span>', unsafe_allow_html=True)
            if "data" in message and message["data"] is not None:
                st.dataframe(message["data"], width='stretch')
            chart_type = message.get("chart_type")
            if chart_type:
                graph_df   = message.get("graph_df", message.get("data"))
                x_axis     = message.get("x_axis")
                y_axis     = message.get("y_axis")
                color_col  = message.get("color_col")
                color_arg  = color_col if color_col and str(color_col).lower() != "none" else None
                if "graph_sql" in message and message["graph_sql"]:
                    with st.expander("📐 Graph SQL"):
                        st.code(message["graph_sql"], language="sql")
                try:
                    if x_axis and y_axis:
                        render_chart(chart_type, graph_df, x_axis, y_axis, color_arg)
                    else:
                        render_chart(chart_type, graph_df, None, None, color_arg)
                except Exception:
                    pass  # Silently skip broken chart replays
    # else:
    #     st.write("No messages yet.")

    # ── Voice input ───────────────────────────────────────────────────────────
    stt_text = speech_to_text(
        language='en',
        start_prompt="Click to Speak",
        stop_prompt="Click to Stop",
        just_once=True,
        key='STT'
    )

    st.markdown("""
        <script>
        setTimeout(() => {
            window.dispatchEvent(new Event('resize'));
        }, 50);
        </script>
        """, unsafe_allow_html=True)
    
    # ── Text input ────────────────────────────────────────────────────────────
    prompt = st.chat_input("Ask a question about your data…")

    if stt_text:
        prompt = stt_text
    if st.session_state.trigger_prompt:
        prompt = st.session_state.trigger_prompt
        st.session_state.trigger_prompt = None

    # ── Process prompt ────────────────────────────────────────────────────────
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("assistant"):
            max_retries = 3
            attempt = 0
            success = False
            sql_query = None
            conversational_fallback = None
            explanation = None
            confidence = None
            error_msg = None
            df_result = None

            while attempt <= max_retries and not success:
                with st.spinner(f"{'🔄 Retrying…' if attempt > 0 else '⚡ Analyzing…'}"):
                    try:
                        sql_query, conversational_fallback, explanation, confidence = generate_sql(
                            prompt, st.session_state.table_schemas, st.session_state.messages, error_msg
                        )
                    except Exception as e:
                        error_msg = f"API Error: {e}"
                        attempt += 1
                        continue

                if sql_query:
                    with st.spinner("🗄️ Running query…"):
                        try:
                            df_result = st.session_state.duckdb_conn.execute(sql_query).df()
                            success = True
                        except Exception as e:
                            error_msg = f"SQL Execution Error: {e}"
                            attempt += 1
                else:
                    success = True  # conversational

            if success and sql_query:
                with st.expander("🔎 Query Details", expanded=True):
                    st.code(sql_query, language="sql")
                    if explanation:
                        st.markdown(f"**Explanation:** {explanation}")
                    if confidence:
                        conf_int = int(confidence) if str(confidence).isdigit() else 0
                        color = "emerald" if conf_int >= 80 else "amber" if conf_int >= 60 else "violet"
                        st.markdown(f'<span class="stat-chip {color}">Confidence: {confidence}%</span>', unsafe_allow_html=True)

                data_str_for_llm = df_result.head(100).to_string()
                st.dataframe(df_result, width='stretch')

                with st.spinner("🎨 Crafting summary and chart…"):
                    summary_max_retries = 3
                    summary_attempt = 0
                    summary_success = False
                    graph_error_msg = None
                    final_summary_text = ""
                    final_chart_type = final_graph_sql = final_x_axis = final_y_axis = final_color_col = final_graph_df = None

                    while summary_attempt <= summary_max_retries and not summary_success:
                        try:
                            summary_text, chart_type, graph_sql, x_axis, y_axis, color_col = generate_summary(
                                prompt, data_str_for_llm, st.session_state.messages,
                                st.session_state.table_schemas, graph_error_msg
                            )
                            final_summary_text = summary_text
                            final_chart_type   = chart_type
                            final_graph_sql    = graph_sql
                            final_x_axis       = x_axis
                            final_y_axis       = y_axis
                            final_color_col    = color_col

                            if chart_type and graph_sql and x_axis and y_axis:
                                try:
                                    clean_sql = re.sub(r'```sql\n', '', graph_sql, flags=re.IGNORECASE)
                                    clean_sql = re.sub(r'\n```', '', clean_sql).strip()
                                    final_graph_df = st.session_state.duckdb_conn.execute(clean_sql).df()
                                    summary_success = True
                                except Exception as de:
                                    graph_error_msg = f"Graph SQL Execution Error: {de}"
                                    summary_attempt += 1
                                    if summary_attempt > summary_max_retries:
                                        final_chart_type = None
                                        summary_success = True
                                    continue
                            else:
                                summary_success = True
                        except Exception:
                            summary_success = True
                            break

                if final_summary_text:
                    st.markdown(final_summary_text)

                if final_chart_type and final_graph_df is not None:
                    try:
                        color_arg = final_color_col if final_color_col and str(final_color_col).lower() != "none" else None
                        render_chart(final_chart_type, final_graph_df, final_x_axis, final_y_axis, color_arg)
                    except Exception:
                        final_chart_type = None

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_summary_text,
                    "sql": sql_query,
                    "explanation": explanation,
                    "confidence": confidence,
                    "data": df_result,
                    "chart_type": final_chart_type,
                    "graph_sql": final_graph_sql,
                    "graph_df": final_graph_df,
                    "x_axis": final_x_axis,
                    "y_axis": final_y_axis,
                    "color_col": final_color_col
                })

            elif success and not sql_query:
                st.markdown(conversational_fallback)
                st.session_state.messages.append({"role": "assistant", "content": conversational_fallback})

            else:
                # All retries exhausted — show a calm, user-friendly message. No raw error.
                friendly_msg = "I wasn't able to answer that question right now. Try rephrasing it, or ask about a different aspect of your data."
                st.markdown(f"""
                <div class="card" style="border-color:rgba(245,158,11,0.4);background:rgba(245,158,11,0.06);">
                  <strong style="color:#FCD34D;">⚠️ Couldn't generate a result</strong><br/>
                  <span style="font-size:0.88rem;color:var(--muted);">{friendly_msg}</span>
                </div>
                """, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": friendly_msg})
        st.rerun()
        st.markdown("<div style='display:none'>force-repaint</div>", unsafe_allow_html=True)

