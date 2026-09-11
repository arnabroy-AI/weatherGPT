import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Starters } from "@/components/chat/starters";

export const EMPTY_HEADING = "Start with a weather question";
export const EMPTY_BODY =
  "Ask in plain words — WeatherGPT grounds every answer and labels it Green to Red. Pick a starter below or type your own.";
export const LOADING_TEXT = "Getting your answer…";
export const DEFAULT_ERROR_TEXT =
  "Couldn't get that answer. Check your connection and try again — nothing you typed was lost.";
export const TRIM_TEXT =
  "Older messages were trimmed to keep this session light.";

export function EmptyState({
  onSelectStarter,
}: {
  onSelectStarter: (query: string) => void;
}) {
  return (
    <div className="glass-card flex flex-col gap-3 rounded-2xl p-6 text-center">
      <h2 className="font-display text-xl font-semibold tracking-tight">
        {EMPTY_HEADING}
      </h2>
      <p className="mx-auto max-w-xl text-base leading-relaxed text-slate-600 dark:text-slate-300">
        {EMPTY_BODY}
      </p>
      <div className="mx-auto">
        <Starters onSelect={onSelectStarter} />
      </div>
    </div>
  );
}

export function LoadingBubble() {
  return (
    <div className="flex justify-start">
      <div
        role="status"
        className="glass-card flex w-full max-w-full flex-col gap-2 px-4 py-3"
      >
        <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
          {LOADING_TEXT}
        </p>
        <div className="flex flex-col gap-2" aria-hidden="true">
          <div className="h-3 w-3/4 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <div className="h-3 w-full animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
          <div className="h-3 w-2/3 animate-pulse rounded bg-slate-200 dark:bg-slate-700" />
        </div>
      </div>
    </div>
  );
}

export function ErrorCard({
  detail,
  onRetry,
  retryDisabled,
}: {
  detail?: string;
  onRetry: () => void;
  retryDisabled?: boolean;
}) {
  return (
    <Card role="alert" className="border-destructive/40 p-4">
      <p className="text-sm text-slate-600 dark:text-slate-300">
        {detail && detail.length > 0 ? detail : DEFAULT_ERROR_TEXT}
      </p>
      <Button
        type="button"
        variant="outline"
        size="sm"
        onClick={onRetry}
        disabled={retryDisabled}
        className="mt-3 min-h-[44px]"
      >
        Retry
      </Button>
    </Card>
  );
}

export function TrimNotice() {
  return (
    <p
      role="status"
      className="text-center text-sm font-semibold text-slate-500 dark:text-slate-400"
    >
      {TRIM_TEXT}
    </p>
  );
}
