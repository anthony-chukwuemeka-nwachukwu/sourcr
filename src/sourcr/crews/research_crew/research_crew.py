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

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from sourcr.llm import get_llm
from sourcr.models import CandidateList


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
            verbose=True,
        )

    @task
    def research_task(self) -> Task:
        return Task(
            config=self.tasks_config["research_task"],
            output_pydantic=CandidateList,  # force structured output
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents,   # auto-collected from @agent methods
            tasks=self.tasks,     # auto-collected from @task methods
            process=Process.sequential,
            verbose=True,
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
