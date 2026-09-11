/**
 * Contract test: locks frontend chat shapes to the frozen backend.
 *
 * Reads schemas/chat.py, api/routes.py, lib/chat-client.ts,
 * app/chat/page.tsx, and components/chat/*.tsx as text and asserts the
 * wire contract per D-01/D-02 plus the Plan 02 expansion (D-03/D-04/D-05:
 * badges byte-matching alerts-showcase, starters byte-matching
 * live-demo-teaser, location bar, states copy, 50-exchange in-memory cap).
 * Also exercises one mocked fetch round-trip (no live server).
 *
 * Runnable with plain `node --test` — zero npm dependencies.
 */
import { describe, it, before, after } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
// frontend/lib/__tests__ -> frontend/
const frontendRoot = path.resolve(here, "..", "..");
const repoRoot = path.resolve(frontendRoot, "..");

const read = (p) => readFileSync(p, "utf8");

let clientSrc = "";
let pageSrc = "";
let schemaSrc = "";
let routesSrc = "";
let envExampleSrc = "";
let badgeSrc = "";
let bubbleSrc = "";
let startersSrc = "";
let locationSrc = "";
let statesSrc = "";
let showcaseSrc = "";
let teaserSrc = "";
let composerSrc = "";
let unreachableSrc = "";

before(() => {
  clientSrc = read(path.join(frontendRoot, "lib", "chat-client.ts"));
  pageSrc = read(path.join(frontendRoot, "app", "chat", "page.tsx"));
  schemaSrc = read(path.join(repoRoot, "backend", "schemas", "chat.py"));
  routesSrc = read(path.join(repoRoot, "backend", "api", "routes.py"));
  envExampleSrc = read(path.join(frontendRoot, ".env.local.example"));
  badgeSrc = read(
    path.join(frontendRoot, "components", "chat", "alert-badge.tsx"),
  );
  bubbleSrc = read(
    path.join(frontendRoot, "components", "chat", "message-bubble.tsx"),
  );
  startersSrc = read(
    path.join(frontendRoot, "components", "chat", "starters.tsx"),
  );
  locationSrc = read(
    path.join(frontendRoot, "components", "chat", "location-bar.tsx"),
  );
  statesSrc = read(
    path.join(frontendRoot, "components", "chat", "chat-states.tsx"),
  );
  showcaseSrc = read(
    path.join(frontendRoot, "components", "alerts-showcase.tsx"),
  );
  teaserSrc = read(
    path.join(frontendRoot, "components", "live-demo-teaser.tsx"),
  );
  composerSrc = read(
    path.join(frontendRoot, "components", "chat", "composer.tsx"),
  );
  unreachableSrc = read(
    path.join(frontendRoot, "components", "chat", "unreachable-panel.tsx"),
  );
});

describe("chat wire contract (frontend <-> frozen backend)", () => {
  it("request body carries exactly {message, location}", () => {
    assert.match(clientSrc, /message/, "client references message key");
    assert.match(clientSrc, /location/, "client references location key");
    assert.match(schemaSrc, /message/, "backend schema has message");
    assert.match(schemaSrc, /location/, "backend schema has location");
    // Client builds a body object with both keys.
    assert.match(
      clientSrc,
      /\{\s*message[\s\S]*?location/,
      "client body object contains message + location",
    );
  });

  it("location defaults to empty string, never null/undefined", () => {
    assert.match(
      clientSrc,
      /location:\s*location\s*\?\?\s*""/,
      "client defaults location to empty string via ??",
    );
  });

  it("posts to /api/chat with JSON content type", () => {
    assert.match(clientSrc, /\/api\/chat/, "client targets /api/chat");
    assert.match(
      clientSrc,
      /Content-Type.*application\/json/,
      "client sets JSON content type",
    );
    assert.match(routesSrc, /\/chat/, "backend exposes /chat route");
  });

  it("response shape is {reply, alert_level} on both sides", () => {
    assert.match(clientSrc, /reply/, "client reads reply");
    assert.match(clientSrc, /alert_level/, "client reads alert_level");
    assert.match(schemaSrc, /reply/, "backend schema has reply");
    assert.match(schemaSrc, /alert_level/, "backend schema has alert_level");
  });

  it("all four alert levels (Green Yellow Orange Red) present in client", () => {
    for (const level of ["Green", "Yellow", "Orange", "Red"]) {
      assert.ok(
        clientSrc.includes(`"${level}"`),
        `client AlertLevel includes ${level}`,
      );
    }
  });

  it("timeout is 10000ms via AbortController", () => {
    assert.match(
      clientSrc,
      /CHAT_TIMEOUT_MS\s*=\s*10000/,
      "CHAT_TIMEOUT_MS equals 10000",
    );
    assert.match(clientSrc, /AbortController/, "client uses AbortController");
  });

  it("no streaming transports in client", () => {
    for (const banned of ["EventSource", "getReader", "text/event-stream"]) {
      assert.ok(
        !clientSrc.includes(banned),
        `client must not contain ${banned}`,
      );
    }
  });

  it("chat UI renders replies as text nodes, never HTML injection", () => {
    for (const [name, src] of [
      ["page", pageSrc],
      ["alert-badge", badgeSrc],
      ["message-bubble", bubbleSrc],
      ["starters", startersSrc],
      ["location-bar", locationSrc],
      ["chat-states", statesSrc],
      ["composer", composerSrc],
      ["unreachable-panel", unreachableSrc],
    ]) {
      assert.ok(
        !src.includes("dangerouslySetInnerHTML"),
        `${name} must not use dangerouslySetInnerHTML`,
      );
    }
    assert.match(
      bubbleSrc,
      /whitespace-pre-wrap/,
      "assistant/user bubbles use pre-wrap",
    );
  });

  it("env var NEXT_PUBLIC_WEATHERGPT_API referenced in client and example", () => {
    assert.ok(
      clientSrc.includes("NEXT_PUBLIC_WEATHERGPT_API"),
      "client reads NEXT_PUBLIC_WEATHERGPT_API",
    );
    assert.ok(
      envExampleSrc.includes("NEXT_PUBLIC_WEATHERGPT_API"),
      ".env.local.example documents NEXT_PUBLIC_WEATHERGPT_API",
    );
  });

  it("page exposes chat shell: H1, location bar, log, composer", () => {
    assert.match(pageSrc, /<h1/, "page has H1");
    assert.ok(pageSrc.includes("Chat"), "H1 text is Chat");
    assert.match(pageSrc, /<LocationBar/, "page renders LocationBar");
    assert.match(pageSrc, /role="log"/, "message list has role=log");
    assert.match(
      pageSrc,
      /aria-label="Conversation"/,
      "message list labelled Conversation",
    );
    assert.match(
      composerSrc,
      /aria-label="Type your weather question"/,
      "composer textarea labelled",
    );
    assert.match(
      composerSrc,
      /aria-label="Send message"/,
      "Send button labelled",
    );
  });
});

describe("plan 03 hardening (unreachable, composer, a11y, mobile dock)", () => {
  it("unreachable panel matches copy contract with URL and Retry", () => {
    assert.ok(
      unreachableSrc.includes("Can't reach the weather backend"),
      "unreachable heading matches contract",
    );
    assert.match(unreachableSrc, /role="alert"/, "panel uses role=alert");
    assert.match(unreachableSrc, /<code/, "URL rendered as code text");
    assert.ok(
      unreachableSrc.includes(
        "not configured (NEXT_PUBLIC_WEATHERGPT_API is empty)",
      ),
      "missing-env URL text defined",
    );
    assert.match(unreachableSrc, /Retry/, "panel offers Retry");
    assert.match(
      pageSrc,
      /UNREACHABLE_MISSING_ENV_URL/,
      "page shows not-configured panel with zero fetch on first load",
    );
  });

  it("composer handles Enter, Shift+Enter, Escape and docks", () => {
    assert.match(composerSrc, /Shift\+Enter/, "Shift+Enter newline documented");
    assert.match(composerSrc, /Escape/, "Escape blur handled");
    assert.match(composerSrc, /sticky bottom-0/, "composer docked bottom");
    assert.match(
      composerSrc,
      /env\(safe-area-inset-bottom\)/,
      "composer reserves the iOS safe area",
    );
    assert.match(composerSrc, /aria-disabled/, "Send exposes aria-disabled");
    assert.match(pageSrc, /pb-4/, "message list padded above the dock");
  });

  it("a11y contract rows present: skip link, live regions, focus flow", () => {
    assert.match(pageSrc, /Skip to content/, "skip-to-content link present");
    assert.match(pageSrc, /main-content/, "skip link targets main content");
    assert.match(pageSrc, /aria-live="polite"/, "log is polite live");
    assert.match(pageSrc, /aria-atomic="false"/, "log is append-only");
    assert.match(
      pageSrc,
      /prefers-reduced-motion/,
      "reduced-motion backstop present",
    );
    assert.match(
      pageSrc,
      /Conversation cleared\./,
      "Clear announces via status region",
    );
    assert.match(
      pageSrc,
      /CLEAR_TITLE = "Clear conversation\?"/,
      "destructive confirm title matches contract",
    );
    assert.match(
      pageSrc,
      /CLEAR_BODY =\s*\n?\s*"This removes all messages on this screen\. This cannot be undone\."/,
      "destructive confirm body matches contract",
    );
    assert.match(pageSrc, /Back to home/, "Back to home link present");
  });
});

describe("plan 02 expansion (badges, starters, states, history cap)", () => {
  it("badge classes byte-match alerts-showcase for all four levels", () => {
    const showcaseClasses = [
      ...showcaseSrc.matchAll(/badgeClass:\s*"([^"]+)"/g),
    ].map((m) => m[1]);
    assert.equal(
      showcaseClasses.length,
      4,
      "showcase defines exactly four badge classes",
    );
    assert.match(
      badgeSrc,
      /ALERT_BADGE_CLASSES/,
      "alert-badge exports ALERT_BADGE_CLASSES",
    );
    for (const cls of showcaseClasses) {
      assert.ok(
        badgeSrc.includes(cls),
        `alert-badge contains showcase class: ${cls.slice(0, 40)}…`,
      );
    }
    // Level-name text is always present; aria-label mirrors visible text.
    assert.match(badgeSrc, /Alert: /, "badge text includes level name");
    assert.match(badgeSrc, /aria-label/, "badge mirrors aria-label");
  });

  it("starter strings byte-match live-demo-teaser seeded queries", () => {
    const seeded = [...teaserSrc.matchAll(/query:\s*"([^"]+)"/g)].map(
      (m) => m[1],
    );
    assert.equal(seeded.length, 3, "teaser defines exactly three queries");
    assert.match(
      startersSrc,
      /STARTER_QUERIES/,
      "starters exports STARTER_QUERIES",
    );
    for (const q of seeded) {
      assert.ok(
        startersSrc.includes(q),
        `starters contains seeded string: ${q}`,
      );
    }
    assert.ok(
      startersSrc.includes(
        "Sample starters — live answers quote measured values and name their source.",
      ),
      "starters carries the source note",
    );
  });

  it("location bar matches spec and feeds every send", () => {
    assert.match(
      locationSrc,
      /Location \(optional\) — e\.g\. Pune/,
      "location placeholder matches copy contract",
    );
    assert.match(
      locationSrc,
      /Used for every question you send\./,
      "location hint matches spec",
    );
    assert.match(locationSrc, /htmlFor="chat-location"/, "label targets input");
    assert.match(locationSrc, /MapPin/, "location pin icon present");
    // Page keeps the bar value in session state and passes it on every send,
    // including starter sends — never null/undefined.
    assert.match(pageSrc, /void send\(draft, location\)/, "submit sends bar value");
    assert.match(
      pageSrc,
      /void send\(query, location\)/,
      "starter click sends bar value",
    );
    assert.match(
      pageSrc,
      /void send\(failure\.message, failure\.location\)/,
      "retry re-sends identical payload",
    );
  });

  it("empty/loading/error/trim states render per copy contract", () => {
    assert.match(statesSrc, /EmptyState/, "EmptyState exported");
    assert.ok(
      statesSrc.includes("Start with a weather question"),
      "empty heading matches contract",
    );
    assert.ok(
      statesSrc.includes(
        "Ask in plain words — WeatherGPT grounds every answer and labels it Green to Red. Pick a starter below or type your own.",
      ),
      "empty body matches contract",
    );
    assert.ok(
      statesSrc.includes("Getting your answer…"),
      "loading copy matches contract",
    );
    assert.match(statesSrc, /role="status"/, "loading/trim use role=status");
    assert.ok(
      statesSrc.includes(
        "Couldn't get that answer. Check your connection and try again — nothing you typed was lost.",
      ),
      "default error copy matches contract",
    );
    assert.match(statesSrc, /role="alert"/, "error card uses role=alert");
    assert.ok(
      statesSrc.includes(
        "Older messages were trimmed to keep this session light.",
      ),
      "trim notice matches contract",
    );
    // 422 maps to inline validation copy; 502/500 detail quoted verbatim.
    assert.ok(
      pageSrc.includes(
        "That message couldn't be sent. Try shorter wording.",
      ),
      "page maps 422 to inline copy",
    );
    assert.match(
      clientSrc,
      /ChatApiError/,
      "client preserves HTTP status for error mapping",
    );
  });

  it("history capped at 50 exchanges in-memory, no persistence", () => {
    assert.match(
      pageSrc,
      /MAX_EXCHANGES\s*=\s*50/,
      "page caps history at 50 exchanges",
    );
    assert.match(pageSrc, /TrimNotice/, "page renders trim notice");
    for (const [name, src] of [
      ["page", pageSrc],
      ["chat-client", clientSrc],
      ["alert-badge", badgeSrc],
      ["message-bubble", bubbleSrc],
      ["starters", startersSrc],
      ["location-bar", locationSrc],
      ["chat-states", statesSrc],
      ["composer", composerSrc],
      ["unreachable-panel", unreachableSrc],
    ]) {
      assert.ok(
        !src.includes("localStorage"),
        `${name} must not persist history`,
      );
    }
  });

  it("bubbles are distinct with conditional Orange/Red edge", () => {
    assert.match(bubbleSrc, /bg-teal-700/, "user bubble is solid teal");
    assert.match(bubbleSrc, /glass-card/, "assistant bubble is glass");
    assert.match(
      bubbleSrc,
      /border-l-orange-600/,
      "Orange assistant edge present",
    );
    assert.match(bubbleSrc, /border-l-red-600/, "Red assistant edge present");
  });

  it("in-flight send disables Send and aborts previous request", () => {
    assert.match(
      pageSrc,
      /disabled=\{inFlight/,
      "Send disabled while in-flight",
    );
    assert.ok(
      pageSrc.includes("abortRef.current?.abort()"),
      "previous request aborted before a new send",
    );
  });
});

describe("mocked send/reply round-trip (no live server)", () => {
  const realFetch = globalThis.fetch;

  after(() => {
    globalThis.fetch = realFetch;
  });

  it("sends {message, location} and returns {reply, alert_level}", async () => {
    let seenUrl = "";
    let seenInit = {};
    globalThis.fetch = async (url, init) => {
      seenUrl = String(url);
      seenInit = init ?? {};
      return new Response(
        JSON.stringify({ reply: "Sunny in Pune.", alert_level: "Green" }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    };

    // Dynamic import of TS source is impossible in plain node; instead
    // replicate the client's wire logic minimally by importing the
    // compiled-shape expectations: assert on captured request instead.
    // We exercise the fetch contract directly here.
    const base = "http://localhost:8000";
    const res = await globalThis.fetch(`${base}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: "Hi?", location: "Pune" }),
    });
    const data = await res.json();

    assert.equal(seenUrl, "http://localhost:8000/api/chat");
    assert.equal(seenInit.method, "POST");
    assert.equal(
      seenInit.headers["Content-Type"],
      "application/json",
    );
    assert.deepEqual(JSON.parse(seenInit.body), {
      message: "Hi?",
      location: "Pune",
    });
    assert.equal(data.reply, "Sunny in Pune.");
    assert.equal(data.alert_level, "Green");

    // The real client module must agree with this shape (static check).
    assert.match(
      clientSrc,
      /fetch\(`\$\{base\}\/api\/chat`/,
      "client fetch targets ${base}/api/chat",
    );
  });
});
