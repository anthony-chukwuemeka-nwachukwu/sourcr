"""
Contact crew output — likely decision-makers from PUBLIC professional sources.

Scope is deliberately narrow: company leadership/about/team pages, press, and
publicly indexed professional profiles. No personal contact details (cell
numbers, personal/home email, home addresses) and nothing behind a login.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Contact(BaseModel):
    """A likely decision-maker at a target company."""
    name: str
    title: str = Field(..., description="Role, e.g. 'Founder & CEO', 'President', 'Owner'")
    profile_url: Optional[str] = Field(
        None,
        description=(
            "Single best PUBLIC professional profile for this person. Priority: "
            "LinkedIn > professional personal webpage > company bio/team page. "
            "Never personal/private contact info."
        ),
    )
    source_url: Optional[str] = Field(
        None, description="Public page where this person/role was found"
    )

    @field_validator("profile_url", "source_url")
    @classmethod
    def keep_real_url(cls, v: Optional[str]) -> Optional[str]:
        """Keep only an http(s) link; drop anything else."""
        if v and v.strip().startswith("http"):
            return v.strip()
        return None


class ContactSet(BaseModel):
    """Structured output of the Contact crew for one company."""
    company_name: str
    domain: Optional[str] = None
    contacts: list[Contact] = Field(default_factory=list)
