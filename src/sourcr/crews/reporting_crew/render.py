"""
render.py

Turns a structured OpportunityBrief into a Markdown document with tables.

Presentation lives here, in deterministic Python — the LLM produces the
*content* (the OpportunityBrief), this produces the *format*. That keeps
rendering reproducible and unit-testable with no API calls.
"""

from __future__ import annotations

from sourcr.models import OpportunityBrief


def _cell(text: str) -> str:
    """Make a string safe for a Markdown table cell."""
    return text.replace("|", "\\|").replace("\n", " ").strip()


def render_brief_markdown(brief: OpportunityBrief) -> str:
    """Render an Opportunity Brief as Markdown, with key-facts and contacts tables."""
    site = brief.website or (f"https://{brief.domain}" if brief.domain else None)

    lines: list[str] = [
        f"# Opportunity Brief — {brief.company_name}",
        "",
        f"**Overall confidence:** {brief.overall_confidence.value}",
    ]
    if site:
        lines.append(f"**Website:** {site}")
    lines += [
        "",
        "## Summary",
        brief.summary.strip(),
        "",
        "## Fit vs. Thesis",
        brief.fit_rationale.strip(),
        "",
        "## Key Facts",
    ]

    if brief.key_facts:
        lines += ["| Fact | Confidence | Sources |", "| --- | --- | --- |"]
        for f in brief.key_facts:
            sources = "<br>".join(f.sources) if f.sources else "—"
            lines.append(f"| {_cell(f.fact)} | {f.confidence.value} | {_cell(sources)} |")
    else:
        lines.append("_No facts recorded._")

    lines += ["", "## Decision-Makers"]
    if brief.decision_makers:
        lines += ["| Name | Title | Profile | Source |", "| --- | --- | --- | --- |"]
        for c in brief.decision_makers:
            profile = c.profile_url or "—"
            source = c.source_url or "—"
            lines.append(f"| {_cell(c.name)} | {_cell(c.title)} | {profile} | {source} |")
    else:
        lines.append("_No decision-makers identified._")

    return "\n".join(lines) + "\n"
