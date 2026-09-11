import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const LEVELS = [
  {
    name: "Green",
    alert: "Alert: Green",
    advisory: "No severe weather expected. Go about your day.",
    badgeClass:
      "border-green-600/40 bg-green-600/10 text-green-700 dark:border-green-400/40 dark:bg-green-400/10 dark:text-green-300",
  },
  {
    name: "Yellow",
    alert: "Alert: Yellow",
    advisory: "Carry an umbrella; no severe weather expected.",
    badgeClass:
      "border-yellow-600/40 bg-yellow-600/10 text-yellow-700 dark:border-yellow-400/40 dark:bg-yellow-400/10 dark:text-yellow-300",
  },
  {
    name: "Orange",
    alert: "Alert: Orange",
    advisory: "Avoid unnecessary travel; carry rain gear and stay alert.",
    badgeClass:
      "border-orange-600/40 bg-orange-600/10 text-orange-700 dark:border-orange-400/40 dark:bg-orange-400/10 dark:text-orange-300",
  },
  {
    name: "Red",
    alert: "Alert: Red",
    advisory: "Avoid travel and stay indoors; move away from flood-prone areas.",
    badgeClass:
      "border-red-600/40 bg-red-600/10 text-red-700 dark:border-red-400/40 dark:bg-red-400/10 dark:text-red-300",
  },
] as const;

export function AlertsShowcase() {
  return (
    <section
      id="alerts"
      aria-labelledby="alerts-heading"
      className="mx-auto w-full max-w-6xl px-4 py-16 md:px-6 md:py-24"
    >
      <div className="mx-auto max-w-2xl text-center">
        <p className="kicker">Alerts</p>
        <h2
          id="alerts-heading"
          className="section-title mt-2 font-display font-semibold"
        >
          One line that tells you how worried to be
        </h2>
        <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
          Four levels. Same wording in the API, the chat badge, and this
          page.
        </p>
      </div>
      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {LEVELS.map(({ name, alert, advisory, badgeClass }) => (
          <Card key={name} className="glass-card">
            <CardContent className="flex flex-col gap-3 p-6">
              <Badge variant="outline" className={badgeClass}>
                {name}
              </Badge>
              <p className="text-base font-semibold leading-snug">{alert}</p>
              <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
                {advisory}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <p className="mx-auto mt-8 max-w-2xl text-center text-sm text-slate-500 dark:text-slate-400">
        Showcase advisories illustrate severity wording. Live advisories are
        derived estimates, never described as IMD-issued warnings.
      </p>
    </section>
  );
}
