"""
Tests for the Flow's deterministic helper functions.

No LLM, no network, no flow run — just the pure helpers that the Flow relies
on (candidate keying, synthesis-integrity reconciliation, brief file output).

Run from the project root:
    python -m pytest                            # whole suite
    python -m pytest tests/test_flow_helpers.py # just this file
"""

from sourcr.main import domain_of, key_of, reconcile_brief, save_brief_markdown
from sourcr.models import (
    Candidate,
    CompanyProfile,
    ConfidenceLevel,
    FactClaim,
    OpportunityBrief,
)


def _candidate(**kw):
    kw.setdefault("rationale", "fits the thesis")
    return Candidate(name=kw.pop("name", "X"), **kw)


def test_domain_of_prefers_domain_and_strips_www():
    assert domain_of(_candidate(domain="www.ABC.com")) == "abc.com"


def test_domain_of_falls_back_to_website_host():
    assert domain_of(_candidate(website="https://www.foo.com/about")) == "foo.com"


def test_domain_of_none_when_unknown():
    assert domain_of(_candidate()) is None


def test_key_of_uses_name_when_no_domain():
    assert key_of(_candidate(name="Foo Bar")) == "foo bar"


def _profile(sources):
    return CompanyProfile(
        name="X",
        fit_assessment="f",
        facts=[FactClaim(fact="a", confidence=ConfidenceLevel.LIKELY, sources=sources)],
    )


def _brief(sources):
    return OpportunityBrief(
        company_name="X",
        summary="s",
        fit_rationale="f",
        key_facts=[FactClaim(fact="a", confidence=ConfidenceLevel.LIKELY, sources=sources)],
    )


def test_reconcile_flags_fabricated_source():
    issues = reconcile_brief(_brief(["https://fake.com"]), _profile(["https://real.com"]))
    assert any("fake.com" in i for i in issues)


def test_reconcile_passes_when_sources_are_a_subset():
    assert reconcile_brief(_brief(["https://real.com"]), _profile(["https://real.com"])) == []


def test_save_brief_markdown_writes_file(tmp_path):
    brief = OpportunityBrief(
        company_name="ABC Co", domain="abc.com", summary="s", fit_rationale="f"
    )
    path = save_brief_markdown(brief, tmp_path)
    assert path.exists()
    assert "Opportunity Brief" in path.read_text(encoding="utf-8")
