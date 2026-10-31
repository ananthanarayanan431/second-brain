/**
 * The self-wiring knowledge graph: you at the center, memories forming around
 * you, and the sources ("verticals") it learns from on the outside. Pure SVG +
 * CSS animation, so it renders on the server with no JavaScript.
 */

type Point = { x: number; y: number };

const YOU: Point = { x: 200, y: 200 };

// Memories the graph has formed.
const MEMORIES: Point[] = [
  { x: 135, y: 150 },
  { x: 265, y: 140 },
  { x: 285, y: 235 },
  { x: 205, y: 290 },
  { x: 120, y: 245 },
  { x: 200, y: 105 },
];

// Sources it learns from. Only newsletters are connected today.
const SOURCES: { label: string; at: Point; memory: number; live: boolean }[] = [
  { label: "Newsletters", at: { x: 345, y: 285 }, memory: 2, live: true },
  { label: "Gmail", at: { x: 55, y: 95 }, memory: 0, live: false },
  { label: "Calendar", at: { x: 345, y: 80 }, memory: 1, live: false },
  { label: "Notes", at: { x: 225, y: 375 }, memory: 3, live: false },
  { label: "Messages", at: { x: 45, y: 300 }, memory: 4, live: false },
];

// Links between memories: the "wiring" that grows as it learns.
const LINKS: [number, number][] = [
  [0, 5],
  [5, 1],
  [1, 2],
  [2, 3],
  [3, 4],
  [4, 0],
  [0, 2],
];

function Edge({ from, to, delay, dashed }: { from: Point; to: Point; delay: number; dashed?: boolean }) {
  return (
    <line
      x1={from.x}
      y1={from.y}
      x2={to.x}
      y2={to.y}
      pathLength={1}
      className={dashed ? "stroke-soon/40" : "graph-edge stroke-accent/50"}
      strokeDasharray={dashed ? "0.02 0.03" : undefined}
      strokeWidth={1}
      style={dashed ? undefined : { animationDelay: `${delay}s` }}
    />
  );
}

export function NeuralGraph() {
  return (
    <figure className="relative mx-auto w-full max-w-md">
      <svg
        viewBox="0 0 400 400"
        role="img"
        aria-label="Your agent at the center of a growing knowledge graph. Newsletters are connected today; Gmail, calendar, notes and messages are coming soon."
        className="w-full"
      >
        {MEMORIES.map((m, i) => (
          <Edge key={`you-${i}`} from={YOU} to={m} delay={0.2 + i * 0.15} />
        ))}
        {LINKS.map(([a, b], i) => (
          <Edge key={`link-${i}`} from={MEMORIES[a]} to={MEMORIES[b]} delay={1.1 + i * 0.12} />
        ))}
        {SOURCES.map((s) => (
          <Edge key={s.label} from={s.at} to={MEMORIES[s.memory]} delay={1.9} dashed={!s.live} />
        ))}

        <circle cx={YOU.x} cy={YOU.y} r={34} className="fill-accent/10 stroke-accent/40" />
        <circle cx={YOU.x} cy={YOU.y} r={20} className="graph-node fill-accent" />
        <text x={YOU.x} y={YOU.y + 4} textAnchor="middle" className="fill-ink font-mono text-[11px] font-semibold">
          YOU
        </text>

        {MEMORIES.map((m, i) => (
          <circle
            key={`m-${i}`}
            cx={m.x}
            cy={m.y}
            r={5}
            className="graph-node fill-text"
            style={{ animationDelay: `${i * 0.4}s` }}
          />
        ))}

        {SOURCES.map((s) => (
          <g key={`s-${s.label}`}>
            <circle
              cx={s.at.x}
              cy={s.at.y}
              r={7}
              className={s.live ? "fill-accent" : "fill-ink stroke-soon"}
              strokeDasharray={s.live ? undefined : "2 2"}
            />
            <text
              x={s.at.x}
              y={s.at.y + 22}
              textAnchor="middle"
              className={`font-mono text-[11px] ${s.live ? "fill-accent" : "fill-muted"}`}
            >
              {s.label}
            </text>
          </g>
        ))}
      </svg>
      <figcaption className="mt-2 flex justify-center gap-5 font-mono text-xs text-muted">
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true" className="h-2 w-2 rounded-full bg-accent" /> connected
        </span>
        <span className="flex items-center gap-1.5">
          <span aria-hidden="true" className="h-2 w-2 rounded-full border border-dashed border-soon" /> coming soon
        </span>
      </figcaption>
    </figure>
  );
}
