# WeatherGPT (SIH26068)

## What This Is

WeatherGPT is a conversational AI for weather forecasting, alerts, and climate information built for the Ministry of Earth Sciences (SIH26068). Backend is Python FastAPI + LangChain (Llama 3.3 via OpenRouter); frontend is a glassmorphism SaaS-style web app (shadcn, custom typography, full landing + chat). Data comes from the IMD API directly.

## Core Value

A user can ask in natural language ("Will it rain in Mumbai tomorrow?") and get a grounded, IMD-backed answer with a clear Green/Yellow/Orange/Red alert — via API and via a polished demo-ready UI.

## Requirements

### Validated

- ✓ FastAPI scaffold with `POST /api/chat` + `GET /health` — existing
- ✓ LangChain tool-calling agent (Llama 3.3 via OpenRouter) + mock `get_current_weather` tool — existing
- ✓ Pydantic `ChatRequest` / `ChatResponse` + `BaseSettings` config from `.env` — existing

### Active

- [ ] Real IMD data replaces mock (current weather, fallback + caching)
- [ ] Forecast + IMD alert engine (5-day, alert levels, advisories)
- [ ] Agent upgrade (multi-tool, location resolution, agri + climate knowledge)
- [ ] Frontend design system + landing + glassmorphism chat UI (shadcn, custom typography)
- [ ] Demo hardening (Docker, docs, SIH-ready deploy)

### Out of Scope

- Mobile native app — web-first for SIH demo
- OAuth / user accounts in v1 — no auth needed for demo
- Voice I/O in v1 — text chat only; voice is v2
- Hindi/multilingual in v1 — English first unless time permits

## Context

- Backend scaffold exists in `H:\weatherGPT`: `main.py`, `core/config.py`, `api/routes.py`, `schemas/chat.py`, `services/agent.py`, `tools/weather.py`.
- SIH demo context: needs to look and feel production-grade, no generic "AI slop" markers.
- Frontend explicitly requested: glassmorphism SaaS style, custom typography, full landing sections, shadcn.
- Data decision: IMD API direct in v1 (not OpenWeather proxy).

## Constraints

- **Tech stack**: Python 3.10+, FastAPI, LangChain, OpenRouter `meta-llama/llama-3.3-70b-instruct`, Pydantic — keep
- **Frontend**: shadcn-compatible (Next.js + Tailwind) with glassmorphism system, custom fonts
- **Data**: IMD-grounded answers; never invent observations; cite source
- **Demo**: Must run via `uvicorn` + frontend dev server; Docker for judging

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| IMD API direct in v1 | Authenticity for MoES/SIH judging | — Pending |
| Vertical MVP phases | Demoable slice every phase | — Pending |
| shadcn + glassmorphism + custom typography | User explicitly requested SaaS landing + chat | — Pending |
| Fine granularity (7 phases) | User asked for small phases | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-09-10 after initialization*
