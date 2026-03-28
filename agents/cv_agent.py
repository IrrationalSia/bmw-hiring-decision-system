"""
CV Agent
--------
Consumes a candidate profile + JD Agent output.
Produces per-requirement scores (0–10) with rationale, a weighted fit score
(0–100), urgency-bias flags, and an overall candidate summary.

Urgency bias: a score is flagged when the candidate's advantage for that
criterion is primarily driven by availability / convenience rather than
genuine competence (e.g. internal candidate scores high on "plant knowledge"
partly because hiring urgently favours known quantities).
"""

import json

from .utils import MODEL, get_client, parse_json

_SYSTEM = (
    "You are an expert manufacturing-sector talent assessor at BMW Group. "
    "You score candidates rigorously against job requirements and are trained to "
    "identify when urgency-driven bias may be inflating a score — for instance "
    "when an internal or immediately-available candidate appears stronger than "
    "their actual competency warrants. "
    "You always return valid JSON and nothing else."
)

_PROMPT_TEMPLATE = """\
You are scoring a candidate for the following role.

Role Summary
------------
{role_summary}

JD Requirements (must-have)
---------------------------
{must_have_json}

JD Requirements (nice-to-have)
-------------------------------
{nice_to_have_json}

Urgency context
---------------
Urgency level: {urgency_level}
Urgency signals detected: {urgency_signals}

Candidate Profile
-----------------
ID  : {candidate_id}
Name: {candidate_name}
{profile}

Task
----
For EVERY requirement listed above (both must-have and nice-to-have), produce a score entry.
Then compute the weighted_fit_score:

  weighted_fit_score = sum(score_i * weight_i) / sum(10 * weight_i) * 100

Return a single JSON object matching this schema:

{{
  "candidate_id": "{candidate_id}",
  "candidate_name": "{candidate_name}",
  "scores": [
    {{
      "requirement": "<exact requirement label from JD>",
      "category": "<category>",
      "weight": <weight from JD>,
      "score": <integer 0–10>,
      "rationale": "<2–3 sentences citing evidence from the profile>",
      "urgency_bias_flag": <true if this score is inflated by availability/urgency pressure, false otherwise>,
      "urgency_bias_reason": "<explain if flagged, else null>"
    }}
  ],
  "weighted_fit_score": <float 0–100, 2 decimal places>,
  "urgency_bias_flags_summary": ["<list of requirement labels where bias was flagged>"],
  "availability_weeks": <integer or 0 for immediate>,
  "candidate_summary": "<3–4 sentence overall assessment>"
}}

Return ONLY the JSON object.
"""


def score_candidate(candidate: dict, jd_analysis: dict) -> dict:
    """
    Args:
        candidate: dict with keys id, name, profile (from synthetic_candidates.py)
        jd_analysis: output of jd_agent.analyze_jd()

    Returns:
        Scored candidate dict.
    """
    client = get_client()

    prompt = _PROMPT_TEMPLATE.format(
        role_summary=jd_analysis.get("role_summary", ""),
        must_have_json=json.dumps(jd_analysis.get("must_have", []), indent=2),
        nice_to_have_json=json.dumps(jd_analysis.get("nice_to_have", []), indent=2),
        urgency_level=jd_analysis.get("urgency_level", "unknown"),
        urgency_signals=", ".join(jd_analysis.get("urgency_signals", [])),
        candidate_id=candidate["id"],
        candidate_name=candidate["name"],
        profile=candidate["profile"].strip(),
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    result = parse_json(response.content[0].text, f"CV Agent [{candidate['name']}]")
    # Attach raw availability string for the decision agent
    result["_availability_raw"] = candidate.get("availability", "unknown")
    return result
