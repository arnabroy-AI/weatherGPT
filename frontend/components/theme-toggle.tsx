"use client";

import { useEffect, useState } from "react";
import { useTheme } from "next-themes";
import { Laptop, Moon, Sun } from "lucide-react";
import { cn } from "@/lib/utils";

const options = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
  { value: "system", label: "System", icon: Laptop },
] as const;

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <div
        className={cn(
          "flex items-center gap-1 rounded-[10px] border border-slate-200 p-1 dark:border-slate-800",
          className
        )}
        aria-hidden="true"
      >
        {options.map(({ value, icon: Icon }) => (
          <span key={value} className="p-2">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
        ))}
      </div>
    );
  }

  return (
    <div
      role="group"
      aria-label="Color theme"
      className={cn(
        "flex items-center gap-1 rounded-[10px] border border-slate-200 bg-white/70 p-1 dark:border-slate-800 dark:bg-slate-900/60",
        className
      )}
    >
      {options.map(({ value, label, icon: Icon }) => {
        const active = theme === value;
        return (
          <button
            key={value}
            type="button"
            onClick={() => setTheme(value)}
            aria-pressed={active}
            aria-label={`${label} theme`}
            title={`${label} theme`}
            className={cn(
              "rounded-md p-2 transition-colors",
              "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:focus-visible:outline-teal-400",
              active
                ? "bg-teal-700 text-white dark:bg-teal-400 dark:text-slate-950"
                : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
            )}
          >
            <Icon className="h-4 w-4" aria-hidden="true" />
          </button>
        );
      })}
    </div>
  );
}
