import Link from "next/link";
import { buttonGhost, buttonPrimary } from "@/components/ui";
import { NeuralGraph } from "./NeuralGraph";

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line">
      <div aria-hidden="true" className="bg-grid absolute inset-0" />
      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:py-28">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-accent">
            One agent · One person
          </p>
          <h1 className="mt-5 text-4xl font-semibold leading-tight tracking-tight sm:text-5xl lg:text-6xl">
            A second brain that knows you, <span className="text-accent">and acts for you.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg text-muted">
            Second Brain is your own AI agent. It learns from every conversation and every source
            you connect, wires it into a living map of how you think, and turns that into answers,
            suggestions, and actions, each with its reason.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/app" className={buttonPrimary}>
              Try Second Brain <span aria-hidden="true">→</span>
            </Link>
            <a href="#capabilities" className={buttonGhost}>
              See what it can do
            </a>
          </div>
          <ul className="mt-10 flex flex-wrap gap-x-6 gap-y-2 border-t border-line pt-6 font-mono text-xs text-muted">
            <li>Private to you</li>
            <li>Learns every day</li>
            <li>Explains its reasons</li>
          </ul>
        </div>
        <NeuralGraph />
      </div>
    </section>
  );
}
