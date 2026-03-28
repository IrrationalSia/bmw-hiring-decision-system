"""
BMW Hiring Decision System — FastAPI wrapper.

Endpoints
---------
GET  /health        — zero-dependency liveness check
GET  /warmup        — pre-loads pipeline modules and Anthropic client
POST /evaluate      — run the full 4-agent pipeline

Start the server
----------------
  uvicorn api:app --reload --port 8000
"""

from __future__ import annotations

import os
import time

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# ── .env loading (best-effort — Render injects vars directly) ─────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass  # python-dotenv not installed or .env absent — env vars already set

# ── Startup: confirm API key is present ───────────────────────────────────────
_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
if _api_key:
    print(f"[startup] ANTHROPIC_API_KEY loaded: {_api_key[:8]}…")
else:
    print("[startup] WARNING: ANTHROPIC_API_KEY is not set — /evaluate will fail")

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="BMW Hiring Decision System",
    description=(
        "Multi-agent pipeline that surfaces the Speed vs Right Hire trade-off. "
        "All candidate data must be synthetic — no real personal data."
    ),
    version="1.0.0",
)

# ── Warmup state ──────────────────────────────────────────────────────────────
_warmed_at: float | None = None


def _do_warmup() -> None:
    """
    Lazy-import pipeline modules and initialise the Anthropic client.
    Runs at most once per process — subsequent calls are instant.
    All imports are inside this function so a missing package cannot
    crash startup or block /health.
    """
    global _warmed_at
    if _warmed_at is not None:
        return

    from agents.utils import get_client          # builds httpx connection pool
    from data.synthetic_candidates import (      # deserialises module-level data
        JOB_DESCRIPTION, CANDIDATES,
    )
    get_client()
    _ = JOB_DESCRIPTION
    _ = CANDIDATES
    _warmed_at = time.time()
    print(f"[warmup] Pipeline modules loaded at {_warmed_at}")


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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health", tags=["ops"])
def health() -> dict:
    """
    Zero-dependency liveness check.
    No agent imports, no API calls, no warmup side-effects.
    Always returns 200 as long as the process is alive.
    """
    return {"status": "ok", "timestamp": time.time()}


@app.get("/warmup", tags=["ops"])
def warmup() -> dict:
    """
    Pre-loads pipeline modules and the Anthropic client into memory.
    Idempotent — safe to call repeatedly. Use before a demo or load test
    to eliminate first-request latency.
    """
    _do_warmup()
    return {"status": "warm", "ready": True, "warmed_at": _warmed_at}


@app.post("/evaluate", tags=["pipeline"])
def evaluate(body: EvaluateRequest = EvaluateRequest()) -> JSONResponse:
    """
    Run the 4-agent hiring decision pipeline.

    Omit both fields to use the built-in synthetic BMW dataset.
    Supply both to evaluate a custom JD and candidate set.

    **human_override is always null** — the final call stays with the hiring manager.
    """
    # Lazy imports — nothing from agents/ or data/ is loaded until this point
    from main import run_pipeline
    from data.synthetic_candidates import JOB_DESCRIPTION, CANDIDATES

    jd    = body.job_description or JOB_DESCRIPTION
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
