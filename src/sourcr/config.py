"""
config.py

Small runtime settings read from the environment.

is_verbose() is read when a crew is *constructed* (not at import), so it
reflects .env — which is loaded by the entrypoints (main/backend/standalone)
before any crew is built.
"""

import os

_TRUTHY = {"1", "true", "yes", "on"}


def is_verbose() -> bool:
    """Whether crews/agents should log their reasoning (VERBOSE in .env).

    Defaults to off for clean runs; set VERBOSE=true to see the agents work.
    """
    return os.getenv("VERBOSE", "false").strip().lower() in _TRUTHY
