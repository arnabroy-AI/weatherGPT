import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const FACTS = [
  {
    badge: "Rain sum",
    badgeClass:
      "border-teal-700/40 bg-teal-700/10 text-teal-700 dark:border-teal-400/40 dark:bg-teal-400/10 dark:text-teal-300",
    title: "Past-30-day rain sum",
    body: "Pune past-30-day rain sum 157.2 mm across 30 observed days, summed from daily precipitation.",
  },
  {
    badge: "Temperature",
    badgeClass:
      "border-amber-600/40 bg-amber-600/10 text-amber-700 dark:border-amber-400/40 dark:bg-amber-400/10 dark:text-amber-300",
    title: "Mean, min, max temperature",
    body: "Mean 27.02°C, min 23.0°C, max 32.0°C over the same 30-day window, from daily max and min means.",
  },
  {
    badge: "Extremes",
    badgeClass:
      "border-slate-500/40 bg-slate-500/10 text-slate-600 dark:border-slate-400/40 dark:bg-slate-400/10 dark:text-slate-300",
    title: "Wettest and driest days",
    body: "Wettest 2026-08-23, driest 2026-08-13, picked from daily precipitation sums in the window.",
  },
] as const;

export function ClimateStrip() {
  return (
    <section
      id="climate"
      aria-labelledby="climate-heading"
      className="mx-auto w-full max-w-6xl px-4 py-16 md:px-6 md:py-24"
    >
      <div className="mx-auto max-w-2xl text-center">
        <p className="kicker">Climate trends</p>
        <h2
          id="climate-heading"
          className="section-title mt-2 font-display font-semibold"
        >
          Past-30-day trends for the monsoon questions
        </h2>
        <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
          Past-30-day rain sum, temperature means, and the wettest and
          driest days — observed aggregates for questions like whether this
          monsoon ran wetter than normal.
        </p>
      </div>
      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FACTS.map(({ badge, badgeClass, title, body }) => (
          <Card key={title} className="glass-card">
            <CardContent className="flex flex-col gap-3 p-6">
              <Badge variant="outline" className={badgeClass}>
                {badge}
              </Badge>
              <p className="text-base font-semibold leading-snug">{title}</p>
              <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
                {body}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <p className="mx-auto mt-8 max-w-2xl text-center text-sm text-slate-500 dark:text-slate-400">
        Illustrative aggregates over the past 30 days from non-IMD model
        data. Live trend answers quote measured archive values and name
        their source, never described as IMD-issued.
      </p>
    </section>
  );
}
