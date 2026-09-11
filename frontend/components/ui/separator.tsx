import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Stock-shadcn Separator API without the Radix peer.
 *
 * The stock shadcn separator wraps `@radix-ui/react-separator`, but this
 * plan ships zero new third-party packages (threat T-05-02-SC), so the
 * divider is a presentational element with the same `orientation` /
 * `decorative` props. Used for the desktop step connectors in
 * `how-it-works.tsx` and footer rules in plan 03.
 */
export interface SeparatorProps extends React.HTMLAttributes<HTMLDivElement> {
  orientation?: "horizontal" | "vertical";
  decorative?: boolean;
}

const Separator = React.forwardRef<HTMLDivElement, SeparatorProps>(
  (
    {
      className,
      orientation = "horizontal",
      decorative = true,
      ...props
    },
    ref
  ) => (
    <div
      ref={ref}
      role={decorative ? "none" : "separator"}
      aria-orientation={decorative ? undefined : orientation}
      className={cn(
        "shrink-0 bg-border",
        orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
        className
      )}
      {...props}
    />
  )
);
Separator.displayName = "Separator";

export { Separator };
