# WeatherGPT

WeatherGPT (SIH26068) — conversational AI for weather forecasting, alerts,
and climate information. English text chat over IMD-style district data.

## Prerequisites

- Docker Desktop (Engine 24+ with `docker compose`) for the primary flow.
- 10 min on the clock: clone to working chat takes under 10 minutes.
- An OpenRouter API key for live answers. No key is needed to verify the
  setup offline (health check plus fixtures path).

## Quick start (Docker, primary)

Run these four steps. Total: about 10 min (mostly image download).

```bash
git clone <repo-url> weatherGPT
cd weatherGPT
cp backend/.env.example backend/.env
# Edit backend/.env and set OPENROUTER_API_KEY to your real key.
docker compose up --build
```

Open the chat at http://localhost:3000. The API answers at
http://localhost:8000 (`GET /health` returns `{"status": "ok"}`).

Stop with `Ctrl+C`, then `docker compose down`.

Keys travel at runtime only: `compose.yaml` reads the host `backend/.env` file via
`env_file`. Keys are never baked into images — do not add them to any
Dockerfile, and do not commit `backend/.env` (it is gitignored).

## Local dev (secondary, no Docker)

Backend (http://localhost:8000) — run from the `backend/` folder:

```bash
cd backend
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY to your real key.
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Frontend (http://localhost:3000) in a second terminal:

```bash
cd frontend
npm ci
NEXT_PUBLIC_WEATHERGPT_API=http://localhost:8000 npm run dev
```

## Seeded demo queries

Type these three lines exactly as written. Each one matches a chat starter
button, so clicking the starter sends the identical string.

1. `Current weather in Pune`
2. `Mumbai this weekend`
3. `Paddy sowing advice for Nashik`

Every reply carries an IMD-style alert badge from Green to Red (Green,
Yellow, Orange, Red) naming the worst expected condition. Example: the Pune
query answers Green, the Mumbai weekend query flags Orange for Saturday.

## Live key versus offline

- Live answers need a real `OPENROUTER_API_KEY` in the host `.env`. Without
  it, chat returns HTTP 502 — setup is still proven by the steps below.
- Offline proof needs no key and no daemon:
  `python scripts/demo_smoke.py --offline` checks that the three seeded
  strings byte-match the chat starters, that `compose.yaml` parses with the
  backend plus frontend services, and probes `GET /health` as optional.
- Opt-in live check against a running backend:
  `python scripts/demo_smoke.py --live`. It posts the trio and reports
  pass/fail per query. Output never prints key values — share logs freely.

## Troubleshooting

| Symptom | Fix |
|---|---|
| `docker compose up` fails with "cannot find the file specified" on the Docker pipe | Docker daemon is down. Start Docker Desktop, wait for green status, retry. `docker compose config` validates files without a daemon; `up` needs the engine running. |
| Port already in use on 3000 or 8000 | Another app holds the port. Stop it, or change the left side of the mapping in `compose.yaml` (e.g. `"3001:3000"`), then retry. |
| `git add` fails with "Unable to create '.git/index.lock': File exists" | Stale lock plus restricted ACL. See `.planning/phases/07-demo-hardening/ENV-REPAIR-STATUS.md`: verify no git process runs, have someone with Modify rights delete `.git/index.lock`, then retry. Do not force-delete while git is running. |
| Chat answers HTTP 502 | Backend is up but the LLM key is missing or invalid. Set a real `OPENROUTER_API_KEY` in `.env` and restart (`docker compose up`). |
| Chat answers HTTP 429 with `Retry-After` | Per-IP throttle tripped (60 requests per minute default). Pause briefly and retry. |

## Scope note

v1 demo is English text chat only. Multilingual input, voice, maps, and
accounts are deferred to v2.
