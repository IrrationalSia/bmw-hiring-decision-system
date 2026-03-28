"""
Scenario Agent
--------------
Consumes CV Agent output + JD analysis.
Re-weights each candidate's per-criterion scores under three BMW-specific scenarios
and returns an adjusted score for each, revealing which candidate wins under
which strategic context.

Scenarios
---------
1. transformation_push
   BMW is accelerating EV/digital transformation. Innovation, change leadership,
   digital fluency, and EV/Industry-4.0 experience weighted significantly higher.

2. automotive_continuity
   BMW faces near-term production pressure — volumes, quality, and OEE must not
   slip. Operational reliability, domain depth (ICE/manufacturing), crisis
   management, and lean/Six Sigma credentials weighted higher.

3. competitive_pressure
   Amazon/Tesla/BYD competition demands speed-to-market and digital-first
   operations. Digital transformation, agile leadership, EV familiarity, and
   proven ability to operate at pace weighted higher. Mirrors "Amazon-experience"
   framing from the use case.
"""

import json

from .utils import MODEL, get_client, parse_json

_SYSTEM = (
    "You are a BMW Group strategic workforce analyst. "
    "You re-weight candidate scores to reflect which strategic context the business "
    "is actually operating in, stripping out urgency-of-hire as a factor. "
    "You always return valid JSON and nothing else."
)

_SCENARIOS = {
    "transformation_push": (
        "BMW is in an aggressive EV and digital transformation phase. "
        "Heavily upweight: EV/battery experience, Industry 4.0 / digital twin, "
        "change leadership, innovation track record, agile methodology. "
        "Lightly downweight: pure ICE domain depth, traditional lean/Six Sigma (still relevant but secondary)."
    ),
    "automotive_continuity": (
        "BMW must protect near-term production volumes and quality targets. "
        "Heavily upweight: OEE track record, lean/Six Sigma, large-team leadership, "
        "crisis / production continuity management, ICE domain experience. "
        "Lightly downweight: digital/EV experience (nice but not urgent now)."
    ),
    "competitive_pressure": (
        "Competitive threat from Amazon, Tesla, and BYD demands digital speed and "
        "customer-centric pace. Heavily upweight: digital transformation delivery, "
        "EV familiarity, agile / fast-decision leadership, cross-industry perspective. "
        "Downweight: institutional seniority, tenure-based credibility."
    ),
}

_PROMPT_TEMPLATE = """\
You have the following candidate scores from the CV Agent:

Candidate: {candidate_name} (ID: {candidate_id})
Weighted Fit Score (baseline): {baseline_score}

Per-criterion scores:
{scores_json}

Role urgency level: {urgency_level}

Your task: re-evaluate this candidate under each of the three BMW strategic scenarios below.
For each scenario, produce an adjusted_score (0–100) by re-weighting the per-criterion scores
according to the scenario's strategic priorities. Show your reasoning.

Scenario definitions:
{scenarios_json}

Return a single JSON object:

{{
  "candidate_id": "{candidate_id}",
  "candidate_name": "{candidate_name}",
  "baseline_fit_score": {baseline_score},
  "scenarios": {{
    "transformation_push": {{
      "adjusted_score": <float 0–100>,
      "key_drivers": ["<top 2–3 criteria that most influenced this score>"],
      "strategic_note": "<1–2 sentences>"
    }},
    "automotive_continuity": {{
      "adjusted_score": <float 0–100>,
      "key_drivers": ["<top 2–3 criteria>"],
      "strategic_note": "<1–2 sentences>"
    }},
    "competitive_pressure": {{
      "adjusted_score": <float 0–100>,
      "key_drivers": ["<top 2–3 criteria>"],
      "strategic_note": "<1–2 sentences>"
    }}
  }},
  "best_fit_scenario": "<transformation_push|automotive_continuity|competitive_pressure>",
  "worst_fit_scenario": "<transformation_push|automotive_continuity|competitive_pressure>",
  "scenario_spread": <float — difference between highest and lowest adjusted score>,
  "scenario_analyst_note": "<2–3 sentences on what the spread tells us about this candidate>"
}}

Return ONLY the JSON object.
"""


def apply_scenarios(cv_result: dict, jd_analysis: dict) -> dict:
    """
    Args:
        cv_result:    output of cv_agent.score_candidate()
        jd_analysis:  output of jd_agent.analyze_jd()

    Returns:
        Scenario-adjusted scores dict.
    """
    client = get_client()

    prompt = _PROMPT_TEMPLATE.format(
        candidate_id=cv_result["candidate_id"],
        candidate_name=cv_result["candidate_name"],
        baseline_score=cv_result["weighted_fit_score"],
        scores_json=json.dumps(cv_result.get("scores", []), indent=2),
        urgency_level=jd_analysis.get("urgency_level", "unknown"),
        scenarios_json=json.dumps(_SCENARIOS, indent=2),
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2500,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    return parse_json(response.content[0].text, f"Scenario Agent [{cv_result['candidate_name']}]")
