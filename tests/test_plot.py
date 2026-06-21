"""
Tests for the pipeline confidence plot.

Deterministic — uses matplotlib's headless Agg backend, writes to tmp_path, no
display and no API. Asserts the counting logic and that a PNG is produced.

Run from the project root:
    python -m pytest                      # whole suite
    python -m pytest tests/test_plot.py   # just this file
"""

from sourcr.models import ConfidenceLevel, FactClaim, OpportunityBrief
from sourcr.plot import confidence_counts, plot_pipeline_confidence


def _brief(name, confidences):
    return OpportunityBrief(
        company_name=name,
        summary="s",
        fit_rationale="f",
        key_facts=[
            FactClaim(fact=f"fact {i}", confidence=c, sources=["https://x.com"])
            for i, c in enumerate(confidences)
        ],
    )


def test_confidence_counts():
    brief = _brief(
        "X",
        [ConfidenceLevel.VERIFIED, ConfidenceLevel.VERIFIED, ConfidenceLevel.LIKELY],
    )
    counts = confidence_counts(brief)
    assert counts[ConfidenceLevel.VERIFIED] == 2
    assert counts[ConfidenceLevel.LIKELY] == 1
    assert counts[ConfidenceLevel.UNVERIFIED] == 0


def test_plot_writes_nonempty_png(tmp_path):
    briefs = [
        _brief("Alpha", [ConfidenceLevel.VERIFIED, ConfidenceLevel.LIKELY]),
        _brief("Beta", [ConfidenceLevel.UNVERIFIED, ConfidenceLevel.CONFLICTING]),
    ]
    out = plot_pipeline_confidence(briefs, tmp_path / "chart.png")
    assert out.exists()
    assert out.stat().st_size > 0
