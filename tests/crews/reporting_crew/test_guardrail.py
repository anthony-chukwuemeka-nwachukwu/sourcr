"""
Tests for the Reporting crew's guardrail.

Deterministic — no LLM calls, no network. Feeds hand-made OpportunityBrief
objects to validate_brief and checks it accepts complete briefs and re-runs on
incomplete ones.

Run from the project root:
    python -m pytest                                               # whole suite
    python -m pytest tests/crews/reporting_crew/test_guardrail.py  # just this file
"""

from types import SimpleNamespace

from sourcr.crews.reporting_crew.reporting_crew import validate_brief
from sourcr.models import ConfidenceLevel, FactClaim, OpportunityBrief, OverallConfidence


def _output(brief):
    """Mimic the TaskOutput the guardrail receives (only .pydantic is used)."""
    return SimpleNamespace(pydantic=brief)


def _brief(summary="Commercial HVAC services firm.",
           fit_rationale="Now PE-backed; fails the founder-led thesis.",
           key_facts=None):
    return OpportunityBrief(
        company_name="Enervise",
        domain="enervise.com",
        summary=summary,
        fit_rationale=fit_rationale,
        key_facts=(
            [FactClaim(fact="Now PE-backed (2025)", confidence=ConfidenceLevel.VERIFIED,
                       sources=["https://percheron.com/x"])]
            if key_facts is None else key_facts
        ),
        overall_confidence=OverallConfidence.MEDIUM,
    )


def test_accepts_complete_brief():
    ok, result = validate_brief(_output(_brief()))
    assert ok is True
    assert isinstance(result, OpportunityBrief)


def test_rejects_empty_summary():
    ok, msg = validate_brief(_output(_brief(summary="   ")))
    assert ok is False
    assert "summary" in msg.lower()


def test_rejects_empty_fit_rationale():
    ok, msg = validate_brief(_output(_brief(fit_rationale="")))
    assert ok is False
    assert "fit_rationale" in msg.lower()


def test_rejects_no_key_facts():
    ok, msg = validate_brief(_output(_brief(key_facts=[])))
    assert ok is False
    assert "key_facts" in msg.lower()
