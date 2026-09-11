import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

export function MoesStrip() {
  return (
    <section
      aria-labelledby="moes-heading"
      className="w-full border-t-2 border-amber-600 bg-slate-100 dark:border-amber-400 dark:bg-slate-900"
    >
      <div className="mx-auto max-w-6xl px-4 py-10 text-center md:px-6 md:py-12">
        <Badge
          variant="outline"
          className="border-amber-600/40 text-amber-600 dark:border-amber-400/40 dark:text-amber-400"
        >
          SIH26068 · MoES track
        </Badge>
        <h2
          id="moes-heading"
          className="mx-auto mt-4 max-w-2xl font-display text-xl font-semibold tracking-tight"
        >
          Built for the Ministry of Earth Sciences (SIH26068)
        </h2>
        <Separator
          className="mx-auto mt-4 max-w-xs bg-slate-300 dark:bg-slate-700"
          aria-hidden="true"
        />
        <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-slate-600 dark:text-slate-300">
          Data roadmap: keyless model engine today with honest disclosure on
          every answer — IMD-direct integration next. Authenticity is the
          judging criterion, so every reply names its source.
        </p>
      </div>
    </section>
  );
}
