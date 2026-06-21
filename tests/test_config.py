"""
Tests for runtime settings.

Deterministic — toggles the VERBOSE env var via monkeypatch, no I/O.

Run from the project root:
    python -m pytest tests/test_config.py
"""

from sourcr.config import is_verbose


def test_verbose_defaults_to_false(monkeypatch):
    monkeypatch.delenv("VERBOSE", raising=False)
    assert is_verbose() is False


def test_verbose_accepts_truthy_values(monkeypatch):
    for value in ["1", "true", "TRUE", "Yes", "on"]:
        monkeypatch.setenv("VERBOSE", value)
        assert is_verbose() is True


def test_verbose_falsey_values(monkeypatch):
    for value in ["0", "false", "no", "", "off"]:
        monkeypatch.setenv("VERBOSE", value)
        assert is_verbose() is False
