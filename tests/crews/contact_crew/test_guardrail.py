"""
Tests for the Contact crew's guardrail.

Deterministic — no LLM calls, no network. Each test feeds a hand-made
ContactSet to validate_contacts and checks it accepts a sourced roster and
re-runs on empty or unsourced ones. profile_url is optional enrichment, so its
absence must NOT trigger a re-run.

Run from the project root:
    python -m pytest                                             # whole suite
    python -m pytest tests/crews/contact_crew/test_guardrail.py  # just this file
"""

from types import SimpleNamespace

from sourcr.crews.contact_crew.contact_crew import validate_contacts
from sourcr.models import Contact, ContactSet


def _output(contacts):
    """Mimic the TaskOutput the guardrail receives (only .pydantic is used)."""
    return SimpleNamespace(pydantic=contacts)


def _contact(name="John Blaylock", title="President",
             source_url="https://enervise.com/about", profile_url=None):
    return Contact(name=name, title=title, source_url=source_url, profile_url=profile_url)


def _set(contacts=None):
    return ContactSet(
        company_name="Enervise",
        domain="enervise.com",
        contacts=[_contact()] if contacts is None else contacts,
    )


def test_accepts_sourced_roster():
    ok, result = validate_contacts(_output(_set()))
    assert ok is True
    assert isinstance(result, ContactSet)


def test_rejects_empty():
    ok, msg = validate_contacts(_output(_set(contacts=[])))
    assert ok is False
    assert "no decision-makers" in msg.lower()


def test_rejects_missing_title():
    ok, msg = validate_contacts(_output(_set([_contact(title="")])))
    assert ok is False
    assert "title" in msg.lower()


def test_rejects_missing_source():
    ok, msg = validate_contacts(_output(_set([_contact(source_url=None)])))
    assert ok is False
    assert "source" in msg.lower()


def test_profile_url_is_optional():
    # A confirmed, sourced contact with no profile link must still pass.
    ok, _ = validate_contacts(_output(_set([_contact(profile_url=None)])))
    assert ok is True
