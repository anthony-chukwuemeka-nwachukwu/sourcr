"""
main.py

The SourcingFlow — the CrewAI Flow that ties every crew together and is the
only place that knows the end-to-end sequencing.

Pipeline:
    begin (load thesis)
      -> research            ResearchCrew -> candidates, then route each
                             candidate via the store (skip excluded, reuse
                             fresh cache, queue the rest for research)
      -> profile_companies   ProfilerCrew   ┐  run IN PARALLEL
      -> find_contacts       ContactCrew    ┘  (both @listen(research))
      -> write_briefs        ReportingCrew (after BOTH finish, via and_),
                             reconcile against the profile, save to the store,
                             and write Markdown briefs to output/.

Run (from the src/ directory):
    cd src
    python -m sourcr.main
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from crewai.flow.flow import Flow, and_, listen, start
from dotenv import find_dotenv, load_dotenv
from pydantic import BaseModel, Field

from sourcr.crews.contact_crew.contact_crew import ContactCrew
from sourcr.crews.profiler_crew.profiler_crew import ProfilerCrew
from sourcr.crews.reporting_crew.render import render_brief_markdown
from sourcr.crews.reporting_crew.reporting_crew import ReportingCrew
from sourcr.crews.research_crew.research_crew import ResearchCrew
from sourcr.models import (
    Candidate,
    CompanyProfile,
    ContactSet,
    EXAMPLE_THESIS,
    InvestmentThesis,
    OpportunityBrief,
    PipelineStatus,
    StoredCompany,
)
from sourcr.plot import plot_pipeline_confidence
from sourcr.store import ResearchStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "output"


def _log(msg: str) -> None:
    print(f"[flow] {msg}")


def _store() -> ResearchStore:
    """Store rooted at the project's output/ dir, regardless of the cwd."""
    return ResearchStore(db_path=str(OUTPUT_DIR / "sourcr.db"))


# --------------------------------------------------------------------------- #
# Small, deterministic helpers (unit-tested in tests/test_flow_helpers.py)    #
# --------------------------------------------------------------------------- #

def domain_of(c: Candidate) -> Optional[str]:
    """Normalized domain for a candidate (its store key), or None."""
    if c.domain:
        return c.domain.strip().lower().removeprefix("www.")
    if c.website:
        raw = c.website if "//" in c.website else "//" + c.website
        host = urlparse(raw).netloc.lower().removeprefix("www.")
        return host or None
    return None


def key_of(c: Candidate) -> str:
    """Stable key for matching/storing a candidate: domain if known, else name."""
    return domain_of(c) or c.name.strip().lower()


def reconcile_brief(brief: OpportunityBrief, profile: CompanyProfile) -> list[str]:
    """Synthesis-integrity check (Flow-level, where we hold both the source
    profile and the brief): flag any brief fact citing a source the profile
    never had — a cheap anti-fabrication guard for the synthesis stage.
    """
    profile_sources = {s for f in profile.facts for s in f.sources}
    issues: list[str] = []
    for bf in brief.key_facts:
        for s in bf.sources:
            if s and s not in profile_sources:
                issues.append(f"fact cites a source absent from the profile: {s}")
    return issues


def _slug(text: str) -> str:
    return "".join(ch if ch.isalnum() else "-" for ch in text.lower()).strip("-")[:60]


def save_brief_markdown(brief: OpportunityBrief, out_dir: Path = OUTPUT_DIR) -> Path:
    """Render a brief to Markdown and write it under out_dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"brief-{_slug(brief.domain or brief.company_name)}.md"
    path.write_text(render_brief_markdown(brief), encoding="utf-8")
    return path


# --------------------------------------------------------------------------- #
# Flow state + flow                                                           #
# --------------------------------------------------------------------------- #

class SourcingState(BaseModel):
    thesis: InvestmentThesis = Field(default_factory=lambda: EXAMPLE_THESIS)
    mandate: str = "default"
    max_candidates: int = 3
    candidates: list[Candidate] = Field(default_factory=list)
    to_research: list[Candidate] = Field(default_factory=list)
    profiles: dict[str, CompanyProfile] = Field(default_factory=dict)   # keyed by key_of()
    contacts: dict[str, ContactSet] = Field(default_factory=dict)       # keyed by key_of()
    cached: list[StoredCompany] = Field(default_factory=list)
    briefs: list[OpportunityBrief] = Field(default_factory=list)


class SourcingFlow(Flow[SourcingState]):
    """Thesis -> candidates -> (cache/conflict routing) -> Profiler ∥ Contact -> briefs."""

    @start()
    def begin(self):
        _log("sourcing for thesis:\n" + self.state.thesis.to_brief_string())

    @listen(begin)
    def research(self):
        result = ResearchCrew().crew().kickoff(
            inputs={
                "thesis": self.state.thesis.to_brief_string(),
                "max_candidates": self.state.max_candidates,
            }
        )
        self.state.candidates = result.pydantic.candidates

        # Routing: decide per candidate using the store (cache + conflict register).
        store = _store()
        for c in self.state.candidates:
            k = key_of(c)
            if store.is_excluded(k):
                _log(f"skip (excluded): {c.name}")
                continue
            if store.needs_research(k):
                self.state.to_research.append(c)
            else:
                rec = store.get(k)
                if rec:
                    self.state.cached.append(rec)
                    _log(f"reuse (cached): {c.name}")
        _log(f"{len(self.state.to_research)} to research, {len(self.state.cached)} from cache")

    @listen(research)
    async def profile_companies(self):
        """Runs in parallel with find_contacts; fans out across candidates."""
        if not self.state.to_research:
            return
        results = await asyncio.gather(
            *[
                ProfilerCrew().crew().kickoff_async(
                    inputs={
                        "company_name": c.name,
                        "company_website": c.website or "",
                        "thesis": self.state.thesis.to_brief_string(),
                    }
                )
                for c in self.state.to_research
            ],
            return_exceptions=True,  # one failure must not sink the batch
        )
        for c, r in zip(self.state.to_research, results):
            if isinstance(r, Exception) or r is None:
                _log(f"profiler failed for {c.name}: {r}")
                continue
            self.state.profiles[key_of(c)] = r.pydantic

    @listen(research)
    async def find_contacts(self):
        """Runs in parallel with profile_companies; fans out across candidates."""
        if not self.state.to_research:
            return
        results = await asyncio.gather(
            *[
                ContactCrew().crew().kickoff_async(
                    inputs={"company_name": c.name, "company_website": c.website or ""}
                )
                for c in self.state.to_research
            ],
            return_exceptions=True,
        )
        for c, r in zip(self.state.to_research, results):
            if isinstance(r, Exception) or r is None:
                _log(f"contact lookup failed for {c.name}: {r}")
                continue
            self.state.contacts[key_of(c)] = r.pydantic

    @listen(and_(profile_companies, find_contacts))
    async def write_briefs(self):
        """Runs only after BOTH parallel branches finish."""
        store = _store()
        fresh = [c for c in self.state.to_research if key_of(c) in self.state.profiles]

        results = await asyncio.gather(
            *[
                ReportingCrew().crew().kickoff_async(
                    inputs={
                        "company_name": self.state.profiles[key_of(c)].name,
                        "thesis": self.state.thesis.to_brief_string(),
                        "profile": self.state.profiles[key_of(c)].model_dump_json(indent=2),
                        "contacts": (
                            self.state.contacts.get(key_of(c))
                            or ContactSet(company_name=c.name)
                        ).model_dump_json(indent=2),
                    }
                )
                for c in fresh
            ],
            return_exceptions=True,
        )

        for c, res in zip(fresh, results):
            if isinstance(res, Exception) or res is None:
                _log(f"reporting failed for {c.name}: {res}")
                continue
            brief: OpportunityBrief = res.pydantic
            profile = self.state.profiles[key_of(c)]
            for issue in reconcile_brief(brief, profile):
                _log(f"[reconcile] {brief.company_name}: {issue}")
            self.state.briefs.append(brief)
            store.save(
                StoredCompany(
                    domain=key_of(c),
                    name=profile.name,
                    mandate=self.state.mandate,
                    profile=profile,
                    contacts=self.state.contacts.get(key_of(c)),
                    brief=brief,
                    status=PipelineStatus.NEW,
                )
            )
            save_brief_markdown(brief)

        # Cached companies still belong in the output set.
        for rec in self.state.cached:
            if rec.brief:
                self.state.briefs.append(rec.brief)
                save_brief_markdown(rec.brief)

        if self.state.briefs:
            chart = plot_pipeline_confidence(
                self.state.briefs, OUTPUT_DIR / "pipeline_confidence.png"
            )
            _log(f"pipeline confidence chart: {chart}")

        _log(f"done — {len(self.state.briefs)} brief(s) written to {OUTPUT_DIR}")


def kickoff():
    """CLI entrypoint: run the full pipeline against the example thesis."""
    load_dotenv(find_dotenv())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    flow = SourcingFlow()
    flow.kickoff()

    print(f"\n=== {len(flow.state.briefs)} OPPORTUNITY BRIEF(S) ===")
    for b in flow.state.briefs:
        print(f"- {b.company_name}: {b.overall_confidence.value}")
    print(f"\nMarkdown briefs + sourcr.db written to: {OUTPUT_DIR}")


if __name__ == "__main__":
    kickoff()
