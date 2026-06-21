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

from typing import Any, Tuple

from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool

from sourcr.llm import get_llm
from sourcr.models import ContactSet


def validate_contacts(output) -> Tuple[bool, Any]:
    """Guardrail: re-run if the contact set is empty or unsourced.

    Every contact needs a role and the public source URL that confirms it.
    profile_url is optional enrichment, so it is not required here.
    """
    contacts: ContactSet = output.pydantic
    if contacts is None or not contacts.contacts:
        return (False, "No decision-makers found — check the company's leadership/about pages and retry.")
    for c in contacts.contacts:
        if not c.title.strip():
            return (False, f"Contact '{c.name}' has no title/role — every contact needs one.")
        if not c.source_url:
            return (False, f"Contact '{c.name}' has no source URL — confirm the role from a public page.")
    return (True, contacts)


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
            guardrail=validate_contacts,     # re-run if empty or unsourced
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
