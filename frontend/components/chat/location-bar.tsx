import { MapPin } from "lucide-react";

export function LocationBar({
  value,
  onChange,
}: {
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="glass-card flex flex-col gap-1 rounded-2xl p-4">
      <label
        htmlFor="chat-location"
        className="flex items-center gap-1.5 text-sm font-semibold"
      >
        <MapPin
          className="h-4 w-4 text-amber-600 dark:text-amber-400"
          aria-hidden="true"
        />
        Location
      </label>
      <input
        id="chat-location"
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Location (optional) — e.g. Pune"
        autoComplete="off"
        className="h-11 rounded-[10px] border border-input bg-background px-3 text-base focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-700 dark:focus-visible:outline-teal-400"
      />
      <p className="text-sm text-slate-500 dark:text-slate-400">
        Used for every question you send.
      </p>
    </div>
  );
}
