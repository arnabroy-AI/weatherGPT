import { Separator } from "@/components/ui/separator";
import { Card, CardContent } from "@/components/ui/card";

const STEPS = [
  {
    n: "01",
    title: "You ask",
    body: "\u201CRain in Delhi tomorrow?\u201D — plus an optional location field so the answer grounds to your district.",
  },
  {
    n: "02",
    title: "Tools ground it",
    body: "Live model data, the 5-day forecast, and curated farm notes feed the answer — values quoted, never invented.",
  },
  {
    n: "03",
    title: "You get answer + alert",
    body: "A plain-words reply, an Alert: Green-to-Red line, and a 1\u20132 line safety advisory when it matters.",
  },
] as const;

export function HowItWorks() {
  return (
    <section
      id="how-it-works"
      aria-labelledby="how-it-works-heading"
      className="mx-auto w-full max-w-6xl px-4 py-16 md:px-6 md:py-24"
    >
      <div className="mx-auto max-w-2xl text-center">
        <p className="kicker">How it works</p>
        <h2
          id="how-it-works-heading"
          className="section-title mt-2 font-display font-semibold"
        >
          Question in, grounded answer out
        </h2>
        <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
          Three steps from a monsoon question to a forecast you can act on —
          every reply names its source.
        </p>
      </div>
      <div className="relative mt-10">
        <Separator
          className="absolute left-0 right-0 top-1/2 hidden bg-slate-200 md:block dark:bg-slate-700"
          aria-hidden="true"
        />
        <ol className="relative grid list-none grid-cols-1 gap-4 p-0 md:grid-cols-3">
          {STEPS.map(({ n, title, body }) => (
            <li key={n}>
              <Card className="glass-card h-full">
                <CardContent className="flex flex-col gap-3 p-6">
                  <span
                    className="font-display text-sm font-semibold tracking-wide text-teal-700 dark:text-teal-400"
                    aria-hidden="true"
                  >
                    {n}
                  </span>
                  <h3 className="text-base font-semibold leading-snug">
                    {title}
                  </h3>
                  <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
                    {body}
                  </p>
                </CardContent>
              </Card>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
