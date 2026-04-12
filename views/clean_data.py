"""Clean Data page for Ask With Data AI.

Handles the LLM-driven data cleaning workflow:
  1. Preview each pending file
  2. AI analysis of anomalies
  3. User instructions input
  4. LLM generates a custom_clean() function
  5. Apply cleaning + load into DuckDB
"""

import re
import streamlit as st
from cleaner import clean_dataframe
from services.database import get_schema
from services.llm import generate_sql  # noqa: not used here, kept for parity


def render_clean_page(client, model_name: str) -> None:
    """Render the Clean Data page."""
    has_pending = bool(st.session_state.pending_files)

    if not has_pending:
        st.markdown("""
        <div class="empty-state">
          <div class="icon">✅</div>
          <h3>All files are clean</h3>
          <p>No pending files to clean. Navigate to Insights or Ask AI to explore your data.</p>
        </div>
        """, unsafe_allow_html=True)
        return

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
                st.dataframe(df.head(5), width="stretch")
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
                    schema_str = (
                        "Columns and Data Types:\n" + str(df.dtypes)
                        + "\n\nSample Data:\n" + df.head(10).to_string()
                    )
                    system_prompt = (
                        "You are a Data Cleaning Expert. Analyze the dataframe schema and sample data. "
                        "Identify anomalies like missing values (NaN, null strings), incorrect data types, "
                        "currency formatting strings (e.g. '$123' instead of numeric), or date strings that "
                        "need conversion. also check if null values are there in form of '.' or '?' . "
                        "Give me a concise summary of the problems found and ask the user how they want to "
                        "handle them (e.g. drop nulls or fill with mean? Strip '$'?). Be conversational and brief."
                    )
                    try:
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user",   "content": schema_str},
                            ],
                            temperature=0.3,
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
                placeholder="e.g. Drop rows with nulls, strip $ from revenue column, convert date to datetime…",
            )

            if st.button("⚡ Apply & Load Table", key=f"clean_btn_{filename}"):
                if user_instruction:
                    with st.spinner("Executing cleaning pipeline…"):
                        schema_for_cleaning = (
                            "Columns and Data Types:\n" + str(df.dtypes)
                            + "\n\nSample Data:\n" + df.head(10).to_string()
                        )
                        cleaning_prompt = f"""
You are a strict code generator. Generate a python function named `custom_clean` that takes a pandas DataFrame `df` as input and returns the cleaned DataFrame.
Apply the user's instructions to clean the data.
User Instructions: "{user_instruction}"
if user says do as you like then do as you think is best for the data and you can use your insights:{st.session_state.cleaning_questions.get(filename, '')}. only use this if the user wants you to do like you suggested.

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

                        while attempt < max_retries and not success:
                            prompt_to_send = cleaning_prompt
                            if error_msg:
                                prompt_to_send += f"\n\nPrevious attempt failed with error: {error_msg}. Please fix the python code."
                            try:
                                code_response = client.chat.completions.create(
                                    model=model_name,
                                    messages=[{"role": "user", "content": prompt_to_send}],
                                    temperature=0.1,
                                )
                                code_str = code_response.choices[0].message.content
                                code_match = re.search(r"```python(.*?)```", code_str, re.DOTALL | re.IGNORECASE)
                                if code_match:
                                    python_code = code_match.group(1).strip()
                                    local_vars = {}
                                    exec(python_code, globals(), local_vars)
                                    custom_clean = local_vars["custom_clean"]
                                    cleaned_df = custom_clean(df.copy())
                                    cleaned_df = clean_dataframe(cleaned_df)

                                    table_name = re.sub(r"[^a-zA-Z0-9_]", "_", filename.split(".")[0]).lower()
                                    original_table_name = table_name
                                    counter = 1
                                    while table_name in st.session_state.table_schemas:
                                        table_name = f"{original_table_name}_{counter}"
                                        counter += 1

                                    st.session_state.duckdb_conn.register(table_name, cleaned_df)
                                    st.session_state.table_schemas[table_name] = get_schema(
                                        st.session_state.duckdb_conn, table_name
                                    )
                                    st.session_state.data_loaded_files.add(filename)
                                    del st.session_state.pending_files[filename]
                                    st.session_state.insights_data = None  # reset insights for new data
                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": f"✅ `{filename}` cleaned and loaded as table **`{table_name}`**. Ready to analyze!",
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
