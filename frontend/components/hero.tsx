import Link from "next/link";
import { ArrowRight, MapPin, ShieldCheck, Star } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

export function Hero() {
  return (
    <section id="top" aria-labelledby="hero-heading" className="relative overflow-hidden">
      <div className="hero-wash pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="relative mx-auto max-w-6xl px-4 py-16 md:px-6 md:py-24">
        <div className="glass-hero-panel mx-auto flex max-w-3xl flex-col items-center px-6 py-10 text-center md:px-12 md:py-14">
          <Badge
            variant="outline"
            className="border-amber-600/40 text-amber-600 dark:border-amber-400/40 dark:text-amber-400"
          >
            Built for SIH26068
          </Badge>
          <p className="kicker mt-4">Built for SIH26068</p>
          <h1
            id="hero-heading"
            className="hero-display mt-4 font-display font-semibold tracking-tight"
          >
            Ask the weather in plain words. Get answers India can act on.
          </h1>
          <p className="mt-4 max-w-xl text-base leading-relaxed text-slate-600 dark:text-slate-300">
            WeatherGPT turns natural-language questions into grounded forecasts
            and clear Green-to-Red alerts — district by district, in seconds.
          </p>
          <div className="mt-8 flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <Button asChild size="lg" className="w-full sm:w-auto">
              <Link href="#live-demo">
                Try a sample question
                <ArrowRight aria-hidden="true" />
              </Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
              <Link href="#how-it-works">See how it works</Link>
            </Button>
          </div>
          <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
            No sign-up · English-first · Honest about its sources
          </p>
          <div
            className="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm font-medium"
            aria-label="Coverage highlights"
          >
            <span className="flex items-center gap-1.5 text-teal-700 dark:text-teal-400">
              <MapPin className="h-4 w-4" aria-hidden="true" />
              18 cities mapped
            </span>
            <span className="text-slate-600 dark:text-slate-300">
              5-day forecasts
            </span>
            <span className="flex items-center gap-1.5 text-slate-600 dark:text-slate-300">
              <ShieldCheck className="h-4 w-4" aria-hidden="true" />
              4 alert levels
            </span>
          </div>
          <p className="mt-4 flex items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400">
            <Star
              className="h-4 w-4 fill-amber-600 text-amber-600 dark:fill-amber-400 dark:text-amber-400"
              aria-hidden="true"
            />
            Current engine: keyless model data — IMD-direct integration pending.
            Every answer says so.
          </p>
        </div>
      </div>
    </section>
  );
}
