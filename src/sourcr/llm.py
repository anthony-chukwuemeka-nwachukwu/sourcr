"""
llm.py

One place that builds LLMs, so the pipeline stays provider-agnostic and each
agent can run on a different model.

CrewAI runs every model through LiteLLM, so a model is just a string:
    "<provider>/<model>"
e.g. "anthropic/claude-sonnet-4-6", "openai/gpt-4o", "gemini/gemini-1.5-pro".

Each agent's model is chosen by an env var, falling back to DEFAULT_MODEL:
    RESEARCH_MODEL, PROFILER_MODEL, CONTACT_MODEL, BRIEF_MODEL

To switch a provider: change the env value and set that provider's API key
(ANTHROPIC_API_KEY / OPENAI_API_KEY / GEMINI_API_KEY). No code changes needed.
"""

import os

from crewai import LLM


# Maps an agent key -> the env var that overrides just that agent's model.
_ENV_BY_AGENT = {
    "research": "RESEARCH_MODEL",
    "profiler": "PROFILER_MODEL",
    "contact": "CONTACT_MODEL",
    "brief": "BRIEF_MODEL",
}


def resolve_model(agent_key: str) -> str:
    """Resolve the model string for an agent.

    Order: <AGENT>_MODEL -> DEFAULT_MODEL (env) -> built-in DEFAULT_MODEL.
    """
    env_var = _ENV_BY_AGENT.get(agent_key)
    return (
        (os.getenv(env_var) if env_var else None)
        or os.getenv("DEFAULT_MODEL")
    )


def get_llm(agent_key: str, temperature: float = 0.2) -> LLM:
    """Return a configured CrewAI LLM for the given agent key.

    Usage in a crew:
        Agent(config=self.agents_config["profiler"], llm=get_llm("profiler"))
    """
    return LLM(model=resolve_model(agent_key), temperature=temperature)
