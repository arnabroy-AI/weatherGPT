import {
  BellRing,
  CalendarDays,
  HelpCircle,
  MessageCircle,
  ShieldCheck,
  Sprout,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

const FEATURES = [
  {
    icon: MessageCircle,
    title: "Ask like you talk",
    body: "\u201CWill it rain in Mumbai this weekend?\u201D No menus, no station codes — just plain words, district by district.",
  },
  {
    icon: BellRing,
    title: "Alerts you can read at a glance",
    body: "Every severity-sensitive answer carries a Green, Yellow, Orange, or Red line, so you know how worried to be.",
  },
  {
    icon: CalendarDays,
    title: "5-day outlooks, day by day",
    body: "Min/max, rain chance, and condition for each day of the 5-day forecast — worst day called out first.",
  },
  {
    icon: Sprout,
    title: "Farm advice grounded in weather",
    body: "Paddy, wheat, cotton, sugarcane, maize, and soybean notes tied to live conditions, not generic crop tips.",
  },
  {
    icon: HelpCircle,
    title: "It asks when unsure",
    body: "No location in your question? One short follow-up pins down your district — never a silent guess.",
  },
  {
    icon: ShieldCheck,
    title: "Honest when data fails",
    body: "Outages return a clearly labelled fallback with its source named — never a confident fabrication.",
  },
] as const;

export function Features() {
  return (
    <section
      id="features"
      aria-labelledby="features-heading"
      className="mx-auto w-full max-w-6xl px-4 py-16 md:px-6 md:py-24"
    >
      <div className="mx-auto max-w-2xl text-center">
        <p className="kicker">Features</p>
        <h2
          id="features-heading"
          className="section-title mt-2 font-display font-semibold"
        >
          Weather answers India can act on
        </h2>
        <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
          Grounded in live model data with IMD-direct on the roadmap — every
          forecast names its source.
        </p>
      </div>
      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {FEATURES.map(({ icon: Icon, title, body }) => (
          <Card key={title} className="glass-card">
            <CardContent className="flex flex-col gap-3 p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-[10px] bg-teal-700/10 text-teal-700 dark:bg-teal-400/10 dark:text-teal-400">
                <Icon className="h-5 w-5" aria-hidden="true" />
              </span>
              <h3 className="text-base font-semibold leading-snug">{title}</h3>
              <p className="text-base leading-relaxed text-slate-600 dark:text-slate-300">
                {body}
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
    </section>
  );
}
