"""
Research crew output — raw, unverified candidate companies.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


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
