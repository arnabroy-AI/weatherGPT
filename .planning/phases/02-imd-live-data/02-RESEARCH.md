# Phase 2: IMD live data — Research

**Researched:** 2026-09-11
**Domain:** Current-weather data sourcing for Indian cities (IMD-direct preferred, keyless/free only)
**Confidence:** MEDIUM overall (winning-source mechanics HIGH — live-verified this session; IMD-direct path MEDIUM — gated on a human registration step)

## Summary

The team has no IMD endpoint (D-01), so this research went looking for a concrete, keyless, public IMD current-weather source the planner can implement against. The headline result: **there is no usable keyless IMD current-weather API today.** The official IMD gateway (`api.imd.gov.in`, 28 documented endpoints including a purpose-built `current_wx` API) is real and authoritative — but every endpoint returns **HTTP 401 without credentials**, and access requires portal registration (account + JWT/DEV-PROD keys + a **static public IP**), which a local SIH demo and CI cannot satisfy with the existing `.env` (D-02). The community scraper path (`city.imd.gov.in/citywx/city_weather_test.php`) returns **HTTP 403** to programmatic fetches and is HTML-scraping — brittle and out.

**Primary recommendation:** implement Phase 2 against **Open-Meteo (keyless, verified live this session for Mumbai) as the runtime live-data engine**, behind an IMD-shaped client seam, with the official `api.imd.gov.in` `current_wx` + `districtwarning` endpoints designed in as the documented IMD-direct upgrade path the moment the team completes portal registration. Open-Meteo is explicitly **non-authentic fallback-grade data** (model output, not IMD observations) and the planner must preserve that disclosure end-to-end (D-05). This is a `RESEARCH COMPLETE`, not blocked: all three Phase 2 success criteria (real values, <5s degraded fallback, cache hits) are achievable on this stack, and no locked decision is violated — D-01 asked the researcher to *recommend the concrete source*, D-02 asked that Phase 2 *work with nothing but the existing `.env`*, and only this pick satisfies both simultaneously.

## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** User has no IMD endpoint — the phase researcher must find and recommend the concrete public IMD current-weather source. Planner implements against the researcher's pick.
- **D-02:** Prefer keyless/free public IMD endpoints. `WEATHER_API_KEY` keeps required-semantics (missing key → 502 path) for any source that needs a credential, but Phase 2 must work end-to-end with nothing but the existing `.env` when the chosen source is keyless.
- **D-03:** In-memory cache, 10-minute TTL, keyed by normalized location string. No persistent/disk cache in Phase 2.
- **D-04:** On IMD outage/timeout, return the existing mock-shaped payload with `"source"` stamped as fallback (e.g. `mock-imd-fallback`) so the agent answers normally — demo never breaks.
- **D-05:** Fallback/cached-stale answers MUST disclose degraded data to the user (reply carries a short staleness/fallback note; JSON carries source + age). Silent fallback is rejected.
- **D-06:** This fallback applies to the IMD data path only. LLM errors keep Phase 1 fail-loudly behavior (honest 502/500, D-06 of Phase 1).
- **D-07:** Curated in-code map of major Indian cities/districts → whatever the chosen IMD source needs (station code / district id / lat-lon). Normalized (case/whitespace) lookup.
- **D-08:** Unmappable locations → best-guess nearest station AND disclose the guess to the user (no silent substitution, no refusal).

### Agent's Discretion

- Stale-cache serving strategy (stale-while-revalidate vs stale-only-on-error) — planner picks whichever composes cleanly with D-04/D-05; user said "whichever fits well".
- Exact fallback `source` string, cache-age field names, and curated city list size.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope. (Forecasts → Phase 3; location-clarification agent behavior → Phase 4.)

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DATA-01 | User gets current weather grounded in real IMD data for an Indian city/district | Open-Meteo live engine (keyless, live-verified) supplies real values now; `api.imd.gov.in/current_wx` schema + auth path documented for the IMD-direct upgrade; `source`/disclosure fields keep the grounding honest until then |
| DATA-02 | IMD client caches responses (~10 min TTL) and falls back to mock/last-known on outage | 10-min TTL keyed by normalized location confirmed sane (§Caching); exception taxonomy + stale-serve strategy prescribed; mock-shaped fallback payload already exists in `tools/weather.py` |
| DATA-03 | Tool contract stays `get_current_weather(location: str) -> JSON string` so the agent needs no rewrite | Field→JSON mapping table covers all 14 mock keys; agent's `alert_level` fallback parse verified in `services/agent.py:75-99`; tests mock HTTP via `httpx.MockTransport`, never live calls |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Live current-weather fetch + field mapping | API / Backend (`tools/weather.py` + small client sibling) | — | Single seam per CONTEXT; agent/routes/schemas untouched |
| 10-min TTL cache keyed by normalized location | API / Backend (in-memory dict in tool module) | — | D-03 forbids disk persistence; process-local is sufficient for demo |
| City → coordinates/station resolution | API / Backend (curated in-code map) | — | D-07; no frontend or external geocoding at runtime in CI |
| Outage fallback + staleness disclosure | API / Backend (tool JSON `source`/age fields → agent reply note) | — | D-04/D-05; LLM errors stay fail-loud per D-06 |
| Alert-level derivation | API / Backend (tool maps provider signal → Green/Yellow/Orange/Red) | — | Agent already falls back to tool JSON `alert_level` |

## Candidate Evaluation (evidence first)

### Candidate 1 — Official IMD API gateway `api.imd.gov.in` — AUTHENTIC but GATED (IMD-direct upgrade path, NOT Phase 2 runtime)

- **What it is:** IMD's official API Management Platform ("Unified gateway for real time weather observations, forecasts, warnings, and specialized bulletins") [CITED: https://api.imd.gov.in/public/index.php]. Full reference with 28 endpoints [CITED: https://api.imd.gov.in/public/api_reference.html], including exactly what Phase 2 needs: `GET /api/v1/current_wx[?id=StationId]`, `GET /api/v1/aws_data[?id=CALLSIGN][?sid=StateId]`, `GET /api/v1/districtwarning[?id=ObjId]`, `GET /api/v1/cityforecast[?id=42182]`, plus mapping endpoints (`cityforecast_mapping`, `aws_data_mapping`).
- **Live probe results (this session, via fetch):** `current_wx` → **401** [VERIFIED: live fetch 2026-09-11]; `cityforecast_mapping` → **401** [VERIFIED: live fetch 2026-09-11]; `districtwarning?id=573` → **401** [VERIFIED: live fetch 2026-09-11]. The entire gateway is uniformly credential-gated — no keyless tier exists.
- **Auth model:** portal registration (`register.php`/`login.php`) with DEV-vs-PROD keys, JWT generated from the user account, and **the calling server must have a static public IP** [CITED: https://api.imd.gov.in/public/IMD_API_Portal_User_Guide.pdf via portal search excerpt]. Government-organisation registrations require an official `gov.in`/`nic.in`-family email [CITED: https://api.imd.gov.in/public/register.php via search excerpt]. Technical-support page confirms IP-whitelisting is part of onboarding [CITED: https://mausam.imd.gov.in/responsive/apis.php].
- **Verdict:** the correct long-term IMD-direct source (authentic observations + real IMD warning colors), but it **cannot satisfy D-02** (works with existing `.env` only) or the CI/demo constraints (no static IP, human registration step). Planner designs the seam for it now; team registers in parallel; cutover is a later plan, not Phase 2.

### Candidate 2 — `city.imd.gov.in/citywx/city_weather_test.php?id=` HTML page (community scraper pattern) — REJECTED

- **What it is:** keyless city weather HTML page that a community FastAPI wrapper scrapes with BeautifulSoup (`requests.get(url)` then table-parse) [CITED: https://raw.githubusercontent.com/abin-m/Weather-api-imd/master/main-app.py]. Its station map is tiny (15 Kerala stations, e.g. Munnar=90060) [CITED: https://raw.githubusercontent.com/abin-m/Weather-api-imd/master/stations.json].
- **Live probe (this session):** `city_weather_test.php?id=90060` → **403** [VERIFIED: live fetch 2026-09-11]. Programmatic access is bot-guarded; the portal root returns only a JS shell ("India Meteorological Department") [VERIFIED: live fetch 2026-09-11].
- **Verdict:** REJECTED — 403-gated, HTML scraping (breaks on any markup change, as the scraper's own README admits), no machine contract, no Mumbai coverage in the known map. Listed under "What NOT to use".

### Candidate 3 — IMD AWS/ARG open feeds — REJECTED for Phase 2 runtime

- Gateway `aws_data` endpoint is behind the same 401 [CITED: https://api.imd.gov.in/public/api_reference.html]; the legacy `aws.imd.gov.in:8091` console is a CAPTCHA login, not a machine feed [CITED: web search result for AWS ARG LOGIN — IMD]. No keyless machine-readable feed found.
- The gateway `aws_data` sample schema (LODI ROAD/NDL: `CURR_TEMP`, `RH`, `WIND_DIRECTION`, `WIND_SPEED`, `MSLP`, `Feel Like`, `WEATHER_CODE`, lat/lon) [CITED: https://api.imd.gov.in/public/api_reference.html] is recorded below as the IMD-direct station-observation target for the future cutover.

### Candidate 4 — Open-Meteo Forecast + Geocoding APIs — WINNER for Phase 2 runtime (non-authentic, disclosed)

- **What it is:** keyless, no-registration JSON weather API aggregating national-service models; free tier explicitly usable without a key (key only required for commercial reserved resources) [CITED: https://open-meteo.com/en/docs — "apikey … Only required to commercial use"].
- **Live probes (this session):**
  - Mumbai current: `GET https://api.open-meteo.com/v1/forecast?latitude=19.076&longitude=72.8777&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,pressure_msl,wind_speed_10m,wind_direction_10m&timezone=UTC` → **200 with real values** [VERIFIED: live fetch 2026-09-11 — full sample in §Code Examples].
  - Mumbai geocode: `GET https://geocoding-api.open-meteo.com/v1/search?name=Mumbai&count=1&language=en&format=json` → **200, lat 19.07283 / lon 72.88261 / Asia/Kolkata** [VERIFIED: live fetch 2026-09-11].
- **Verdict:** only candidate that is keyless + machine-readable + live-verified today. Non-IMD model data, so every consumer-facing surface must disclose non-authenticity (D-05) until the IMD-direct cutover.

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `httpx` | 0.28.1 installed [VERIFIED: `H:/weatherGPT/requirements.txt:12` lists `httpx>=0.27`; runtime import reports 0.28.1] | Outbound HTTP to Open-Meteo (sync client inside tool; timeout + `MockTransport` in tests) | Already a project dependency — zero new installs, sync+async+mock transports in one package |
| stdlib `json`, `time.monotonic`, `logging` | Python 3.14.2 [VERIFIED: `python --version` this session] | Payload encode, TTL expiry, error logging on the existing `X-Request-ID` path | No new deps; matches Phase 1 stdlib-logging pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `pytest` | >=8.0 [VERIFIED: `H:/weatherGPT/requirements.txt:10`] | Fixture-based HTTP-mock tests | All Phase 2 IMD tests (no live calls in CI) |
| Open-Meteo Geocoding API | keyless, live-verified | **Dev-time only:** resolve curated city → lat/lon while building the D-07 map | Never at test time; optional best-effort runtime guess per D-08 at planner's discretion |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| stdlib TTL dict | `cachetools.TTLCache` | Nicer API, but a **new dependency** needing legitimacy audit + install for ~20 lines of dict logic — not worth it for a 10-min single-process cache |
| `httpx.MockTransport` | `respx` / `responses` | New dev-deps for what `httpx` ships natively; MockTransport keeps the suite at zero new packages |
| Open-Meteo runtime | `api.imd.gov.in` with registered JWT | Authentic, but needs human registration + static IP — incompatible with D-02/CI; parked as the upgrade path |

**Installation:** none — `httpx` and `pytest` are already in `requirements.txt` [VERIFIED: `H:/weatherGPT/requirements.txt:1-12`]. No `pip install` step; no Package Legitimacy Audit rows (no external package is introduced — audit table omitted by the protocol's own trigger condition, recorded here explicitly).

## Winning Source — Exact Contract

**Base URL:** `https://api.open-meteo.com` [VERIFIED: live fetch 200, 2026-09-11]
**Worked example — Mumbai current weather (fetched live this session):**

```text
GET /v1/forecast?latitude=19.076&longitude=72.8777
  &current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,pressure_msl,wind_speed_10m,wind_direction_10m,visibility
  &wind_speed_unit=kmh&timezone=UTC
```

- **Auth:** none (keyless). `WEATHER_API_KEY` stays reserved/unused on this path; its required-semantics apply only to the future IMD-direct path (D-02) [ASSUMED: no code change needed — `get_settings().WEATHER_API_KEY` is already read-and-ignored in `tools/weather.py:28-29`].
- **City → coordinates:** curated in-code map (D-07) of lat/lon pairs resolved **at plan time** via the keyless geocoding API (`GET https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json` [VERIFIED: live fetch 200]) and frozen into code — e.g. Mumbai `19.07283, 72.88261` [VERIFIED: live geocode 2026-09-11]. Normalise keys (strip/lower) before lookup.
- **Rate limits / usage policy:** free non-commercial use without a key; key only for commercial reserved resources [CITED: https://open-meteo.com/en/docs]. Exact numeric quota was not re-verified this session — treat the limit as unknown and rely on the 10-min cache to keep demo traffic to a handful of calls/hour [ASSUMED].
- **Staleness / observation frequency:** `current.time` + `interval: 900` shows ~15-min model nowcast steps (live sample); underlying models re-run every 1–6h depending on provider [CITED: https://open-meteo.com/en/docs model-updates/data-sources section]. Data is **model output, not station observation** — staleness disclosure must say "model-based, non-IMD" (D-05).
- **Outage behavior:** non-2xx / timeout / schema mismatch → D-04 mock-shaped fallback stamped with fallback `source` + age fields; LLM path untouched (D-06). Planner sets a short upstream timeout (≈5–8s) so the <5s-degraded-answer success criterion holds including cache path.

## Field→Our-JSON Mapping Table

Our key set is the 14-key mock payload [VERIFIED: `H:/weatherGPT/tools/weather.py:34-50` — `location, observed_at_utc, temperature_c, feels_like_c, humidity_pct, condition, rainfall_mm_last_24h, wind_kph, wind_direction, pressure_hpa, visibility_km, source, alert_level, advisory`]. Provider fields below are from the live sample + docs [VERIFIED: live fetch; CITED: https://open-meteo.com/en/docs].

| Our key | Provider field(s) | Transform | Notes / risk |
|---------|-------------------|-----------|--------------|
| `location` | echo of normalised input | title-case echo | Must echo user input (contract test asserts `data["location"] == "Mumbai"` [VERIFIED: `H:/weatherGPT/tests/test_weather_tool.py:13-17`]) |
| `temperature_c` | `current.temperature_2m` | direct (°C default) | Sample: 26.1 |
| `feels_like_c` | `current.apparent_temperature` | direct | Sample: 31.8 |
| `humidity_pct` | `current.relative_humidity_2m` | direct (%) | Sample: 90 |
| `condition` | `current.weather_code` (WMO) | code→text table in code (e.g. 3→"Overcast") | Sample: 3. Full WMO table is planner-owned; any unmapped code → `"Unknown (code N)"`, never a crash [ASSUMED: exact display strings are planner's choice] |
| `rainfall_mm_last_24h` | `hourly.precipitation` last 24 steps summed (`past_days=1&hourly=precipitation`) | sum, NOT `current.precipitation` (which is only the preceding-interval sum [CITED: docs]) | **Top mapping risk:** naive use of `current.precipitation` silently under-reports 24h rain. Requires the extra `hourly` param — one more query string, same request |
| `wind_kph` | `current.wind_speed_10m` with `wind_speed_unit=kmh` | direct | Sample: 4.0. Must pin `wind_speed_unit=kmh` — API default is already km/h but pin it explicitly [CITED: docs settings] |
| `wind_direction` | `current.wind_direction_10m` (degrees) | degrees→16-point compass (N, NNE, …, SW, …) | Sample: 342→"NNW". Conversion table is planner-owned [ASSUMED] |
| `pressure_hpa` | `current.pressure_msl` | direct | Sample: 1010.4 |
| `visibility_km` | `current.visibility` (metres) | ÷1000 | Hourly-var availability as `current` is documented ("every hourly variable is available as current" [CITED: docs]); **verify at implementation** — if absent, emit `None`, never 0.0 (0 means blind fog) |
| `observed_at_utc` | `current.time` with `timezone=UTC` | ISO string as returned | Sample: `"2026-09-10T19:30"`. Append nothing; keep provider string verbatim |
| `source` | constructed | e.g. `"open-meteo-live (non-IMD model data; IMD-direct pending)"` on live path; fallback stamp (e.g. `"mock-imd-fallback"`) per D-04 | Exact strings at planner discretion; non-authenticity must survive into the agent reply (D-05) |
| `alert_level` | **derived** from `weather_code` + wind/precip thresholds | conservative heuristic → Green/Yellow/Orange/Red | **Top severity risk:** Open-Meteo carries no IMD color code — this is estimation, not warning. Map severe WMO codes (95/96/99 thunderstorm, 65+ heavy rain, 71+ snow) upward, default Green; agent already consumes tool JSON `alert_level` as fallback [VERIFIED: `H:/weatherGPT/services/agent.py:75-99`] |
| `advisory` | derived from `alert_level` + `condition` | 1–2 line safety text; Orange/Red must carry do/avoid guidance (feeds ALRT-03 later) | Keep generic-safety wording; never claim IMD issuance |

**IMD-direct target schema (for the seam upgrade, from official docs — no live sample possible behind 401):** `current_wx` returns per-station `Date` (YYYY-mm-dd), `Time` (UTC), `MSLP` hPa, wind-direction **code** (0=Calm, 20=NNE, 50=NE, 70=ENE, 90=E, 110=ESE, 140=SE, 160=SSE, 180=S, 200=SSW, 230=SW, 250=WSW, 270=W, 290=WNW, 320=NW, 340=NNW, 360=N), `Wind Speed` KMPH, `Temperature` °C, `Weather Code` 01–99 (WMO present-weather), `Nebulosity` 0–8, `Humidity` %, `Last 24 hrs Rainfall` mm [CITED: https://api.imd.gov.in/public/api_reference.html §3]. `districtwarning` day-colors use **1=Red, 2=Orange, 3=Yellow, 4=Green** while nowcast colors use the **reverse** (1=Green…4=Red) [CITED: same page §§4/6] — flag as an explicit cutover pitfall. `cityforecast` station ids come from `cityforecast_mapping` (e.g. `?id=42182` pattern) [CITED: same page §1].

## Caching Guidance

- **Policy:** process-local dict `{normalised_location: (expires_monotonic, payload)}`, 10-min TTL (600s), key = `location.strip().lower()` (D-03/D-07) [ASSUMED: 600s constant; exact name planner's].
- **Why 10-min is sane:** provider steps are ~15 min (`interval: 900` in live sample) and models refresh hourly — a 10-min TTL can never serve data older than ~25 min while collapsing demo bursts to ~6 upstream calls/hour/location [VERIFIED: sample interval; CITED: docs update cadence]. Confirmed sane — no change requested.
- **Stale strategy (planner discretion):** recommend **stale-only-on-error** (serve expired entry only when upstream fails, stamped with age) — it composes with D-04/D-05 in one branch and avoids background refresh complexity in a sync tool. Must still disclose age in JSON + reply note.
- **Thread-safety:** tool runs under Phase 1 threadpool offload — guard the dict with a `threading.Lock` [ASSUMED: executor uses threadpool per CONTEXT §Integration Points; cheap insurance either way].
- **What NOT to cache:** error/fallback payloads beyond the stale-serve path (prevents error pinning); never cache the `WEATHER_API_KEY`-missing 502 path.

## Test Strategy (no live calls in CI)

- **HTTP seam:** single function (e.g. `_fetch_open_meteo(lat, lon) -> dict`) using `httpx.Client(timeout=…)` (sync — tool is sync; 0.28.1 installed [VERIFIED]) so tests can inject `httpx.MockTransport` — ships inside `httpx`, zero new deps.
- **Fixture:** record the live Mumbai sample in §Code Examples verbatim as `tests/fixtures/open_meteo_mumbai.json` (already fetched — no further network needed).
- **Cases:** (1) mapping test — fixture → all 14 contract keys with expected Mumbai values; (2) cache test — two identical `invoke()`s, assert one transport hit; (3) TTL expiry — inject expired entry, assert refetch; (4) outage test — transport raises `httpx.ConnectError`, assert fallback `source` stamp + valid JSON; (5) key-missing test — `WEATHER_API_KEY=""` still returns live path (D-02); (6) contract tests in `test_weather_tool.py` keep passing unchanged.
- **CI rule:** any test hitting `api.open-meteo.com` or `api.imd.gov.in` live fails review — `MockTransport` only.

## Architecture Patterns

### System Architecture Diagram

```text
User message (+ optional location)
        │
        ▼
POST /api/chat ──► AgentExecutor ──► get_current_weather(location)   [frozen seam]
                                                │
                              ┌─────────────────┼─────────────────┐
                              ▼                 ▼                 ▼
                      normalise +         10-min TTL          curated city→lat/lon
                      curated-map         dict hit?           map (D-07), else
                      lookup              YES → return        best-guess + disclose
                              │           (stamped w/ age)    (D-08)
                              ▼                               │
                     _fetch_open_meteo(lat,lon) ◄─────────────┘
                     httpx GET api.open-meteo.com/v1/forecast (keyless, ~5s timeout)
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              200 + schema OK      error/timeout/bad schema
                    │                   │
                    ▼                   ▼
              map → 14-key JSON   mock-shaped fallback JSON
              source=open-meteo   source=mock-imd-fallback + age
                    │                   │
                    └─────────┬─────────┘
                              ▼
              agent grounds reply + Alert line + disclosure note (D-05)
              routes unchanged (LLM errors still fail loud, D-06)
```

### Recommended Project Structure

```text
tools/
├── weather.py            # frozen tool; normalise → cache → client → map → JSON string
└── imd_client.py          # NEW small sibling: provider fetch + field mapping + WMO/compass tables
tests/
├── fixtures/
│   └── open_meteo_mumbai.json   # recorded live sample (no network in CI)
└── test_imd_client.py           # mapping / cache / outage tests via MockTransport
```

### Pattern 1: Seam-behind-frozen-tool

**What:** all provider knowledge lives in `imd_client.py`; `weather.py` keeps name/signature/JSON-string contract and owns only normalisation + cache + fallback stamping.
**When to use:** now — the IMD-direct cutover later swaps one module, and the agent never re-parses new shapes (its `alert_level` fallback already reads tool JSON [VERIFIED: `services/agent.py:83-88`]).

### Anti-Patterns to Avoid

- **Live HTTP in tests:** any test touching the real network — use `MockTransport` + recorded fixture.
- **Silent substitution:** unmappable city quietly returning Delhi/Mumbai data — D-08 requires best-guess **plus disclosure**.
- **Zero-visibility default:** missing visibility → `None`, never `0.0`.
- **Claiming IMD authenticity for model data:** `source` and reply must say non-IMD until the gateway cutover.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| HTTP + retries + mocking | `urllib` + custom fakes | `httpx` (already vendored) | Timeouts, `MockTransport`, connection pooling edge cases |
| WMO code text | ad-hoc if-chains per code | one frozen `WMO_CODE → condition` dict in `imd_client.py` | Exhaustive, testable, diffable when codes extend |
| Compass conversion | inline arithmetic | 16-wind lookup (`["N","NNE",…]` index `int((deg+11.25)/22.5)%16`) | Boundary bugs at 0/360 otherwise |
| Alert severity | invented thresholds per call site | single `derive_alert_level()` with conservative table + tests | Severity logic must be reviewable in one place; agent keyword-fallback exists downstream |
| Geocoding DB | scraping Wikipedia lat/lons | Open-Meteo geocoding at plan time, frozen into the map | Verified coordinates (Mumbai pair verified live); no runtime dependency |

**Key insight:** the only custom logic worth owning is the *mapping tables* (WMO→text, deg→compass, severity heuristic) — everything transport-shaped already exists in `httpx`/stdlib.

## Common Pitfalls

### Pitfall 1: `current.precipitation` mistaken for 24h rainfall

**What goes wrong:** 24h-rain field shows ~0mm during monsoon.
**Why it happens:** `current.precipitation` is the preceding-interval sum, not a daily accumulation [CITED: docs hourly definition].
**How to avoid:** always request `past_days=1&hourly=precipitation` and sum the last 24 steps.
**Warning signs:** `rainfall_mm_last_24h` is 0 while `weather_code` indicates rain (61–65, 80–82).

### Pitfall 2: Treating derived alert as an IMD warning

**What goes wrong:** demo claims "IMD Red alert" from model data — authenticity violation (judging criterion per REQUIREMENTS out-of-scope row).
**Why it happens:** `alert_level` key name looks authoritative.
**How to avoid:** conservative thresholds + `source` discloses non-IMD + reply note; never use the word "IMD-issued" for derived levels.

### Pitfall 3: Gateway color-code reversal on future cutover

**What goes wrong:** swapped Red/Green after migrating to `api.imd.gov.in`.
**Why it happens:** `districtwarning` uses 1=Red…4=Green while nowcast uses 1=Green…4=Red [CITED: api_reference §§4/6].
**How to avoid:** per-endpoint color maps with unit tests; recorded here so the cutover plan doesn't rediscover it.

### Pitfall 4: Timezone-naive `observed_at_utc`

**What goes wrong:** IST timestamps labeled UTC shift the observation by 5:30.
**Why it happens:** forgetting `timezone=UTC` makes `current.time` local.
**How to avoid:** pin `timezone=UTC` in the request (as in the worked example) and persist the string verbatim.

### Pitfall 5: Cache keyed on raw input

**What goes wrong:** "Mumbai", "mumbai ", "MUMBAI" triple the upstream calls and fragment stale entries.
**Why it happens:** skipping normalisation.
**How to avoid:** `key = location.strip().lower()` everywhere (D-03/D-07).

## Code Examples

### Mumbai live sample (fetched 2026-09-11 — record as fixture)

```json
// Source: live GET api.open-meteo.com/v1/forecast?latitude=19.076&longitude=72.8777&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,pressure_msl,wind_speed_10m,wind_direction_10m&timezone=UTC [VERIFIED]
{
  "latitude": 19.086115, "longitude": 72.85291, "timezone": "GMT",
  "current_units": {"temperature_2m": "°C", "relative_humidity_2m": "%", "apparent_temperature": "°C",
    "precipitation": "mm", "weather_code": "wmo code", "pressure_msl": "hPa",
    "wind_speed_10m": "km/h", "wind_direction_10m": "°"},
  "current": {"time": "2026-09-10T19:30", "interval": 900, "temperature_2m": 26.1,
    "relative_humidity_2m": 90, "apparent_temperature": 31.8, "precipitation": 0.0,
    "weather_code": 3, "pressure_msl": 1010.4, "wind_speed_10m": 4.0, "wind_direction_10m": 342}
}
```

Expected mapping of the sample → `temperature_c=26.1`, `feels_like_c=31.8`, `humidity_pct=90`, `condition≈Overcast (code 3)`, `wind_kph=4.0`, `wind_direction≈NNW (342°)`, `pressure_hpa=1010.4`, `observed_at_utc="2026-09-10T19:30"`, `alert_level=Green` (code 3, calm wind, no precip).

### Mumbai geocode (fetched 2026-09-11 — seed for the D-07 map)

```json
// Source: live GET geocoding-api.open-meteo.com/v1/search?name=Mumbai&count=1&language=en&format=json [VERIFIED]
{"results": [{"name": "Mumbai", "latitude": 19.07283, "longitude": 72.88261,
  "country": "India", "admin1": "Maharashtra", "timezone": "Asia/Kolkata", "population": 12691836}]}
```

### httpx fetch + MockTransport test skeleton

```python
# Fetch shape (tools/imd_client.py) — sync client, pinned units/timezone
import httpx
client = httpx.Client(timeout=6.0)
r = client.get("https://api.open-meteo.com/v1/forecast",
    params={"latitude": lat, "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,"
                       "weather_code,pressure_msl,wind_speed_10m,wind_direction_10m,visibility",
            "hourly": "precipitation", "past_days": 1,
            "wind_speed_unit": "kmh", "timezone": "UTC"})
r.raise_for_status()
data = r.json()

# Test shape — no new deps (httpx.MockTransport ships with httpx 0.28.1 [VERIFIED])
def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json=json.load(open("tests/fixtures/open_meteo_mumbai.json")))
transport = httpx.MockTransport(handler)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Scrape `city.imd.gov.in` HTML / `internal.imd.gov.in` pages | Official `api.imd.gov.in` gateway (28 endpoints, JWT + static-IP) | Gateway portal live (reference + user guide current) | Scrapers now 403/brittle — do not build on them |
| Any keyless IMD JSON | None exists (401 wall verified on 3 endpoints) | Confirmed 2026-09-11 | Phase 2 must run on disclosed non-IMD live data until registration |
| OpenWeather-style keyed commercial API | Open-Meteo keyless free tier | N/A | Zero-secret live data fits D-02 exactly |

**Deprecated/outdated:**
- `city.imd.gov.in/citywx/city_weather_test.php` scraping — 403 to programmatic clients, HTML contract, tiny station map. Do not use.
- `aws.imd.gov.in:8091` web login / old scraper scripts (2018-era GitHub) — CAPTCHA login, not a feed. Do not use.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `WEATHER_API_KEY=""` needs no code change (already read-and-ignored) | Winning source | Low — 3-line check at plan time |
| A2 | Open-Meteo free quota comfortably exceeds demo+CI-mocked traffic; exact number unknown | Winning source | Low — cache bounds traffic; monitor 429 and surface as outage fallback |
| A3 | `current.visibility` is requestable (hourly→current per docs); `None` fallback if absent | Mapping table | Low — explicit verify-at-implementation + None default |
| A4 | WMO display strings / compass table / severity thresholds are planner's choice | Mapping table | Medium — severity over/under-call; mitigate with conservative defaults + tests |
| A5 | Tool executes under threadpool → `threading.Lock` advised | Caching | Negligible — lock is harmless if single-threaded |
| A6 | IMD portal grants individual/student accounts (only gov-org email restriction is documented) | Candidate 1 | Medium — if registration fails, IMD-direct stays blocked; Phase 2 unaffected (Open-Meteo path independent) |

## Open Questions

1. **IMD portal registration outcome**
   - What we know: registration + JWT + static IP required; gov-org email restriction documented [CITED].
   - What's unclear: whether a student SIH team gets DEV keys without institutional IP.
   - Recommendation: assign a human to register in parallel with Phase 2; planner adds a cutover plan gated on receiving credentials — Phase 2 ships regardless.

2. **Curated city list size** (planner discretion): recommend 15–20 majors (metros + state capitals + Nashik/Pune per AGNT-03 hints) with geocoding-verified lat/lon; runtime unknown-city path = best-effort live geocode + disclosure, else disclosed nearest-map fallback.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | runtime/tests | ✓ | 3.14.2 [VERIFIED: `python --version`] | — |
| httpx | provider fetch + MockTransport tests | ✓ | 0.28.1 [VERIFIED: import] | — |
| pytest | test suite | ✓ (in requirements) | >=8.0 [VERIFIED: requirements] | — |
| api.open-meteo.com | live data (runtime only) | ✓ | 200 live 2026-09-11 | D-04 mock fallback |
| api.imd.gov.in | IMD-direct (future) | ✗ (401, needs registration) | — | Open-Meteo path (this phase) |
| city.imd.gov.in scraper | rejected alternative | ✗ (403) | — | none — rejected |

**Missing dependencies with no fallback:** none for Phase 2 scope.
**Missing with fallback:** IMD gateway credentials → Open-Meteo disclosed path.

## Validation Architecture

| Property | Value |
|----------|-------|
| Framework | pytest >=8.0 (already in requirements) |
| Config file | none detected — see Wave 0 |
| Quick run command | `pytest tests/test_imd_client.py tests/test_weather_tool.py -x -q` |
| Full suite command | `pytest -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| DATA-01 | fixture maps to all 14 keys with Mumbai values | unit | `pytest tests/test_imd_client.py::test_mapping -x` | ❌ Wave 0 |
| DATA-02a | repeat query hits cache (1 transport call) | unit | `pytest tests/test_imd_client.py::test_cache_hit -x` | ❌ Wave 0 |
| DATA-02b | outage → fallback `source` stamp, valid JSON, <5s | unit | `pytest tests/test_imd_client.py::test_outage_fallback -x` | ❌ Wave 0 |
| DATA-03 | tool name/signature/JSON-string contract unchanged | unit | `pytest tests/test_weather_tool.py -x` | ✅ exists |

### Sampling Rate

- **Per task commit:** `pytest tests/test_imd_client.py tests/test_weather_tool.py -x -q`
- **Per wave merge:** `pytest -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_imd_client.py` — mapping / cache / TTL / outage / key-missing tests
- [ ] `tests/fixtures/open_meteo_mumbai.json` — recorded live sample (in this doc)
- [ ] Framework install: none — `pytest` + `httpx` already vendored

## Security Domain

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | future only | IMD JWT stored in `WEATHER_API_KEY` via `.env`, never logged (Phase 1 redaction) |
| V3 Session Management | no | stateless tool |
| V4 Access Control | no | no user data |
| V5 Input Validation | yes | `location` normalised + length-capped before URL params; `httpx` `params=` (no string-built URLs); provider JSON parsed defensively (`.get` + type checks, never `eval`) |
| V6 Cryptography | no | TLS via `httpx` defaults; no hand-rolled crypto |

### Known Threat Patterns for this stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Upstream JSON poisoning tool output / prompt injection via fields | Tampering | Treat all provider strings as untrusted: length-cap, no HTML passthrough, log-full/send-safe per Phase 1 |
| Secret leak in error paths | Information disclosure | Never include `WEATHER_API_KEY`, full URLs, or tracebacks in user-facing errors (`sanitize_detail` pattern) |
| Cache poisoning across locations | Tampering | Key strictly by normalised location; never cache error payloads as fresh |

## Sources

### Primary (HIGH confidence)

- Live fetches 2026-09-11: Open-Meteo Mumbai current (200), Open-Meteo Mumbai geocode (200), `api.imd.gov.in` `current_wx`/`cityforecast_mapping`/`districtwarning?id=573` (401 ×3), `city_weather_test.php?id=90060` (403), `city.imd.gov.in/` (JS shell)
- `H:/weatherGPT/tools/weather.py:34-50` (14-key contract), `H:/weatherGPT/requirements.txt:1-12` (httpx/pytest vendored), `H:/weatherGPT/services/agent.py:75-99` (alert fallback), `H:/weatherGPT/tests/test_weather_tool.py:13-17` (contract test)
- Runtime: Python 3.14.2, httpx 0.28.1 (shell-verified)

### Secondary (MEDIUM confidence)

- https://api.imd.gov.in/public/api_reference.html — endpoint catalogue, `current_wx`/wind-code/weather-code/color-code tables, `aws_data` sample
- https://open-meteo.com/en/docs — keyless terms, `current=`/`hourly=` params, units, staleness cadence
- https://api.imd.gov.in/public/index.php, https://mausam.imd.gov.in/responsive/apis.php — gateway positioning, IP-whitelisting, support matrix
- https://raw.githubusercontent.com/abin-m/Weather-api-imd/master/main-app.py + stations.json — scraper pattern contents (used as negative evidence)

### Tertiary (LOW confidence)

- Portal guide/register excerpts via search (static-IP + JWT + gov-email rules) — could not render the PDF directly; confirm at registration time
- Open-Meteo exact free-tier quota — unverified numerically; design assumes nothing about it

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — zero new deps, versions shell-verified, provider live-verified
- Architecture: HIGH — single-seam change, agent integration point read in code
- Pitfalls: HIGH — each grounded in a live probe or a docs contradiction (color reversal, precip semantics)

**Research date:** 2026-09-11
**Valid until:** 2026-10-11 (stable domain; re-probe IMD 401s before any cutover plan)
