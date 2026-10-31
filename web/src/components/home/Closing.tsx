import Link from "next/link";
import { ART, Illustration } from "@/components/Illustration";
import { LogoMark } from "@/components/Logo";
import { buttonPrimary } from "@/components/ui";

export function FinalCta() {
  return (
    <section className="relative overflow-hidden">
      <div aria-hidden="true" className="bg-grid absolute inset-0" />
      <div className="relative mx-auto max-w-6xl px-4 py-24 sm:px-6">
        <div className="grid items-center gap-8 rounded-2xl border border-line bg-panel p-8 sm:p-12 md:grid-cols-[1fr_auto]">
          <div className="max-w-xl">
            <h2 className="font-serif text-4xl leading-tight tracking-tight sm:text-5xl">
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
          <Illustration {...ART.grow} box={240} className="md:w-64" />
        </div>
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
