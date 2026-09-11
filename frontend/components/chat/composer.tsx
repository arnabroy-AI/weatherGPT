"use client";

import { useEffect, useRef, type RefObject } from "react";
import { Loader2, SendHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";

/** Cap for the 1-to-4-row auto-grow (~4 rows of 16px/1.5 + vertical padding). */
const MAX_COMPOSER_PX = 116;

/**
 * Docked accessible composer (D-06, D-07). Textarea auto-grows 1–4 rows,
 * Enter sends, Shift+Enter inserts a newline, Escape blurs. The Send button
 * shows text on desktop and is an icon-only 44px target with an aria-label
 * on mobile; while in-flight it is disabled (aria-disabled) with a spinner.
 * The bar is sticky bottom-0 with glass fill, blur, a top hairline border,
 * 12px padding plus the iOS safe-area inset.
 */
export function Composer({
  value,
  onChange,
  onSend,
  disabled,
  textareaRef,
}: {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  /** In-flight state — disables Send to make double-submit impossible. */
  disabled?: boolean;
  textareaRef?: RefObject<HTMLTextAreaElement>;
}) {
  const fallbackRef = useRef<HTMLTextAreaElement | null>(null);
  const ref = textareaRef ?? fallbackRef;

  // Auto-grow 1–4 rows as the draft changes.
  useEffect(() => {
    const el = ref.current;
    if (!el) {
      return;
    }
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, MAX_COMPOSER_PX)}px`;
  }, [ref, value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      // Plain Enter sends (guarded while in-flight); Shift+Enter keeps its
      // native newline behavior.
      e.preventDefault();
      if (!disabled) {
        onSend();
      }
    } else if (e.key === "Escape") {
      e.currentTarget.blur();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!disabled) {
      onSend();
    }
  };

  const sendable = value.trim().length > 0;

  return (
    <form
      onSubmit={handleSubmit}
      className="sticky bottom-0 flex items-end gap-2 border-t border-slate-200/60 bg-slate-50/95 p-3 pb-[calc(0.75rem+env(safe-area-inset-bottom))] backdrop-blur-sm dark:border-slate-800/60 dark:bg-slate-950/95"
    >
      <textarea
        ref={ref}
        aria-label="Type your weather question"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder="Ask about the weather…"
        className="max-h-[116px] min-h-[44px] flex-1 resize-none rounded-[10px] border border-input bg-background px-3 py-2.5 text-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:focus-visible:outline-teal-400"
      />
      <Button
        type="submit"
        aria-label="Send message"
        aria-disabled={disabled}
        disabled={disabled || !sendable}
        className="h-11 w-11 shrink-0 md:w-auto"
      >
        {disabled ? (
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
        ) : (
          <SendHorizontal className="h-4 w-4" aria-hidden="true" />
        )}
        <span className="hidden md:inline">Send message</span>
        <span className="sr-only md:hidden">Send message</span>
      </Button>
    </form>
  );
}
