"""Global CSS injected into every page via st.markdown(GLOBAL_CSS, unsafe_allow_html=True)."""

GLOBAL_CSS = """
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
"""
