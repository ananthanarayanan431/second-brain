import type { ReactNode } from "react";
import type { AskResponse } from "@/lib/types";
import { CitationList } from "./CitationList";

const CITATION = /\[(\d+)\]/g;

/** Turns "[2]" markers into links to the matching citation below the answer. */
function withCitationLinks(text: string, cited: Set<number>): ReactNode[] {
  const out: ReactNode[] = [];
  let last = 0;
  for (const match of text.matchAll(CITATION)) {
    const n = Number(match[1]);
    out.push(text.slice(last, match.index));
    out.push(
      cited.has(n) ? (
        <sup key={`${match.index}-${n}`}>
          <a href={`#cite-${n}`} className="font-mono text-accent hover:underline" aria-label={`Source ${n}`}>
            [{n}]
          </a>
        </sup>
      ) : (
        match[0]
      ),
    );
    last = (match.index ?? 0) + match[0].length;
  }
  out.push(text.slice(last));
  return out;
}

export function AnswerView({ result }: { result: AskResponse }) {
  const cited = new Set(result.citations.map((c) => c.citation_idx));
  const paragraphs = result.answer.split(/\n{2,}/).filter((p) => p.trim());

  return (
    <article className="space-y-6">
      <div className="rounded-lg border border-line bg-panel p-6">
        <div className="space-y-4 leading-relaxed">
          {paragraphs.map((p, i) => (
            <p key={i} className="whitespace-pre-line">
              {withCitationLinks(p, cited)}
            </p>
          ))}
        </div>
        <p className="mt-6 flex flex-wrap gap-x-5 gap-y-1 border-t border-line pt-4 font-mono text-xs text-muted">
          <span>As of {new Date(result.as_of).toLocaleDateString()}</span>
          <span>{result.latency_ms.toLocaleString()} ms</span>
          <span>
            {result.citations.length} source{result.citations.length === 1 ? "" : "s"}
          </span>
        </p>
      </div>
      {result.citations.length > 0 && <CitationList citations={result.citations} />}
    </article>
  );
}
