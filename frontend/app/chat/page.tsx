"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Trash2 } from "lucide-react";
import { Header } from "@/components/header";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import {
  AssistantBubble,
  UserBubble,
} from "@/components/chat/message-bubble";
import { LocationBar } from "@/components/chat/location-bar";
import {
  EmptyState,
  ErrorCard,
  LoadingBubble,
  TrimNotice,
} from "@/components/chat/chat-states";
import {
  UnreachablePanel,
  UNREACHABLE_MISSING_ENV_URL,
} from "@/components/chat/unreachable-panel";
import { Composer } from "@/components/chat/composer";
import {
  ChatApiError,
  getApiBaseUrl,
  sendChatMessage,
  type AlertLevel,
} from "@/lib/chat-client";

/** History cap: 50 exchanges (100 message bubbles), in-memory only. */
const MAX_EXCHANGES = 50;
const MAX_BUBBLES = MAX_EXCHANGES * 2;

/** Exact destructive-confirm copy (UI-SPEC copywriting contract). */
const CLEAR_TITLE = "Clear conversation?";
const CLEAR_BODY =
  "This removes all messages on this screen. This cannot be undone.";

type ChatMessage =
  | { id: number; role: "user"; text: string; at: string }
  | { id: number; role: "assistant"; text: string; alertLevel?: AlertLevel };

interface FailedSend {
  message: string;
  location: string;
  detail: string;
}

interface UnreachableSend {
  message: string;
  location: string;
  url: string;
}

let nextId = 1;
function newId(): number {
  nextId += 1;
  return nextId;
}

export default function ChatPage() {
  const [location, setLocation] = useState("");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inFlight, setInFlight] = useState(false);
  const [failure, setFailure] = useState<FailedSend | null>(null);
  const [unreachable, setUnreachable] = useState<UnreachableSend | null>(null);
  const [trimmed, setTrimmed] = useState(false);
  const [confirmingClear, setConfirmingClear] = useState(false);
  const [announcement, setAnnouncement] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const sendSeqRef = useRef(0);
  const composerRef = useRef<HTMLTextAreaElement>(null);
  const headingRef = useRef<HTMLHeadingElement | null>(null);
  const listEndRef = useRef<HTMLDivElement | null>(null);
  const reduceMotionRef = useRef(false);
  // Mirror for the zero-messages-yet routing check inside the stable send().
  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  // Missing/empty env → unreachable panel on first load, zero fetch attempted.
  const apiBase = getApiBaseUrl();
  const envMissing = apiBase.length === 0;

  // Route entry: move focus to the chat H1 (D-07 focus flow).
  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true });
  }, []);

  useEffect(() => {
    reduceMotionRef.current =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }, []);

  // Auto-scroll to latest on send/receive — instant when reduced motion.
  useEffect(() => {
    listEndRef.current?.scrollIntoView({
      behavior: reduceMotionRef.current ? "auto" : "smooth",
      block: "end",
    });
  }, [messages.length, inFlight]);

  const send = useCallback(async (text: string, loc: string) => {
    const trimmedText = text.trim();
    if (!trimmedText) {
      return;
    }
    // D-08 routing: zero messages yet + network failure/timeout/missing env
    // renders the full panel; anything with history keeps inline errors.
    const hadMessages = messagesRef.current.length > 0;
    // Abort any previous in-flight request before starting a new send.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    sendSeqRef.current += 1;
    const seq = sendSeqRef.current;
    const isCurrent = () => sendSeqRef.current === seq;

    setInFlight(true);
    setFailure(null);
    setUnreachable(null);
    setAnnouncement("");

    const userMsg: ChatMessage = {
      id: newId(),
      role: "user",
      text: trimmedText,
      at: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
    setMessages((prev) => [...prev, userMsg]);
    setDraft("");

    try {
      const res = await sendChatMessage(trimmedText, loc, {
        signal: controller.signal,
      });
      if (!isCurrent()) {
        return;
      }
      const assistantMsg: ChatMessage = {
        id: newId(),
        role: "assistant",
        text: res.reply,
        alertLevel: res.alert_level,
      };
      setMessages((prev) => {
        const next = [...prev, assistantMsg];
        if (next.length > MAX_BUBBLES) {
          setTrimmed(true);
          return next.slice(next.length - MAX_BUBBLES);
        }
        return next;
      });
    } catch (err) {
      if (!isCurrent()) {
        return;
      }
      if (!hadMessages && !(err instanceof ChatApiError)) {
        // First exchange died on the wire (or env missing): full friendly
        // panel with the exact URL. Payload retained for manual Retry.
        // Focus is NOT stolen — the live region announces the panel.
        const url = getApiBaseUrl() || UNREACHABLE_MISSING_ENV_URL;
        setUnreachable({ message: trimmedText, location: loc, url });
      } else {
        // The typed message stays visible as the user bubble and is retained
        // in the failure payload so Retry re-sends the identical message —
        // nothing the user typed is lost. Location is never cleared.
        const detail =
          err instanceof ChatApiError && err.status === 422
            ? "That message couldn't be sent. Try shorter wording."
            : err instanceof Error
              ? err.message
              : "Request failed.";
        setFailure({ message: trimmedText, location: loc, detail });
      }
    } finally {
      if (isCurrent()) {
        setInFlight(false);
        // The Send button disables while in-flight, which drops focus to
        // <body> — restore it to the composer without stealing focus that
        // the user deliberately moved elsewhere mid-flight.
        if (
          typeof document !== "undefined" &&
          document.activeElement === document.body
        ) {
          composerRef.current?.focus();
        }
      }
    }
  }, []);

  const handleSend = () => {
    void send(draft, location);
  };

  const handleRetry = () => {
    if (!failure) {
      return;
    }
    void send(failure.message, failure.location);
  };

  const handleUnreachableRetry = () => {
    const pending = unreachable;
    if (!pending || inFlight) {
      return;
    }
    // Manual Retry only — re-sends the identical message + location once per
    // click (T-06-06: no auto-backoff, Send stays disabled while in-flight).
    setUnreachable(null);
    void send(pending.message, pending.location);
  };

  const handleStarterSelect = (query: string) => {
    composerRef.current?.focus();
    void send(query, location);
  };

  const handleClear = () => {
    setMessages([]);
    setFailure(null);
    setUnreachable(null);
    setTrimmed(false);
    setConfirmingClear(false);
    setAnnouncement("Conversation cleared.");
    composerRef.current?.focus();
  };

  const showEmptyPanel =
    messages.length === 0 && !inFlight && !failure && !unreachable;

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-50 focus:rounded-[10px] focus:bg-teal-700 focus:px-4 focus:py-2 focus:text-base focus:font-semibold focus:text-white"
      >
        Skip to content
      </a>
      <Header />
      <main
        id="main-content"
        aria-labelledby="chat-heading"
        className="bg-slate-50 dark:bg-slate-950"
      >
        {/* Reduced-motion backstop: static skeleton bars (D-07). */}
        <style>{`@media (prefers-reduced-motion: reduce){.chat-loading-static *{animation:none !important}}`}</style>
        <div className="mx-auto flex min-h-[calc(100vh-4rem)] w-full max-w-3xl flex-col gap-4 px-4 py-6 md:px-6">
          <div className="flex items-center justify-between gap-2">
            <h1
              ref={headingRef}
              id="chat-heading"
              tabIndex={-1}
              className="font-display text-xl font-semibold tracking-tight md:text-2xl"
            >
              Chat
            </h1>
            <div className="flex items-center gap-2">
              <Button asChild variant="ghost" className="min-h-[44px]">
                <Link href="/">Back to home</Link>
              </Button>
              <Button
                type="button"
                variant="ghost"
                onClick={() => setConfirmingClear(true)}
                aria-label="Clear conversation"
                className="h-11 w-11 text-red-600 md:h-9 md:w-auto dark:text-red-400"
              >
                <Trash2 className="h-4 w-4" aria-hidden="true" />
                <span className="hidden md:inline">Clear conversation</span>
              </Button>
            </div>
          </div>

          {confirmingClear && (
            <div
              role="alertdialog"
              aria-modal="true"
              aria-labelledby="clear-title"
              aria-describedby="clear-desc"
              className="glass-card flex flex-col gap-3 rounded-2xl p-4"
            >
              <h2
                id="clear-title"
                className="font-display text-lg font-semibold tracking-tight"
              >
                {CLEAR_TITLE}
              </h2>
              <p
                id="clear-desc"
                className="text-base leading-relaxed text-slate-600 dark:text-slate-300"
              >
                {CLEAR_BODY}
              </p>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="destructive"
                  onClick={handleClear}
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      setConfirmingClear(false);
                    }
                  }}
                  className="min-h-[44px]"
                >
                  Clear
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setConfirmingClear(false)}
                  className="min-h-[44px]"
                >
                  Cancel
                </Button>
              </div>
            </div>
          )}

          <Separator />

          <LocationBar value={location} onChange={setLocation} />

          {announcement && (
            <p role="status" className="sr-only">
              {announcement}
            </p>
          )}

          {showEmptyPanel ? (
            envMissing ? (
              <UnreachablePanel
                url={UNREACHABLE_MISSING_ENV_URL}
                onRetry={handleUnreachableRetry}
                retryDisabled={inFlight}
              />
            ) : (
              <EmptyState onSelectStarter={handleStarterSelect} />
            )
          ) : (
            <div
              role="log"
              aria-live="polite"
              aria-atomic="false"
              aria-label="Conversation"
              className="flex min-h-[40vh] flex-col gap-3 pb-4 md:gap-4"
            >
              {trimmed && <TrimNotice />}
              {messages.map((msg) =>
                msg.role === "user" ? (
                  <div key={msg.id} className="flex justify-end">
                    <UserBubble text={msg.text} timestamp={msg.at} />
                  </div>
                ) : (
                  <div key={msg.id} className="flex justify-start">
                    <AssistantBubble
                      text={msg.text}
                      alertLevel={msg.alertLevel}
                    />
                  </div>
                ),
              )}
              {inFlight && (
                <div className="chat-loading-static">
                  <LoadingBubble />
                </div>
              )}
              {failure && (
                <ErrorCard
                  detail={failure.detail}
                  onRetry={handleRetry}
                  retryDisabled={inFlight}
                />
              )}
              {unreachable && (
                <UnreachablePanel
                  url={unreachable.url}
                  onRetry={handleUnreachableRetry}
                  retryDisabled={inFlight}
                />
              )}
              <div ref={listEndRef} aria-hidden="true" />
            </div>
          )}

          <Composer
            value={draft}
            onChange={setDraft}
            onSend={handleSend}
            disabled={inFlight}
            textareaRef={composerRef}
          />
        </div>
      </main>
    </>
  );
}
