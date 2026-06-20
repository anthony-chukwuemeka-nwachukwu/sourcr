"""
Tests for the Research crew's output validation.

These are deterministic — no LLM calls and no network. They exercise only the
Python validation logic (the guardrail and the URL field validator), so they
run fast, cost nothing, and give the same result every time. Validating the
LLM's actual answers is the job of guardrails at runtime, not unit tests.

Run from the project root:
    python -m pytest                                              # whole suite
    python -m pytest tests/crews/research_crew/test_guardrail.py  # just this file
"""

from types import SimpleNamespace

from sourcr.crews.research_crew.research_crew import validate_candidates
from sourcr.models import Candidate, CandidateList


def _output(candidates):
    """Mimic the TaskOutput object the guardrail receives (only .pydantic is used)."""
    return SimpleNamespace(pydantic=CandidateList(candidates=candidates))


def _candidate(name="ABC Mechanical", domain="abcmech.com", urls=("https://abcmech.com",)):
    return Candidate(
        name=name, domain=domain, rationale="fits the thesis", source_urls=list(urls)
    )


# --- guardrail: validate_candidates -------------------------------------- #

def test_accepts_valid_candidates():
    ok, result = validate_candidates(_output([_candidate()]))
    assert ok is True
    assert isinstance(result, CandidateList)


def test_rejects_empty_list():
    ok, msg = validate_candidates(_output([]))
    assert ok is False
    assert "at least one" in msg.lower()


def test_rejects_candidate_without_source():
    ok, msg = validate_candidates(_output([_candidate(urls=())]))
    assert ok is False
    assert "source" in msg.lower()


def test_rejects_duplicate_companies():
    ok, msg = validate_candidates(_output([_candidate(), _candidate()]))
    assert ok is False
    assert "duplicate" in msg.lower()


# --- field validator: Candidate.keep_real_urls --------------------------- #

def test_validator_keeps_only_http_urls():
    c = Candidate(
        name="X",
        rationale="r",
        source_urls=["", "   ", "ftp://nope", "https://ok.com"],
    )
    assert c.source_urls == ["https://ok.com"]
