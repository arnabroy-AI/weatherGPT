/**
 * Chat API client — direct client fetch to the FastAPI backend (D-01).
 *
 * Single JSON response per message (D-02, no streaming). Location value is
 * always a string — empty string when blank, never null/undefined.
 */

/**
 * Per-request timeout in milliseconds (90s). The live chain fans out to
 * multiple providers per message (agent LLM x2 + Open-Meteo + optional
 * Sarvam translate x2 for non-English), measured at ~12s English and
 * ~25-30s Hindi end-to-end — a 10s budget aborted nearly every live answer.
 */
export const CHAT_TIMEOUT_MS = 90000;

/** IMD-style alert levels returned by the backend `alert_level` field. */
export type AlertLevel = "Green" | "Yellow" | "Orange" | "Red";

/** Request payload sent to POST {base}/api/chat. */
export interface ChatRequestBody {
  message: string;
  location: string;
}

/** Successful response shape: {reply, alert_level}. */
export interface ChatResponseBody {
  reply: string;
  alert_level: AlertLevel;
}

/**
 * Error thrown for non-2xx chat responses. Carries the HTTP status so the
 * page can map 422 (validation) to inline copy while quoting 502/500
 * `detail` strings verbatim as text. The message itself is always a plain
 * string safe to render via text nodes (never HTML).
 */
export class ChatApiError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ChatApiError";
    this.status = status;
  }
}

/**
 * Read the backend base URL from the public env var. Trims whitespace;
 * returns an empty string when unset so callers can show the
 * unreachable/missing-env state instead of attempting a fetch.
 */
export function getApiBaseUrl(): string {
  const raw = process.env.NEXT_PUBLIC_WEATHERGPT_API;
  if (typeof raw !== "string") {
    return "";
  }
  return raw.trim();
}

/**
 * Send one chat message to the backend and return the single-JSON reply.
 *
 * POST {base}/api/chat with Content-Type application/json and body
 * {message, location}. Aborts via AbortController at CHAT_TIMEOUT_MS.
 * Throws on non-2xx (with backend `detail` quoted verbatim when present)
 * or on network/timeout failure.
 */
export async function sendChatMessage(
  message: string,
  location?: string,
  init?: { signal?: AbortSignal; baseUrl?: string },
): Promise<ChatResponseBody> {
  const base = (init?.baseUrl ?? getApiBaseUrl()).replace(/\/+$/, "");
  if (!base) {
    throw new Error(
      "not configured (NEXT_PUBLIC_WEATHERGPT_API is empty)",
    );
  }

  const body: ChatRequestBody = {
    message,
    location: location ?? "",
  };

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), CHAT_TIMEOUT_MS);
  const onExternalAbort = () => controller.abort();
  init?.signal?.addEventListener("abort", onExternalAbort, { once: true });

  try {
    const res = await fetch(`${base}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: init?.signal ? controller.signal : controller.signal,
    });

    const data = (await res.json()) as Partial<ChatResponseBody> & {
      detail?: unknown;
    };

    if (!res.ok) {
      const detail =
        typeof data?.detail === "string" && data.detail.length > 0
          ? data.detail
          : `Request failed with status ${res.status}.`;
      throw new ChatApiError(detail, res.status);
    }

    return {
      reply: typeof data.reply === "string" ? data.reply : "",
      alert_level: data.alert_level as AlertLevel,
    };
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new Error(
        "The request timed out. Check your connection and try again.",
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
    init?.signal?.removeEventListener("abort", onExternalAbort);
  }
}
