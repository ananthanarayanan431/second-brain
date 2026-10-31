"use client";

import { type KeyboardEvent, useRef, useState } from "react";
import { Logo } from "@/components/Logo";
import { AskPanel } from "./AskPanel";
import { HealthBadge } from "./HealthBadge";
import { SearchPanel } from "./SearchPanel";
import { SourcesPanel } from "./SourcesPanel";

const TABS = [
  { id: "ask", label: "Ask", hint: "Answers with citations" },
  { id: "search", label: "Search", hint: "Everything it has read" },
  { id: "sources", label: "Teach it", hint: "Add a source" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export function AppWorkspace() {
  const [active, setActive] = useState<TabId>("ask");
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([]);

  // Arrow keys move between tabs (WAI-ARIA tabs pattern).
  const onKeyDown = (e: KeyboardEvent, index: number) => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    e.preventDefault();
    const next = (index + (e.key === "ArrowRight" ? 1 : -1) + TABS.length) % TABS.length;
    setActive(TABS[next].id);
    tabRefs.current[next]?.focus();
  };

  return (
    <div className="flex min-h-full flex-1 flex-col">
      <header className="border-b border-line">
        <div className="mx-auto flex h-16 max-w-4xl items-center justify-between px-4 sm:px-6">
          <Logo />
          <HealthBadge />
        </div>
      </header>

      <main id="main" className="mx-auto w-full max-w-4xl flex-1 px-4 py-10 sm:px-6">
        <h1 className="font-serif text-3xl tracking-tight sm:text-4xl">Your second brain</h1>
        <p className="mt-2 text-muted">
          Ask it anything it has read, search its memory, or teach it something new.
        </p>

        <div role="tablist" aria-label="Workspace" className="mt-8 grid grid-cols-3 gap-2 border-b border-line">
          {TABS.map((t, i) => {
            const selected = t.id === active;
            return (
              <button
                key={t.id}
                ref={(el) => {
                  tabRefs.current[i] = el;
                }}
                id={`tab-${t.id}`}
                role="tab"
                aria-selected={selected}
                aria-controls={`panel-${t.id}`}
                tabIndex={selected ? 0 : -1}
                onClick={() => setActive(t.id)}
                onKeyDown={(e) => onKeyDown(e, i)}
                className={`-mb-px border-b-2 px-2 pb-3 text-left transition-colors ${
                  selected ? "border-accent text-text" : "border-transparent text-muted hover:text-text"
                }`}
              >
                <span className="block font-semibold">{t.label}</span>
                <span className="hidden font-mono text-xs text-muted sm:block">{t.hint}</span>
              </button>
            );
          })}
        </div>

        {TABS.map((t) => (
          <section
            key={t.id}
            id={`panel-${t.id}`}
            role="tabpanel"
            aria-labelledby={`tab-${t.id}`}
            hidden={t.id !== active}
            className="pt-8"
          >
            {t.id === "ask" && <AskPanel />}
            {t.id === "search" && <SearchPanel />}
            {t.id === "sources" && <SourcesPanel />}
          </section>
        ))}
      </main>
    </div>
  );
}
