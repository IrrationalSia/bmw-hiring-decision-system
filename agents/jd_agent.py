"""
JD Agent
--------
Consumes a raw job description.
Produces:
  - must_have:        list of essential requirements (weight 0.8–1.0)
  - nice_to_have:     list of desirable requirements (weight 0.3–0.6)
  - urgency_signals:  verbatim phrases flagging time pressure
  - urgency_level:    "low" | "medium" | "high"
  - urgency_reasoning: brief explanation
  - role_summary:     one-paragraph context for downstream agents
"""

from .utils import MODEL, get_client, parse_json

_SYSTEM = (
    "You are a senior HR analyst specialising in automotive and manufacturing sector hiring. "
    "You extract structured requirements from job descriptions with precision and explicitly flag "
    "urgency-driven hiring signals that may compromise long-term candidate quality standards. "
    "You always return valid JSON and nothing else."
)

_PROMPT_TEMPLATE = """\
Analyse the following job description and return a single JSON object.

Schema
------
{{
  "must_have": [
    {{
      "requirement": "<clear label>",
      "category": "<leadership|technical|domain|operational|soft_skill>",
      "weight": <float 0.8–1.0>
    }}
  ],
  "nice_to_have": [
    {{
      "requirement": "<clear label>",
      "category": "<leadership|technical|domain|operational|soft_skill>",
      "weight": <float 0.3–0.6>
    }}
  ],
  "urgency_signals": ["<verbatim phrase or observation>"],
  "urgency_level": "<low|medium|high>",
  "urgency_reasoning": "<1–2 sentences>",
  "role_summary": "<1 paragraph context for downstream agents>"
}}

Rules
-----
- must_have weights reflect relative criticality within the must-have set.
- Urgency signals include: backfill language, "immediate start", compressed timelines,
  phrases like "cannot afford a gap", head-count freeze lift, competitor pressure.
- Return ONLY the JSON object — no markdown, no explanation outside it.

Job Description
---------------
{jd}
"""


def analyze_jd(job_description: str) -> dict:
    """
    Args:
        job_description: Raw JD text.

    Returns:
        Structured dict with must_have, nice_to_have, urgency_signals,
        urgency_level, urgency_reasoning, role_summary.
    """
    client = get_client()
    prompt = _PROMPT_TEMPLATE.format(jd=job_description)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    result = parse_json(response.content[0].text, "JD Agent")

    # Attach original JD for downstream reference
    result["_raw_jd"] = job_description
    return result
