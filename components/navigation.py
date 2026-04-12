import streamlit as st


def render_navigation(has_data: bool, has_pending: bool) -> None:
    """Render the step progress bar and the three navigation pill buttons.

    Reads and writes ``st.session_state.active_page``.
    """
    active_page = st.session_state.active_page

    # ── Progress steps ────────────────────────────────────────────────────────
    step_clean = (
        "active" if active_page == "clean"
        else ("done" if has_data else "")
    )
    step_insights = (
        "active" if active_page == "insights"
        else ("done" if has_data and active_page == "chat" else "")
    )
    step_chat = "active" if active_page == "chat" else ""

    st.markdown(f"""
<div class="step-row">
  <div class="step {step_clean}">① Clean Data</div>
  <div class="step {step_insights}">② Insights</div>
  <div class="step {step_chat}">③ Ask Questions</div>
</div>
""", unsafe_allow_html=True)

    # ── Nav pill buttons ──────────────────────────────────────────────────────
    nav_cols = st.columns([1, 1, 1])

    with nav_cols[0]:
        if has_pending:
            st.button(
                "🧹 Clean Data", key="nav_clean", width="stretch",
                on_click=lambda: st.session_state.update({"active_page": "clean"})
            )
        elif has_data:
            if st.button("🧹 Clean Data", key="nav_clean", width="stretch"):
                st.session_state.active_page = "clean"

    with nav_cols[1]:
        if has_data:
            if st.button("📊 Insights", key="nav_insights", width="stretch"):
                st.session_state.active_page = "insights"

    with nav_cols[2]:
        if has_data:
            if st.button("💬 Ask AI", key="nav_chat", width="stretch"):
                st.session_state.active_page = "chat"

    st.markdown("<hr/>", unsafe_allow_html=True)
