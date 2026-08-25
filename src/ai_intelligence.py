"""
ai_intelligence.py
-------------------
For HIGH-priority prospects only: calls an LLM to generate short,
structured prospect intelligence based STRICTLY on the data we
already have. If no API key is set, falls back to a deterministic
mock/demo mode so the rest of the pipeline still runs end-to-end.

The prompt explicitly forbids the model from inventing company facts,
since our dataset is synthetic.
"""

import os
import json
import requests

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

SYSTEM_INSTRUCTION = (
    "You are a sales research assistant. Use ONLY the information "
    "supplied in the input. If information is unavailable, say that "
    "it is unavailable. Do not invent company facts. Respond with "
    "valid JSON only, no markdown formatting, matching this schema: "
    '{"business_context": str, "potential_pain_point": str, '
    '"conversation_angle": str, "next_action": str}'
)

# Fields kept out of the "why relevant" field on purpose — icp_score /
# qualification_reason already explain WHY it's high priority, so the
# AI's job is the human-judgment layer on top: context, pain point, angle.
EMPTY_RESULT = {
    "ai_business_context": "unavailable",
    "ai_potential_pain_point": "unavailable",
    "ai_conversation_angle": "unavailable",
    "ai_next_action": "unavailable",
}


def _build_user_prompt(row) -> str:
    return (
        f"Company: {row['company_name']}\n"
        f"Industry: {row['industry']}\n"
        f"Country: {row['country']}\n"
        f"Employee count: {row['employee_count']}\n"
        f"Decision maker: {row['decision_maker']}\n"
        f"Decision maker title: {row['decision_maker_title']}\n"
        f"ICP score: {row['total_icp_score']}\n"
        f"Qualification reason: {row['qualification_reason']}\n\n"
        "Based only on the above, provide: business_context, "
        "potential_pain_point, conversation_angle, next_action."
    )


def _mock_response(row) -> dict:
    """Deterministic, template-based 'demo mode' response — used when
    no API key is configured. Clearly labeled as demo output so it's
    never mistaken for a real AI call in an interview walkthrough."""
    return {
        "ai_business_context": (
            f"[DEMO MODE] {row['company_name']} is a {row['employee_count']:.0f}-person "
            f"{row['industry']} company in {row['country']}, sized to plausibly need "
            "a scalable sales/ops solution."
        ),
        "ai_potential_pain_point": (
            f"[DEMO MODE] At this employee count, {row['decision_maker_title']}-level "
            "roles often struggle with manual prospect research and inconsistent pipeline data."
        ),
        "ai_conversation_angle": (
            f"[DEMO MODE] Open with how peer {row['industry']} companies in "
            f"{row['country']} cut manual research time using automated ICP scoring."
        ),
        "ai_next_action": "[DEMO MODE] Send a short, personalized outreach email referencing their role and industry.",
    }


def _call_openai(row, api_key: str) -> dict:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": _build_user_prompt(row)},
        ],
        "temperature": 0.3,
    }

    try:
        resp = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=20)
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return {
            "ai_business_context": parsed.get("business_context", "unavailable"),
            "ai_potential_pain_point": parsed.get("potential_pain_point", "unavailable"),
            "ai_conversation_angle": parsed.get("conversation_angle", "unavailable"),
            "ai_next_action": parsed.get("next_action", "unavailable"),
        }
    except requests.exceptions.RequestException as e:
        print(f"  [warning] API call failed for {row['company_name']}: {e}")
        return dict(EMPTY_RESULT)
    except (KeyError, json.JSONDecodeError) as e:
        print(f"  [warning] Could not parse API response for {row['company_name']}: {e}")
        return dict(EMPTY_RESULT)


def generate_intelligence(row) -> dict:
    """Returns a dict of the four ai_* fields for one HIGH-priority row."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _mock_response(row)
    return _call_openai(row, api_key)
