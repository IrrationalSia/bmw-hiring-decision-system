"""
BMW Hiring Decision System — multi-agent pipeline.

Agent execution order:
  1. jd_agent.analyze_jd(job_description)
  2. cv_agent.score_candidate(candidate, jd_analysis)
  3. scenario_agent.apply_scenarios(cv_result, jd_analysis)
  4. decision_agent.make_decision(cv_result, scenario_result, jd_analysis)
"""
