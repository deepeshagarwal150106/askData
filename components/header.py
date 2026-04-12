import streamlit as st


def render_header() -> None:
    """Render the top application header bar."""
    st.markdown("""
<div class="app-header">
  <div class="app-logo">⚡</div>
  <div>
    <div class="app-title">Ask With Data AI</div>
    <div class="app-sub">Natural language analytics · Powered by Groq</div>
  </div>
</div>
""", unsafe_allow_html=True)

    # Force a resize event so Streamlit reflows the layout correctly
    st.markdown("""
<script>
setTimeout(() => {
    window.dispatchEvent(new Event('resize'));
}, 50);
</script>
""", unsafe_allow_html=True)
