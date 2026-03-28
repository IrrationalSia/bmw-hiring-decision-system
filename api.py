"""
BMW Hiring Decision System — FastAPI wrapper.

Endpoints
---------
GET  /health        — liveness check + lightweight module warmup
GET  /warmup        — pre-loads synthetic data and Anthropic client; returns ready state
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

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from main import run_pipeline
from data.synthetic_candidates import JOB_DESCRIPTION, CANDIDATES

load_dotenv()

# ── Warmup state ──────────────────────────────────────────────────────────────
# Tracks whether the Anthropic client and synthetic data have been loaded into
# memory. Warmup is idempotent — subsequent calls are instant.

_warmed_at: float | None = None


def _do_warmup() -> None:
    """
    Force-import the Anthropic client and touch the synthetic dataset so both
    are resident in memory before the first real request arrives.
    Runs at most once per process lifetime.
    """
    global _warmed_at
    if _warmed_at is not None:
        return

    # Importing get_client constructs the Anthropic SDK instance (validates the
    # API key, initialises httpx connection pool) without making a network call.
    from agents.utils import get_client
    get_client()

    # Touch the synthetic data to ensure it is deserialised and cached.
    _ = JOB_DESCRIPTION
    _ = CANDIDATES

    _warmed_at = time.time()

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
    warmed: bool


class WarmupResponse(BaseModel):
    status: str
    ready: bool
    warmed_at: float


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse, tags=["ops"])
def health() -> HealthResponse:
    """Liveness check. Also triggers a one-time module warmup on first call."""
    _do_warmup()
    return HealthResponse(status="ok", timestamp=time.time(), warmed=_warmed_at is not None)


@app.get("/warmup", response_model=WarmupResponse, tags=["ops"])
def warmup() -> WarmupResponse:
    """
    Pre-loads the Anthropic client and synthetic dataset into memory.
    Safe to call repeatedly — warmup runs at most once per process.
    Use this endpoint to eliminate cold-start latency before a demo or load test.
    """
    _do_warmup()
    return WarmupResponse(status="warm", ready=True, warmed_at=_warmed_at)


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
