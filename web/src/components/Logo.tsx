import Link from "next/link";

/*
 * The mark is the knowledge graph from the original hero, distilled: you at the
 * center (with a halo), the memories it has wired around you, and one live
 * source (Newsletters) reaching in from outside. Coordinates are the graph's own,
 * so the shape keeps its hand-placed, irregular feel.
 */
const YOU = { x: 200, y: 200 };
const MEMORIES = [
  { x: 135, y: 150 },
  { x: 265, y: 140 },
  { x: 285, y: 235 },
  { x: 205, y: 290 },
  { x: 120, y: 245 },
  { x: 200, y: 105 },
];
const LINKS: [number, number][] = [
  [0, 5],
  [5, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 0],
  [0, 2],
];
const SOURCE = { x: 345, y: 285 };
const LIVE = MEMORIES[2];

/** Dark parts follow currentColor; the "you" node and live source use the accent. */
export function LogoMark({ className = "h-6 w-6" }: { className?: string }) {
  return (
    <svg viewBox="95 80 275 275" className={className} aria-hidden="true">
      <g strokeWidth={10} strokeLinecap="round">
        {MEMORIES.map((m, i) => (
          <line key={`s${i}`} x1={YOU.x} y1={YOU.y} x2={m.x} y2={m.y} className="stroke-accent/55" />
        ))}
        {LINKS.map(([a, b]) => (
          <line
            key={`l${a}-${b}`}
            x1={MEMORIES[a].x}
            y1={MEMORIES[a].y}
            x2={MEMORIES[b].x}
            y2={MEMORIES[b].y}
            stroke="currentColor"
          />
        ))}
        <line x1={LIVE.x} y1={LIVE.y} x2={SOURCE.x} y2={SOURCE.y} className="stroke-accent" />
        <circle cx={YOU.x} cy={YOU.y} r={44} className="fill-ink stroke-accent/50" />
      </g>
      <circle cx={YOU.x} cy={YOU.y} r={26} className="fill-accent" />
      {MEMORIES.map((m, i) => (
        <circle key={`m${i}`} cx={m.x} cy={m.y} r={13} fill="currentColor" />
      ))}
      <circle cx={SOURCE.x} cy={SOURCE.y} r={17.5} className="fill-accent" />
    </svg>
  );
}

export function Logo() {
  return (
    <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight text-text">
      <LogoMark className="h-7 w-7" />
      <span>Second Brain</span>
    </Link>
  );
}
