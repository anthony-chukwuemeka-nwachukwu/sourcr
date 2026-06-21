"""
Persistence contract — what the research store keeps for each company.

`mandate` is reserved so status can later be scoped per client (multi-mandate)
without a schema change; for now it defaults to 'default'.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .contact import ContactSet
from .profiler import CompanyProfile
from .reporting import OpportunityBrief


class PipelineStatus(str, Enum):
    """A company's standing in the sourcing pipeline — the conflict register."""
    NEW = "NEW"                  # researched but not yet surfaced to the client
    IN_PIPELINE = "IN_PIPELINE"  # already surfaced / under review
    CONTACTED = "CONTACTED"      # owner outreach has begun
    EXCLUDED = "EXCLUDED"        # passed on / conflicted out — do not resurface


class StoredCompany(BaseModel):
    """A cache record + conflict-register entry for one company."""
    domain: str                                   # primary key (with mandate)
    name: str
    mandate: str = "default"
    status: PipelineStatus = PipelineStatus.NEW
    profile: Optional[CompanyProfile] = None
    contacts: Optional[ContactSet] = None
    brief: Optional[OpportunityBrief] = None
    researched_at: Optional[str] = Field(
        None, description="ISO-8601 UTC timestamp of last research — drives TTL/freshness"
    )
