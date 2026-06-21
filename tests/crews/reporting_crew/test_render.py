"""
Tests for the Opportunity Brief Markdown renderer.

Pure Python, no LLM and no network — render.py just formats a structured
OpportunityBrief, so it is fully and cheaply testable.

Run from the project root:
    python -m pytest                                            # whole suite
    python -m pytest tests/crews/reporting_crew/test_render.py  # just this file
"""

from sourcr.crews.reporting_crew.render import render_brief_markdown
from sourcr.models import (
    ConfidenceLevel,
    Contact,
    FactClaim,
    OpportunityBrief,
    OverallConfidence,
)


def _full_brief():
    return OpportunityBrief(
        company_name="Enervise",
        domain="enervise.com",
        summary="Commercial HVAC services firm.",
        fit_rationale="Now PE-backed; fails the founder-led thesis.",
        key_facts=[
            FactClaim(
                fact="Now PE-backed (2025)",
                confidence=ConfidenceLevel.VERIFIED,
                sources=["https://percheron.com/x", "https://enervise.com/news"],
            ),
        ],
        decision_makers=[
            Contact(
                name="John Blaylock",
                title="President",
                source_url="https://enervise.com/about",
                profile_url="https://linkedin.com/in/jb",
            ),
        ],
        overall_confidence=OverallConfidence.MEDIUM,
    )


def test_renders_heading_and_sections():
    md = render_brief_markdown(_full_brief())
    assert "# Opportunity Brief — Enervise" in md
    assert "## Summary" in md
    assert "## Fit vs. Thesis" in md
    assert "**Overall confidence:** MEDIUM" in md


def test_renders_key_facts_table_with_joined_sources():
    md = render_brief_markdown(_full_brief())
    assert "| Fact | Confidence | Sources |" in md
    assert "VERIFIED" in md
    assert "https://percheron.com/x<br>https://enervise.com/news" in md


def test_renders_decision_makers_table():
    md = render_brief_markdown(_full_brief())
    assert "| Name | Title | Profile | Source |" in md
    assert "John Blaylock" in md
    assert "https://linkedin.com/in/jb" in md


def test_handles_empty_facts_and_contacts():
    brief = OpportunityBrief(company_name="X", summary="s", fit_rationale="f")
    md = render_brief_markdown(brief)
    assert "_No facts recorded._" in md
    assert "_No decision-makers identified._" in md


def test_escapes_pipe_in_fact_cell():
    brief = OpportunityBrief(
        company_name="X",
        summary="s",
        fit_rationale="f",
        key_facts=[
            FactClaim(fact="Revenue A | B", confidence=ConfidenceLevel.LIKELY,
                      sources=["https://x.com"]),
        ],
    )
    md = render_brief_markdown(brief)
    assert "Revenue A \\| B" in md
