import Link from "next/link";
import { CloudSun } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";

const PRODUCT_LINKS = [
  { href: "#features", label: "Features" },
  { href: "#live-demo", label: "Live demo" },
  { href: "#alerts", label: "Alerts" },
  { href: "#how-it-works", label: "How it works" },
] as const;

const PROJECT_LINKS = [
  { href: "#top", label: "SIH26068" },
  { href: "#faq", label: "MoES track" },
  { href: "#faq", label: "API docs" },
  { href: "#top", label: "Status: v1 demo" },
] as const;

export function Footer() {
  return (
    <footer className="w-full bg-slate-100 dark:bg-slate-900">
      <div className="mx-auto max-w-6xl px-4 py-12 md:px-6 md:py-16">
        <div className="grid grid-cols-1 gap-10 sm:grid-cols-2 md:grid-cols-4">
          <div className="flex flex-col gap-3">
            <Link
              href="#top"
              className="flex items-center gap-2 rounded-md focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:focus-visible:outline-teal-400"
            >
              <span className="flex h-9 w-9 items-center justify-center rounded-[10px] bg-teal-700 text-white dark:bg-teal-400 dark:text-slate-950">
                <CloudSun className="h-5 w-5" aria-hidden="true" />
              </span>
              <span className="font-display text-lg font-semibold tracking-tight">
                WeatherGPT
              </span>
            </Link>
            <Badge
              variant="outline"
              className="w-fit border-amber-600/40 text-amber-600 dark:border-amber-400/40 dark:text-amber-400"
            >
              SIH26068
            </Badge>
          </div>

          <nav aria-label="Product">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Product
            </h2>
            <ul className="mt-3 flex flex-col items-start gap-1">
              {PRODUCT_LINKS.map(({ href, label }) => (
                <li key={label}>
                  <Button asChild variant="ghost" size="sm">
                    <Link href={href}>{label}</Link>
                  </Button>
                </li>
              ))}
            </ul>
          </nav>

          <nav aria-label="Project">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Project
            </h2>
            <ul className="mt-3 flex flex-col items-start gap-1">
              {PROJECT_LINKS.map(({ href, label }) => (
                <li key={label}>
                  <Button asChild variant="ghost" size="sm">
                    <Link href={href}>{label}</Link>
                  </Button>
                </li>
              ))}
            </ul>
          </nav>

          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400">
              Fine print
            </h2>
            <p className="mt-3 text-base leading-relaxed text-slate-600 dark:text-slate-300">
              Demo build — forecasts are model estimates, not official IMD
              warnings. For official warnings follow IMD.
            </p>
          </div>
        </div>

        <Separator
          className="my-8 bg-slate-300 dark:bg-slate-700"
          aria-hidden="true"
        />

        <div className="flex flex-col items-center justify-between gap-2 text-sm text-slate-500 sm:flex-row dark:text-slate-400">
          <p>© 2026 WeatherGPT · SIH26068</p>
          <p>English-first · No accounts in v1</p>
        </div>
      </div>
    </footer>
  );
}
