"use client";

import { type FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { SearchMode, SearchResult } from "@/lib/types";
import { ART } from "@/components/Illustration";
import { buttonPrimary, EmptyState, ErrorNote, inputBase, Skeleton } from "@/components/ui";

const MODES: { id: SearchMode; label: string; hint: string }[] = [
  { id: "hybrid", label: "Hybrid", hint: "Keywords + meaning + graph, fused" },
  { id: "sparse", label: "Keyword", hint: "BM25 full-text" },
  { id: "dense", label: "Meaning", hint: "Vector similarity" },
];

const SNIPPET_CHARS = 280;

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "done"; query: string; results: SearchResult[] };

function ResultItem({ r }: { r: SearchResult }) {
  const snippet = r.text.length > SNIPPET_CHARS ? `${r.text.slice(0, SNIPPET_CHARS)}…` : r.text;
  return (
    <li className="p-4">
      <a href={r.url} target="_blank" rel="noreferrer" className="font-medium hover:text-accent">
        {r.title}
      </a>
      <p className="font-mono text-xs text-muted">
        {r.author ?? "Unknown author"}
        {r.published_at && ` · ${new Date(r.published_at).toLocaleDateString()}`}
        {typeof r.rank === "number" && ` · score ${r.rank.toFixed(3)}`}
      </p>
      {r.claim_text && (
        <p className="mt-2 text-sm">
          <span className="font-mono text-xs text-accent">{r.claim_type ?? "claim"}: </span>
          {r.claim_text}
        </p>
      )}
      <p className="mt-2 text-sm text-muted">{snippet}</p>
    </li>
  );
}

export function SearchPanel() {
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [state, setState] = useState<State>({ kind: "idle" });

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const q = query.trim();
    if (!q) return;
    setState({ kind: "loading" });
    try {
      const { results } = await api.search(q, mode);
      setState({ kind: "done", query: q, results });
    } catch (err) {
      setState({ kind: "error", message: err instanceof ApiError ? err.message : String(err) });
    }
  }

  return (
    <div className="space-y-8">
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="flex gap-2">
          <label htmlFor="search" className="sr-only">
            Search query
          </label>
          <input
            id="search"
            type="search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="agentic RAG evals"
            className={inputBase}
          />
          <button type="submit" className={buttonPrimary} disabled={state.kind === "loading" || !query.trim()}>
            Search
          </button>
        </div>
        <fieldset className="flex flex-wrap gap-2">
          <legend className="sr-only">Search mode</legend>
          {MODES.map((m) => (
            <label
              key={m.id}
              className={`cursor-pointer rounded-md border px-3 py-1.5 text-sm transition-colors has-focus-visible:outline-2 has-focus-visible:outline-accent ${
                mode === m.id ? "border-accent text-accent" : "border-line text-muted hover:text-text"
              }`}
            >
              <input
                type="radio"
                name="mode"
                value={m.id}
                checked={mode === m.id}
                onChange={() => setMode(m.id)}
                className="sr-only"
              />
              {m.label} <span className="hidden font-mono text-xs sm:inline">· {m.hint}</span>
            </label>
          ))}
        </fieldset>
      </form>

      <div aria-live="polite">
        {state.kind === "idle" && (
          <EmptyState title="Search everything your second brain has read" art={ART.search}>
            Compare modes on the same query to see what each one finds.
          </EmptyState>
        )}
        {state.kind === "loading" && <Skeleton lines={4} label="Searching" />}
        {state.kind === "error" && <ErrorNote message={state.message} />}
        {state.kind === "done" &&
          (state.results.length === 0 ? (
            <EmptyState title={`Nothing found for “${state.query}”`} art={ART.noResults}>
              Try different words, or teach it a source that covers this topic.
            </EmptyState>
          ) : (
            <ol className="divide-y divide-line rounded-lg border border-line">
              {state.results.map((r) => (
                <ResultItem key={`${r.passage_id}-${r.claim_id ?? ""}`} r={r} />
              ))}
            </ol>
          ))}
      </div>
    </div>
  );
}
