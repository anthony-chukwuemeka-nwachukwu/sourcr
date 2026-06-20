"""
Tests for the Profiler crew's guardrail.

Deterministic — no LLM calls, no network. Each test feeds a hand-made
CompanyProfile to validate_profile and checks it accepts complete profiles
and triggers a re-run on incomplete ones.

Run from the project root:
    python -m pytest                                              # whole suite
    python -m pytest tests/crews/profiler_crew/test_guardrail.py  # just this file
"""

from types import SimpleNamespace

from sourcr.crews.profiler_crew.profiler_crew import validate_profile
from sourcr.models import CompanyProfile, ConfidenceLevel, FactClaim


def _output(profile):
    """Mimic the TaskOutput the guardrail receives (only .pydantic is used)."""
    return SimpleNamespace(pydantic=profile)


def _fact(fact="Founded in 1985", confidence=ConfidenceLevel.VERIFIED, sources=("https://x.com",)):
    return FactClaim(fact=fact, confidence=confidence, sources=list(sources))


def _profile(facts=None, fit_assessment="Good service fit; PE-backed, so weak on ownership."):
    return CompanyProfile(
        name="Enervise",
        domain="enervise.com",
        facts=[_fact()] if facts is None else facts,
        fit_assessment=fit_assessment,
    )


def test_accepts_complete_profile():
    ok, result = validate_profile(_output(_profile()))
    assert ok is True
    assert isinstance(result, CompanyProfile)


def test_rejects_no_facts():
    ok, msg = validate_profile(_output(_profile(facts=[])))
    assert ok is False
    assert "facts" in msg.lower()


def test_rejects_fact_without_source():
    ok, msg = validate_profile(_output(_profile(facts=[_fact(sources=())])))
    assert ok is False
    assert "source" in msg.lower()


def test_rejects_empty_fit_assessment():
    ok, msg = validate_profile(_output(_profile(fit_assessment="   ")))
    assert ok is False
    assert "fit" in msg.lower()
