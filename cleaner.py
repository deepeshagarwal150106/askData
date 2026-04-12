import pandas as pd
import numpy as np
import re

def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans a pandas DataFrame according to specified rules:
    - Replaces empty strings, 'null', 'None' with NaN
    - Strips whitespace from string columns
    - Detects and converts DATE columns, including '01/24', 'Jan-2024'
    - Detects and cleans NUMERIC/CURRENCY columns by stripping symbols and parsing
    - Infers best datatypes using pandas
    """
    df_clean = df.copy()

    # 🔹 NULL HANDLING: Replace empty strings ("" , "null", "None") with NaN
    null_strings = ['', 'null', 'None', 'NULL', 'NONE', 'nan', 'NaN']
    with pd.option_context("future.no_silent_downcasting", True):
        df_clean = df_clean.replace(null_strings, np.nan)
        df_clean = df_clean.replace(r'^\s*$', np.nan, regex=True)

    for col in df_clean.columns:
        if df_clean[col].dtype == 'object' or df_clean[col].dtype == 'string':
            # 🔹 STRING CLEANING: Strip leading/trailing spaces
            df_clean[col] = df_clean[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

            # Dropna for checking types
            col_dropna = df_clean[col].dropna()
            if col_dropna.empty:
                continue

            # 🔹 DATE CLEANING
            is_converted_to_date = False
            str_mask = col_dropna.apply(lambda x: isinstance(x, str))
            
            if str_mask.any():
                def looks_like_date(s):
                    if not isinstance(s, str): return False
                    s = s.lower()
                    # Check for separators or month names
                    has_sep = bool(re.search(r'[-/]', s))
                    has_month = bool(re.search(r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)', s))
                    return has_sep or has_month

                date_like_ratio = col_dropna[str_mask].apply(looks_like_date).mean()
                if date_like_ratio > 0.5:
                    # Try general parsing first
                    date_series = pd.to_datetime(df_clean[col], errors='coerce', dayfirst=True)
                    
                    # Try specific format like '01/24' (m/y)
                    date_series_my = pd.to_datetime(df_clean[col], format='%m/%y', errors='coerce')
                    
                    # Combine the results preferring whichever parsed successfully
                    combined_dates = date_series.fillna(date_series_my)
                            
                    # If we successfully parsed at least 50% of the non-null values
                    if combined_dates.notna().sum() >= len(col_dropna) * 0.5:
                        df_clean[col] = combined_dates
                        continue # Done with this column, go to next

            # 🔹 NUMERIC / CURRENCY CLEANING
            def clean_numeric(x):
                if isinstance(x, (int, float)): return x
                if isinstance(x, str):
                    # Remove $, €, ₹, commas, spaces
                    x_cleaned = re.sub(r'[$€₹£,\s]', '', x)
                    return x_cleaned
                return x

            cleaned_col = df_clean[col].apply(clean_numeric)
            numeric_series = pd.to_numeric(cleaned_col, errors='coerce')

            # We consider it numeric if a substantial amount (>=40%) are valid numbers.
            # Invalid ones become NaN automatically by pd.to_numeric(errors='coerce')
            if numeric_series.notna().sum() >= len(col_dropna) * 0.4:
                df_clean[col] = numeric_series

    # 🔹 AUTOMATIC TYPE INFERENCE
    df_clean = df_clean.convert_dtypes()

    return df_clean
