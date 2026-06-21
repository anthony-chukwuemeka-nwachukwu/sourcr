"""
Data contracts for the pipeline, organized by stage.

Everything is re-exported here, so callers keep importing from one place
(`from sourcr.models import X`) no matter which submodule X lives in:

    shared    -> InvestmentThesis + enums (used by every crew)
    research  -> Candidate / CandidateList   (Research crew output)
    profiler  -> CompanyProfile / FactClaim  (Profiler crew output)
    contact   -> Contact / ContactSet        (Contact crew output)
    reporting -> OpportunityBrief             (Reporting crew output)
    storage   -> StoredCompany / PipelineStatus (what the research store keeps)
"""

from .contact import Contact, ContactSet
from .profiler import CompanyProfile, ConfidenceLevel, FactClaim, OverallConfidence
from .reporting import OpportunityBrief
from .research import Candidate, CandidateList
from .shared import EXAMPLE_THESIS, IndustryFocus, InvestmentThesis, OwnershipType
from .storage import PipelineStatus, StoredCompany

__all__ = [
    # shared
    "IndustryFocus",
    "OwnershipType",
    "InvestmentThesis",
    "EXAMPLE_THESIS",
    # research
    "Candidate",
    "CandidateList",
    # profiler
    "ConfidenceLevel",
    "OverallConfidence",
    "FactClaim",
    "CompanyProfile",
    # contact
    "Contact",
    "ContactSet",
    # reporting
    "OpportunityBrief",
    # storage
    "PipelineStatus",
    "StoredCompany",
]
