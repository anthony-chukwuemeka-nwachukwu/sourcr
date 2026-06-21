"""
Reporting crew output — the final Opportunity Brief for one company.

Pure synthesis of upstream stages: it reuses the Profiler's FactClaim and the
Contact crew's Contact rather than defining new fact/contact shapes.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .contact import Contact
from .profiler import FactClaim, OverallConfidence


class OpportunityBrief(BaseModel):
    """The final, decision-ready deliverable for one company."""
    company_name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    summary: str = Field(..., description="2-4 sentence overview")
    fit_rationale: str = Field(..., description="How it fits the thesis, weighing confidence")
    key_facts: list[FactClaim] = Field(default_factory=list)
    decision_makers: list[Contact] = Field(default_factory=list)
    overall_confidence: OverallConfidence = OverallConfidence.NEEDS_REVIEW
