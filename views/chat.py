"""Ask AI (Chat) page for Ask With Data AI.

Handles the full conversational query flow:
  - Renders chat history with SQL details, data frames, and charts
  - Accepts voice input (speech-to-text) and text input
  - Supports trigger_prompt from the Insights page
  - Runs SQL with up to 3 retry attempts
  - Generates a natural language summary and optional chart for each result
"""

import re
import streamlit as st
from streamlit_mic_recorder import speech_to_text

from services.llm import generate_sql, generate_summary
from utils.charts import render_chart


def render_chat_page(client, model_name: str) -> None:
    """Render the Ask AI chat page."""

    st.markdown("<div style='display:none'>force-repaint</div>", unsafe_allow_html=True)

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

            if message.get("sql"):
                with st.expander("🔎 Query Details"):
                    st.code(message["sql"], language="sql")
                    if message.get("explanation"):
                        st.markdown(f"**Explanation:** {message['explanation']}")
                    if message.get("confidence"):
                        conf = int(message["confidence"]) if str(message["confidence"]).isdigit() else 0
                        color = "emerald" if conf >= 80 else "amber" if conf >= 60 else "rose"
                        st.markdown(
                            f'<span class="stat-chip {color}">Confidence: {message["confidence"]}%</span>',
                            unsafe_allow_html=True,
                        )

            if message.get("data") is not None:
                st.dataframe(message["data"], width="stretch")

            chart_type = message.get("chart_type")
            if chart_type:
                graph_df  = message.get("graph_df", message.get("data"))
                x_axis    = message.get("x_axis")
                y_axis    = message.get("y_axis")
                color_col = message.get("color_col")
                color_arg = color_col if color_col and str(color_col).lower() != "none" else None
                if message.get("graph_sql"):
                    with st.expander("📐 Graph SQL"):
                        st.code(message["graph_sql"], language="sql")
                try:
                    if x_axis and y_axis:
                        render_chart(chart_type, graph_df, x_axis, y_axis, color_arg)
                    else:
                        render_chart(chart_type, graph_df, None, None, color_arg)
                except Exception:
                    pass  # Silently skip broken chart replays

    # ── Voice input ───────────────────────────────────────────────────────────
    stt_text = speech_to_text(
        language="en",
        start_prompt="Click to Speak",
        stop_prompt="Click to Stop",
        just_once=True,
        key="STT",
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
    if not prompt:
        return

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
                        client, model_name, prompt,
                        st.session_state.table_schemas,
                        st.session_state.messages,
                        error_msg,
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
                success = True  # conversational — no SQL needed

        # ── Render result ─────────────────────────────────────────────────────
        if success and sql_query:
            with st.expander("🔎 Query Details", expanded=True):
                st.code(sql_query, language="sql")
                if explanation:
                    st.markdown(f"**Explanation:** {explanation}")
                if confidence:
                    conf_int = int(confidence) if str(confidence).isdigit() else 0
                    color = "emerald" if conf_int >= 80 else "amber" if conf_int >= 60 else "violet"
                    st.markdown(
                        f'<span class="stat-chip {color}">Confidence: {confidence}%</span>',
                        unsafe_allow_html=True,
                    )

            data_str_for_llm = df_result.head(100).to_string()
            st.dataframe(df_result, width="stretch")

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
                            client, model_name, prompt, data_str_for_llm,
                            st.session_state.messages,
                            st.session_state.table_schemas,
                            graph_error_msg,
                        )
                        final_summary_text = summary_text
                        final_chart_type   = chart_type
                        final_graph_sql    = graph_sql
                        final_x_axis       = x_axis
                        final_y_axis       = y_axis
                        final_color_col    = color_col

                        if chart_type and graph_sql and x_axis and y_axis:
                            try:
                                clean_sql = re.sub(r"```sql\n", "", graph_sql, flags=re.IGNORECASE)
                                clean_sql = re.sub(r"\n```", "", clean_sql).strip()
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
                    color_arg = (
                        final_color_col
                        if final_color_col and str(final_color_col).lower() != "none"
                        else None
                    )
                    render_chart(final_chart_type, final_graph_df, final_x_axis, final_y_axis, color_arg)
                except Exception:
                    final_chart_type = None

            st.session_state.messages.append({
                "role":       "assistant",
                "content":    final_summary_text,
                "sql":        sql_query,
                "explanation": explanation,
                "confidence":  confidence,
                "data":        df_result,
                "chart_type":  final_chart_type,
                "graph_sql":   final_graph_sql,
                "graph_df":    final_graph_df,
                "x_axis":      final_x_axis,
                "y_axis":      final_y_axis,
                "color_col":   final_color_col,
            })

        elif success and not sql_query:
            st.markdown(conversational_fallback)
            st.session_state.messages.append({"role": "assistant", "content": conversational_fallback})

        else:
            friendly_msg = (
                "I wasn't able to answer that question right now. "
                "Try rephrasing it, or ask about a different aspect of your data."
            )
            st.markdown(f"""
            <div class="card" style="border-color:rgba(245,158,11,0.4);background:rgba(245,158,11,0.06);">
              <strong style="color:#FCD34D;">⚠️ Couldn't generate a result</strong><br/>
              <span style="font-size:0.88rem;color:var(--muted);">{friendly_msg}</span>
            </div>
            """, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": friendly_msg})

    st.rerun()
    st.markdown("<div style='display:none'>force-repaint</div>", unsafe_allow_html=True)
