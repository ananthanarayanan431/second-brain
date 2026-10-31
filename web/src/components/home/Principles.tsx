import { SectionHeading } from "@/components/ui";

const PRINCIPLES = [
  {
    title: "Yours, and only yours",
    body: "One agent for one person. It is shaped by your conversations, your sources, and your way of working. Nothing about it is shared or generic.",
  },
  {
    title: "A memory that wires itself",
    body: "Everything it learns becomes part of a knowledge graph: people, topics, claims, and how they connect. The more you talk to it, the more it understands, and the better its next answer.",
  },
  {
    title: "It acts, and tells you why",
    body: "It does not wait to be asked. It notices what needs attention, suggests the next step, and always gives its reason, so you stay in charge.",
  },
];

export function Principles() {
  return (
    <section id="what" className="scroll-mt-16 border-b border-line">
      <div className="mx-auto grid max-w-6xl gap-12 px-4 py-20 sm:px-6 lg:grid-cols-5">
        <div className="lg:col-span-2">
          <SectionHeading eyebrow="What is a second brain?" title="Not a chatbot. A brain that grows with you.">
            Your first brain is busy. Your second brain remembers what you read, understands what
            matters to you, and keeps track of the details you would rather not.
          </SectionHeading>
        </div>
        <ol className="space-y-8 lg:col-span-3">
          {PRINCIPLES.map((p, i) => (
            <li key={p.title} className="grid grid-cols-[3rem_1fr] gap-4 border-t border-line pt-6">
              <span className="font-mono text-sm text-accent">{String(i + 1).padStart(2, "0")}</span>
              <div>
                <h3 className="text-lg font-semibold">{p.title}</h3>
                <p className="mt-2 text-muted">{p.body}</p>
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
