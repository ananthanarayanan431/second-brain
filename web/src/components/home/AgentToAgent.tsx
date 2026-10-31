import { StatusBadge } from "@/components/StatusBadge";
import { SectionHeading } from "@/components/ui";

const EXCHANGE = [
  { from: "Your agent", text: "Can Priya meet for 30 minutes this week about the launch?" },
  { from: "Priya’s agent", text: "Thursday 15:00 or Friday 10:30 work. Priya prefers Thursday." },
  { from: "Your agent", text: "Thursday 15:00, then. Sending the invite and the agenda." },
];

const TRUST = [
  {
    title: "You set the limits",
    body: "You decide what your agent may do for you: read only, draft for approval, or act.",
  },
  {
    title: "It asks before going further",
    body: "Anything outside what you allowed comes back to you as a question, not an action.",
  },
  {
    title: "Every action leaves a receipt",
    body: "You can see who it talked to, what was agreed, and why.",
  },
];

function AgentLink() {
  return (
    <div className="flex items-center justify-between gap-3 font-mono text-xs">
      <span className="rounded-md border border-accent/50 px-3 py-2 text-accent">Your agent</span>
      <svg viewBox="0 0 100 8" className="h-2 flex-1" aria-hidden="true" preserveAspectRatio="none">
        <line x1="0" y1="4" x2="100" y2="4" className="signal-flow stroke-accent" strokeWidth="2" />
      </svg>
      <span className="rounded-md border border-line px-3 py-2 text-muted">Priya’s agent</span>
    </div>
  );
}

export function AgentToAgent() {
  return (
    <section id="agents" className="scroll-mt-16 border-b border-line">
      <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
        <StatusBadge status="soon" />
        <div className="mt-4 grid gap-12 lg:grid-cols-2">
          <SectionHeading eyebrow="Agent to agent" title="Busy? Your agent talks to theirs.">
            When you cannot be in the conversation, your second brain can be. It gets information
            and agreements from other people, or from their agents, and reports back. It is
            designed around the open standards emerging for agents that work on someone’s behalf.
          </SectionHeading>
          <div className="rounded-lg border border-line bg-panel p-6">
            <AgentLink />
            <ol className="mt-6 space-y-3 text-sm">
              {EXCHANGE.map((m, i) => (
                <li key={i} className="grid grid-cols-[7.5rem_1fr] gap-3">
                  <span className={`font-mono text-xs ${m.from === "Your agent" ? "text-accent" : "text-muted"}`}>
                    {m.from}
                  </span>
                  <span>{m.text}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
        <ul className="mt-12 grid gap-8 border-t border-line pt-8 sm:grid-cols-3">
          {TRUST.map((t) => (
            <li key={t.title}>
              <h3 className="font-semibold">{t.title}</h3>
              <p className="mt-2 text-sm text-muted">{t.body}</p>
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
