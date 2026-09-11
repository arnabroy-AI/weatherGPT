import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

/** Heading for the dead-backend / bad-env panel (D-08 copy contract). */
export const UNREACHABLE_HEADING = "Can't reach the weather backend";

/**
 * URL text shown when NEXT_PUBLIC_WEATHERGPT_API is missing or empty.
 * In that state no fetch is attempted — the panel is the whole story.
 */
export const UNREACHABLE_MISSING_ENV_URL =
  "not configured (NEXT_PUBLIC_WEATHERGPT_API is empty)";

/**
 * Friendly dead-backend / bad-env panel (D-08). Always names the configured
 * URL as code text plus a manual Retry that re-sends the identical payload
 * once per click — never a blank screen, never automatic retries.
 */
export function UnreachablePanel({
  url,
  onRetry,
  retryDisabled,
}: {
  /** Exact configured backend URL, or the not-configured text. */
  url: string;
  onRetry: () => void;
  retryDisabled?: boolean;
}) {
  return (
    <Card role="alert" className="flex flex-col gap-3 p-6">
      <h2 className="font-display text-xl font-semibold tracking-tight">
        {UNREACHABLE_HEADING}
      </h2>
      <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
        WeatherGPT couldn&apos;t connect at{" "}
        <code className="rounded bg-slate-100 px-1.5 py-0.5 font-mono text-sm text-slate-800 dark:bg-slate-800 dark:text-slate-200">
          {url}
        </code>
        . Start the backend (<code>uvicorn</code>) or check{" "}
        <code>NEXT_PUBLIC_WEATHERGPT_API</code>, then retry.
      </p>
      <div>
        <Button
          type="button"
          onClick={onRetry}
          disabled={retryDisabled}
          className="min-h-[44px]"
        >
          Retry
        </Button>
      </div>
    </Card>
  );
}
