def get_schema(conn, table_name: str) -> str:
    """Return a human-readable schema string for *table_name* including sample data.

    Uses DuckDB's DESCRIBE command to list column names and types, then fetches
    the first 5 rows as a sample.  Returns an error string on failure so that
    callers never receive an exception.
    """
    try:
        schema_df = conn.execute(f"DESCRIBE {table_name}").df()
        schema_str = "Columns and Data Types:\n"
        for _, row in schema_df.iterrows():
            schema_str += f"- {row['column_name']} ({row['column_type']})\n"
        sample_df = conn.execute(f"SELECT * FROM {table_name} LIMIT 5").df()
        schema_str += "\nSample Data (Top 5 rows):\n"
        schema_str += sample_df.to_string(index=False) + "\n"
        return schema_str
    except Exception as e:
        return str(e)
