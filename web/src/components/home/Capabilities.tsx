import { type Availability, StatusBadge } from "@/components/StatusBadge";
import { SectionHeading } from "@/components/ui";

type Capability = { title: string; body: string };

const NOW: Capability[] = [
  {
    title: "Ask anything, get cited answers",
    body: "Answers come only from what it has read, with inline citations back to the exact passage.",
  },
  {
    title: "Search everything you follow",
    body: "Keyword, meaning, and knowledge-graph search, fused into one ranked list.",
  },
  {
    title: "Opinion vs. fact, kept apart",
    body: "Every claim is labeled as a measurement, an opinion, or a prediction, and traced to its quote.",
  },
  {
    title: "Learns from the newsletters you read",
    body: "Add a publication or a single article, and it is read, understood, and wired into your graph.",
  },
];

const SOON: Capability[] = [
  {
    title: "Voice agent on your phone",
    body: "Double-tap, speak, and get an answer or an action back.",
  },
  {
    title: "Gmail, calendar, notes, and messages",
    body: "More sources to learn from, so it sees the whole picture of your day.",
  },
  {
    title: "Proactive nudges",
    body: "“He replied this morning. Should I answer, or talk to him for you?”",
  },
  {
    title: "Talks to other agents for you",
    body: "When you are busy, your agent gets things done with other people or their agents.",
  },
];

function Column({ status, items }: { status: Availability; items: Capability[] }) {
  return (
    <div className="rounded-lg border border-line bg-panel p-6">
      <StatusBadge status={status} />
      <ul className="mt-6 divide-y divide-line">
        {items.map((c) => (
          <li key={c.title} className="py-4 first:pt-0 last:pb-0">
            <h3 className="font-semibold">{c.title}</h3>
            <p className="mt-1 text-sm text-muted">{c.body}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function Capabilities() {
  return (
    <section id="capabilities" className="scroll-mt-16 border-b border-line">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <SectionHeading eyebrow="Capabilities" title="What it can do today, and what is next.">
          No vapor: everything marked available now works in the app you can try below.
        </SectionHeading>
        <div className="mt-12 grid gap-6 lg:grid-cols-2">
          <Column status="now" items={NOW} />
          <Column status="soon" items={SOON} />
        </div>
      </div>
    </section>
  );
}
