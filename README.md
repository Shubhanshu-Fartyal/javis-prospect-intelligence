# Prospect Research & ICP Scoring Automation Prototype

A small, end-to-end prototype that demonstrates a simplified version of a
sales-research automation workflow: turning a raw list of companies into a
prioritized, AI-enriched prospect list — automatically.

## Project Overview

Given a list of companies, this pipeline cleans the data, checks each
company against an Ideal Customer Profile (ICP), scores and ranks them,
and generates short AI-written talking points for the top prospects. The
output is a single sorted CSV a sales team could act on directly.

## Business Problem

Sales and demand-gen teams are often handed large, messy lists of
companies and have to manually decide who's worth pursuing. That manual
triage is slow, inconsistent between reviewers, and doesn't scale. This
prototype automates the triage step: clean the data once, apply the same
ICP rules to every record, and let the team start their day with a
ranked, explained list instead of a raw spreadsheet.

## Workflow

```
Input CSV (companies.csv)
        |
Data Cleaning (strip whitespace, standardize casing, fix types)
        |
Validation (remove duplicates, flag missing required fields)
        |
ICP Qualification (industry / country / size / decision-maker checks)
        |
ICP Scoring (weighted, 0-100, fully transparent)
        |
Priority Classification (High / Medium / Low)
        |
AI Prospect Intelligence (High-priority only, mock mode if no API key)
        |
Final CSV (prospect_intelligence.csv, sorted by score)
```

## Technologies

Python, Pandas, Requests, JSON/CSV, OpenAI API (optional — mock mode
available).

## ICP Rules

Defined in one place: `src/icp_scoring.py`, `ICP_CONFIG` dict.

**Target profile:**
- Industry: SaaS / Software / Technology
- Country: India
- Employee count: 50–500
- Decision-maker title contains: Founder, Co-Founder, CEO, VP Sales,
  Head of Sales, or Sales Director

**Scoring (max 100 points, additive):**
| Criterion | Points |
|---|---|
| Industry match | +30 |
| Country match | +20 |
| Employee count in range | +20 |
| Decision-maker title match | +30 |

**Priority:**
- 80–100 → High
- 50–79 → Medium
- Below 50 → Low

## How to Run

```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

python src/main.py
```

To enable real AI calls instead of demo mode, copy `.env.example` to
`.env` and add your `OPENAI_API_KEY`. Without a key, the pipeline still
runs completely — the AI fields are filled with clearly labeled
`[DEMO MODE]` template text instead.

## Example Output

```
--- Data Quality Summary ---
Total records:                     28
Duplicates removed:                1
Records missing required fields:   2
Valid records remaining:           25
-----------------------------

High: 17  Medium: 5  Low: 3
```

Sample row from `output/prospect_intelligence.csv`:

| company_name | total_icp_score | priority | qualification_reason |
|---|---|---|---|
| CloudNest Technologies | 100 | High | Matches target industry, country, employee range and decision-maker criteria. |

## Screenshots

**Pipeline run:**
<img width="723" height="646" alt="Screenshot 2026-08-25 124542" src="https://github.com/user-attachments/assets/18f48518-19a6-4941-ba27-f7dfadb54089" />

**Final output CSV:**
<img width="1410" height="395" alt="Screenshot 2026-08-25 124631" src="https://github.com/user-attachments/assets/b886707f-3be9-4d7e-b911-4ccc75b50da1" />

## Limitations

- Dataset is synthetic — fictional companies, not scraped or real.
- Does not scrape live websites or connect to any CRM.
- ICP scoring uses manually defined, additive rules (no gating logic —
  see below).
- AI-generated intelligence is based only on the structured data
  supplied to it; it is explicitly instructed not to invent facts.
- This is a prototype, not a production system — no auth, no
  database, no retry/rate-limit handling beyond basic error catching.
- **Known scoring nuance:** because scoring is additive rather than
  gated, a company that misses one non-negotiable criterion (e.g. an
  otherwise perfect match based outside India) can still reach the
  High-priority threshold. A production version would add hard
  gates for non-negotiable criteria (e.g. country) rather than
  relying on points alone.

## What I'd Improve in Production

- Hard-gate non-negotiable ICP criteria instead of pure additive scoring.
- Pull firmographic data from a real source (Clearbit/LinkedIn/CRM API)
  instead of a static CSV.
- Add logging, retries, and rate-limiting around the LLM calls.
- Store results in a database instead of a CSV for querying/history.
- Add unit tests for the scoring functions (they're pure functions,
  so this would be straightforward).
