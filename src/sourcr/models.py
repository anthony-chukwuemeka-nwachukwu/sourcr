"""
models.py

The typed data contracts that flow between stages of the pipeline.

We grow this file one agent at a time: it currently holds the shared input
contract (the investment thesis) plus the Research crew's output. Later
slices add the models their agents produce (profiles, contacts, briefs, etc.).
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# --------------------------------------------------------------------------- #
# Shared input contract                                                       #
# --------------------------------------------------------------------------- #

class IndustryFocus(str, Enum):
    """AlphaCurrent's three target verticals."""
    B2B_SERVICES = "Business-to-Business Services"
    INDUSTRIAL_INFRASTRUCTURE = "Industrial & Infrastructure Services"
    CONSUMER_NON_DISCRETIONARY = "Non-Discretionary Consumer Services"


class OwnershipType(str, Enum):
    FOUNDER_LED = "founder-led"
    FAMILY_OWNED = "family-owned"
    PE_BACKED = "pe-backed"   # usually screened out when thesis prefers founder-led
    ANY = "any"


class InvestmentThesis(BaseModel):
    """The mandate definition — what the client is looking to acquire.

    Every agent reads from this, so it lives in the shared base.
    """

    industry: IndustryFocus
    sub_sector: str = Field(..., description="e.g. 'commercial HVAC services'")
    geography: str = Field(..., description="e.g. 'Midwest US', 'Texas'")
    revenue_min: Optional[float] = Field(None, description="USD annual revenue floor")
    revenue_max: Optional[float] = Field(None, description="USD annual revenue ceiling")
    employee_min: Optional[int] = None
    employee_max: Optional[int] = None
    ownership_preference: OwnershipType = OwnershipType.FOUNDER_LED
    notes: Optional[str] = Field(None, description="Extra screening criteria / rationale")

    def to_brief_string(self) -> str:
        """Human-readable summary used inside agent prompts."""
        parts = [
            f"Industry: {self.industry.value}",
            f"Sub-sector: {self.sub_sector}",
            f"Geography: {self.geography}",
        ]
        if self.revenue_min or self.revenue_max:
            lo = f"${self.revenue_min:,.0f}" if self.revenue_min else "no floor"
            hi = f"${self.revenue_max:,.0f}" if self.revenue_max else "no ceiling"
            parts.append(f"Revenue range: {lo} - {hi}")
        if self.employee_min or self.employee_max:
            parts.append(
                f"Employee range: {self.employee_min or '?'} - {self.employee_max or '?'}"
            )
        parts.append(f"Ownership preference: {self.ownership_preference.value}")
        if self.notes:
            parts.append(f"Notes: {self.notes}")
        return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Research crew output                                                         #
# --------------------------------------------------------------------------- #

class Candidate(BaseModel):
    """A raw company surfaced by the Research crew — not yet verified."""
    name: str
    website: Optional[str] = None
    domain: Optional[str] = Field(
        None, description="Normalized domain (e.g. 'abcmech.com') — used as the store key later"
    )
    rationale: str = Field(..., description="Why it plausibly fits the thesis")
    source_urls: list[str] = Field(default_factory=list)

    @field_validator("source_urls")
    @classmethod
    def keep_real_urls(cls, urls: list[str]) -> list[str]:
        """Drop blanks and keep only http(s) links — cheap hallucination filter."""
        return [u.strip() for u in urls if u and u.strip().startswith("http")]


class CandidateList(BaseModel):
    """Structured output of the Research crew."""
    candidates: list[Candidate] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# Example thesis (used to test crews in isolation)                            #
# --------------------------------------------------------------------------- #

EXAMPLE_THESIS = InvestmentThesis(
    industry=IndustryFocus.INDUSTRIAL_INFRASTRUCTURE,
    sub_sector="commercial HVAC and mechanical services",
    geography="Midwest US (IL, MO, IN, OH)",
    revenue_min=5_000_000,
    revenue_max=20_000_000,
    employee_min=20,
    employee_max=150,
    ownership_preference=OwnershipType.FOUNDER_LED,
    notes="Prioritize companies with recurring service contracts over project-only revenue.",
)
