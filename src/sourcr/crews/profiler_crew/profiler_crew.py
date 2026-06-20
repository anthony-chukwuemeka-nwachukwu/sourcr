"""
profiler_crew.py

Pipeline stage 2 — the Profiler crew.

Takes ONE candidate company and goes deep: verifies ownership, size,
longevity, and recurring-revenue signals, tagging every fact with a
confidence level, then assesses fit against the thesis. Narrow and deep —
the opposite of the wide-net Research stage. Output is a CompanyProfile.

Uses Tavily (cleaner, agent-friendly results) for the verification reads.

Run standalone (from the src/ directory):
    cd src
    python -m sourcr.crews.profiler_crew.profiler_crew
"""

from typing import Any, Tuple

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import TavilySearchTool

from sourcr.llm import get_llm
from sourcr.models import CompanyProfile


def validate_profile(output) -> Tuple[bool, Any]:
    """Guardrail: re-run if the profile is structurally incomplete.

    We only assert that the agent did the work and sourced it — not whether
    the facts are true (that's what the confidence tags already express).
    Returning (False, message) makes CrewAI re-run with the message as feedback.
    """
    profile: CompanyProfile = output.pydantic
    if profile is None:
        return (False, "No profile was produced.")
    if not profile.facts:
        return (False, "No facts reported — research and verify the company before answering.")
    for f in profile.facts:
        if not f.sources:
            return (False, f"The fact '{f.fact[:60]}…' has no source URL — every fact needs one.")
    if not profile.fit_assessment.strip():
        return (False, "fit_assessment is empty — assess the company against the thesis.")
    return (True, profile)


@CrewBase
class ProfilerCrew:
    """Verifies and confidence-tags a single candidate company."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def profiler(self) -> Agent:
        return Agent(
            config=self.agents_config["profiler"],
            tools=[TavilySearchTool()],     # verification reads
            llm=get_llm("profiler"),
            verbose=True,
        )

    @task
    def profile_task(self) -> Task:
        return Task(
            config=self.tasks_config["profile_task"],
            output_pydantic=CompanyProfile,
            guardrail=validate_profile,      # re-run if the profile is incomplete
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
    # Standalone test against one hardcoded candidate.
    from dotenv import find_dotenv, load_dotenv

    from sourcr.models import EXAMPLE_THESIS

    load_dotenv(find_dotenv())

    result = ProfilerCrew().crew().kickoff(
        inputs={
            "company_name": "Enervise",
            "company_website": "https://www.enervise.com",
            "thesis": EXAMPLE_THESIS.to_brief_string(),
        }
    )

    profile: CompanyProfile = result.pydantic
    print("\n=== PROFILE ===")
    print(f"{profile.name} ({profile.domain or profile.website or 'no site'})")
    print(f"Overall confidence: {profile.overall_confidence.value}")
    print(f"Fit: {profile.fit_assessment}\n")
    for f in profile.facts:
        print(f"- [{f.confidence.value}] {f.fact}")
        for src in f.sources:
            print(f"    src: {src}")
