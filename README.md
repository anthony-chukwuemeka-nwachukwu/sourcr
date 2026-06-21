# Sourcr

A multi-agent **M&A target-sourcing pipeline** built with [CrewAI](https://docs.crewai.com/) Flows.

Given an investment thesis (industry, size, geography, ownership), Sourcr finds
candidate private companies, **verifies** them with confidence-tagged facts,
surfaces likely **decision-makers** from public sources, and writes a
decision-ready **Opportunity Brief** per company — automating the
research-intensive front end of lower-middle-market deal origination.

It is deliberately AI-forward: a CrewAI Flow orchestrates four specialized
crews, runs two of them **in parallel**, mixes LLM providers per agent, and
keeps a small knowledge base so it never re-researches (or resurfaces) a
company it already knows.

## Architecture

```
SourcingFlow (main.py)                         CrewAI Flow — owns sequencing + state
│
├─ begin            load the investment thesis
├─ research         ResearchCrew  →  candidate companies                        [Serper]
│                   route each candidate via the store:
│                     • excluded?      → skip (conflict register)
│                     • fresh in cache → reuse
│                     • new / stale    → queue for research
│
├─ profile_companies  ProfilerCrew  ┐  run IN PARALLEL                          [Tavily]
├─ find_contacts      ContactCrew   ┘  (two @listen(research) branches)         [Serper]
│
└─ write_briefs     after BOTH finish (and_):  ReportingCrew  →  Opportunity Briefs
                    reconcile vs. the profile, save to the store,
                    render Markdown + a pipeline confidence chart to output/
        ▲
   ResearchStore (SQLite): research cache + conflict register
```

## Design highlights

- **CrewAI Flow with real parallelism** — Profiler and Contact run concurrently
  (`@listen(research)` ×2, joined by `and_(...)`), fanning out across candidates
  with `asyncio.gather`.
- **Provider-agnostic, per-agent models** — each agent's model is an env var
  (`<AGENT>_MODEL` → `DEFAULT_MODEL`); the demo mixes **OpenAI** (research /
  profiling / contacts) and **Claude** (the written brief) with no code change.
- **Confidence-tagged verification** — every fact is graded
  `VERIFIED / LIKELY / UNVERIFIED / CONFLICTING`; the Profiler favors independent
  sources and treats multiple pages of one domain as a single source.
- **Self-correcting guardrails** — each crew's task re-runs (bounded retries)
  when its output is structurally bad (missing sources, duplicates, empty
  fields), feeding the reason back to the agent.
- **Knowledge base + conflict register** — SQLite store caches profiled
  companies (TTL freshness) and tracks pipeline status so the router skips
  companies already in play or passed on.
- **Synthesis-integrity reconciliation** — the Flow checks the brief's facts
  against the source profile and flags any fabricated sources.
- **Presentation in Python, not the LLM** — the Markdown tables and the
  confidence chart are rendered deterministically from structured Pydantic
  output (reproducible and unit-testable).
- **Ethical contact research** — public professional sources only (leadership
  pages, press, LinkedIn); never personal/private contact details.
- **Tested** — fast, deterministic unit tests (no API) for all guardrails,
  validators, the store, the renderer, the plot, and flow helpers, plus one
  opt-in live end-to-end test.

## Project layout

```
src/sourcr/
├── main.py              # the SourcingFlow + CLI entrypoint
├── llm.py               # provider-agnostic, per-agent LLM factory
├── store.py             # SQLite research store + conflict register
├── plot.py              # pipeline confidence chart (matplotlib)
├── models/              # Pydantic contracts: shared, research, profiler,
│                        #   contact, reporting, storage
└── crews/
    ├── research_crew/   # find candidates            (Serper)
    ├── profiler_crew/   # verify + confidence-tag    (Tavily)
    ├── contact_crew/    # decision-makers            (Serper, public only)
    └── reporting_crew/  # synthesize brief + render.py (Markdown/tables)
backend/                 # FastAPI service over the pipeline (job + polling)
frontend/                # React + Vite + Tailwind SPA (calls the backend)
tests/                   # deterministic unit tests + opt-in integration test
```

Each crew is self-contained (`agents.yaml` + `tasks.yaml` + a `@CrewBase`
class) and runnable on its own. The web layer is fully decoupled: the
`backend/` API imports `sourcr` and runs the Flow; the `frontend/` SPA only
talks to that API.

## Setup

Requires **Python 3.13** (CrewAI does not yet support 3.14).

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt          # add -r requirements-dev.txt for tests

copy .env.example .env                    # then fill in the keys below
```

Keys in `.env`: `OPENAI_API_KEY`, `SERPER_API_KEY`, `TAVILY_API_KEY`, and
`ANTHROPIC_API_KEY` (the brief agent runs on Claude). Models are configurable
via `DEFAULT_MODEL` / `<AGENT>_MODEL`.

## Running

### Web app (React + FastAPI)

Two processes — the API and the SPA (the Vite dev server proxies `/api` to the backend):

```powershell
# Terminal 1 — backend API (from the project root, venv active)
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm install      # first time only
npm run dev      # open the printed http://localhost:5173
```

Enter a thesis, run the pipeline, and view the briefs + confidence chart.

### CLI

```powershell
cd src

# Full pipeline (writes briefs + chart + sourcr.db to output/)
python -m sourcr.main

# Any crew on its own
python -m sourcr.crews.research_crew.research_crew
python -m sourcr.crews.profiler_crew.profiler_crew
python -m sourcr.crews.contact_crew.contact_crew
python -m sourcr.crews.reporting_crew.reporting_crew
```

Tip: run the full pipeline twice — the second run reuses the cached companies
and skips re-researching them (the knowledge base + router at work).

## Tests

```powershell
python -m pytest                 # fast, deterministic — no API calls
# opt-in live end-to-end test (real API): set RUN_LIVE=1 in .env, or:
$env:RUN_LIVE=1; python -m pytest tests/test_integration.py -v
```

## Output (`output/`)

- `brief-<company>.md` — Opportunity Brief per company (summary, fit, key-facts
  table, decision-makers table)
- `pipeline_confidence.png` — fact-confidence comparison across companies
- `sourcr.db` — the SQLite research store / conflict register

## Stack

CrewAI 1.14 (agents, tasks, flows) · OpenAI + Anthropic (LiteLLM) · Serper &
Tavily (search) · Pydantic (typed contracts) · SQLite · matplotlib · pytest ·
FastAPI + Uvicorn (backend) · React + Vite + TypeScript + Tailwind + Recharts
(frontend).
