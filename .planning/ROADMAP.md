# Roadmap: WeatherGPT

**Project:** WeatherGPT (SIH26068) — Conversational AI for Weather, Alerts, Climate
**Mode:** Vertical MVP — every phase is end-to-end demoable
**Granularity:** Fine — 7 small phases, 20 v1 requirements, 100% mapped ✓

| # | Phase | Goal | Requirements | Success Criteria |
|---|-------|------|--------------|------------------|
| 1 | Backend hardening | Production-ready FastAPI baseline with tests | BACK-01, BACK-02, BACK-03, BACK-04 | 4 |
| 2 | IMD live data | Real IMD current weather with cache + fallback | DATA-01, DATA-02, DATA-03 | 3 |
| 3 | Forecast + alerts | 5-day forecast + IMD alert levels + advisories | ALRT-01, ALRT-02, ALRT-03 | 3 |
| 4 | Agent upgrade | Multi-tool grounded agent: location, agri, climate | AGNT-01, AGNT-02, AGNT-03, AGNT-04 | 4 |
| 5 | Frontend shell + landing | Glassmorphism SaaS landing + design system | FRNT-01, FRNT-02 | 4 |
| 6 | Chat UI wiring | Glassmorphism chat wired to FastAPI | FRNT-03, FRNT-04 | 3 |
| 7 | Demo hardening | One-command SIH demo (Docker + docs) | DEMO-01, DEMO-02 | 2 |

### Phase 1: Backend hardening
**Goal:** Production-ready FastAPI baseline with tests
**Mode:** mvp
**Requirements:** BACK-01, BACK-02, BACK-03, BACK-04
**Success Criteria:**
1. `POST /api/chat` returns `{reply, alert_level}` for "Hi in Mumbai" via mocked LLM
2. `GET /health` returns `{status: ok}` and CORS allows the frontend origin
3. Missing `OPENROUTER_API_KEY` yields a clear 502, no traceback leak
4. `pytest` passes covering schemas, tool JSON contract, and route error paths
**Plans:** 3 plans
Plans:
- [ ] 01-01-PLAN.md — Tracer: mocked POST /api/chat end-to-end with pytest scaffold and threadpool offload
- [ ] 01-02-PLAN.md — Agent timeout/retry plus sanitized 502/500/422 error contract with tests
- [ ] 01-03-PLAN.md — Request-id middleware, INFO logging, secret-safety tests, COVERAGE.md, full-suite gate

### Phase 2: IMD live data
**Goal:** Real IMD current weather with cache + fallback
**Mode:** mvp
**Requirements:** DATA-01, DATA-02, DATA-03
**Success Criteria:**
1. "Current weather in Pune" returns real IMD values (not mock) with source cited
2. Killing the IMD endpoint still returns a degraded answer in <5s (fallback path)
3. Repeated identical queries hit cache (no duplicate upstream calls within TTL)
**Plans:** 3 plans
Plans:
- [ ] 02-01-PLAN.md — Tracer: Open-Meteo live path end-to-end for one known city with recorded fixture
- [ ] 02-02-PLAN.md — 10-min TTL cache plus outage fallback with disclosure
- [ ] 02-03-PLAN.md — Curated city map plus best-guess, secret-safety, COVERAGE.md gate

### Phase 3: Forecast + alerts
**Goal:** 5-day forecast + IMD alert levels + advisories
**Mode:** mvp
**Requirements:** ALRT-01, ALRT-02, ALRT-03
**Success Criteria:**
1. "Mumbai this weekend" returns day-wise min/max + rain chance for ≥3 days
2. A heavy-rain scenario returns `Orange`/`Red` in both the `Alert:` line and `alert_level`
3. Orange/Red replies include a 1–2 line safety advisory
**Plans:** 3 plans
Plans:
- [ ] 03-01-PLAN.md — Tracer: 5-day forecast end-to-end through new get_weather_forecast tool with worst-day Alert line
- [ ] 03-02-PLAN.md — Per-day advisories plus rollup plus minimal agent wiring
- [ ] 03-03-PLAN.md — Forecast cache, partial fallback, secret-safety tests plus COVERAGE.md gate

### Phase 4: Agent upgrade
**Goal:** Multi-tool grounded agent: location, agri, climate
**Mode:** mvp
**Requirements:** AGNT-01, AGNT-02, AGNT-03, AGNT-04
**Success Criteria:**
1. Current-weather answers quote tool values (spot-check: temp matches tool JSON)
2. "Will it rain tomorrow?" with no location triggers one clarifying question
3. "Paddy sowing advice for Nashik" returns a grounded agri advisory, not generic text
4. Simulated tool outage yields a graceful degraded message, not a 500
**Plans:** 3 plans
Plans:
- [ ] 04-01-PLAN.md — Tracer: upgraded grounding/disclosure/location prompt plus mocked-LLM harness
- [ ] 04-02-PLAN.md — Curated agri module plus live-grounded agri/climate rules and tests
- [ ] 04-03-PLAN.md — Named-gap degradation, secret-safety, Alert-regex, full-suite gate

### Phase 5: Frontend shell + landing
**Goal:** Glassmorphism SaaS landing + design system
**Mode:** mvp
**Requirements:** FRNT-01, FRNT-02
**UI hint:** yes — use `/gsd-ui-phase 5` before planning
**Success Criteria:**
1. Landing renders hero, features, live-demo teaser, alerts showcase, how-it-works, MoES strip, FAQ, footer with zero lorem ipsum
2. Custom typography + glassmorphism tokens + shadcn components render consistently (light/dark check)
3. No AI-slop markers on visual review (no purple-blue gradient cliché, no robot clipart)
4. `npm run build` passes with no type errors
**Plans:** 3 plans
Plans:
- [ ] 05-01-PLAN.md — Tracer: scaffold + tokens/fonts + header/hero, build gate
- [ ] 05-02-PLAN.md — Features, teaser, alerts showcase, how-it-works with copy gates
- [ ] 05-03-PLAN.md — MoES strip, FAQ, footer, full assembly + anti-slop + pytest guard

### Phase 6: Chat UI wiring
**Goal:** Glassmorphism chat wired to FastAPI
**Mode:** mvp
**Requirements:** FRNT-03, FRNT-04
**UI hint:** yes — use `/gsd-ui-phase 6` before planning
**Success Criteria:**
1. User sends "Rain in Delhi?" and sees an answer in <8s with Green→Red alert badge
2. Location input + empty/loading/error states all work; mobile 390px has no overlap
3. Backend base URL comes from env; pointing at a dead backend shows a friendly error, not a blank screen
**Plans:** 3 plans
Plans:
- [ ] 06-01-PLAN.md — Tracer: /chat shell + composer + one mocked round-trip, contract test, build gate
- [ ] 06-02-PLAN.md — Badges/bubbles/starters + location bar + history cap + chat states
- [ ] 06-03-PLAN.md — Unreachable panel + env + a11y + 390px dock + slop gates + pytest guard

### Phase 7: Demo hardening
**Goal:** One-command SIH demo (Docker + docs)
**Mode:** mvp
**Requirements:** DEMO-01, DEMO-02
**Success Criteria:**
1. A fresh clone follows README and reaches working chat in ≤10 min
2. `docker compose up` brings up backend + frontend with 3 seeded demo queries passing
**Plans:** 2 plans
Plans:
- [ ] 07-01-PLAN.md — Tracer: env-repair probe + CORS allowlist + per-IP throttle + ignore hygiene, pytest guard
- [ ] 07-02-PLAN.md — Dockerfiles + compose pair + README 10-min flow + seeded smoke script

### Phase 8: Climate trends (MoES gap-closure, added 2026-09-11)
**Goal:** Historical trend answers grounded in observed aggregates + climate strip on landing
**Mode:** mvp
**Requirements:** CLIM-01, CLIM-02, CLIM-03
**Success Criteria:**
1. "Was this monsoon wetter than normal in Pune?" returns past-30-day rain sum, temp means, wettest/driest days from the archive API via `get_climate_trends` — no invented numbers
2. Trend replies disclose window + non-IMD sourcing; outage degrades like the current path (stamped + disclosed)
3. Landing climate strip renders with real copy, zero lorem; `npm run build` + pytest stay green
**Plans:** 2 plans
Plans:
- [ ] 08-01-PLAN.md — Tracer: 30-day archive trend end-to-end for Pune with tool plus agent rule plus number-match test
- [ ] 08-02-PLAN.md — Trend cache/fallback/disclosure hardening plus climate strip plus full gates

---
*Roadmap created: 2026-09-10 | 7 phases | 20 requirements mapped | All v1 covered ✓*
*Updated: 2026-09-11 — Phase 8 (CLIM-01…03) added for MoES climate-information gap*

### Phase 9: Multilingual voice + chat (added 2026-09-11, Sarvam key live)
**Goal:** Chat + voice in Hindi and regional languages via Sarvam
**Mode:** mvp
**Requirements:** MULT-01, VOIC-01
**Success Criteria:**
1. User sends a Hindi (Devanagari) query and gets a Hindi grounded reply (translate in/out around the frozen English agent core)
2. Voice input (STT) + voice output (TTS) round-trip for a seeded query, mocked in CI
3. Unsupported language / STT failure degrades gracefully in the user's language where possible, English otherwise; pytest + contract gates stay green
**Plans:** 3 plans
Plans:
- [ ] 09-01-PLAN.md — Tracer: Hindi round-trip end-to-end via mocked Sarvam translate plus frozen agent core with number preservation
- [ ] 09-02-PLAN.md — Six-language capability map plus STT/TTS clients plus voice endpoints with caps and throttle
- [ ] 09-03-PLAN.md — Sarvam secret-safety plus coverage matrix with pins plus opt-in live test plus full gates

### Phase 10: Proactive push alerts (added 2026-09-11, FCM credential live)
**Goal:** Threshold watcher dispatches FCM push for Orange/Red alerts
**Mode:** mvp
**Requirements:** NOTF-01, NOTF-02
**Success Criteria:**
1. Orange/Red condition triggers an FCM dispatch (topic + token paths) with key-free logs; unit-proven with mocked FCM endpoint
2. Watcher runs on schedule, dedupes repeat alerts, never storms; pytest green
3. No secrets in code/logs; service-account file gitignored and validated at startup
**Plans:** 2 plans
Plans:
- [ ] 10-01-PLAN.md — Tracer: FCM client auth seam plus token/topic send, Orange fixture over mocked FCM
- [ ] 10-02-PLAN.md — Watcher plus registry plus alert endpoints plus dedup plus coverage matrix, full gates
