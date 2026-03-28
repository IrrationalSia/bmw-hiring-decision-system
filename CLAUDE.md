# BMW Hiring Decision System — CLAUDE.md

## Overview

This system helps BMW hiring managers distinguish between candidates selected for
**genuine fit** versus those selected under **urgency and time pressure**. It is a
multi-agent pipeline powered by `claude-sonnet-4-6` via the Anthropic API.

The core trade-off surfaced per candidate:

| Metric              | Meaning                                                   |
|---------------------|-----------------------------------------------------------|
| `fit_score`         | How well the candidate genuinely meets the JD requirements (0–100) |
| `speed_pressure_score` | How much urgency is distorting the hire decision (0–100; high = risk) |

---

## Architecture

```
main.py  (orchestrator)
│
├── agents/jd_agent.py          ← Step 1: JD analysis
├── agents/cv_agent.py          ← Step 2: candidate scoring
├── agents/scenario_agent.py    ← Step 3: BMW scenario re-weighting
├── agents/decision_agent.py    ← Step 4: final synthesis
│
├── agents/utils.py             ← shared: Anthropic client, JSON parsing
│
└── data/synthetic_candidates.py  ← job description + 3 synthetic candidates
```

### Agent 1 — JD Agent (`agents/jd_agent.py`)

**Input**: raw job description text
**Output**:
- `must_have[]` — essential requirements with category and weight (0.8–1.0)
- `nice_to_have[]` — desirable requirements with weight (0.3–0.6)
- `urgency_signals[]` — verbatim phrases signalling time pressure
- `urgency_level` — `"low"` | `"medium"` | `"high"`
- `urgency_reasoning` — plain-language explanation
- `role_summary` — context passed to downstream agents

**Why it exists**: Separates what the role actually needs from what urgency adds to
the mix. Sets the scoring framework for the CV Agent.

---

### Agent 2 — CV Agent (`agents/cv_agent.py`)

**Input**: candidate profile dict + JD Agent output
**Output**:
- `scores[]` — per-requirement score (0–10), rationale, and `urgency_bias_flag`
- `weighted_fit_score` — weighted average across all requirements (0–100)
- `urgency_bias_flags_summary[]` — which requirements show potential bias inflation
- `availability_weeks` — parsed availability
- `candidate_summary` — overall assessment

**Why it exists**: Creates an evidence-based score for each JD criterion and
explicitly tags where urgency may be artificially inflating a candidate's appeal
(e.g. an internal candidate scoring well on "plant knowledge" when urgency favours
the known quantity).

---

### Agent 3 — Scenario Agent (`agents/scenario_agent.py`)

**Input**: CV Agent output + JD analysis
**Output**: Three scenario-adjusted scores (0–100) plus analysis:

| Scenario | Description |
|----------|-------------|
| `transformation_push` | BMW accelerating EV/digital; upweights EV, Industry 4.0, change leadership |
| `automotive_continuity` | Near-term volume protection; upweights OEE, lean/Six Sigma, ICE domain depth |
| `competitive_pressure` | Amazon/Tesla/BYD threat; upweights digital delivery, agile leadership, speed |

Also produces `scenario_spread` (difference between best and worst scenario score)
as an indicator of candidate versatility.

**Why it exists**: The "right hire" depends on BMW's strategic reality at the moment
of hire. The same candidate can look very different under different scenarios.

---

### Agent 4 — Decision Agent (`agents/decision_agent.py`)

**Input**: CV Agent + Scenario Agent + JD Agent outputs
**Output**:
- `fit_score` — bias-corrected genuine fit (0–100)
- `speed_pressure_score` — urgency distortion indicator (0–100)
- `recommendation` — `strong_hire` | `hire` | `hold` | `pass`
- `confidence_level` — `low` | `medium` | `high`
- `reasoning` — plain-language argument
- `strengths[]`, `risks[]`
- `urgency_warning` — plain-language alert if speed pressure ≥ 30
- `scenario_recommendation` — which BMW scenario this candidate is best for
- `human_override` — **always `null`** — see Ethical Constraints below
- `human_override_prompt` — reflection questions for the hiring manager

---

## Running the System

### Prerequisites

```bash
# Python 3.10+
pip install -r requirements.txt

# Set your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### Run the full pipeline

```bash
# Linux / Mac
export $(cat .env | xargs) && python main.py

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=<your-key>
python main.py

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="<your-key>"
python main.py
```

### Run individual agents (for debugging / iteration)

```python
from dotenv import load_dotenv; load_dotenv()

from agents.jd_agent import analyze_jd
from data.synthetic_candidates import JOB_DESCRIPTION

jd = analyze_jd(JOB_DESCRIPTION)
print(jd)
```

### Output

- **Console**: Rich-formatted live output with spinner per step
- **`results.json`**: Full structured output for all candidates (written to project root)

---

## Data

All candidate data in `data/synthetic_candidates.py` is **entirely fictional**.
The three synthetic candidates are designed to stress-test the urgency vs fit tension:

| ID  | Name           | Archetype         | Availability | Core tension |
|-----|----------------|-------------------|--------------|--------------|
| 001 | Dr. M. Hartmann | Strong genuine fit | 8 weeks      | Best fit, but slow to start |
| 002 | J. Okoro       | Future-fit (EV)   | 6 weeks      | Great for transformation, weaker on continuity |
| 003 | S. Brenner     | Urgency candidate | Immediate    | Convenient now, developmental risk |

---

## Ethical Constraints

### 1. Synthetic data only

This system must **never** be run against real candidate data without:
- Explicit written consent from each candidate
- A data protection impact assessment (DPIA) under GDPR
- Legal sign-off from BMW Group's data privacy team

### 2. Human-in-the-loop is mandatory

`human_override` is always `null` in agent output. The system is a **decision
support tool**, not a decision-making tool. No hiring or rejection should occur
solely on the basis of system output.

The hiring manager must:
- Review the `urgency_warning` field for each candidate
- Actively consider whether `speed_pressure_score` is distorting their view
- Fill in `human_override` with their own reasoned conclusion

### 3. Urgency bias is named, not hidden

The system is explicitly designed to surface urgency-driven distortions. Hiring
managers should treat a high `speed_pressure_score` as a prompt to pause, not
as a reason to accelerate.

### 4. No protected characteristics

The agents are instructed to score on competency evidence only. The synthetic
profiles contain no age, gender, race, disability, or other protected
characteristic data. Any production deployment must audit prompts for disparate
impact before use.

### 5. Audit trail

`results.json` provides a full, replayable audit trail of every agent's reasoning
for every candidate. This should be retained per BMW Group record-keeping policy.

---

## Model

All agents use `claude-sonnet-4-6` via the Anthropic Messages API.
Model ID is set in `agents/utils.py` and can be changed centrally.

---

## Project structure

```
BMW/
├── CLAUDE.md                        ← this file
├── requirements.txt
├── .env.example
├── main.py                          ← orchestrator / entry point
├── results.json                     ← written at runtime
├── agents/
│   ├── __init__.py
│   ├── utils.py                     ← Anthropic client + JSON parser
│   ├── jd_agent.py
│   ├── cv_agent.py
│   ├── scenario_agent.py
│   └── decision_agent.py
└── data/
    ├── __init__.py
    └── synthetic_candidates.py      ← JD + 3 synthetic candidates
```
