"""
research_crew.py

Pipeline stage 1 — the Research crew.

Takes an InvestmentThesis and casts a wide, disciplined net to surface
candidate private companies that plausibly fit it. Breadth over depth:
deep verification happens in a later stage. Output is a structured
CandidateList.

Run standalone (from the src/ directory):
    cd src
    python -m sourcr.crews.research_crew.research_crew
"""

from typing import Any, Tuple

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from sourcr.config import is_verbose
from sourcr.llm import get_llm
from sourcr.models import CandidateList


def validate_candidates(output) -> Tuple[bool, Any]:
    """Guardrail: checks the research output and triggers a re-run if it's bad.

    Returning (False, message) makes CrewAI re-run the task with `message` as
    feedback (up to max_retries). Returning (True, result) accepts the output.

    We only check what's cheap and deterministic here — structure, not truth.
    Verifying the companies are real is the Profiler's job downstream.
    """
    result: CandidateList = output.pydantic
    if result is None or not result.candidates:
        return (False, "No candidates returned. Search again and return at least one.")

    seen: set[str] = set()
    for c in result.candidates:
        if not c.source_urls:
            return (False, f"'{c.name}' has no source URL — every company needs one.")
        key = (c.domain or c.name).strip().lower()
        if key in seen:
            return (False, f"Duplicate company '{c.name}' — return distinct companies only.")
        seen.add(key)

    return (True, result)


@CrewBase
class ResearchCrew:
    """Identifies candidate private companies for a given investment thesis."""

    # Paths are resolved relative to this file by the @CrewBase decorator.
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def researcher(self) -> Agent:
        return Agent(
            config=self.agents_config["researcher"],
            tools=[SerperDevTool()],        # web search
            llm=get_llm("research"),        # provider-agnostic, per-agent model
            verbose=is_verbose(),
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
            output_pydantic=CandidateList,   # force structured output
            guardrail=validate_candidates,   # re-run if output is inconsistent
            max_retries=3,                   # cap the re-runs
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,   # auto-collected from @agent methods
            tasks=self.tasks,     # auto-collected from @task methods
            process=Process.sequential,
            verbose=is_verbose(),
        )


if __name__ == "__main__":
    # Standalone test against the example thesis.
    from dotenv import find_dotenv, load_dotenv

    from sourcr.models import EXAMPLE_THESIS

    load_dotenv(find_dotenv())

    result = ResearchCrew().crew().kickoff(
        inputs={
            "thesis": EXAMPLE_THESIS.to_brief_string(),
            "max_candidates": 5,
        }
    )

    candidates: CandidateList = result.pydantic
    print("\n=== CANDIDATES ===")
    for c in candidates.candidates:
        site = c.domain or c.website or "no site"
        print(f"- {c.name} ({site})\n    {c.rationale}")
        for url in c.source_urls:
            print(f"    src: {url}")
