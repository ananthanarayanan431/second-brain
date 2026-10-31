export type Availability = "now" | "soon";

/** Says in words (not only color) whether a feature works today. */
export function StatusBadge({ status }: { status: Availability }) {
  const now = status === "now";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-mono text-xs ${
        now ? "border-accent/40 text-accent" : "border-soon/40 text-soon"
      }`}
    >
      <span
        aria-hidden="true"
        className={`h-1.5 w-1.5 rounded-full ${now ? "bg-accent" : "border border-soon"}`}
      />
      {now ? "Available now" : "Coming soon"}
    </span>
  );
}
