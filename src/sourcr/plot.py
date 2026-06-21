"""
plot.py

Pipeline-level visualization: a stacked horizontal bar of fact-confidence
counts per company across all Opportunity Briefs, so you can compare at a
glance how well-verified each opportunity is.

Pure Python (matplotlib, headless 'Agg' backend) — deterministic and testable
with no display and no API calls.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: render to file, no GUI/display needed

import matplotlib.pyplot as plt  # noqa: E402  (must follow use("Agg"))

from sourcr.models import ConfidenceLevel, OpportunityBrief

# Stacking order and colors: strong (green) -> weak (red).
_LEVELS = [
    ConfidenceLevel.VERIFIED,
    ConfidenceLevel.LIKELY,
    ConfidenceLevel.UNVERIFIED,
    ConfidenceLevel.CONFLICTING,
]
_COLORS = {
    ConfidenceLevel.VERIFIED: "#2e7d32",
    ConfidenceLevel.LIKELY: "#9ccc65",
    ConfidenceLevel.UNVERIFIED: "#ffb300",
    ConfidenceLevel.CONFLICTING: "#e53935",
}


def confidence_counts(brief: OpportunityBrief) -> dict[ConfidenceLevel, int]:
    """Count a brief's key facts by confidence level."""
    counts = {lvl: 0 for lvl in _LEVELS}
    for fact in brief.key_facts:
        if fact.confidence in counts:
            counts[fact.confidence] += 1
    return counts


def plot_pipeline_confidence(briefs: list[OpportunityBrief], out_path: Path) -> Path:
    """Render a stacked bar of fact-confidence counts per company to out_path."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    names = [b.company_name for b in briefs]
    counts = [confidence_counts(b) for b in briefs]

    fig, ax = plt.subplots(figsize=(9, max(2.0, 0.6 * len(briefs) + 1)))
    left = [0] * len(briefs)
    for lvl in _LEVELS:
        widths = [c[lvl] for c in counts]
        ax.barh(names, widths, left=left, color=_COLORS[lvl], label=lvl.value)
        left = [base + w for base, w in zip(left, widths)]

    ax.set_xlabel("Number of facts")
    ax.set_title("Opportunity pipeline — fact confidence by company")
    if names:
        ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=120)
    plt.close(fig)
    return out_path
