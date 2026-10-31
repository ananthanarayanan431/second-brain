import Link from "next/link";
import { Logo } from "@/components/Logo";

const LINKS = [
  { href: "#what", label: "What it is" },
  { href: "#voice", label: "Voice" },
  { href: "#capabilities", label: "Capabilities" },
  { href: "#agents", label: "Agent to agent" },
  { href: "#name", label: "The name" },
];

export function Nav() {
  return (
    <header className="sticky top-0 z-20 border-b border-line bg-ink/80 backdrop-blur">
      <nav
        aria-label="Main"
        className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
      >
        <Logo />
        <ul className="hidden items-center gap-8 text-sm text-muted md:flex">
          {LINKS.map((l) => (
            <li key={l.href}>
              <a href={l.href} className="transition-colors hover:text-text">
                {l.label}
              </a>
            </li>
          ))}
        </ul>
        <Link
          href="/app"
          className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-ink transition-colors hover:bg-accent-strong"
        >
          Try it
        </Link>
      </nav>
    </header>
  );
}
