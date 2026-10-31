import { Icon, IconTile, type IconName } from "@/components/Icon";
import { SectionHeading } from "@/components/ui";

const PARTS: { icon: IconName; word: string; script?: string; lang: string; body: string }[] = [
  {
    icon: "clock",
    word: "Neram",
    script: "நேரம்",
    lang: "Tamil · time",
    body: "The hours of your day: where they go, where they slip away, and where you never seem to have enough.",
  },
  {
    icon: "mind",
    word: "Mind",
    lang: "English",
    body: "Something that pays attention, remembers what it has seen, and connects one thing to the next.",
  },
];

const PROMISES: { icon: IconName; title: string; body: string }[] = [
  {
    icon: "eye",
    title: "It watches how your hours go",
    body: "Not to judge them. It learns your real rhythm: when you focus, when you drift, what always runs over.",
  },
  {
    icon: "hourglass",
    title: "It notices where time slips away",
    body: "And where it is missing. The meeting that eats your mornings, the task that never finds a slot.",
  },
  {
    icon: "bulb",
    title: "It suggests the right thing, at the right time",
    body: "Not a new plan for your whole life. Just the next good move: “This hour, you can do this one.”",
  },
];

export function NameMeaning() {
  return (
    <section id="name" className="scroll-mt-16 border-b border-line">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <SectionHeading eyebrow="The name" title="Why Neramind?">
          Neramind (<span className="font-mono text-base">NEH-ruh-mind</span>) joins a Tamil word
          and an English one. Together they say what it is for: a mind for your time.
        </SectionHeading>

        {/* The word, as an equation: Neram + Mind = Neramind */}
        <div className="mt-12 grid items-stretch gap-4 lg:grid-cols-[1fr_auto_1fr_auto_1.15fr]">
          {PARTS.map((p, i) => (
            <div key={p.word} className="contents">
              {i > 0 && <Operator symbol="+" />}
              <div className="rounded-lg border border-line bg-panel p-6">
                <div className="flex items-start justify-between gap-4">
                  <IconTile name={p.icon} />
                  <span className="font-mono text-xs uppercase tracking-widest text-muted">{p.lang}</span>
                </div>
                <p className="mt-5 font-serif text-3xl">
                  {p.word}
                  {p.script && (
                    <span lang="ta" className="ml-3 text-2xl text-accent">
                      {p.script}
                    </span>
                  )}
                </p>
                <p className="mt-2 text-muted">{p.body}</p>
              </div>
            </div>
          ))}
          <Operator symbol="=" />
          <div className="rounded-lg border border-accent/40 bg-accent p-6 text-ink">
            <div className="flex items-start justify-between gap-4">
              <span className="inline-flex h-11 w-11 items-center justify-center rounded-lg bg-ink/15">
                <Icon name="compass" className="h-5 w-5" />
              </span>
              <span className="font-mono text-xs uppercase tracking-widest text-ink/70">Together</span>
            </div>
            <p className="mt-5 font-serif text-3xl">Neramind</p>
            <p className="mt-2 text-ink/85">
              A mind that understands your time, and guides you to the right thing at the right
              moment.
            </p>
          </div>
        </div>

        <h3 className="mt-16 font-mono text-xs uppercase tracking-widest text-accent">
          What the name promises
        </h3>
        <ol className="mt-5 grid gap-4 md:grid-cols-3">
          {PROMISES.map((p) => (
            <li key={p.title} className="flex gap-4 rounded-lg border border-line bg-panel p-5">
              <IconTile name={p.icon} />
              <div>
                <p className="font-serif text-xl leading-snug">{p.title}</p>
                <p className="mt-2 text-sm text-muted">{p.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

function Operator({ symbol }: { symbol: string }) {
  return (
    <span
      aria-hidden="true"
      className="flex items-center justify-center font-serif text-3xl text-muted lg:px-1"
    >
      {symbol}
    </span>
  );
}
