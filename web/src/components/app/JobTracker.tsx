"use client";

import { useEffect, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { JobStatus, QueuedJob } from "@/lib/types";

const POLL_MS = 3_000;
const FINISHED = new Set(["completed", "Completed", "failed", "Failed", "Cancelled"]);

/** Follows one ingestion job until it finishes. */
export function JobTracker({ job, label }: { job: QueuedJob; label: string }) {
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const poll = () =>
      api
        .job(job.event_id)
        .then((s) => {
          if (cancelled) return;
          setStatus(s);
          setError(null);
          if (!FINISHED.has(s.status) && !FINISHED.has(s.run_status ?? "")) timer = setTimeout(poll, POLL_MS);
        })
        .catch((err: unknown) => {
          if (cancelled) return;
          // A just-queued job is not visible yet (404): keep polling.
          if (err instanceof ApiError && err.status === 404) timer = setTimeout(poll, POLL_MS);
          else setError(err instanceof ApiError ? err.message : String(err));
        });
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [job.event_id]);

  const failed = status?.run_status === "Failed" || status?.status === "failed";
  const total = status?.articles_total ?? 0;
  const done = status?.articles_done ?? 0;
  const pct = total > 0 ? Math.round((done / total) * 100) : null;

  return (
    <li className="rounded-lg border border-line bg-panel p-4">
      <div className="flex items-center justify-between gap-3">
        <p className="min-w-0 truncate text-sm font-medium" title={label}>
          {label}
        </p>
        <span className={`shrink-0 font-mono text-xs ${failed || error ? "text-danger" : "text-accent"}`}>
          {error ? "error" : (status?.status ?? "queued")}
        </span>
      </div>
      {pct !== null && (
        <div
          className="mt-3 h-1.5 rounded-full bg-raised"
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label={`${label} progress`}
        >
          <div className="h-full rounded-full bg-accent transition-all" style={{ width: `${pct}%` }} />
        </div>
      )}
      <p className="mt-2 flex flex-wrap gap-x-4 font-mono text-xs text-muted">
        {total > 0 && (
          <span>
            {done} / {total} articles
          </span>
        )}
        <a href={job.trace_url} target="_blank" rel="noreferrer" className="hover:text-accent">
          View run in Inngest ↗
        </a>
      </p>
      {error && <p className="mt-2 text-xs text-danger">{error}</p>}
    </li>
  );
}
