"use client";

import { type FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { AskResponse } from "@/lib/types";
import { ART } from "@/components/Illustration";
import { buttonPrimary, EmptyState, ErrorNote, inputBase, Skeleton } from "@/components/ui";
import { AnswerView } from "./AnswerView";

const EXAMPLES = [
  "Do rerankers actually improve RAG quality?",
  "What do authors disagree on about agent evals?",
  "When should I use hybrid search instead of vectors alone?",
];

type State =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "error"; message: string }
  | { kind: "done"; result: AskResponse };

export function AskPanel() {
  const [question, setQuestion] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });

  async function ask(q: string) {
    const trimmed = q.trim();
    if (!trimmed) return;
    setState({ kind: "loading" });
    try {
      setState({ kind: "done", result: await api.ask(trimmed) });
    } catch (err) {
      setState({ kind: "error", message: err instanceof ApiError ? err.message : String(err) });
    }
  }

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    void ask(question);
  };

  return (
    <div className="space-y-8">
      <form onSubmit={onSubmit} className="space-y-3">
        <label htmlFor="question" className="text-sm font-medium">
          Ask Neramind
        </label>
        <textarea
          id="question"
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void ask(question);
            }
          }}
          placeholder="What do the newsletters you follow say about…"
          className={`${inputBase} resize-y`}
        />
        <div className="flex items-center justify-between gap-4">
          <span className="font-mono text-xs text-muted">Enter to ask · Shift+Enter for a new line</span>
          <button type="submit" className={buttonPrimary} disabled={state.kind === "loading" || !question.trim()}>
            {state.kind === "loading" ? "Thinking…" : "Ask"}
          </button>
        </div>
      </form>

      <div aria-live="polite">
        {state.kind === "idle" && (
          <EmptyState title="Ask a question to get started" art={ART.ask}>
            <p>Answers come only from what it has read, with a citation for every claim.</p>
            <ul className="mt-4 flex flex-wrap justify-center gap-2">
              {EXAMPLES.map((ex) => (
                <li key={ex}>
                  <button
                    type="button"
                    onClick={() => {
                      setQuestion(ex);
                      void ask(ex);
                    }}
                    className="rounded-full border border-line px-3 py-1 text-xs text-text transition-colors hover:border-accent"
                  >
                    {ex}
                  </button>
                </li>
              ))}
            </ul>
          </EmptyState>
        )}
        {state.kind === "loading" && <Skeleton lines={4} label="Writing an answer" />}
        {state.kind === "error" && <ErrorNote message={state.message} />}
        {state.kind === "done" && <AnswerView result={state.result} />}
      </div>
    </div>
  );
}
