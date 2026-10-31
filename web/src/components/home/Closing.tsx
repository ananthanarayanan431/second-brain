import Link from "next/link";
import { LogoMark } from "@/components/Logo";
import { buttonPrimary } from "@/components/ui";

export function FinalCta() {
  return (
    <section className="relative overflow-hidden">
      <div aria-hidden="true" className="bg-grid absolute inset-0" />
      <div className="relative mx-auto max-w-3xl px-4 py-24 text-center sm:px-6">
        <h2 className="text-3xl font-semibold tracking-tight sm:text-4xl">
          Start with what works today.
        </h2>
        <p className="mt-4 text-lg text-muted">
          Ask your second brain a question, search everything it has read, or teach it a new
          source. It gets smarter from here.
        </p>
        <Link href="/app" className={`${buttonPrimary} mt-8`}>
          Try Second Brain <span aria-hidden="true">→</span>
        </Link>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-3 px-4 py-8 text-sm text-muted sm:flex-row sm:px-6">
        <span className="flex items-center gap-2">
          <LogoMark className="h-4 w-4" /> Second Brain
        </span>
        <span className="font-mono text-xs">One agent. One person.</span>
      </div>
    </footer>
  );
}
