import Link from "next/link";
import { buttonGhost, buttonPrimary } from "@/components/ui";
import { Icon, type IconName } from "@/components/Icon";
import { ART, Illustration } from "@/components/Illustration";

const TRAITS: { icon: IconName; label: string }[] = [
  { icon: "lock", label: "Private to you" },
  { icon: "sprout", label: "Learns every day" },
  { icon: "message", label: "Explains its reasons" },
];

export function Hero() {
  return (
    <section className="relative overflow-hidden border-b border-line">
      <div aria-hidden="true" className="bg-grid absolute inset-0" />
      <div className="relative mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2 lg:py-28">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-accent">
            One agent · One person
          </p>
          <h1 className="mt-5 font-serif text-5xl leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">
            A mind for your time. <span className="italic text-accent">It knows you, and acts for you.</span>
          </h1>
          <p className="mt-6 max-w-xl text-lg text-muted">
            Neramind is your own AI agent. It learns how your days really go from every
            conversation and source you connect, notices where time slips away, and suggests the
            right next step, each with its reason.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/app" className={buttonPrimary}>
              Try Neramind <span aria-hidden="true">→</span>
            </Link>
            <a href="#capabilities" className={buttonGhost}>
              See what it can do
            </a>
          </div>
          <ul className="mt-10 flex flex-wrap gap-x-6 gap-y-2 border-t border-line pt-6 font-mono text-xs text-muted">
            {TRAITS.map((t) => (
              <li key={t.label} className="flex items-center gap-2">
                <Icon name={t.icon} className="h-4 w-4 text-accent" />
                {t.label}
              </li>
            ))}
          </ul>
        </div>
        <Illustration {...ART.hero} box={420} priority />
      </div>
    </section>
  );
}
