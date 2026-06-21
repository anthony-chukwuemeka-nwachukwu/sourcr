"""
backend/main.py

FastAPI service that exposes the Sourcr pipeline to the React frontend.

The pipeline takes ~a minute, so runs are handled as background jobs:
    POST /api/runs        -> start a run, returns {run_id}
    GET  /api/runs/{id}   -> poll {status, briefs?, error?}
Plus GET /api/options (form enums) and GET /api/health.

Run from the project root:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

import sys
import threading
import uuid
from pathlib import Path
from typing import Optional

# Make the src/ layout importable.
ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from sourcr.main import SourcingFlow
from sourcr.models import IndustryFocus, InvestmentThesis, OpportunityBrief, OwnershipType

app = FastAPI(title="Sourcr API", version="1.0.0")

# Allow the Vite dev server to call the API during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Schemas + in-memory job store                                               #
# --------------------------------------------------------------------------- #

class RunRequest(BaseModel):
    thesis: InvestmentThesis
    max_candidates: int = Field(3, ge=1, le=8)


class RunStatus(BaseModel):
    status: str = "pending"  # pending | running | done | error
    briefs: list[OpportunityBrief] = Field(default_factory=list)
    error: Optional[str] = None


# Simple in-process store. Fine for a single-worker dev/demo server; swap for
# Redis/a DB if this ever needs multiple workers or persistence.
_RUNS: dict[str, RunStatus] = {}
_LOCK = threading.Lock()


def _execute(run_id: str, req: RunRequest) -> None:
    with _LOCK:
        _RUNS[run_id].status = "running"
    try:
        flow = SourcingFlow()
        flow.kickoff(
            inputs={"thesis": req.thesis.model_dump(), "max_candidates": req.max_candidates}
        )
        with _LOCK:
            _RUNS[run_id].briefs = list(flow.state.briefs)
            _RUNS[run_id].status = "done"
    except Exception as exc:  # surface to the client via the job status
        with _LOCK:
            _RUNS[run_id].status = "error"
            _RUNS[run_id].error = str(exc)


# --------------------------------------------------------------------------- #
# Routes                                                                      #
# --------------------------------------------------------------------------- #

@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/options")
def options() -> dict:
    """Enum values the frontend uses to build the thesis form."""
    return {
        "industries": [i.value for i in IndustryFocus],
        "ownership_types": [o.value for o in OwnershipType],
    }


@app.post("/api/runs")
def create_run(req: RunRequest) -> dict:
    run_id = str(uuid.uuid4())
    with _LOCK:
        _RUNS[run_id] = RunStatus(status="pending")
    threading.Thread(target=_execute, args=(run_id, req), daemon=True).start()
    return {"run_id": run_id}


@app.get("/api/runs/{run_id}", response_model=RunStatus)
def get_run(run_id: str) -> RunStatus:
    with _LOCK:
        status = _RUNS.get(run_id)
    if status is None:
        raise HTTPException(status_code=404, detail="run not found")
    return status
