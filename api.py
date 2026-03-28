"""
BMW Hiring Decision System — FastAPI wrapper.

Endpoints
---------
GET  /health        — liveness check
POST /evaluate      — run the full pipeline; accepts custom JD + candidates
                      or falls back to the built-in synthetic dataset

Start the server
----------------
  uvicorn api:app --reload --port 8000

Example request (synthetic dataset)
-------------------------------------
  curl -X POST http://localhost:8000/evaluate

Example request (custom payload)
----------------------------------
  curl -X POST http://localhost:8000/evaluate \\
       -H "Content-Type: application/json" \\
       -d @payload.json
"""

from __future__ import annotations

import time
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from main import run_pipeline
from data.synthetic_candidates import JOB_DESCRIPTION, CANDIDATES

load_dotenv()

app = FastAPI(
    title="BMW Hiring Decision System",
    description=(
        "Multi-agent pipeline that surfaces the Speed vs Right Hire trade-off. "
        "All candidate data must be synthetic — no real personal data."
    ),
    version="1.0.0",
)


# ── Request / Response models ─────────────────────────────────────────────────

class CandidateInput(BaseModel):
    id: str
    name: str
    current_role: str = ""
    years_experience: int = 0
    availability: str
    profile: str


class EvaluateRequest(BaseModel):
    job_description: str | None = Field(
        default=None,
        description="Raw JD text. Omit to use the built-in synthetic dataset.",
    )
    candidates: list[CandidateInput] | None = Field(
        default=None,
        description="Candidate profiles. Omit to use the built-in synthetic dataset.",
    )


class HealthResponse(BaseModel):
    status: str
    timestamp: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    return HealthResponse(status="ok", timestamp=time.time())


@app.post("/evaluate", tags=["pipeline"])
def evaluate(body: EvaluateRequest = EvaluateRequest()) -> JSONResponse:
    """
    Run the 4-agent hiring decision pipeline.

    - If `job_description` and `candidates` are omitted, the built-in
      synthetic BMW dataset is used (great for demos).
    - Supply both fields to evaluate your own JD and candidates.

    Returns the full structured output: JD analysis, per-candidate CV scores,
    scenario re-weightings, and final decisions including fit_score,
    speed_pressure_score, and urgency_warning.

    **human_override is always null** — the final call stays with the hiring manager.
    """
    jd   = body.job_description or JOB_DESCRIPTION
    cands = (
        [c.model_dump() for c in body.candidates]
        if body.candidates
        else CANDIDATES
    )

    if not jd.strip():
        raise HTTPException(status_code=422, detail="job_description must not be empty.")
    if not cands:
        raise HTTPException(status_code=422, detail="candidates list must not be empty.")

    try:
        results = run_pipeline(jd, cands)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return JSONResponse(content=results)
