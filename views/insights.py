"""Insights page for DataPulse AI.

Generates an executive summary, key analytical findings with SQL-backed charts,
and suggested follow-up questions based on the loaded tables.
"""

import streamlit as st
from services.llm import build_and_execute_insights
from utils.charts import render_chart


def render_insights_page(client, model_name: str) -> None:
    """Render the Executive Insights page."""

    # Build (or reuse cached) insights data
    if not st.session_state.insights_data:
        with st.spinner("🧠 Generating executive insights…"):
            st.session_state.insights_data = build_and_execute_insights(
                client,
                model_name,
                st.session_state.table_schemas,
                st.session_state.duckdb_conn,
            )

    insights_data = st.session_state.insights_data

    if not (insights_data and insights_data.get("summary")):
        return

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="section-title">📊 Executive Insights <span class="section-badge">Auto-Generated</span></div>
    """, unsafe_allow_html=True)

    # ── Summary card ──────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="card card-violet">
      <div style="font-size:0.78rem;color:var(--violet-lt);font-weight:700;
                  letter-spacing:0.5px;text-transform:uppercase;margin-bottom:8px;">
        Executive Summary
      </div>
      <div style="font-size:0.95rem;line-height:1.65;">{insights_data['summary']}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Stats row ─────────────────────────────────────────────────────────────
    n_tables   = len(st.session_state.table_schemas)
    n_insights = len(insights_data.get("insights", []))
    n_q        = len(insights_data.get("suggested_questions", []))
    st.markdown(f"""
    <div class="stat-row">
      <div class="stat-chip violet">📋 {n_tables} table{'s' if n_tables != 1 else ''}</div>
      <div class="stat-chip cyan">✨ {n_insights} insight{'s' if n_insights != 1 else ''}</div>
      <div class="stat-chip emerald">💡 {n_q} suggested question{'s' if n_q != 1 else ''}</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Key findings ──────────────────────────────────────────────────────────
    insights = insights_data.get("insights", [])
    if insights:
        st.markdown('<div class="section-title">🔍 Key Findings</div>', unsafe_allow_html=True)
        numbered = "①②③④⑤⑥⑦⑧⑨⑩"
        for i, ins in enumerate(insights):
            label = (numbered[i] if i < len(numbered) else str(i + 1))
            with st.expander(f"{label}  {ins.get('title', f'Insight {i + 1}')}", expanded=(i == 0)):
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
                            st.dataframe(df, width="stretch")
                    else:
                        st.dataframe(df, width="stretch")

                with st.popover("🔎 View SQL"):
                    st.code(ins.get("sql_query", ""), language="sql")

    # ── Suggested questions ───────────────────────────────────────────────────
    suggested = insights_data.get("suggested_questions", [])
    if suggested:
        st.markdown(
            '<div class="section-title" style="margin-top:1.2rem;">💡 Suggested Questions</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:var(--muted);font-size:0.85rem;margin-bottom:0.8rem;">'
            "Click any question to instantly ask the AI on the chat page.</p>",
            unsafe_allow_html=True,
        )

        cols = st.columns(min(len(suggested), 3))
        for i, q in enumerate(suggested):
            with cols[i % 3]:
                if st.button(q, key=f"sugg_q_{i}", width="stretch"):
                    st.session_state.trigger_prompt = q
                    st.session_state.active_page = "chat"
                    st.rerun()
