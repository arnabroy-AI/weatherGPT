"use client";

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";

const ITEMS = [
  {
    value: "item-1",
    question: "Where does the weather data come from?",
    answer:
      "A keyless model-data engine today; every answer names its source and IMD-direct is the roadmap. We never present estimates as IMD-issued warnings.",
  },
  {
    value: "item-2",
    question: "What happens when live data fails?",
    answer:
      "You get a clearly labelled fallback in under 5 seconds — stale-with-age or mock-shaped values with a disclosure note, never silence.",
  },
  {
    value: "item-3",
    question: "Which places are covered?",
    answer:
      "18 mapped cities at launch — metros, state capitals, Nashik and Pune — plus best-guess resolution that always discloses the guess.",
  },
  {
    value: "item-4",
    question: "Can farmers use it?",
    answer:
      "Yes — six kharif/rabi crop notes (paddy, wheat, cotton, sugarcane, maize, soybean) grounded in live conditions; anything else gets a best-effort dry-window advisory.",
  },
  {
    value: "item-5",
    question: "Hindi or other languages?",
    answer: "English first in v1; Hindi and regional languages are v2.",
  },
  {
    value: "item-6",
    question: "Is there an API?",
    answer:
      "Yes — POST /api/chat takes {message, location} and returns {reply, alert_level}; GET /health is the liveness probe.",
  },
] as const;

export function Faq() {
  return (
    <section
      id="faq"
      aria-labelledby="faq-heading"
      className="mx-auto w-full max-w-6xl px-4 py-16 md:px-6 md:py-24"
    >
      <div className="mx-auto w-full max-w-3xl">
        <div className="mx-auto max-w-2xl text-center">
          <p className="kicker">FAQ</p>
          <h2
            id="faq-heading"
            className="section-title mt-2 font-display font-semibold"
          >
            Questions, answered honestly
          </h2>
          <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
            Sources, coverage, and limits — the same disclosures every
            WeatherGPT answer carries.
          </p>
        </div>
        <Accordion
          type="single"
          collapsible
          className="glass-card mt-10 px-6"
        >
          {ITEMS.map(({ value, question, answer }) => (
            <AccordionItem key={value} value={value}>
              <AccordionTrigger>{question}</AccordionTrigger>
              <AccordionContent>{answer}</AccordionContent>
            </AccordionItem>
          ))}
        </Accordion>
      </div>
    </section>
  );
}
