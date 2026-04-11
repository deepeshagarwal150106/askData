import streamlit as st
import pandas as pd
import duckdb
from groq import Groq
import os
import re
import numpy as np
import time
import json
from dotenv import load_dotenv
import plotly.express as px
from cleaner import clean_dataframe
from streamlit_mic_recorder import speech_to_text

# Load env variables if any
load_dotenv()

# Set page config
st.set_page_config(page_title="AI Data Analyst", page_icon="✨", layout="wide")

# Custom CSS for a bit more premium feel
st.markdown("""
<style>
    .stChatFloatingInputContainer {
        padding-bottom: 20px;
    }
    .stChatMessage {
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("✨ AI Data Analyst (Powered by Groq)")
st.markdown("Upload your CSV data and ask questions. Our AI will analyze the data, generate SQL queries, and visualize the results for you in real-time using lightning-fast open-source models.")

# --- SIDEBAR & CONFIG ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key_input = st.text_input("Groq API Key", type="password", value=os.environ.get("GROQ_API_KEY", ""))
    
    if api_key_input:
        client = Groq(api_key=api_key_input)
    else:
        st.warning("Please enter your Groq API Key to continue.")
        st.markdown("[Get your free Groq API key here](https://console.groq.com/keys)")
        st.stop()

    # Groq model selector (Gemma, Llama)
    model_name = st.selectbox("Select Model", [
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-120b",
        "llama-3.1-8b-instant",  
        "gemma2-9b-it", 
        "mixtral-8x7b-32768"
    ], index=0)
    
    st.markdown("---")
    st.header("📄 Upload Data")
    uploaded_files = st.file_uploader("Upload CSVs", type=["csv"], accept_multiple_files=True)

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "duckdb_conn" not in st.session_state:
    st.session_state.duckdb_conn = duckdb.connect(database=':memory:', read_only=False)

if "table_schemas" not in st.session_state:
    st.session_state.table_schemas = {}
    
if "data_loaded_files" not in st.session_state:
    st.session_state.data_loaded_files = set()

if "pending_files" not in st.session_state:
    st.session_state.pending_files = {}

if "cleaning_questions" not in st.session_state:
    st.session_state.cleaning_questions = {}

if "insights_data" not in st.session_state:
    st.session_state.insights_data = None

if "trigger_prompt" not in st.session_state:
    st.session_state.trigger_prompt = None

def get_schema(conn, table_name):
    # Retrieve schema string for LLM and a few sample rows
    try:
        # 1. Get Schema
        schema_df = conn.execute(f"DESCRIBE {table_name}").df()
        schema_str = "Columns and Data Types:\n"
        for _, row in schema_df.iterrows():
            schema_str += f"- {row['column_name']} ({row['column_type']})\n"
            
        # 2. Get Sample Rows
        sample_df = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").df()
        schema_str += "\nSample Data (Top 5 rows):\n"
        schema_str += sample_df.to_string(index=False) + "\n"
        
        return schema_str
    except Exception as e:
        return str(e)

# --- DATA LOADING ---
if uploaded_files:
    for uploaded_file in uploaded_files:
        if uploaded_file.name not in st.session_state.data_loaded_files and uploaded_file.name not in st.session_state.pending_files:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.pending_files[uploaded_file.name] = df
            except Exception as e:
                st.error(f"Error reading {uploaded_file.name}: {e}")
                st.stop()

# --- DATA CLEANING SETUP ---
if st.session_state.pending_files:
    st.header("🛠️ Data Setup & Review")
    st.markdown("Before querying, let's clean your data. Please review the recommended actions below for each file.")
    
    for filename, df in list(st.session_state.pending_files.items()):
        with st.expander(f"Clean file: {filename}", expanded=True):
            if filename not in st.session_state.cleaning_questions:
                with st.spinner(f"Analyzing {filename} for cleaning..."):
                    schema_str = "Columns and Data Types:\n" + str(df.dtypes) + "\n\nSample Data:\n" + df.head(10).to_string()
                    system_prompt = "You are a Data Cleaning Expert. Analyze the dataframe schema and sample data. Identify anomalies like missing values (NaN, null strings), incorrect data types, currency formatting strings (e.g. '$123' instead of numeric), or date strings that need conversion. Give me a concise summary of the problems found and ask the user how they want to handle them (e.g. drop nulls or fill with mean? Strip '$'?). Be conversational and brief."
                    try:
                        response = client.chat.completions.create(
                            model=model_name,
                            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": schema_str}],
                            temperature=0.3
                        )
                        st.session_state.cleaning_questions[filename] = response.choices[0].message.content
                    except Exception as e:
                        st.session_state.cleaning_questions[filename] = f"Could not analyze data due to API error: {e}"
            
            st.markdown(st.session_state.cleaning_questions[filename])
            
            user_instruction = st.text_area("How would you like to clean this data?", key=f"clean_input_{filename}")
            
            if st.button("Apply Cleaning & Load", key=f"clean_btn_{filename}"):
                if user_instruction:
                    with st.spinner("Executing cleaning..."):
                        schema_for_cleaning = "Columns and Data Types:\n" + str(df.dtypes) + "\n\nSample Data:\n" + df.head(10).to_string()
                        cleaning_prompt = f"""
You are a strict code generator. Generate a python function named `custom_clean` that takes a pandas DataFrame `df` as input and returns the cleaned DataFrame.
Apply the user's instructions to clean the data.
User Instructions: "{user_instruction}"

Data Schema & Sample:
{schema_for_cleaning}

Rules:
1. You MUST use only Pandas and standard Python libraries (re, numpy). `import pandas as pd`, `import numpy as np`, `import re` inside the function.
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
                                    cleaned_df=clean_dataframe(cleaned_df)
                                    
                                    # Register in DuckDB
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
                                    st.session_state.messages.append({"role": "assistant", "content": f"✅ Successfully cleaned and loaded `{filename}` as table `{table_name}`. Use the chat to ask questions about your data!"})
                                    st.rerun() 
                                    success = True
                                else:
                                    error_msg = "No python code block found in response."
                                    attempt += 1
                            except Exception as e:
                                error_msg = str(e)
                                attempt += 1
                                
                        if not success:
                            st.error(f"Failed to apply cleaning after {max_retries} attempts. Last error: {error_msg}")
                            with st.expander("Show Generated Code Attempt"):
                                st.code(python_code if 'python_code' in locals() else code_str)
                else:
                    st.warning("Please provide cleaning instructions.")

    # Stop execution here if there are pending files so user must clean them before chat
    if st.session_state.pending_files:
        st.stop()

if st.session_state.data_loaded_files:
    st.sidebar.success(f"Loaded {len(st.session_state.data_loaded_files)} file(s)")
    st.sidebar.markdown("**Schemas:**")
    for t_name, t_schema in st.session_state.table_schemas.items():
        with st.sidebar.expander(f"Table: {t_name}"):
            st.text(t_schema)

if not st.session_state.data_loaded_files and not st.session_state.pending_files:
    st.info("👈 Please upload CSV file(s) from the sidebar to get started.")
    st.stop()

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
        system_instruction += f"\n\nPREVIOUS ERROR: Your previous JSON was invalid or failed softly. Please fix it. Error: {error_msg}"
        
    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": system_instruction}],
        temperature=0.3
    )
    
    reply = response.choices[0].message.content
    return reply

def fix_insight_sql(failed_sql, error_msg, schemas_dict):
    schema_text = ""
    for t_name, t_schema in schemas_dict.items():
        schema_text += f"Table: {t_name}\n{t_schema}\n\n"

    system_instruction = f"""
    You are a DuckDB SQL expert. 
    The following SQL query failed with the error below:
    
    ERROR: {error_msg}
    
    FAILED SQL:
    {failed_sql}
    
    Schemas:
    {schema_text}
    
    Return ONLY the corrected SQL query inside a ```sql ... ``` block. Do not provide any other text.
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
    clean_sql = re.sub(r'\n```', '', clean_sql, flags=re.IGNORECASE)
    return clean_sql.strip()
    
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


# --- EXECUTIVE INSIGHTS ---
if not st.session_state.pending_files and st.session_state.data_loaded_files:
    if not st.session_state.insights_data:
        with st.spinner("🧠 Generating Executive Data Insights..."):
            st.session_state.insights_data = build_and_execute_insights(st.session_state.table_schemas, st.session_state.duckdb_conn)
            
    insights_data = st.session_state.insights_data
    if insights_data and insights_data.get("summary"):
        st.header("📊 Executive Data Insights")
        st.markdown(insights_data["summary"])
        
        insights = insights_data.get("insights", [])
        if insights:
            st.subheader("Key Findings")
            for i, ins in enumerate(insights):
                with st.expander(f"✨ {ins.get('title', f'Insight {i+1}')}"):
                    st.markdown(f"**{ins.get('description', '')}**")
                    
                    df = ins.get("data")
                    if df is not None:
                         if ins.get("is_graph") and ins.get("chart_type"):
                             chart_type = ins.get("chart_type")
                             x_col = ins.get("x_axis")
                             y_col = ins.get("y_axis")
                             color_col = ins.get("color_col")
                             color_arg = color_col if color_col and str(color_col).lower() != "none" else None
                             
                             try:
                                 if chart_type == "bar":
                                     st.bar_chart(df, x=x_col, y=y_col, color=color_arg)
                                 elif chart_type == "line":
                                     st.line_chart(df, x=x_col, y=y_col, color=color_arg)
                                 elif chart_type == "scatter":
                                     st.scatter_chart(df, x=x_col, y=y_col, color=color_arg)
                                 elif chart_type in ["pie", "histogram", "heatmap"]:
                                     y_val = y_col[0] if isinstance(y_col, list) and y_col else y_col
                                     if chart_type == "pie":
                                         fig = px.pie(df, names=x_col, values=y_val, color=color_arg)
                                     elif chart_type == "histogram":
                                         fig = px.histogram(df, x=x_col, y=y_val, color=color_arg)
                                     elif chart_type == "heatmap":
                                         fig = px.density_heatmap(df, x=x_col, y=y_val, z=color_arg)
                                     st.plotly_chart(fig, use_container_width=True)
                             except Exception as e:
                                 st.warning(f"Could not render graph: {e}")
                                 st.dataframe(df, use_container_width=True)
                         else:
                             st.dataframe(df, use_container_width=True)
                             
                    with st.popover("View SQL"):
                         st.code(ins.get("sql_query", ""), language="sql")
                         
        suggested = insights_data.get("suggested_questions", [])
        if suggested:
            st.subheader("Suggested Questions")
            cols = st.columns(len(suggested))
            for i, q in enumerate(suggested):
                if cols[i].button(q, key=f"sugg_q_{i}", use_container_width=True):
                    st.session_state.trigger_prompt = q
                    st.rerun()

    st.markdown("---")

# --- CHAT DISPLAY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message and message["sql"]:
            with st.expander("Show Query Details"):
                st.code(message["sql"], language="sql")
                if message.get("explanation"):
                    st.markdown(f"**Explanation:** {message['explanation']}")
                if message.get("confidence"):
                    st.markdown(f"**Confidence:** {message['confidence']}%")
        if "data" in message and message["data"] is not None:
            st.dataframe(message["data"], use_container_width=True)
            
        chart_type = message.get("chart_type")
        if chart_type:
            graph_df = message.get("graph_df", message.get("data"))
            x_axis = message.get("x_axis")
            y_axis = message.get("y_axis")
            
            color_col = message.get("color_col")
            color_arg = color_col if color_col and str(color_col).lower() != "none" else None

            if "graph_sql" in message and message["graph_sql"]:
                with st.expander("Show Graph SQL"):
                    st.code(message["graph_sql"], language="sql")
                    
            try:
                if x_axis and y_axis:
                    if chart_type == "bar":
                        st.bar_chart(graph_df, x=x_axis, y=y_axis, color=color_arg)
                    elif chart_type == "line":
                        st.line_chart(graph_df, x=x_axis, y=y_axis, color=color_arg)
                    elif chart_type == "scatter":
                        st.scatter_chart(graph_df, x=x_axis, y=y_axis, color=color_arg)
                    elif chart_type in ["pie", "histogram", "heatmap"]:
                        y_val = y_axis[0] if isinstance(y_axis, list) and y_axis else y_axis
                        if chart_type == "pie":
                            fig = px.pie(graph_df, names=x_axis, values=y_val, color=color_arg)
                        elif chart_type == "histogram":
                            fig = px.histogram(graph_df, x=x_axis, y=y_val, color=color_arg)
                        elif chart_type == "heatmap":
                            fig = px.density_heatmap(graph_df, x=x_axis, y=y_val, z=color_arg)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    if chart_type == "bar":
                        st.bar_chart(graph_df)
                    elif chart_type == "line":
                        st.line_chart(graph_df)
                    elif chart_type == "scatter":
                        st.scatter_chart(graph_df)
                    elif chart_type in ["pie", "histogram", "heatmap"]:
                        if chart_type == "pie":
                            fig = px.pie(graph_df)
                        elif chart_type == "histogram":
                            fig = px.histogram(graph_df)
                        elif chart_type == "heatmap":
                            fig = px.density_heatmap(graph_df)
                        st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"Error rendering chart: {e}")

# --- LLM FUNCTIONS ---

def generate_sql(user_prompt, schemas_dict, history, error_msg=None):
    schema_text = ""
    for t_name, t_schema in schemas_dict.items():
        schema_text += f"Table: {t_name}\n{t_schema}\n\n"

    system_instruction = f"""
    You are an expert DuckDB Data Analyst. 
    The user has uploaded the following tables with their schemas:
    
    {schema_text}
    
    Your goal is to generate a DuckDB SQL query to answer the user's question.
    Please carefully infer primary and foreign keys across these tables by analyzing column names (e.g., matching 'id' to 'user_id' or 'customer_id') and use them to construct correct JOIN operations when the question requires data from multiple tables.
    
    You MUST provide the following in your answer:
    1. The SQL query inside a ```sql ... ``` block.
    2. A brief explanation of the query logic inside <explanation>...</explanation> tags.
    3. Your confidence in the generated query on a scale of 0 to 100 inside <confidence>...</confidence> tags.
    
    If the question is conversational and doesn't require querying the database, simply reply with natural language and do not use the SQL block, explanation, or confidence tags.
    Make meaningful alias for the column names that are derived from some operations.
    """
    
    if error_msg:
        system_instruction += f"\n\nWARNING: Your previous query failed with error: {error_msg}\nPlease fix the SQL query so it works correctly."
        
    # Format history for Groq
    messages_payload = [{"role": "system", "content": system_instruction}]
    for m in history:
        # History includes the user's latest prompt already
        messages_payload.append({"role": m["role"], "content": m["content"]})
        
    response = client.chat.completions.create(
        model=model_name,
        messages=messages_payload,
        temperature=0.1
    )
    
    reply = response.choices[0].message.content
    
    # Extract SQL, Explanation and Confidence
    sql_match = re.search(r"```sql(.*?)```", reply, re.DOTALL | re.IGNORECASE)
    explanation_match = re.search(r"<explanation>(.*?)</explanation>", reply, re.DOTALL | re.IGNORECASE)
    confidence_match = re.search(r"<confidence>(.*?)</confidence>", reply, re.DOTALL | re.IGNORECASE)
    
    explanation = explanation_match.group(1).strip() if explanation_match else None
    confidence = confidence_match.group(1).strip() if confidence_match else None

    if sql_match:
        sql = sql_match.group(1).strip()
        clean_fallback = re.sub(r"```sql.*?```", "", reply, flags=re.DOTALL | re.IGNORECASE)
        clean_fallback = re.sub(r"<explanation>.*?</explanation>", "", clean_fallback, flags=re.DOTALL | re.IGNORECASE)
        clean_fallback = re.sub(r"<confidence>.*?</confidence>", "", clean_fallback, flags=re.DOTALL | re.IGNORECASE)
        return sql, clean_fallback.strip(), explanation, confidence
    return None, reply, None, None

def generate_summary(user_prompt, data_str, history, schemas_dict, error_msg=None):
    schema_text = ""
    for t_name, t_schema in schemas_dict.items():
        schema_text += f"Table: {t_name}\n{t_schema}\n\n"

    system_instruction = f"""
    You are an AI Data Assistant. The user asked a question, and a SQL query was executed against their data.
    You will be provided with the user's question, the query results (data), and the database schemas.
    Please provide a concise, natural language summary of the results answering the user's question.
    
    Additionally, you must strictly evaluate whether visualizing the answer as a chart makes logical sense. 
    If a graph is sensible, you MUST write a SEPARATE DuckDB SQL query specifically designed for the visualization. This graph query should handle aggregations, formatting, sorting, and limiting (e.g., top 10) appropriately.
    You must also choose the best chart type (bar, line, scatter, pie, histogram, or heatmap), identify the exact column names for the x-axis and y-axis from your graph query's SELECT clause, and if you want to group/color the data by a specific category, provide that column name as well. For pie charts, x_axis acts as the labels and y_axis as the values. For heatmaps, x_axis is x, y_axis is y, and color_col represents the z (values/intensity) column.
    
    

    Database Schemas for Graph Query:
    {schema_text}
    IMPORTANT FOR GRAPH SQL: [
        llm should see the sample rows and then try to understand how to fetch only the required information from the data like only fetch 23 as int from "$123" and how to get data as date type if date is in different formats like mm/yy or mm/dd/yyyy or any.
        All columns you refer to in your SELECT clause MUST either exist in the provided schemas or be explicitly computed (e.g., using `COUNT(*) AS number_of_users`). Do NOT hallucinate columns that don't exist.,
        see the schema text for all tables and see how the data is stored in each colmn and how the data is related to each other. also handle things like converting "$123" to 123 and "1,234" to 1234 and "12.34%" to 0.1234 and "2022-01-01" to a date.,
        If numeric columns contain symbols like '$' or ',', clean using REGEXP_REPLACE.,
        If numeric values are stored as strings, CAST them properly.,
        If date columns are strings, convert using CAST or STRPTIME before using EXTRACT.,
    ]

    A graph is sensible to show ONLY if:
    1. The data represents meaningful comparisons, trends, or relationships (e.g., categorical distributions, time series).
    2. The data is not just a single scalar value, a list of IDs/names without metrics, or unrelated text.

    If a graph makes sense, append the following XML tags at the end of your response:
    <chart_type>bar OR line OR scatter OR pie OR histogram OR heatmap</chart_type>
    <graph_sql>your duckdb sql query here</graph_sql>
    <x_axis>column_name_for_x</x_axis>
    <y_axis>column_name_for_y_or_comma_separated</y_axis>
    <color_col>column_name_for_color_or_legend_if_needed_else_NONE</color_col>
    
    If a graph would be senseless or uninformative, DO NOT output any of these tags.
    """

    if error_msg:
        system_instruction += f"\n\nWARNING: Your previous graph query failed with error: {error_msg}\nPlease fix the graph SQL query so it works correctly."

    messages_payload = [{"role": "system", "content": system_instruction}]
    # Optional: pass history here if context is strictly needed for the summary, 
    # but since Groq context limits are large enough, we can afford it.
    # To save tokens, we only pass the recent user prompt and data.
    user_content = f"User Question: {user_prompt}\n\nQuery Results:\n{data_str}"
    messages_payload.append({"role": "user", "content": user_content})
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages_payload,
        temperature=0.3
    )
    
    reply = response.choices[0].message.content
    
    # Extract tags if any
    chart_type_match = re.search(r"<chart_type>(.*?)</chart_type>", reply, re.IGNORECASE | re.DOTALL)
    graph_sql_match = re.search(r"<graph_sql>(.*?)</graph_sql>", reply, re.IGNORECASE | re.DOTALL)
    x_axis_match = re.search(r"<x_axis>(.*?)</x_axis>", reply, re.IGNORECASE | re.DOTALL)
    y_axis_match = re.search(r"<y_axis>(.*?)</y_axis>", reply, re.IGNORECASE | re.DOTALL)
    color_col_match = re.search(r"<color_col>(.*?)</color_col>", reply, re.IGNORECASE | re.DOTALL)
    
    chart_type = chart_type_match.group(1).strip().lower() if chart_type_match else None
    graph_sql = graph_sql_match.group(1).strip() if graph_sql_match else None
    x_axis = x_axis_match.group(1).strip() if x_axis_match else None
    y_axis = [y.strip() for y in y_axis_match.group(1).split(',')] if y_axis_match else None
    color_col = color_col_match.group(1).strip() if color_col_match else None

    # Remove all tags from text to just keep the summary
    text = re.sub(r"<chart_type>.*?</chart_type>", "", reply, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<graph_sql>.*?</graph_sql>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<x_axis>.*?</x_axis>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<y_axis>.*?</y_axis>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<color_col>.*?</color_col>", "", text, flags=re.IGNORECASE | re.DOTALL).strip()
    
    return text, chart_type, graph_sql, x_axis, y_axis, color_col

# --- USER INPUT ---
st.markdown("---")
st.write("🎙️ **Voice Input:**")

stt_text = speech_to_text(
    language='en',
    start_prompt="Click to Speak",
    stop_prompt="Click to Stop",
    just_once=True,
    key='STT'
)


prompt = st.chat_input("Ask a question about your data...")

if stt_text:
    prompt = stt_text

if st.session_state.trigger_prompt:
    prompt = st.session_state.trigger_prompt
    st.session_state.trigger_prompt = None

if prompt:
    # Render user prompt
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Process
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
            with st.spinner(f"Analyzing and generating query{' (Retry ' + str(attempt) + ')' if attempt > 0 else ''}..."):
                try:
                    sql_query, conversational_fallback, explanation, confidence = generate_sql(prompt, st.session_state.table_schemas, st.session_state.messages, error_msg)
                except Exception as e:
                    error_msg = f"API Error: {e}"
                    attempt += 1
                    continue
                
            if sql_query:
                with st.spinner("Executing query..."):
                    try:
                        df_result = st.session_state.duckdb_conn.execute(sql_query).df()
                        success = True
                    except Exception as e:
                        error_msg = f"SQL Execution Error: {e}"
                        attempt += 1
            else:
                success = True # Conversational fallback success

        if success and sql_query:
            with st.expander("Query Details", expanded=True):
                st.code(sql_query, language="sql")
                if explanation:
                    st.markdown(f"**Explanation:** {explanation}")
                if confidence:
                    st.markdown(f"**Confidence:** {confidence}%")
                
            data_str_for_llm = df_result.head(100).to_string()
            st.dataframe(df_result, use_container_width=True)
            
            with st.spinner("Generating summary and graph..."):
                summary_max_retries = 3
                summary_attempt = 0
                summary_success = False
                graph_error_msg = None
                
                final_summary_text = ""
                final_chart_type = None
                final_graph_sql = None
                final_x_axis = None
                final_y_axis = None
                final_color_col = None
                final_graph_df = None
                
                while summary_attempt <= summary_max_retries and not summary_success:
                    try:
                        summary_text, chart_type, graph_sql, x_axis, y_axis, color_col = generate_summary(prompt, data_str_for_llm, st.session_state.messages, st.session_state.table_schemas, graph_error_msg)
                        
                        final_summary_text = summary_text
                        final_chart_type = chart_type
                        final_graph_sql = graph_sql
                        final_x_axis = x_axis
                        final_y_axis = y_axis
                        final_color_col = color_col
                        
                        if chart_type and graph_sql and x_axis and y_axis:
                            try:
                                # Clean up formatting that LLMs sometimes hallucinate around the SQL
                                clean_sql = re.sub(r'```sql\n', '', graph_sql, flags=re.IGNORECASE)
                                clean_sql = re.sub(r'\n```', '', clean_sql, flags=re.IGNORECASE)
                                clean_sql = clean_sql.strip()

                                final_graph_df = st.session_state.duckdb_conn.execute(clean_sql).df()
                                summary_success = True
                            except Exception as de:
                                graph_error_msg = f"Graph SQL Execution Error: {de}"
                                summary_attempt += 1
                                if summary_attempt > summary_max_retries:
                                    st.warning(f"Could not execute graph query after {summary_max_retries} retries: {de}")
                                    final_chart_type = None # prevent saving broken chart info
                                    summary_success = True
                                continue
                        else:
                            summary_success = True
                            
                    except Exception as e:
                        st.error(f"Error generating summary API call: {e}")
                        # Don't infinitely retry API errors unless we explicitly want to, we'll just break
                        summary_success = True
                        break

                if final_summary_text:
                    st.markdown(final_summary_text)
                    if final_chart_type and final_graph_df is not None:
                        try:
                            # Evaluate color argument logic
                            color_arg = final_color_col if final_color_col and str(final_color_col).lower() != "none" else None
                            
                            # Render the chart
                            if final_chart_type == "bar":
                                st.bar_chart(final_graph_df, x=final_x_axis, y=final_y_axis, color=color_arg)
                            elif final_chart_type == "line":
                                st.line_chart(final_graph_df, x=final_x_axis, y=final_y_axis, color=color_arg)
                            elif final_chart_type == "scatter":
                                st.scatter_chart(final_graph_df, x=final_x_axis, y=final_y_axis, color=color_arg)
                            elif final_chart_type in ["pie", "histogram", "heatmap"]:
                                y_val = final_y_axis[0] if isinstance(final_y_axis, list) and final_y_axis else final_y_axis
                                if final_chart_type == "pie":
                                    fig = px.pie(final_graph_df, names=final_x_axis, values=y_val, color=color_arg)
                                elif final_chart_type == "histogram":
                                    fig = px.histogram(final_graph_df, x=final_x_axis, y=y_val, color=color_arg)
                                elif final_chart_type == "heatmap":
                                    fig = px.density_heatmap(final_graph_df, x=final_x_axis, y=y_val, z=color_arg)
                                st.plotly_chart(fig, use_container_width=True)
                        except Exception as e:
                            st.warning(f"Could not render graph UI: {e}")
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
        elif not success:
            final_error = f"Failed to generate correct SQL after {max_retries} retries. Last error:\n{error_msg}"
            st.error(final_error)
            st.session_state.messages.append({"role": "assistant", "content": final_error})
