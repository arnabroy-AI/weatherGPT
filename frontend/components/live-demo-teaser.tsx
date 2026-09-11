import Link from "next/link";
import { MessageSquareText } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

const SEEDED = [
  {
    query: "Current weather in Pune",
    reply:
      "33.2\u00B0C, Partly cloudy in Pune (model data). No severe weather expected.",
    alert: "Alert: Green",
    alertClass:
      "border-green-600/40 bg-green-600/10 text-green-700 dark:border-green-400/40 dark:bg-green-400/10 dark:text-green-300",
  },
  {
    query: "Mumbai this weekend",
    reply:
      "Day-wise highs, rain chance, and condition for Sat\u2013Sun — worst day called out first.",
    alert: "Alert: Orange (Sat)",
    alertClass:
      "border-orange-600/40 bg-orange-600/10 text-orange-700 dark:border-orange-400/40 dark:bg-orange-400/10 dark:text-orange-300",
  },
  {
    query: "Paddy sowing advice for Nashik",
    reply:
      "Transplant 20\u201325 day seedlings after onset; drain excess water — tied to Nashik conditions.",
    alert: "Alert: Green",
    alertClass:
      "border-green-600/40 bg-green-600/10 text-green-700 dark:border-green-400/40 dark:bg-green-400/10 dark:text-green-300",
  },
] as const;

export function LiveDemoTeaser() {
  return (
    <section
      id="live-demo"
      aria-labelledby="live-demo-heading"
      className="mx-auto w-full max-w-6xl px-4 py-16 md:px-6 md:py-24"
    >
      <div className="glass-hero-panel px-6 py-10 md:px-12 md:py-14">
        <div className="mx-auto max-w-2xl text-center">
          <p className="kicker">Live demo</p>
          <h2
            id="live-demo-heading"
            className="section-title mt-2 font-display font-semibold"
          >
            See what an answer looks like
          </h2>
          <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
            Real reply shapes from the WeatherGPT API — try these on launch
            day.
          </p>
        </div>
        <div className="mt-10 grid grid-cols-1 gap-4 lg:grid-cols-3">
          {SEEDED.map(({ query, reply, alert, alertClass }) => (
            <Card key={query} className="glass-card">
              <CardContent className="flex flex-col gap-3 p-6">
                <p className="flex items-start gap-2 text-base font-semibold leading-snug">
                  <MessageSquareText
                    className="mt-0.5 h-5 w-5 shrink-0 text-teal-700 dark:text-teal-400"
                    aria-hidden="true"
                  />
                  {query}
                </p>
                <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
                  {reply}
                </p>
                <Badge variant="outline" className={alertClass}>
                  {alert}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>
        <p className="mx-auto mt-8 max-w-xl text-center text-sm text-slate-500 dark:text-slate-400">
          Sample values shown. Live answers quote measured tool values and
          name their source — district forecasts, never invented numbers.
        </p>
        <div className="mt-4 flex flex-col items-center gap-2">
          <Button type="button" size="lg" asChild>
            <Link href="/chat">Open the chat</Link>
          </Button>
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Live now — ask anything, answers quote measured tool values.
          </p>
        </div>
      </div>
    </section>
  );
}
