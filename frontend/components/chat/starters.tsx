import { Button } from "@/components/ui/button";

/**
 * Seeded starter queries — MUST byte-match the SEEDED query strings in
 * frontend/components/live-demo-teaser.tsx. Clicking one sends the exact
 * string as the user's message.
 */
export const STARTER_QUERIES = [
  "Current weather in Pune",
  "Mumbai this weekend",
  "Paddy sowing advice for Nashik",
] as const;

export const STARTER_SOURCE_NOTE =
  "Sample starters — live answers quote measured values and name their source.";

export function Starters({ onSelect }: { onSelect: (query: string) => void }) {
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {STARTER_QUERIES.map((query) => (
          <Button
            key={query}
            type="button"
            variant="outline"
            onClick={() => onSelect(query)}
            className="min-h-[44px] rounded-full"
          >
            {query}
          </Button>
        ))}
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400">
        {STARTER_SOURCE_NOTE}
      </p>
    </div>
  );
}
