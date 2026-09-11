# Requirements: WeatherGPT

**Defined:** 2026-09-10
**Core Value:** User asks in natural language and gets an IMD-grounded answer with a clear Green/Yellow/Orange/Red alert, via API and polished UI.

## v1 Requirements

### Backend foundation

- [ ] **BACK-01**: Backend serves `POST /api/chat` accepting `{message, location}` and returning `{reply, alert_level}`
- [ ] **BACK-02**: Backend serves `GET /health` liveness probe and permissive local-dev CORS
- [ ] **BACK-03**: Secrets load from `.env` via `BaseSettings`; missing `OPENROUTER_API_KEY` fails with a clear 502 (never hardcoded)
- [ ] **BACK-04**: Backend has pytest coverage for schemas, mock tool, and `/chat` route (mocked LLM)

### IMD data

- [ ] **DATA-01**: User gets current weather grounded in real IMD data for an Indian city/district
- [ ] **DATA-02**: IMD client caches responses (~10 min TTL) and falls back to mock/last-known on outage
- [ ] **DATA-03**: Tool contract stays `get_current_weather(location: str) -> JSON string` so the agent needs no rewrite

### Forecast + alerts

- [ ] **ALRT-01**: User can ask 3–5 day forecast ("Mumbai this weekend") and get day-wise min/max, rain chance, condition
- [ ] **ALRT-02**: Every severity-sensitive reply carries an IMD `Alert: Green|Yellow|Orange|Red` line and matching `alert_level` field
- [ ] **ALRT-03**: Orange/Red replies include a short safety advisory (what to do / avoid)

### Agent

- [ ] **AGNT-01**: Agent calls `get_current_weather` for current-weather questions and grounds answers in tool output (no invented observations)
- [ ] **AGNT-02**: Agent resolves location from message or `location` field; asks a brief follow-up when location is unknown
- [ ] **AGNT-03**: User can ask agri advisories ("paddy sowing in Nashik?") and climate summaries grounded in weather data + curated knowledge
- [ ] **AGNT-04**: Agent handles IMD/outage errors gracefully with a clear degraded-mode message

### Frontend

- [ ] **FRNT-01**: Landing page ships all sections (hero, features, live demo teaser, alerts showcase, how-it-works, MoES/IMD strip, FAQ, footer) with custom typography
- [ ] **FRNT-02**: Design system is glassmorphism SaaS + shadcn components; no generic AI-slop markers (no purple gradients, no robot clipart, no lorem ipsum)
- [ ] **FRNT-03**: User can chat in a glassmorphism chat UI (streamed or fast responses, location input, alert badge Green→Red, mobile responsive)
- [ ] **FRNT-04**: Frontend calls the FastAPI backend via env-configured base URL with loading/error/empty states

### Demo readiness

- [ ] **DEMO-01**: Full stack runs locally (`uvicorn` + frontend dev server) documented in README
- [ ] **DEMO-02**: Repo ships `Dockerfile`/`docker-compose` for one-command SIH demo + seeded demo queries

### Climate trends (MoES gap-closure, added 2026-09-11)

- [ ] **CLIM-01**: User can ask trend questions ("was this monsoon wetter than normal?") and get answers grounded in past-30-day observed aggregates (rain sum, temp means, wettest/driest days) via a new `get_climate_trends` tool — never LLM guesses
- [ ] **CLIM-02**: Trend replies disclose the observation window + non-IMD model-data sourcing, reusing the Phase 2 disclosure voice
- [ ] **CLIM-03**: Landing shows a compact climate strip (reuse showcase pattern, real copy, zero lorem) surfacing the trends capability

### Multilingual voice + chat (added 2026-09-11, Sarvam key live)

- [ ] **MULT-01**: User can chat in Hindi + 2–3 regional languages (Sarvam translate, reply in user's language)
- [ ] **VOIC-01**: User can use voice input (Sarvam STT) and voice output (Sarvam TTS) in supported languages

### Proactive push alerts (added 2026-09-11, FCM credential live)

- [ ] **NOTF-01**: Backend can dispatch FCM push for Orange/Red alerts (service-account auth, topic + token targeting, key-free logs)
- [ ] **NOTF-02**: Threshold watcher evaluates latest data on a schedule and triggers NOTF-01 dispatch (in-process scheduler, no duplicate storms)

## v2 Requirements

### Nice to have

- **MAPS-01**: User sees radar/satellite map overlays and severe-weather push alerts
- **AUTH-01**: Saved locations + alert subscriptions with accounts
- SMS/WhatsApp dispatch: needs provider key + DLT registration (deferred until credentials land)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Native mobile app | Web-first; SIH demo is browser-based |
| OAuth / accounts in v1 | No auth needed for demo value |
| Non-IMD global data in v1 | MoES/IMD authenticity is the judging criterion |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| BACK-01 | Phase 1 | Pending |
| BACK-02 | Phase 1 | Pending |
| BACK-03 | Phase 1 | Pending |
| BACK-04 | Phase 1 | Pending |
| DATA-01 | Phase 2 | Pending |
| DATA-02 | Phase 2 | Pending |
| DATA-03 | Phase 2 | Pending |
| ALRT-01 | Phase 3 | Pending |
| ALRT-02 | Phase 3 | Pending |
| ALRT-03 | Phase 3 | Pending |
| AGNT-01 | Phase 4 | Pending |
| AGNT-02 | Phase 4 | Pending |
| AGNT-03 | Phase 4 | Pending |
| AGNT-04 | Phase 4 | Pending |
| FRNT-01 | Phase 5 | Pending |
| FRNT-02 | Phase 5 | Pending |
| FRNT-03 | Phase 6 | Pending |
| FRNT-04 | Phase 6 | Pending |
| DEMO-01 | Phase 7 | Pending |
| DEMO-02 | Phase 7 | Pending |
| CLIM-01 | Phase 8 | Pending |
| CLIM-02 | Phase 8 | Pending |
| CLIM-03 | Phase 8 | Pending |
| MULT-01 | Phase 9 | Pending |
| VOIC-01 | Phase 9 | Pending |
| NOTF-01 | Phase 10 | Pending |
| NOTF-02 | Phase 10 | Pending |

**Coverage:**
- v1 requirements: 27 total
- Mapped to phases: 27
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-10*
*Last updated: 2026-09-10 after initial definition*
