"""Sidebar component for Ask With Data AI.

Renders the full sidebar (brand, config status, model selector, file uploader,
loaded tables with schema pills and sample data, footer) and returns the values
needed by the rest of the app.
"""

import os
import streamlit as st
from groq import Groq
from config.settings import MODEL_OPTIONS


def render_sidebar() -> tuple:
    """Render the sidebar and return (client, model_name, uploaded_files).

    The Groq client is initialised here because the sidebar owns the API key
    status indicator.  If the key is missing, ``st.stop()`` is called so the
    rest of the app never runs.
    """
    with st.sidebar:
        # ── Brand header ──────────────────────────────────────────────────────
        st.markdown("""
    <div class="sidebar-brand">
      <div class="sidebar-brand-icon">⚡</div>
      <div>
        <div class="sidebar-brand-text">Ask With Data AI</div>
        <div class="sidebar-brand-sub">Intelligent Data Analytics</div>
      </div>
    </div>
    <div class="sidebar-divider glow"></div>
    """, unsafe_allow_html=True)

        # ── Configuration section ──────────────────────────────────────────────
        st.markdown("""
    <div class="sidebar-section-label"><span class="dot dot-violet"></span> CONFIGURATION</div>
    """, unsafe_allow_html=True)

        api_key = os.environ.get("GROQ_API_KEY")

        if api_key:
            client = Groq(api_key=api_key)
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

        model_name = st.selectbox(
            "Model", MODEL_OPTIONS, index=0, label_visibility="collapsed"
        )

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # ── Upload section ─────────────────────────────────────────────────────
        st.markdown("""
    <div class="sidebar-section-label"><span class="dot dot-cyan"></span> DATA SOURCE</div>
    """, unsafe_allow_html=True)

        uploaded_files = st.file_uploader(
            "Drop CSV or Excel files here",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        # ── Loaded tables section ──────────────────────────────────────────────
        if st.session_state.get("data_loaded_files"):
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

            for t_name in st.session_state.get("table_schemas", {}):
                try:
                    conn = st.session_state.duckdb_conn
                    schema_df = conn.execute(f"DESCRIBE {t_name}").df()
                    col_count = len(schema_df)
                    row_count = conn.execute(f"SELECT COUNT(*) FROM {t_name}").fetchone()[0]
                    sample_df = conn.execute(f"SELECT * FROM {t_name} LIMIT 3").df()
                except Exception:
                    col_count = 0
                    row_count = 0
                    schema_df = None
                    sample_df = None

                # Build column pills HTML
                col_pills_html = ""
                if schema_df is not None:
                    for _, row in schema_df.iterrows():
                        c_name = row["column_name"]
                        c_type = row["column_type"]
                        type_class = "type-varchar"
                        if "INT" in c_type.upper() or "BIGINT" in c_type.upper():
                            type_class = "type-int"
                        elif any(t in c_type.upper() for t in ["DOUBLE", "FLOAT", "DECIMAL"]):
                            type_class = "type-float"
                        elif any(t in c_type.upper() for t in ["DATE", "TIME", "TIMESTAMP"]):
                            type_class = "type-date"
                        col_pills_html += (
                            f'<span class="schema-col-pill">'
                            f'<span class="col-name">{c_name}</span>'
                            f'<span class="col-type {type_class}">{c_type}</span>'
                            f'</span>'
                        )

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

                with st.expander("📋 View Schema", expanded=False):
                    st.markdown(f"""
                <div class="schema-columns-grid">
                  {col_pills_html}
                </div>
                {sample_html}
                """, unsafe_allow_html=True)

        # ── Footer ─────────────────────────────────────────────────────────────
        st.markdown(
            '<div class="sidebar-divider glow" style="margin-top:auto;"></div>',
            unsafe_allow_html=True,
        )
        st.markdown("""
    <div class="sidebar-footer">
      <div class="sidebar-footer-text">Powered by Groq &amp; DuckDB</div>
      <div class="sidebar-footer-badge">v2.0 · Pro</div>
    </div>
    """, unsafe_allow_html=True)

    return client, model_name, uploaded_files
