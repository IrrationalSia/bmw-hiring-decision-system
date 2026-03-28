# BMW Hiring Decision System
### Speed vs Right Hire — Multi-Agent Hiring Intelligence

> A multi-agent AI pipeline that helps BMW hiring managers distinguish between candidates
> selected for **genuine fit** and those selected under **urgency and time pressure** —
> surfacing the trade-off before the decision is made, not after.

---

## The Problem

When a key role needs to be filled urgently — a backfill, a production gap, a competitive
response — hiring managers face a silent pressure: *take the available candidate, not the
right one*. This bias rarely appears in the hiring record. It shows up six months later,
in performance reviews and retention numbers.

This system makes that trade-off **visible and explicit** at decision time.

---

## What the System Does

For any job description and set of candidates, the pipeline:

1. **Extracts** must-have vs nice-to-have requirements from the JD and flags urgency signals
2. **Scores** each candidate per criterion (0–10) and tags where urgency may be inflating scores
3. **Re-weights** scores under three BMW-specific strategic scenarios to show who wins where
4. **Synthesises** a final recommendation with a `fit_score` vs `speed_pressure_score` —
   the core trade-off in a single number pair

The final call **always stays with the hiring manager**. The system provides structured
evidence, not a binding verdict.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        INPUT LAYER                              │
│          Job Description Text  +  Candidate Profiles           │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 1 — JD Agent                  agents/jd_agent.py        │
│                                                                 │
│  • Classifies requirements: must-have vs nice-to-have          │
│  • Assigns category (leadership / technical / operational …)   │
│  • Assigns weights (must-have: 0.8–1.0 / nice-to-have: 0.3–0.6)│
│  • Detects urgency signals ("immediate start", "backfill" …)   │
│  • Outputs urgency_level: low | medium | high                  │
└───────────────────────┬─────────────────────────────────────────┘
                        │  jd_analysis
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 2 — CV Agent                  agents/cv_agent.py        │
│  (runs once per candidate)                                      │
│                                                                 │
│  • Scores each requirement 0–10 with cited evidence            │
│  • Computes weighted_fit_score (0–100)                         │
│  • Flags urgency_bias on individual criteria                   │
│    (e.g. internal candidate inflated by availability)          │
└───────────────────────┬─────────────────────────────────────────┘
                        │  cv_result
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 3 — Scenario Agent        agents/scenario_agent.py      │
│  (runs once per candidate)                                      │
│                                                                 │
│  Re-weights scores under 3 BMW strategic contexts:             │
│                                                                 │
│  ① Transformation Push                                         │
│     EV / digital / change leadership weighted higher           │
│                                                                 │
│  ② Automotive Continuity                                       │
│     OEE / lean / ICE domain depth weighted higher              │
│                                                                 │
│  ③ Competitive Pressure  (Amazon / Tesla / BYD response)       │
│     Digital delivery / agile speed weighted higher             │
│                                                                 │
│  Outputs adjusted score per scenario + scenario_spread         │
└───────────────────────┬─────────────────────────────────────────┘
                        │  scenario_result
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  AGENT 4 — Decision Agent        agents/decision_agent.py      │
│  (runs once per candidate)                                      │
│                                                                 │
│  • fit_score          — bias-corrected genuine fit (0–100)     │
│  • speed_pressure_score — urgency distortion level (0–100)     │
│  • recommendation     — strong_hire | hire | hold | pass       │
│  • confidence_level   — low | medium | high                    │
│  • urgency_warning    — plain-language alert if bias detected  │
│  • human_override     — always null  ← filled by human        │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       OUTPUT LAYER                              │
│   Console (Rich) + results.json + POST /evaluate response      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Model Selection: Why claude-sonnet-4-6

All four agents use **`claude-sonnet-4-6`** via the Anthropic Messages API.

| Requirement | Why Sonnet 4.6 fits |
|---|---|
| Structured JSON output | Reliably follows strict schemas across all four agents without post-processing failures |
| Long-context reasoning | Holds the full JD + all candidate scores in context for the Decision Agent synthesis |
| Nuanced judgement | Distinguishes "urgency inflation" from genuine competency gaps — requires calibrated reasoning, not just classification |
| Latency | Fast enough to run 10+ sequential API calls in a demo setting without timeout risk |
| Cost | Suitable for a hackathon budget while matching Opus-level output quality on structured tasks |

Each agent has a **dedicated system prompt** that scopes its role — the JD Agent is a requirements analyst,
the CV Agent is a talent assessor, the Scenario Agent is a strategic workforce planner, the Decision Agent
is a synthesis advisor. Role separation prevents context bleed between agents.

---

## Synthetic Dataset

Three deliberately contrasted candidates for **Head of Production, Regensburg Plant**:

| Candidate | Archetype | Availability | Core tension |
|---|---|---|---|
| Dr. Maria Hartmann | Strongest genuine fit — OEE 88–91%, Six Sigma Black Belt, 16 yrs Audi | 8 weeks | Best match, slowest start |
| James Okoro | Future-fit — Tesla EMEA VP, EV + digital twin expert | 6 weeks | Ideal for transformation, weaker on continuity |
| Stefan Brenner | Urgency candidate — internal BMW, knows the plant | Immediate | Convenient now, developmental risk |

The dataset is designed so Brenner scores highest on **speed** but lowest on **genuine fit** —
making the urgency trade-off impossible to ignore.

> All data is entirely fictional. No real persons are represented.

---

## Running Locally

**Prerequisites:** Python 3.11+, an Anthropic API key.

```bash
# 1. Clone
git clone https://github.com/IrrationalSia/bmw-hiring-decision-system.git
cd bmw-hiring-decision-system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure API key
cp .env.example .env
# Edit .env and set: ANTHROPIC_API_KEY=your_key_here

# 4. Run the pipeline
python main.py
```

The console prints live progress per agent per candidate and ends with a
comparison table. Full results are written to `results.json`.

---

## Running the API

```bash
uvicorn api:app --reload --port 8000
```

Interactive docs: **http://localhost:8000/docs**

### Endpoints

#### `GET /health`
```json
{ "status": "ok", "timestamp": 1743100800.0 }
```

#### `POST /evaluate`

**Option A — use the built-in synthetic dataset (no body required):**
```bash
curl -X POST http://localhost:8000/evaluate
```

**Option B — supply a custom JD and candidates:**
```bash
curl -X POST http://localhost:8000/evaluate \
     -H "Content-Type: application/json" \
     -d '{
       "job_description": "...",
       "candidates": [
         {
           "id": "c1",
           "name": "Jane Example",
           "current_role": "Production Manager, OEM",
           "years_experience": 12,
           "availability": "4 weeks",
           "profile": "..."
         }
       ]
     }'
```

**Response shape (abbreviated):**
```json
{
  "jd_analysis": {
    "must_have": [...],
    "nice_to_have": [...],
    "urgency_level": "high",
    "urgency_signals": ["immediate start", "backfill", "cannot afford a gap"]
  },
  "candidates": [
    {
      "candidate": { "id": "candidate_001", "name": "Dr. Maria Hartmann", ... },
      "cv_result": {
        "weighted_fit_score": 84.2,
        "urgency_bias_flags_summary": []
      },
      "scenario_result": {
        "scenarios": {
          "transformation_push":   { "adjusted_score": 71.0 },
          "automotive_continuity": { "adjusted_score": 89.5 },
          "competitive_pressure":  { "adjusted_score": 68.0 }
        },
        "best_fit_scenario": "automotive_continuity"
      },
      "decision": {
        "fit_score": 84.2,
        "speed_pressure_score": 12.0,
        "recommendation": "strong_hire",
        "confidence_level": "high",
        "urgency_warning": null,
        "human_override": null
      }
    }
  ]
}
```

---

## Deployment (Railway)

The repository includes Railway-ready configuration:

| File | Purpose |
|---|---|
| `Procfile` | `web: uvicorn api:app --host 0.0.0.0 --port $PORT` |
| `runtime.txt` | `python-3.11.0` |

Steps:
1. Railway → **New Project** → Deploy from GitHub → select this repo
2. Add environment variable: `ANTHROPIC_API_KEY = <your key>`
3. Deploy — Railway detects the `Procfile` automatically

---

## Ethical Constraints

### 1. Synthetic data only
This system must not be run against real candidate data without explicit written consent,
a GDPR Data Protection Impact Assessment (DPIA), and legal sign-off from BMW Group's data
privacy team.

### 2. Human-in-the-loop is mandatory
`human_override` is always `null` in agent output. No hire or rejection should occur
solely on the basis of system output. The hiring manager reviews, decides, and signs off.

### 3. Urgency bias is named, not suppressed
The `speed_pressure_score` and `urgency_warning` fields exist to make bias visible.
A high speed-pressure score is a prompt to pause — not a reason to accelerate.

### 4. No protected characteristics
Agents score on competency evidence only. Profiles contain no age, gender, race,
disability, or other protected characteristic data. Any production deployment must
audit prompts for disparate impact before use.

### 5. Full audit trail
`results.json` provides a replayable record of every agent's reasoning for every
candidate. This supports accountability and review under BMW Group record-keeping policy.

---

## Project Structure

```
bmw-hiring-decision-system/
├── CLAUDE.md                    # Architecture reference and ethical constraints
├── README.md                    # This file
├── Procfile                     # Railway process definition
├── runtime.txt                  # Python version pin
├── requirements.txt
├── .env.example                 # API key template
├── main.py                      # CLI orchestrator + run_pipeline() core function
├── api.py                       # FastAPI wrapper (POST /evaluate, GET /health)
├── agents/
│   ├── utils.py                 # Shared: Anthropic client, JSON parser
│   ├── jd_agent.py              # Agent 1: requirement extraction + urgency detection
│   ├── cv_agent.py              # Agent 2: candidate scoring + bias flagging
│   ├── scenario_agent.py        # Agent 3: BMW scenario re-weighting
│   └── decision_agent.py        # Agent 4: fit vs speed-pressure synthesis
└── data/
    └── synthetic_candidates.py  # JD + 3 synthetic candidates (Head of Production)
```

---

## Built With

- [Anthropic API](https://docs.anthropic.com) — `claude-sonnet-4-6` for all agent reasoning
- [FastAPI](https://fastapi.tiangolo.com) — API layer
- [Rich](https://rich.readthedocs.io) — CLI output
- [Railway](https://railway.app) — deployment

---

*Built for the BMW Group Hackathon — March 2026*
*All candidate data is synthetic. Human oversight is required for all hiring decisions.*
