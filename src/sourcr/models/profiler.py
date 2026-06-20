"""
Profiler crew output — a verified, confidence-tagged company profile.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class ConfidenceLevel(str, Enum):
    """How well a single claimed fact is supported by its sources."""
    VERIFIED = "VERIFIED"        # corroborated by 2+ independent sources
    LIKELY = "LIKELY"            # one credible source (company site, filing)
    UNVERIFIED = "UNVERIFIED"    # one weak source (forum, directory, aggregator)
    CONFLICTING = "CONFLICTING"  # sources disagree — surface, don't pick one


class OverallConfidence(str, Enum):
    """Headline confidence for a whole company profile / brief."""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class FactClaim(BaseModel):
    """A single researched fact, tagged with confidence and its sources."""
    fact: str
    confidence: ConfidenceLevel
    sources: list[str] = Field(default_factory=list)


class CompanyProfile(BaseModel):
    """Structured output of the Profiler crew for one company."""
    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    facts: list[FactClaim] = Field(default_factory=list)
    fit_assessment: str = Field(..., description="Short rationale against the thesis")
    overall_confidence: OverallConfidence = OverallConfidence.NEEDS_REVIEW
