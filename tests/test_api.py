"""
Tests for the FastAPI backend.

Deterministic — exercises the read endpoints via FastAPI's TestClient, no
pipeline run and no network. (The live pipeline is covered by the opt-in
integration test.)

Run from the project root:
    python -m pytest                   # whole suite
    python -m pytest tests/test_api.py # just this file
"""

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_options_lists_enum_values():
    r = client.get("/api/options")
    assert r.status_code == 200
    data = r.json()
    assert "Business-to-Business Services" in data["industries"]
    assert "founder-led" in data["ownership_types"]


def test_unknown_run_is_404():
    r = client.get("/api/runs/does-not-exist")
    assert r.status_code == 404
