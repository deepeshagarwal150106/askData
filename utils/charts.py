import streamlit as st
import plotly.express as px


def render_chart(chart_type: str, df, x_col, y_col, color_arg=None) -> None:
    """Render a chart using Streamlit / Plotly based on chart_type.

    Supports: bar, line, scatter, pie, histogram, heatmap.
    Falls back gracefully for unsupported types.
    """
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
