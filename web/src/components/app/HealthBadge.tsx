"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Health } from "@/lib/types";

type State = { kind: "checking" } | { kind: "offline" } | { kind: "ready"; health: Health };

const POLL_MS = 30_000;

/** Live backend status: Postgres, Inngest, and Memgraph, plus corpus counts. */
export function HealthBadge() {
  const [state, setState] = useState<State>({ kind: "checking" });

  useEffect(() => {
    let cancelled = false;
    const check = () =>
      api
        .health()
        .then((health) => !cancelled && setState({ kind: "ready", health }))
        .catch(() => !cancelled && setState({ kind: "offline" }));
    check();
    const id = setInterval(check, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  const { label, tone } =
    state.kind === "checking"
      ? { label: "Checking…", tone: "text-muted border-line" }
      : state.kind === "offline"
        ? { label: "Backend offline", tone: "text-danger border-danger/40" }
        : state.health.status === "ok"
          ? { label: "All systems ok", tone: "text-accent border-accent/40" }
          : { label: "Degraded", tone: "text-soon border-soon/40" };

  return (
    <details className="relative">
      <summary
        className={`flex cursor-pointer list-none items-center gap-2 rounded-full border px-3 py-1 font-mono text-xs ${tone}`}
      >
        <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
        {label}
      </summary>
      <div className="absolute right-0 z-10 mt-2 w-64 rounded-lg border border-line bg-panel p-4 text-sm">
        {state.kind === "ready" ? (
          <dl className="grid grid-cols-2 gap-x-4 gap-y-1.5 font-mono text-xs">
            {(["database", "inngest", "memgraph"] as const).map((k) => (
              <div key={k} className="contents">
                <dt className="text-muted">{k}</dt>
                <dd className={state.health[k] === "ok" ? "text-accent" : "truncate text-danger"} title={state.health[k]}>
                  {state.health[k] === "ok" ? "ok" : "error"}
                </dd>
              </div>
            ))}
            {(["articles", "passages", "claims", "topics"] as const).map((k) => (
              <div key={k} className="contents">
                <dt className="text-muted">{k}</dt>
                <dd>{state.health[k].toLocaleString()}</dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="text-muted">
            {state.kind === "offline"
              ? "Start the backend with `make services` and `make app`."
              : "Contacting the backend…"}
          </p>
        )}
      </div>
    </details>
  );
}
