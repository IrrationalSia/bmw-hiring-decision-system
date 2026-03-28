"""
Decision Agent
--------------
Synthesises JD Agent + CV Agent + Scenario Agent outputs into a final
hiring recommendation for a single candidate.

Core trade-off surfaced
-----------------------
fit_score          — how well the candidate genuinely fits the role requirements
                     (urgency-adjusted, i.e. bias-corrected version of CV score)

speed_pressure_score — 0–100 indicator of how much urgency is inflating this
                     candidate's apparent attractiveness. High = the hire may be
                     driven more by need-to-fill-now than genuine fit.

Human override
--------------
The field `human_override` is ALWAYS null in agent output.
The final hiring decision is a human judgement call. This system provides
structured evidence, not a binding verdict.
"""

import json

from .utils import MODEL, get_client, parse_json

_SYSTEM = (
    "You are BMW Group's Chief Talent Decision Advisor. "
    "You synthesise multi-agent hiring analysis into an honest, evidence-based "
    "recommendation that explicitly separates genuine candidate fit from urgency-driven "
    "hiring pressure. You are frank about risk and never let time pressure override "
    "quality standards without naming it clearly. "
    "You always return valid JSON and nothing else."
)

_PROMPT_TEMPLATE = """\
You must produce a final hiring decision analysis for one candidate.

=== JD Context ===
Role summary     : {role_summary}
Urgency level    : {urgency_level}
Urgency signals  : {urgency_signals}
Urgency reasoning: {urgency_reasoning}

=== CV Agent Result ===
Candidate        : {candidate_name} (ID: {candidate_id})
Baseline fit score: {baseline_score}  (weighted average across all JD requirements)
Availability     : {availability}
Urgency bias flags: {bias_flags}
Candidate summary: {candidate_summary}

Per-criterion scores (abbreviated):
{top_scores_json}

=== Scenario Agent Result ===
Transformation push score   : {score_transform}
Automotive continuity score : {score_continuity}
Competitive pressure score  : {score_competitive}
Best fit scenario           : {best_scenario}
Scenario spread             : {scenario_spread}
Scenario analyst note       : {scenario_note}

=== Your Task ===
Produce a final hiring decision analysis following this schema exactly:

{{
  "candidate_id": "{candidate_id}",
  "candidate_name": "{candidate_name}",

  "fit_score": <float 0–100 — genuine fit, with urgency-bias corrections applied>,
  "speed_pressure_score": <float 0–100 — how much urgency is inflating this candidate's case;
                           0 = no urgency distortion, 100 = hire entirely driven by availability>,

  "recommendation": "<strong_hire|hire|hold|pass>",
  "confidence_level": "<low|medium|high>",

  "reasoning": "<3–5 sentences — the core argument for or against this hire, referencing both
                 genuine strengths and any urgency-driven risks>",

  "strengths": ["<2–4 genuine differentiating strengths>"],
  "risks": ["<2–4 honest risks or gaps>"],
  "urgency_warning": "<null if speed_pressure_score < 30, otherwise a plain-language warning
                       for the hiring manager about the urgency distortion observed>",

  "scenario_recommendation": "<which BMW scenario this candidate is best suited for and why — 1–2 sentences>",

  "human_override": null,
  "human_override_prompt": "The final hiring decision rests with the hiring manager. \
Consider: does the speed_pressure_score change your view? What would you do if the \
vacancy timeline were extended by 6 weeks?"
}}

Calibration notes:
- fit_score should be close to baseline_score if no bias was flagged; lower if bias flags are present.
- speed_pressure_score rises with: immediate availability, high urgency level, bias flags, internal-convenience signals.
- Be honest. If the urgency_warning field is warranted, write it clearly.

Return ONLY the JSON object.
"""


def make_decision(cv_result: dict, scenario_result: dict, jd_analysis: dict) -> dict:
    """
    Args:
        cv_result:       output of cv_agent.score_candidate()
        scenario_result: output of scenario_agent.apply_scenarios()
        jd_analysis:     output of jd_agent.analyze_jd()

    Returns:
        Final decision dict. human_override is always null.
    """
    client = get_client()

    scenarios = scenario_result.get("scenarios", {})
    top_scores = sorted(
        cv_result.get("scores", []),
        key=lambda s: s.get("weight", 0),
        reverse=True,
    )[:8]  # top 8 by weight to keep prompt concise

    prompt = _PROMPT_TEMPLATE.format(
        role_summary=jd_analysis.get("role_summary", ""),
        urgency_level=jd_analysis.get("urgency_level", "unknown"),
        urgency_signals=", ".join(jd_analysis.get("urgency_signals", [])),
        urgency_reasoning=jd_analysis.get("urgency_reasoning", ""),
        candidate_id=cv_result["candidate_id"],
        candidate_name=cv_result["candidate_name"],
        baseline_score=cv_result.get("weighted_fit_score", 0),
        availability=cv_result.get("_availability_raw", "unknown"),
        bias_flags=", ".join(cv_result.get("urgency_bias_flags_summary", [])) or "none",
        candidate_summary=cv_result.get("candidate_summary", ""),
        top_scores_json=json.dumps(top_scores, indent=2),
        score_transform=scenarios.get("transformation_push", {}).get("adjusted_score", "n/a"),
        score_continuity=scenarios.get("automotive_continuity", {}).get("adjusted_score", "n/a"),
        score_competitive=scenarios.get("competitive_pressure", {}).get("adjusted_score", "n/a"),
        best_scenario=scenario_result.get("best_fit_scenario", "unknown"),
        scenario_spread=scenario_result.get("scenario_spread", 0),
        scenario_note=scenario_result.get("scenario_analyst_note", ""),
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )

    result = parse_json(response.content[0].text, f"Decision Agent [{cv_result['candidate_name']}]")

    # Enforce the invariant: human_override is always null from the agent
    result["human_override"] = None
    return result
