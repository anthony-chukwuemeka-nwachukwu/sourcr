"""
reporting_crew.py

Pipeline stage 4 — the Reporting crew.

Pure synthesis: given a verified CompanyProfile and a ContactSet, it writes a
decision-ready OpportunityBrief. NO search tool — it must not introduce new
facts, only organize and assess what the upstream stages found. The structured
brief is then rendered to Markdown (with tables) by render.py.

Run standalone (from the src/ directory):
    cd src
    python -m sourcr.crews.reporting_crew.reporting_crew
"""

from typing import Any, Tuple

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from sourcr.llm import get_llm
from sourcr.models import OpportunityBrief


def validate_brief(output) -> Tuple[bool, Any]:
    """Guardrail: re-run if the brief is structurally incomplete.

    Structural checks only. Whether the writer preserved facts/confidence
    faithfully (no invented facts, no upgraded tags) is reconciled in the Flow,
    which holds both the source profile and the resulting brief.
    """
    brief: OpportunityBrief = output.pydantic
    if brief is None:
        return (False, "No brief was produced.")
    if not brief.summary.strip():
        return (False, "summary is empty — write a 2-4 sentence overview.")
    if not brief.fit_rationale.strip():
        return (False, "fit_rationale is empty — assess fit against the thesis.")
    if not brief.key_facts:
        return (False, "No key_facts — carry over the decision-relevant facts from the profile.")
    return (True, brief)


@CrewBase
class ReportingCrew:
    """Synthesizes verified research into an Opportunity Brief."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def brief_writer(self) -> Agent:
        return Agent(
            config=self.agents_config["brief_writer"],
            llm=get_llm("brief"),
            verbose=True,
            # No tools: synthesis only, no new research.
        )

    @task
    def write_brief_task(self) -> Task:
        return Task(
            config=self.tasks_config["write_brief_task"],
            output_pydantic=OpportunityBrief,
            guardrail=validate_brief,        # re-run if the brief is incomplete
            max_retries=3,
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )


if __name__ == "__main__":
    # Standalone test against a small hardcoded profile + contacts, so we can
    # exercise synthesis + rendering without running the upstream crews.
    from dotenv import find_dotenv, load_dotenv

    from sourcr.crews.reporting_crew.render import render_brief_markdown
    from sourcr.models import (
        CompanyProfile,
        ConfidenceLevel,
        Contact,
        ContactSet,
        EXAMPLE_THESIS,
        FactClaim,
        OverallConfidence,
    )

    load_dotenv(find_dotenv())

    profile = CompanyProfile(
        name="Enervise",
        domain="enervise.com",
        facts=[
            FactClaim(
                fact="No longer founder-led; PE-backed via Percheron/Solidaire as of Sept 2025.",
                confidence=ConfidenceLevel.VERIFIED,
                sources=[
                    "https://www.enervise.com/company-news/enervise-partners-with-solidaire",
                    "https://percheron.com/media/percheron-capital-announces-partnership-with-enervise",
                ],
            ),
            FactClaim(
                fact="Approximately 120-125 employees.",
                confidence=ConfidenceLevel.LIKELY,
                sources=["https://www.linkedin.com/company/enervise"],
            ),
            FactClaim(
                fact="Founded in 1985; 40+ years in commercial HVAC/mechanical services.",
                confidence=ConfidenceLevel.VERIFIED,
                sources=["https://www.enervise.com/about-us"],
            ),
        ],
        fit_assessment="Strong on services and size; fails ownership (now PE-backed).",
        overall_confidence=OverallConfidence.MEDIUM,
    )

    contacts = ContactSet(
        company_name="Enervise",
        domain="enervise.com",
        contacts=[
            Contact(
                name="John Blaylock",
                title="President",
                source_url="https://www.enervise.com/about-us",
                profile_url="https://www.linkedin.com/in/john-blaylock-9a92a621",
            )
        ],
    )

    result = ReportingCrew().crew().kickoff(
        inputs={
            "company_name": profile.name,
            "thesis": EXAMPLE_THESIS.to_brief_string(),
            "profile": profile.model_dump_json(indent=2),
            "contacts": contacts.model_dump_json(indent=2),
        }
    )

    brief: OpportunityBrief = result.pydantic
    print("\n=== OPPORTUNITY BRIEF (markdown) ===\n")
    print(render_brief_markdown(brief))
