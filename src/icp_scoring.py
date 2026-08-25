"""
icp_scoring.py
---------------
Defines the Ideal Customer Profile (ICP) rules in ONE place (the
config section below) and applies transparent, rule-based scoring
to each cleaned record.

Design choice: every score is deterministic and traceable back to a
single rule, so this can be explained line-by-line in an interview —
there is no ML/black-box scoring here on purpose.
"""

import pandas as pd

ICP_CONFIG = {
    "target_industries": ["saas", "software", "technology"],
    "target_country": "india",
    "employee_range": (50, 500),
    "decision_maker_keywords": [
        "founder", "co-founder", "ceo", "vp sales",
        "head of sales", "sales director",
    ],
    "weights": {
        "industry": 30,
        "country": 20,
        "company_size": 20,
        "decision_maker": 30,
    },
    "priority_thresholds": {
        "high": 80,
        "medium": 50,
    },
}


def _score_industry(industry: str) -> int:
    if pd.isna(industry):
        return 0
    return ICP_CONFIG["weights"]["industry"] if industry.lower() in ICP_CONFIG["target_industries"] else 0


def _score_country(country: str) -> int:
    if pd.isna(country):
        return 0
    return ICP_CONFIG["weights"]["country"] if country.lower() == ICP_CONFIG["target_country"] else 0


def _score_company_size(employee_count) -> int:
    if pd.isna(employee_count):
        return 0
    low, high = ICP_CONFIG["employee_range"]
    return ICP_CONFIG["weights"]["company_size"] if low <= employee_count <= high else 0


def _score_decision_maker(title: str) -> int:
    if pd.isna(title):
        return 0
    title_lower = title.lower()
    match = any(kw in title_lower for kw in ICP_CONFIG["decision_maker_keywords"])
    return ICP_CONFIG["weights"]["decision_maker"] if match else 0


def _priority_for_score(score: int) -> str:
    t = ICP_CONFIG["priority_thresholds"]
    if score >= t["high"]:
        return "High"
    if score >= t["medium"]:
        return "Medium"
    return "Low"


def _qualification_reason(row: pd.Series) -> str:
    """Build the reason string directly from which sub-scores hit,
    so it's generated from real logic, never hallucinated."""
    matched = []
    if row["industry_score"] > 0:
        matched.append("target industry")
    if row["country_score"] > 0:
        matched.append("target country")
    if row["company_size_score"] > 0:
        matched.append("employee range")
    if row["decision_maker_score"] > 0:
        matched.append("decision-maker criteria")

    if not matched:
        return "Does not match any core ICP criteria."
    if len(matched) == 4:
        return "Matches target industry, country, employee range and decision-maker criteria."
    return "Matches " + ", ".join(matched) + "."


def score_prospects(df: pd.DataFrame) -> pd.DataFrame:
    """Adds scoring columns to the cleaned DataFrame and returns it,
    sorted by total_icp_score descending."""
    df = df.copy()

    df["industry_score"] = df["industry"].apply(_score_industry)
    df["country_score"] = df["country"].apply(_score_country)
    df["company_size_score"] = df["employee_count"].apply(_score_company_size)
    df["decision_maker_score"] = df["decision_maker_title"].apply(_score_decision_maker)

    df["total_icp_score"] = (
        df["industry_score"] + df["country_score"]
        + df["company_size_score"] + df["decision_maker_score"]
    )

    df["priority"] = df["total_icp_score"].apply(_priority_for_score)

    # icp_match: broadly satisfies the CORE requirements (industry + country
    # at minimum — the two non-negotiable filters for this ICP)
    df["icp_match"] = (df["industry_score"] > 0) & (df["country_score"] > 0)

    df["qualification_reason"] = df.apply(_qualification_reason, axis=1)

    return df.sort_values("total_icp_score", ascending=False).reset_index(drop=True)
