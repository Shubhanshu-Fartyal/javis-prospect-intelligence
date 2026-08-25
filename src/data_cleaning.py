import pandas as pd

REQUIRED_FIELDS = ["company_name", "industry", "country", "decision_maker_title"]
# If any of these are missing, the record is flagged (not silently dropped)

def load_data(csv_path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Could not find input file at '{csv_path}'. "
            "Check the path or run main.py from the project root."
        )
    if df.empty:
        raise ValueError("Input CSV was found but contains no rows.")
    return df


def _strip_and_normalize_text(df: pd.DataFrame) -> pd.DataFrame:
    text_cols = df.select_dtypes(include="object").columns
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()
        # Treat literal "nan"/"" strings (from missing cells) as true NaN
        df[col] = df[col].replace({"nan": pd.NA, "": pd.NA})

    for col in ["industry", "country", "city"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: x.title() if pd.notna(x) else x)

    if "company_name" in df.columns:
        df["company_name"] = df["company_name"].apply(
            lambda x: x if pd.isna(x) else x.strip()
        )

    return df


def _remove_duplicates(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """A duplicate = same company_name (case-insensitive) + same city.
    We keep the first occurrence."""
    before = len(df)
    dedup_key = (
        df["company_name"].str.lower().fillna("")
        + "|"
        + df["city"].str.lower().fillna("")
    )
    df = df.loc[~dedup_key.duplicated()]
    removed = before - len(df)
    return df, removed


def _validate_employee_count(df: pd.DataFrame) -> pd.DataFrame:
    """Convert employee_count to numeric. Invalid or missing values
    become NaN rather than crashing the pipeline."""
    df["employee_count"] = pd.to_numeric(df["employee_count"], errors="coerce")
    return df


def clean_and_validate(csv_path: str) -> tuple[pd.DataFrame, dict]:
    """Main entry point. Returns (clean_df, summary)."""
    df = load_data(csv_path)
    total_records = len(df)

    df = _strip_and_normalize_text(df)
    df, duplicates_removed = _remove_duplicates(df)
    df = _validate_employee_count(df)

    # Flag missing required fields (per-row), then split into valid/invalid
    missing_mask = df[REQUIRED_FIELDS].isna().any(axis=1)
    invalid_df = df.loc[missing_mask]
    valid_df = df.loc[~missing_mask].copy()

    summary = {
        "total_records": total_records,
        "duplicates_removed": duplicates_removed,
        "records_missing_required_fields": len(invalid_df),
        "valid_records_remaining": len(valid_df),
    }

    valid_df["data_quality_status"] = "valid"
    return valid_df.reset_index(drop=True), summary


def print_summary(summary: dict) -> None:
    print("\n--- Data Quality Summary ---")
    print(f"Total records:                     {summary['total_records']}")
    print(f"Duplicates removed:                {summary['duplicates_removed']}")
    print(f"Records missing required fields:   {summary['records_missing_required_fields']}")
    print(f"Valid records remaining:           {summary['valid_records_remaining']}")
    print("-----------------------------\n")
