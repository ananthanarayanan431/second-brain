import { StatusBadge } from "@/components/StatusBadge";
import { SectionHeading } from "@/components/ui";

const BARS = [0.4, 0.8, 0.55, 1, 0.65, 0.9, 0.45, 0.75, 0.5];

const TRANSCRIPT = [
  { from: "you", text: "Anything I missed this morning?" },
  {
    from: "agent",
    text: "Ravi replied about the launch at 9:12. He needs a yes or no by noon. Want me to draft a reply, or talk to him for you?",
  },
  { from: "you", text: "Tell him yes, and ask for the final deck." },
] as const;

function Phone() {
  return (
    <div className="mx-auto w-full max-w-xs rounded-3xl border border-line bg-panel p-3">
      <div className="rounded-2xl border border-line bg-ink p-5">
        <div className="flex items-center justify-between font-mono text-xs text-muted">
          <span>Neramind</span>
          <span className="flex items-center gap-1.5 text-accent">
            <span aria-hidden="true" className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent" />
            listening
          </span>
        </div>
        <ul className="mt-5 space-y-3 text-sm">
          {TRANSCRIPT.map((line, i) => (
            <li
              key={i}
              className={
                line.from === "you"
                  ? "ml-8 rounded-lg rounded-br-sm bg-raised px-3 py-2"
                  : "mr-4 rounded-lg rounded-bl-sm border border-accent/30 px-3 py-2 text-text"
              }
            >
              <span className="sr-only">{line.from === "you" ? "You: " : "Agent: "}</span>
              {line.text}
            </li>
          ))}
        </ul>
        <div aria-hidden="true" className="mt-6 flex h-10 items-end justify-center gap-1">
          {BARS.map((h, i) => (
            <span
              key={i}
              className="voice-bar w-1.5 rounded-full bg-accent"
              style={{ height: `${h * 100}%`, animationDelay: `${i * 0.09}s` }}
            />
          ))}
        </div>
        <p className="mt-3 text-center font-mono text-xs text-muted">double-tap to talk</p>
      </div>
    </div>
  );
}

export function VoiceAgent() {
  return (
    <section id="voice" className="scroll-mt-16 border-b border-line">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2">
        <div>
          <StatusBadge status="soon" />
          <div className="mt-4">
            <SectionHeading eyebrow="Voice first" title="Double-tap. Talk. Done.">
              Neramind lives on your phone. Double-tap and speak, the way you would to an
              assistant who already knows your day. No apps to open, no forms to fill.
            </SectionHeading>
          </div>
          <ul className="mt-8 space-y-3 text-muted">
            <li>It answers from everything you have read and connected.</li>
            <li>It tells you what changed, and what needs a decision.</li>
            <li>It offers to handle the follow-up, and waits for your yes.</li>
          </ul>
        </div>
        <Phone />
      </div>
    </section>
  );
}
