import { StatusBadge } from "@/components/StatusBadge";
import { SectionHeading } from "@/components/ui";

const TODAY = [
  { task: "Launch review with Ravi", time: "10:00", keep: true },
  { task: "Write Q4 planning doc", time: "11:30", keep: true },
  { task: "Reply to vendor contract", time: "13:00", keep: false },
  { task: "1:1 with Meera", time: "14:30", keep: true },
  { task: "Read 3 saved articles", time: "16:00", keep: false },
  { task: "Gym", time: "18:30", keep: true },
];

export function DayBalance() {
  const moved = TODAY.filter((t) => !t.keep).length;
  return (
    <section className="border-b border-line">
      <div className="mx-auto grid max-w-6xl items-center gap-12 px-4 py-20 sm:px-6 lg:grid-cols-2">
        <div className="order-2 rounded-lg border border-line bg-panel p-6 lg:order-1">
          <div className="flex items-center justify-between font-mono text-xs text-muted">
            <span>Today</span>
            <span>
              Load <span className="text-soon">high</span>
            </span>
          </div>
          <div className="mt-3 h-1.5 rounded-full bg-raised" aria-hidden="true">
            <div className="h-full w-11/12 rounded-full bg-soon" />
          </div>
          <ul className="mt-5 space-y-2 text-sm">
            {TODAY.map((t) => (
              <li key={t.task} className="flex items-center justify-between gap-4">
                <span className={t.keep ? "" : "text-muted line-through"}>{t.task}</span>
                <span className="font-mono text-xs text-muted">{t.keep ? t.time : "→ tomorrow"}</span>
              </li>
            ))}
          </ul>
          <p className="mt-6 rounded-md border border-accent/30 p-4 text-sm">
            <span className="font-semibold text-accent">Suggestion: </span>
            Move {moved} things to tomorrow. Your planning doc needs a clear head, and neither of
            these has a deadline this week. Want me to reschedule?
          </p>
        </div>
        <div className="order-1 lg:order-2">
          <StatusBadge status="soon" />
          <div className="mt-4">
            <SectionHeading eyebrow="Looks after you" title="It notices when your day is too full.">
              Because it knows your commitments and how you work, it can see overload coming. It
              suggests what to move, explains why, and takes the pressure off before it builds up.
            </SectionHeading>
          </div>
        </div>
      </div>
    </section>
  );
}
