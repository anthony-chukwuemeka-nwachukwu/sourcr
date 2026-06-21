"""
contact_crew.py

Pipeline stage 3 (runs in PARALLEL with the Profiler) — the Contact crew.

Takes one company and surfaces its likely decision-makers (founder, owner,
CEO, president) from PUBLIC professional sources only — company leadership
pages, press, and publicly indexed profiles. No personal contact details and
nothing behind a login. Output is a ContactSet.

Uses Serper (broad discovery of team/leadership pages and public profiles).

Run standalone (from the src/ directory):
    cd src
    python -m sourcr.crews.contact_crew.contact_crew
"""

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from sourcr.llm import get_llm
from sourcr.models import ContactSet


@CrewBase
class ContactCrew:
    """Surfaces likely decision-makers for a single company, from public sources."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    @agent
    def contact_finder(self) -> Agent:
        return Agent(
            config=self.agents_config["contact_finder"],
            tools=[SerperDevTool()],
            llm=get_llm("contact"),
            verbose=True,
        )

    @task
    def find_contacts_task(self) -> Task:
        return Task(
            config=self.tasks_config["find_contacts_task"],
            output_pydantic=ContactSet,
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
    # Standalone test against one hardcoded company.
    from dotenv import find_dotenv, load_dotenv

    load_dotenv(find_dotenv())

    result = ContactCrew().crew().kickoff(
        inputs={
            "company_name": "Enervise",
            "company_website": "https://www.enervise.com",
        }
    )

    contacts: ContactSet = result.pydantic
    print("\n=== CONTACTS ===")
    print(f"{contacts.company_name} ({contacts.domain or 'no domain'})")
    for c in contacts.contacts:
        print(f"- {c.name} — {c.title}")
        if c.profile_url:
            print(f"    profile: {c.profile_url}")
        if c.source_url:
            print(f"    src: {c.source_url}")
