"""LLM interaction functions for DataPulse AI.

All functions accept an explicit `client` (Groq) and `model_name` (str) so they
are fully self-contained and testable in isolation.
"""

import re
import json


# ── Chat / Query page ─────────────────────────────────────────────────────────

def generate_sql(client, model_name: str, user_prompt: str, schemas_dict: dict,
                 history: list, error_msg: str = None):
    """Generate a DuckDB SQL query (and metadata) from a natural language prompt.

    Returns:
        tuple: (sql, conversational_fallback, explanation, confidence)
    """
    schema_text = "".join(f"Table: {t}\n{s}\n\n" for t, s in schemas_dict.items())
    system_instruction = f"""
You are an expert DuckDB Data Analyst.
The user has uploaded the following tables with their schemas:

{schema_text}

Your goal is to generate a DuckDB SQL query to answer the user's question.
Please carefully infer primary and foreign keys across these tables by analyzing column names
and use them to construct correct JOIN operations when needed.

You MUST provide:
1. The SQL query inside a ```sql ... ``` block.
2. A brief explanation inside <explanation>...</explanation> tags.
3. Your confidence (0–100) inside <confidence>...</confidence> tags.

If conversational (no SQL needed), reply in natural language only — no SQL/explanation/confidence tags.
Make meaningful aliases for derived columns.
"""
    if error_msg:
        system_instruction += f"\n\nWARNING: Previous query failed: {error_msg}\nPlease fix the SQL."

    messages_payload = [{"role": "system", "content": system_instruction}]
    for m in history:
        messages_payload.append({"role": m["role"], "content": m["content"]})

    response = client.chat.completions.create(model=model_name, messages=messages_payload, temperature=0.1)
    reply = response.choices[0].message.content

    sql_match         = re.search(r"```sql(.*?)```",             reply, re.DOTALL | re.IGNORECASE)
    explanation_match = re.search(r"<explanation>(.*?)</explanation>", reply, re.DOTALL | re.IGNORECASE)
    confidence_match  = re.search(r"<confidence>(.*?)</confidence>",   reply, re.DOTALL | re.IGNORECASE)

    explanation = explanation_match.group(1).strip() if explanation_match else None
    confidence  = confidence_match.group(1).strip()  if confidence_match  else None

    if sql_match:
        sql = sql_match.group(1).strip()
        clean_fallback = re.sub(r"```sql.*?```",             "", reply, flags=re.DOTALL | re.IGNORECASE)
        clean_fallback = re.sub(r"<explanation>.*?</explanation>", "", clean_fallback, flags=re.DOTALL | re.IGNORECASE)
        clean_fallback = re.sub(r"<confidence>.*?</confidence>",   "", clean_fallback, flags=re.DOTALL | re.IGNORECASE)
        return sql, clean_fallback.strip(), explanation, confidence
    return None, reply, None, None


def generate_summary(client, model_name: str, user_prompt: str, data_str: str,
                     history: list, schemas_dict: dict, error_msg: str = None):
    """Generate a natural language summary of query results, optionally with a chart.

    Returns:
        tuple: (text, chart_type, graph_sql, x_axis, y_axis, color_col)
    """
    schema_text = "".join(f"Table: {t}\n{s}\n\n" for t, s in schemas_dict.items())
    system_instruction = f"""
You are an AI Data Assistant. Provide a concise natural language summary of query results.
important: [only give answers to relavant questions related to data provided, dataset issues and data cleaning that was done. if user asked anything else that is irrelevant to the data provided, politely refuse the user to answer and dont execute anyting.,
    if the question is not related to context provided simply refuse to answer.,
    boundaries: llm should not answer any question that is biassed or reveals any private information. also it should not give violent response.
    eg: user:"what is a cow" assistant:"I cannot answer this question as it is not related to the data provided.",
    eg: user:"what is the capital of France" assistant:"I cannot answer this question as it is not related to the data provided.",
    eg: user:"how to make cake" assistant:"I cannot answer this question as it is not related to the data provided.",
]

Additionally evaluate whether a chart makes sense. If it does, write a SEPARATE DuckDB SQL
query for visualization and choose the best chart type.

Database Schemas:
{schema_text}

IMPORTANT FOR GRAPH SQL:
- Only use columns that exist in schemas or are explicitly computed.
- Handle '$123'→123, '1,234'→1234, '12.34%'→0.1234, date strings appropriately.
- Use REGEXP_REPLACE for symbols, CAST for types, STRPTIME for date strings.

A graph makes sense ONLY for comparisons, trends, distributions — NOT single scalars.

If graph makes sense, append:
<chart_type>bar|line|scatter|pie|histogram|heatmap</chart_type>
<graph_sql>sql here</graph_sql>
<x_axis>col</x_axis>
<y_axis>col</y_axis>
<color_col>col or NONE</color_col>
"""
    if error_msg:
        system_instruction += f"\n\nWARNING: Previous graph query failed: {error_msg}"

    messages_payload = [
        {"role": "system", "content": system_instruction},
        {"role": "user",   "content": f"User Question: {user_prompt}\n\nQuery Results:\n{data_str}"}
    ]
    response = client.chat.completions.create(model=model_name, messages=messages_payload, temperature=0.3)
    reply = response.choices[0].message.content

    ct_m  = re.search(r"<chart_type>(.*?)</chart_type>", reply, re.IGNORECASE | re.DOTALL)
    gs_m  = re.search(r"<graph_sql>(.*?)</graph_sql>",   reply, re.IGNORECASE | re.DOTALL)
    xa_m  = re.search(r"<x_axis>(.*?)</x_axis>",         reply, re.IGNORECASE | re.DOTALL)
    ya_m  = re.search(r"<y_axis>(.*?)</y_axis>",         reply, re.IGNORECASE | re.DOTALL)
    cc_m  = re.search(r"<color_col>(.*?)</color_col>",   reply, re.IGNORECASE | re.DOTALL)

    chart_type = ct_m.group(1).strip().lower() if ct_m else None
    graph_sql  = gs_m.group(1).strip()          if gs_m else None
    x_axis     = xa_m.group(1).strip()          if xa_m else None
    y_axis     = [y.strip() for y in ya_m.group(1).split(",")] if ya_m else None
    color_col  = cc_m.group(1).strip()          if cc_m else None

    text = re.sub(r"<chart_type>.*?</chart_type>", "", reply, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<graph_sql>.*?</graph_sql>",   "", text,  flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<x_axis>.*?</x_axis>",         "", text,  flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<y_axis>.*?</y_axis>",         "", text,  flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<color_col>.*?</color_col>",   "", text,  flags=re.IGNORECASE | re.DOTALL).strip()

    return text, chart_type, graph_sql, x_axis, y_axis, color_col


# ── Insights page ─────────────────────────────────────────────────────────────

def generate_insight_plan(client, model_name: str, schemas_dict: dict,
                          error_msg: str = None) -> str:
    """Ask the LLM for a comprehensive analytical plan as structured JSON.

    Returns the raw response string (JSON or markdown-wrapped JSON).
    """
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
        system_instruction += f"\n\nPREVIOUS ERROR: {error_msg}"

    response = client.chat.completions.create(
        model=model_name,
        messages=[{"role": "system", "content": system_instruction}],
        temperature=0.3
    )
    return response.choices[0].message.content


def fix_insight_sql(client, model_name: str, failed_sql: str, error_msg: str,
                    schemas_dict: dict) -> str:
    """Ask the LLM to repair a broken SQL query and return the fixed SQL string."""
    schema_text = "".join(f"Table: {t}\n{s}\n\n" for t, s in schemas_dict.items())
    system_instruction = f"""
You are a DuckDB SQL expert.
The following SQL query failed with the error below:
ERROR: {error_msg}
FAILED SQL: {failed_sql}
Schemas: {schema_text}
Return ONLY the corrected SQL query inside a ```sql ... ``` block.
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
    clean_sql = re.sub(r"```.*?\n", "", reply, flags=re.IGNORECASE)
    return re.sub(r"\n```", "", clean_sql).strip()


def build_and_execute_insights(client, model_name: str, schemas_dict: dict,
                               duckdb_conn) -> dict:
    """Generate the full insights plan and execute each SQL query.

    Retries failing queries up to 3 times using fix_insight_sql.

    Returns:
        dict with keys: summary, insights (with data), suggested_questions
    """
    plan_json_str = generate_insight_plan(client, model_name, schemas_dict)
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
                    current_sql = fix_insight_sql(client, model_name, current_sql, str(e), schemas_dict)
                except Exception:
                    break
        if success:
            insight["sql_query"] = current_sql
            insight["data"] = df_res
            evaluated_insights.append(insight)

    plan["insights"] = evaluated_insights
    return plan
