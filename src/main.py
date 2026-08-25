"""
main.py
-------
Orchestrates the full pipeline:

companies.csv -> clean/validate -> ICP score -> prioritize
              -> AI intelligence (High priority only) -> prospect_intelligence.csv

Run from the project root:
    python src/main.py
"""

import os
import sys
import pandas as pd

# Allow running this file directly (python src/main.py) by adding
# the src/ folder to the path so sibling imports work either way.
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_cleaning import clean_and_validate, print_summary
from icp_scoring import score_prospects
from ai_intelligence import generate_intelligence

INPUT_PATH = os.path.join("data", "companies.csv")
OUTPUT_PATH = os.path.join("output", "prospect_intelligence.csv")

OUTPUT_COLUMNS = [
    "company_name", "industry", "country", "city", "employee_count",
    "decision_maker", "decision_maker_title", "data_quality_status",
    "icp_match", "industry_score", "country_score", "company_size_score",
    "decision_maker_score", "total_icp_score", "priority",
    "qualification_reason", "ai_business_context", "ai_potential_pain_point",
    "ai_conversation_angle", "ai_next_action",
]


def main():
    print("Step 1: Loading and cleaning data...")
    try:
        clean_df, summary = clean_and_validate(INPUT_PATH)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    print_summary(summary)

    if clean_df.empty:
        print("ERROR: No valid records remain after cleaning. Stopping.")
        sys.exit(1)

    print("Step 2: Scoring prospects against the ICP...")
    scored_df = score_prospects(clean_df)
    counts = scored_df["priority"].value_counts()
    print(f"  High: {counts.get('High', 0)}  Medium: {counts.get('Medium', 0)}  Low: {counts.get('Low', 0)}\n")

    print("Step 3: Generating AI prospect intelligence for High-priority prospects...")
    demo_mode = not os.getenv("OPENAI_API_KEY")
    if demo_mode:
        print("  No OPENAI_API_KEY found -> running in DEMO/MOCK mode.\n")

    ai_columns = {
        "ai_business_context": [], "ai_potential_pain_point": [],
        "ai_conversation_angle": [], "ai_next_action": [],
    }
    for _, row in scored_df.iterrows():
        if row["priority"] == "High":
            result = generate_intelligence(row)
            print(f"  Generated intelligence for: {row['company_name']}")
        else:
            result = {k: "" for k in ai_columns}
        for k in ai_columns:
            ai_columns[k].append(result[k])

    for k, v in ai_columns.items():
        scored_df[k] = v

    print("\nStep 4: Exporting final results...")
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    final_df = scored_df[OUTPUT_COLUMNS]
    final_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Done. {len(final_df)} records written to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
