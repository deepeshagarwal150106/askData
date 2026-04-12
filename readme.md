# Talk With Data

 Natural language analytics — upload a file, clean it with AI, explore insights, and chat with your data.
____________________________________________________________________________________________________

## Overview

Ask With Data AI is a Streamlit web app that lets anyone explore tabular data using plain English — no SQL or coding required. Users upload a CSV or Excel file, receive AI-generated data cleaning suggestions, and then ask questions about their data through a chat interface that supports both typing and voice. It solves the barrier between non-technical users and their data by automating query writing, chart generation, and data cleaning through an LLM. The intended users are data analysts, product managers, researchers, and students who need fast insights from spreadsheets without writing code.

____________________________________________________________________________________________________

## Features

- **CSV and Excel upload** — Upload `.csv`, `.xlsx`, or `.xls` files via the sidebar; multiple files load as separate queryable tables

- **AI anomaly detection** — On upload, the LLM scans each file's schema and sample rows and reports problems such as null values, incorrect data types, currency-formatted strings, and inconsistent column names

- **Natural language data cleaning** — Describe how to fix the data in plain English; the LLM generates and executes a Python cleaning function, with up to 3 automatic retries on error

- **In-memory SQL engine** — Cleaned data is loaded into DuckDB, enabling fast SQL queries directly on DataFrames

- **Auto-generated insights** — After loading, the LLM produces an executive summary and up to 6 insight cards, each with a pre-written SQL query executed and rendered as a chart

- **Six chart types** — Bar, line, scatter, pie, histogram, and heatmap rendered via Plotly and Streamlit native charts

- **Natural language chat** — Ask any question about your data; the LLM writes the SQL, runs it, and returns a plain-English summary with an optional chart

- **Voice input** — Ask questions by speaking; the mic recorder transcribes speech to text

- **Confidence scoring** — Each generated SQL query shows a 0–100 confidence score and a brief explanation

- **Suggested questions** — The Insights page shows clickable questions that jump directly into the chat

____________________________________________________________________________________________________

## Install and Run

### Prerequisites

- Python 3.13
- A Groq API key — get one free at [console.groq.com](https://console.groq.com/)

### public repo
https://github.com/deepeshagarwal150106/askData


### public url
https://askdata-6flrrbbzjcvrv3glr3lt3q.streamlit.app/

### Step 1 — Clone the repository

```bash
git clone https://github.com/deepeshagarwal150106/askData
cd askData
```

### Step 2 — Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Set up environment variables

```bash
cp .env.example .env
```

Open `.env` in any text editor and paste your Groq API key:

```
GROQ_API_KEY=your_groq_api_key_here
```

### Step 5 — Run the app

```bash
streamlit run app.py
```

The app opens automatically at `http://localhost:8501`.

____________________________________________________________________________________________________

## Usage Examples

### Example 1 — Uploading and cleaning a sales file

1. Open the sidebar and upload `sales_2024.csv`
2. The AI analysis panel appears and reports:
   ```
   Found 3 issues:
   - Column "Revenue" contains strings like "$1,200" — should be numeric
   - Column "Date" is stored as object, not datetime
   - 14 null values in column "Region"
   ```
3. In the instructions box, type:
   ```
   Strip $ and commas from Revenue and cast to float.
   Convert Date to datetime. Fill nulls in Region with "Unknown".
   ```
4. Click **Apply & Load** — the cleaned table registers in DuckDB and the app moves to Insights.

---

### Example 2 — Reading auto-generated insights

After loading, the Insights page shows cards like:

| Insight | Chart type |
|---|---|
| Top 5 products by total revenue | Bar chart |
| Monthly revenue trend | Line chart |
| Revenue distribution by region | Pie chart |

Each card shows the underlying SQL in a collapsible expander:

```sql
SELECT product_name, SUM(revenue) AS total_revenue
FROM sales_2024
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 5
```

---

### Example 3 — Asking questions in chat

**User input (typed or spoken):**
```
Which region had the lowest average order value in Q3?
```

**App response:**
```
The South region had the lowest average order value in Q3 at $142.30,
compared to the overall average of $198.60.
```

A bar chart comparing all regions is rendered below the answer, along with the generated SQL and a confidence score of 87%.

---

### Example 4 — Multi-file cross-table query

Upload both `orders.csv` and `customers.xlsx`. Once both are loaded, ask:

```
How many orders did each customer segment place last month?
```

The LLM infers the join key and generates:

```sql
SELECT c.segment, COUNT(o.order_id) AS order_count
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE DATE_TRUNC('month', o.order_date) =
      DATE_TRUNC('month', CURRENT_DATE - INTERVAL 1 MONTH)
GROUP BY c.segment
ORDER BY order_count DESC
```

____________________________________________________________________________________________________

## Tech Stack

| Category           | Technology 
|--------------------|------------
| Language           | Python 3.13 
| UI framework       | Streamlit 
| LLM inference      | Groq API 
| SQL engine         | DuckDB (in-memory)
| Data manipulation  | Pandas, NumPy 
| Charting           | Plotly Express, Streamlit native charts 
| Voice input        | streamlit-mic-recorder (browser STT) 
| Excel reading      | openpyxl (via Pandas) 
| Environment config | python-dotenv 

____________________________________________________________________________________________________

## Architecture Notes

The app is a single-page Streamlit application with three internal views managed via `st.session_state`:

```
File Upload (CSV / Excel)
        │
        ▼
① Clean Data page
   └─ Groq LLM: detect anomalies, suggest fixes
   └─ Groq LLM: generate Python cleaning function
   └─ exec() runs the function on the DataFrame
   └─ cleaner.py: post-execution sanitisation
        │
        ▼
DuckDB (in-memory) ── tables registered from cleaned DataFrames
        │
        ├──► ② Insights page
        │        └─ Groq LLM: JSON insight plan with SQL per insight
        │        └─ DuckDB executes each query
        │        └─ Charts rendered
        │
        └──► ③ Ask AI page
                 └─ Input: typed text OR voice (speech-to-text)
                 └─ Groq LLM: natural language → DuckDB SQL (retry ×3)
                 └─ DuckDB executes query → DataFrame result
                 └─ Groq LLM: NL summary + optional chart SQL
                 └─ Chart rendered if applicable
```


Session state persists the DuckDB connection, table schemas, and full chat history across Streamlit reruns within the same browser session.

____________________________________________________________________________________________________

## Limitations

- **No persistent storage** — all data and chat history are lost when the browser tab is closed
- **CSV and Excel only** — Parquet, JSON, and direct database connections are not supported
- **LLM-driven chart axes** — axis column selection is automatic and may occasionally be suboptimal
- **`exec()` for cleaning code** — safe for local and demo use, but not for multi-user production without sandboxing

____________________________________________________________________________________________________

## Future Improvements

- Persistent sessions backed by SQLite or a cloud store
- Support for Parquet files and direct database connections (PostgreSQL, SQLite)
- User-controlled chart axis overrides
- Export cleaned data as CSV or Excel
- Multi-turn chart editing ("make it a line chart", "colour by region")
- Docker image for one-command deployment
- Multi-sheet Excel support
- authorisation

____________________________________________________________________________________________________

## Project Structure

```
Ask With Data-ai/
├── app.py              # Application entrypoint
├── components/         # Reusable UI elements (sidebar, navigation)
├── config/             # App settings & LLM configuration
├── services/           # DB and LLM integration logic
├── styles/             # Global CSS definitions
├── utils/              # Helper utilities (session state, charts)
├── views/              # Main page views (clean_data, insights, chat)
├── cleaner.py          # Post-exec DataFrame sanitiser
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── LICENSE             # Apache 2.0
└── README.md           # This file
```

____________________________________________________________________________________________________

## License

Apache License
Version 2.0, January 2004
http://www.apache.org/licenses/

TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION

1. Definitions.

"License" shall mean the terms and conditions for use, reproduction,
and distribution as defined by Sections 1 through 9 of this document.

"Licensor" shall mean the copyright owner.

"Legal Entity" shall mean the union of the acting entity.

"You" shall mean an individual or Legal Entity exercising permissions.

2. Grant of Copyright License.

Each contributor grants you a worldwide, royalty-free, non-exclusive license to use, reproduce, and distribute the Work.

3. Grant of Patent License.

Each contributor grants a patent license for their contributions.

4. Redistribution.

You may distribute copies with:
- A copy of this license
- Notice of changes made
- Proper attribution

5. Submission of Contributions.

Unless stated otherwise, contributions are under this license.

6. Trademarks.

This license does not grant trademark rights.

7. Disclaimer of Warranty.

The software is provided "AS IS", without warranties.

8. Limitation of Liability.

Contributors are not liable for damages.

END OF TERMS AND CONDITIONS