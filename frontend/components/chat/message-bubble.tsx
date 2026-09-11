import { Card } from "@/components/ui/card";
import type { AlertLevel } from "@/lib/chat-client";
import { AlertBadge } from "@/components/chat/alert-badge";

/** Right-aligned solid-teal user bubble with a muted timestamp. */
export function UserBubble({
  text,
  timestamp,
}: {
  text: string;
  timestamp?: string;
}) {
  return (
    <div className="flex flex-col items-end">
      <div className="max-w-[85%] rounded-2xl rounded-br-md bg-teal-700 px-4 py-3 text-white dark:bg-teal-400 dark:text-slate-950">
        <p className="whitespace-pre-wrap text-base leading-relaxed">{text}</p>
      </div>
      {timestamp ? (
        <p className="mt-1 text-right text-sm font-semibold text-slate-500 dark:text-slate-400">
          {timestamp}
        </p>
      ) : null}
    </div>
  );
}

const LEVEL_BORDER: Record<string, string> = {
  Orange: "border-l-2 border-l-orange-600 dark:border-l-orange-400",
  Red: "border-l-2 border-l-red-600 dark:border-l-red-400",
};

/** Left-aligned glass assistant bubble with badge + Orange/Red edge. */
export function AssistantBubble({
  text,
  alertLevel,
}: {
  text: string;
  alertLevel?: string;
}) {
  const level = (alertLevel ?? "") as AlertLevel;
  const border = LEVEL_BORDER[level] ?? "";
  return (
    <Card className={`glass-card max-w-full px-4 py-3 ${border}`.trimEnd()}>
      <p className="whitespace-pre-wrap text-base leading-relaxed">{text}</p>
      {level ? (
        <div className="mt-2">
          <AlertBadge level={level} />
        </div>
      ) : null}
    </Card>
  );
}
