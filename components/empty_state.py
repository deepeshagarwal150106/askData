import streamlit as st


def render_empty_state() -> None:
    """Render the landing page shown when no data has been loaded yet.

    Calls st.stop() after rendering so the rest of the app is not executed.
    """
    st.markdown("""
<div class="empty-state">
  <div class="icon">📂</div>
  <h3>No data loaded yet</h3>
  <p>Upload one or more CSV or Excel (.xlsx) files from the sidebar to get started.
     DataPulse will auto-clean, analyze, and let you chat with your data.</p>
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
