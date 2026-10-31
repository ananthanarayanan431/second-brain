import type { ReactNode } from "react";

export function SectionHeading({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: ReactNode;
  children?: ReactNode;
}) {
  return (
    <div className="max-w-2xl">
      <p className="font-mono text-xs uppercase tracking-widest text-accent">{eyebrow}</p>
      <h2 className="mt-3 text-3xl font-semibold tracking-tight sm:text-4xl">{title}</h2>
      {children && <p className="mt-4 text-lg text-muted">{children}</p>}
    </div>
  );
}

export function ErrorNote({ message }: { message: string }) {
  return (
    <div role="alert" className="rounded-md border border-danger/40 bg-danger/5 p-4 text-sm">
      <p className="font-medium text-danger">Something went wrong</p>
      <p className="mt-1 text-muted">{message}</p>
    </div>
  );
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div role="status" className="rounded-md border border-dashed border-line p-8 text-center">
      <p className="font-medium">{title}</p>
      {children && <div className="mt-2 text-sm text-muted">{children}</div>}
    </div>
  );
}

export function Skeleton({ lines = 3, label }: { lines?: number; label: string }) {
  return (
    <div aria-busy="true" aria-label={label} className="space-y-3">
      {Array.from({ length: lines }, (_, i) => (
        <div
          key={i}
          className={`h-4 animate-pulse rounded bg-raised ${i === lines - 1 ? "w-2/3" : "w-full"}`}
        />
      ))}
    </div>
  );
}

export const buttonPrimary =
  "inline-flex items-center justify-center gap-2 rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-ink transition-colors hover:bg-accent-strong disabled:cursor-not-allowed disabled:opacity-50";

export const buttonGhost =
  "inline-flex items-center justify-center gap-2 rounded-md border border-line px-4 py-2.5 text-sm font-semibold text-text transition-colors hover:border-muted";

export const inputBase =
  "w-full rounded-md border border-line bg-panel px-3 py-2.5 text-sm text-text placeholder:text-muted/70 focus:border-accent focus:outline-none";
