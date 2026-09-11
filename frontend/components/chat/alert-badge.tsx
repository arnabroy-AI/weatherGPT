import { Badge } from "@/components/ui/badge";
import type { AlertLevel } from "@/lib/chat-client";

/**
 * Data-color badge classes — MUST byte-match the badgeClass strings in
 * frontend/components/alerts-showcase.tsx (light + dark variants).
 * Never use these classes on interactive elements.
 */
export const ALERT_BADGE_CLASSES: Record<AlertLevel, string> = {
  Green:
    "border-green-600/40 bg-green-600/10 text-green-700 dark:border-green-400/40 dark:bg-green-400/10 dark:text-green-300",
  Yellow:
    "border-yellow-600/40 bg-yellow-600/10 text-yellow-700 dark:border-yellow-400/40 dark:bg-yellow-400/10 dark:text-yellow-300",
  Orange:
    "border-orange-600/40 bg-orange-600/10 text-orange-700 dark:border-orange-400/40 dark:bg-orange-400/10 dark:text-orange-300",
  Red: "border-red-600/40 bg-red-600/10 text-red-700 dark:border-red-400/40 dark:bg-red-400/10 dark:text-red-300",
};

const KNOWN_LEVELS: readonly string[] = ["Green", "Yellow", "Orange", "Red"];

function isAlertLevel(level: string | undefined): level is AlertLevel {
  return (
    typeof level === "string" &&
    (KNOWN_LEVELS as readonly string[]).includes(level)
  );
}

export function AlertBadge({ level }: { level?: string }) {
  if (!isAlertLevel(level)) {
    return null;
  }
  const text = `Alert: ${level}`;
  return (
    <Badge
      variant="outline"
      className={ALERT_BADGE_CLASSES[level]}
      aria-label={text}
    >
      {text}
    </Badge>
  );
}
