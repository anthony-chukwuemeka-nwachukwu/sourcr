"""
Opt-in live integration test for the full SourcingFlow.

Unlike the rest of the suite, this actually runs the pipeline end to end —
real LLM + search API calls — so it is SKIPPED by default. Enable it with
RUN_LIVE=1 and valid API keys in your .env:

    # bash
    RUN_LIVE=1 python -m pytest tests/test_integration.py -v
    # PowerShell
    $env:RUN_LIVE=1; python -m pytest tests/test_integration.py -v

It asserts loose invariants (not exact content), since LLM output varies run
to run. Keep candidate count at 1 to keep it cheap.
"""

import os

import pytest

RUN_LIVE = os.getenv("RUN_LIVE") == "1"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not RUN_LIVE, reason="set RUN_LIVE=1 (and API keys) to run the live pipeline"),
]


def test_full_pipeline_produces_briefs():
    from dotenv import find_dotenv, load_dotenv

    from sourcr.main import SourcingFlow
    from sourcr.models import OpportunityBrief

    load_dotenv(find_dotenv())

    flow = SourcingFlow()
    flow.kickoff(inputs={"max_candidates": 1})  # keep it small + cheap

    briefs = flow.state.briefs
    assert isinstance(briefs, list)

    # If research surfaced any candidate, we expect at least one well-formed brief.
    if flow.state.candidates:
        assert len(briefs) >= 1
        brief = briefs[0]
        assert isinstance(brief, OpportunityBrief)
        assert brief.company_name.strip()
        assert brief.summary.strip()
        assert brief.fit_rationale.strip()
