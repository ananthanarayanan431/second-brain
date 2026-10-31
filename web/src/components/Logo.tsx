import Link from "next/link";

/** Three linked nodes: a tiny knowledge graph. */
export function LogoMark({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" className={className} aria-hidden="true">
      <path d="M6 17 L12 6 L18 15 Z" fill="none" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="12" cy="6" r="2.5" className="fill-accent" />
      <circle cx="6" cy="17" r="2.5" fill="currentColor" />
      <circle cx="18" cy="15" r="2.5" fill="currentColor" />
    </svg>
  );
}

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-text">
      <LogoMark />
      <span>Second Brain</span>
    </Link>
  );
}
