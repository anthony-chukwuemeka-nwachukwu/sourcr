"""
Tests for the research store (SQLite cache + conflict register).

Deterministic — uses a temp SQLite file via pytest's tmp_path, no network.

Run from the project root:
    python -m pytest                       # whole suite
    python -m pytest tests/test_store.py   # just this file
"""

from sourcr.models import (
    CompanyProfile,
    OverallConfidence,
    PipelineStatus,
    StoredCompany,
)
from sourcr.store import ResearchStore


def _store(tmp_path, ttl_days=30):
    return ResearchStore(db_path=str(tmp_path / "test.db"), ttl_days=ttl_days)


def test_unseen_company_needs_research(tmp_path):
    store = _store(tmp_path)
    assert store.needs_research("abcmech.com") is True
    assert store.get("abcmech.com") is None


def test_saved_company_is_cached(tmp_path):
    store = _store(tmp_path)
    store.save(StoredCompany(domain="abcmech.com", name="ABC Mechanical"))
    assert store.needs_research("abcmech.com") is False
    rec = store.get("abcmech.com")
    assert rec is not None and rec.name == "ABC Mechanical"
    assert rec.researched_at is not None


def test_stale_company_needs_reresearch(tmp_path):
    store = _store(tmp_path, ttl_days=0)  # TTL of 0 => anything is immediately stale
    store.save(StoredCompany(domain="abcmech.com", name="ABC Mechanical"))
    assert store.needs_research("abcmech.com") is True


def test_excluded_company_is_skipped(tmp_path):
    store = _store(tmp_path)
    store.save(StoredCompany(domain="abcmech.com", name="ABC Mechanical"))
    store.set_status("abcmech.com", PipelineStatus.EXCLUDED)
    assert store.is_excluded("abcmech.com") is True
    assert store.needs_research("abcmech.com") is False  # do not resurface


def test_in_pipeline_company_not_reresearched(tmp_path):
    store = _store(tmp_path, ttl_days=0)  # stale, but already in play
    store.save(StoredCompany(domain="abcmech.com", name="ABC Mechanical"))
    store.set_status("abcmech.com", PipelineStatus.IN_PIPELINE)
    assert store.needs_research("abcmech.com") is False


def test_round_trips_nested_profile(tmp_path):
    store = _store(tmp_path)
    profile = CompanyProfile(
        name="ABC", fit_assessment="fits", overall_confidence=OverallConfidence.HIGH
    )
    store.save(StoredCompany(domain="abc.com", name="ABC", profile=profile))
    rec = store.get("abc.com")
    assert rec.profile is not None
    assert rec.profile.overall_confidence == OverallConfidence.HIGH
