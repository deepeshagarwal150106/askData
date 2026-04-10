import streamlit as st
import pandas as pd
import duckdb
from groq import Groq
import os
import re
import time
from dotenv import load_dotenv

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
        "llama-3.1-8b-instant",  
        "gemma2-9b-it", 
        "mixtral-8x7b-32768"
    ], index=0)
    
    st.markdown("---")
    st.header("📄 Upload Data")
    uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if "duckdb_conn" not in st.session_state:
    st.session_state.duckdb_conn = duckdb.connect(database=':memory:', read_only=False)

if "table_schema" not in st.session_state:
    st.session_state.table_schema = None

def get_schema(conn, table_name):
    # Retrieve schema string for LLM
    try:
        schema_df = conn.execute(f"DESCRIBE {table_name}").df()
        schema_str = "Columns and Data Types:\n"
        for _, row in schema_df.iterrows():
            schema_str += f"- {row['column_name']} ({row['column_type']})\n"
        return schema_str
    except Exception as e:
        return str(e)

# --- DATA LOADING ---
if uploaded_file:
    # Read the file only once into duckdb
    if "data_loaded" not in st.session_state or st.session_state.data_loaded != uploaded_file.name:
        try:
            df = pd.read_csv(uploaded_file)
            # Register in DuckDB
            # We enforce a standard table name so LLM knows what to query
            table_name = "data_table"
            st.session_state.duckdb_conn.register(table_name, df)
            
            # Extract schema
            st.session_state.table_schema = get_schema(st.session_state.duckdb_conn, table_name)
            st.session_state.data_loaded = uploaded_file.name
            st.session_state.messages.append({"role": "assistant", "content": f"✅ Successfully loaded `{uploaded_file.name}`. Use the chat to ask questions about your data!"})
        except Exception as e:
            st.error(f"Error loading CSV: {e}")
            st.stop()
            
    st.sidebar.success(f"Loaded {uploaded_file.name}")
    st.sidebar.markdown("**Schema:**")
    st.sidebar.text(st.session_state.table_schema)

else:
    st.info("👈 Please upload a CSV file from the sidebar to get started.")
    st.stop()

# --- CHAT DISPLAY ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sql" in message:
            with st.expander("Show Generated SQL"):
                st.code(message["sql"], language="sql")
        if "data" in message:
            st.dataframe(message["data"], use_container_width=True)
        if "chart_type" in message and message["chart_type"]:
            chart_type = message["chart_type"]
            data = message["data"]
            if chart_type == "bar":
                st.bar_chart(data)
            elif chart_type == "line":
                st.line_chart(data)
            elif chart_type == "scatter":
                st.scatter_chart(data)

# --- LLM FUNCTIONS ---
def generate_sql(user_prompt, schema, history):
    system_instruction = f"""
    You are an expert DuckDB Data Analyst. 
    The user has uploaded a table named 'data_table' with the following schema:
    {schema}
    
    Your goal is to generate a DuckDB SQL query to answer the user's question.
    Only return the SQL query inside a ```sql ... ``` block. DO NOT add any other explanation.
    If the question is conversational and doesn't require querying the database, reply with conversational text (no SQL block).
    """
    
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
    
    # Extract SQL
    sql_match = re.search(r"```sql(.*?)```", reply, re.DOTALL | re.IGNORECASE)
    if sql_match:
        return sql_match.group(1).strip(), reply
    return None, reply

def generate_summary(user_prompt, data_str, history):
    system_instruction = """
    You are an AI Data Assistant. The user asked a question, and a SQL query was executed against their data.
    You will be provided with the user's question and the resulting data (in string format).
    Please provide a concise, natural language summary of the results answering the user's question.
    
    Additionally, if the data is a 1D or 2D series that makes sense to visualize, output exactly one of the following strings on a new line at the end of your response to render a chart:
    [CHART:bar]
    [CHART:line]
    [CHART:scatter]
    If it doesn't make sense to visualize, DO NOT output a [CHART:...] tag.
    """
    
    messages_payload = [{"role": "system", "content": system_instruction}]
    # Optional: pass history here if context is strictly needed for the summary, 
    # but since Groq context limits are large enough, we can afford it.
    # To save tokens, we only pass the recent user prompt and data.
    user_content = f"User Question: {user_prompt}\\n\\nQuery Results:\\n{data_str}"
    messages_payload.append({"role": "user", "content": user_content})
    
    response = client.chat.completions.create(
        model=model_name,
        messages=messages_payload,
        temperature=0.3
    )
    
    reply = response.choices[0].message.content
    
    # Extract chart tag if any
    chart_match = re.search(r"\[CHART:(bar|line|scatter)\]", reply, re.IGNORECASE)
    chart_type = None
    if chart_match:
        chart_type = chart_match.group(1).lower()
        # Clean the text
        text = re.sub(r"\[CHART:(bar|line|scatter)\]", "", reply, flags=re.IGNORECASE).strip()
    else:
        text = reply.strip()
        
    return text, chart_type

# --- USER INPUT ---
if prompt := st.chat_input("Ask a question about your data..."):
    # Render user prompt
    with st.chat_message("user"):
        st.markdown(prompt)
        
    # Process
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.spinner("Analyzing and generating query..."):
        sql_query, conversational_fallback = generate_sql(prompt, st.session_state.table_schema, st.session_state.messages)
        
    if sql_query:
        with st.chat_message("assistant"):
            with st.expander("Generated SQL Query", expanded=True):
                st.code(sql_query, language="sql")
                
            with st.spinner("Executing query..."):
                try:
                    df_result = st.session_state.duckdb_conn.execute(sql_query).df()
                    # Limit output passed to LLM to avoid token limits
                    data_str_for_llm = df_result.head(100).to_string()
                    
                    st.dataframe(df_result, use_container_width=True)
                    
                    with st.spinner("Generating summary..."):
                        summary_text, chart_type = generate_summary(prompt, data_str_for_llm, st.session_state.messages)
                        
                        st.markdown(summary_text)
                        
                        if chart_type:
                            if chart_type == "bar":
                                st.bar_chart(df_result)
                            elif chart_type == "line":
                                st.line_chart(df_result)
                            elif chart_type == "scatter":
                                st.scatter_chart(df_result)
                                
                    # Save to state
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": summary_text,
                        "sql": sql_query,
                        "data": df_result,
                        "chart_type": chart_type
                    })
                    
                except Exception as e:
                    error_msg = f"Error executing query: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        # It was a conversational response
        with st.chat_message("assistant"):
            st.markdown(conversational_fallback)
            st.session_state.messages.append({"role": "assistant", "content": conversational_fallback})
