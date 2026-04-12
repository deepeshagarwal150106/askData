import streamlit as st
import duckdb


def init_session_state() -> None:
    """Initialise all required session state keys with default values.

    Safe to call on every rerun — only sets keys that don't already exist.
    """
    defaults = {
        "messages":           [],
        "duckdb_conn":        duckdb.connect(database=":memory:", read_only=False),
        "table_schemas":      {},
        "data_loaded_files":  set(),
        "pending_files":      {},
        "cleaning_questions": {},
        "insights_data":      None,
        "trigger_prompt":     None,
        "active_page":        "clean",
    }
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default
