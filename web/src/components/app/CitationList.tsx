"use client";

import { useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { Citation, SourceProvenance } from "@/lib/types";
import { ErrorNote, Skeleton } from "@/components/ui";

type Detail = { kind: "loading" } | { kind: "error"; message: string } | { kind: "done"; source: SourceProvenance };

function SourceDetail({ detail }: { detail: Detail }) {
  if (detail.kind === "loading") return <Skeleton lines={2} label="Loading source" />;
  if (detail.kind === "error") return <ErrorNote message={detail.message} />;
  const s = detail.source;
  return (
    <div className="space-y-3 text-sm">
      <blockquote className="border-l-2 border-accent pl-3 text-text">“{s.verbatim_quote}”</blockquote>
      <dl className="grid grid-cols-[7rem_1fr] gap-x-3 gap-y-1 font-mono text-xs">
        <dt className="text-muted">publication</dt>
        <dd>{s.publication.name}</dd>
        <dt className="text-muted">author</dt>
        <dd>{s.author}</dd>
        {s.claim_type && (
          <>
            <dt className="text-muted">claim type</dt>
            <dd>{s.claim_type}</dd>
          </>
        )}
        <dt className="text-muted">status</dt>
        <dd>{s.validity.is_active ? "current" : "superseded"}</dd>
      </dl>
    </div>
  );
}

export function CitationList({ citations }: { citations: Citation[] }) {
  const [open, setOpen] = useState<Record<string, Detail>>({});

  async function toggle(c: Citation) {
    const id = c.claim_id ?? c.passage_id;
    if (open[id]) {
      setOpen((o) => {
        const next = { ...o };
        delete next[id];
        return next;
      });
      return;
    }
    setOpen((o) => ({ ...o, [id]: { kind: "loading" } }));
    try {
      const source = await api.source(id);
      setOpen((o) => ({ ...o, [id]: { kind: "done", source } }));
    } catch (err) {
      const message = err instanceof ApiError ? err.message : String(err);
      setOpen((o) => ({ ...o, [id]: { kind: "error", message } }));
    }
  }

  return (
    <section aria-labelledby="sources-heading">
      <h2 id="sources-heading" className="font-mono text-xs uppercase tracking-widest text-muted">
        Sources
      </h2>
      <ol className="mt-3 divide-y divide-line rounded-lg border border-line">
        {citations.map((c) => {
          const id = c.claim_id ?? c.passage_id;
          const detail = open[id];
          return (
            <li key={c.citation_idx} id={`cite-${c.citation_idx}`} className="scroll-mt-20 p-4">
              <div className="flex items-start gap-3">
                <span className="font-mono text-sm text-accent">[{c.citation_idx}]</span>
                <div className="min-w-0 flex-1">
                  <a href={c.url} target="_blank" rel="noreferrer" className="font-medium hover:text-accent">
                    {c.title}
                  </a>
                  <p className="text-sm text-muted">
                    {c.author ?? "Unknown author"}
                    {c.claim_type && ` · ${c.claim_type}`}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => void toggle(c)}
                  aria-expanded={Boolean(detail)}
                  className="shrink-0 font-mono text-xs text-muted hover:text-accent"
                >
                  {detail ? "Hide" : "Inspect"}
                </button>
              </div>
              {detail && (
                <div className="mt-4 pl-8">
                  <SourceDetail detail={detail} />
                </div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
