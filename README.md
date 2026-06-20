# Sourcr

A multi-agent M&A target-sourcing pipeline built with **CrewAI Flows**.

Given an investment thesis (industry, size, geography, ownership profile),
Sourcr identifies candidate private companies, then runs two agents **in
parallel** — a **Profiler** (size, ownership, fit, confidence-tagged facts)
and a **Contact Finder** (likely decision-makers from public sources) — and
merges their output into a structured **Opportunity Brief** per company.

Inspired by the front end of a lower-middle-market buy-side origination
process: thesis intake → company identification → verification → brief.

## Architecture (planned)

```
SourcingFlow                       CrewAI Flow — owns sequencing + state
│
├─ load thesis
├─ ResearchCrew        → candidate companies
│
├─ ProfilerCrew    ┐   run in parallel (independent of each other)
├─ ContactCrew     ┘
│
└─ ReportingCrew       → Opportunity Briefs (merges Profiler + Contact)
```

Each crew is its own module with its own `agents.yaml` / `tasks.yaml`, so it
can be understood, run, and tested on its own. The Flow is the only piece
that knows the order things run in.

## Stack

- [CrewAI](https://docs.crewai.com/) (v1.14.7) — agents, tasks, flows
- `SerperDevTool` — web search
- Anthropic Claude — agent LLM
- Pydantic — typed inputs/outputs between stages

## Status

🚧 Early development — building one crew at a time, committing at each stage.
