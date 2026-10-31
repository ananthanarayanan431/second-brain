"use client";

import { type FormEvent, useState } from "react";
import { ApiError, api } from "@/lib/api";
import type { QueuedJob } from "@/lib/types";
import { buttonPrimary, ErrorNote, inputBase } from "@/components/ui";
import { JobTracker } from "./JobTracker";

type Tracked = { job: QueuedJob; label: string };

function AddForm({
  id,
  title,
  hint,
  placeholder,
  submit,
  onQueued,
}: {
  id: string;
  title: string;
  hint: string;
  placeholder: string;
  submit: (url: string) => Promise<QueuedJob>;
  onQueued: (t: Tracked) => void;
}) {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    const value = url.trim();
    if (!value) return;
    setBusy(true);
    setError(null);
    try {
      onQueued({ job: await submit(value), label: value });
      setUrl("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3 rounded-lg border border-line p-5">
      <div>
        <label htmlFor={id} className="font-semibold">
          {title}
        </label>
        <p className="mt-1 text-sm text-muted">{hint}</p>
      </div>
      <div className="flex gap-2">
        <input
          id={id}
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder={placeholder}
          className={inputBase}
        />
        <button type="submit" className={buttonPrimary} disabled={busy || !url.trim()}>
          {busy ? "Adding…" : "Add"}
        </button>
      </div>
      {error && <ErrorNote message={error} />}
    </form>
  );
}

export function SourcesPanel() {
  const [jobs, setJobs] = useState<Tracked[]>([]);
  const track = (t: Tracked) => setJobs((js) => [t, ...js]);

  return (
    <div className="space-y-8">
      <p className="text-muted">
        Teach Neramind a new source. It reads it, pulls out the claims, and wires them
        into its knowledge graph. Sources must be on the allowlist in{" "}
        <code className="font-mono text-sm text-text">publications.yaml</code>.
      </p>
      <div className="grid gap-4 lg:grid-cols-2">
        <AddForm
          id="feed-url"
          title="Follow a publication"
          hint="Its whole RSS feed is read in the background."
          placeholder="https://www.decodingai.com/feed"
          submit={api.addPublication}
          onQueued={track}
        />
        <AddForm
          id="article-url"
          title="Read one article now"
          hint="Jumps ahead of any queued backfill."
          placeholder="https://www.decodingai.com/p/…"
          submit={api.addArticle}
          onQueued={track}
        />
      </div>
      {jobs.length > 0 && (
        <section aria-labelledby="jobs-heading">
          <h2 id="jobs-heading" className="font-mono text-xs uppercase tracking-widest text-muted">
            Learning now
          </h2>
          <ul className="mt-3 space-y-3">
            {jobs.map((t) => (
              <JobTracker key={t.job.event_id} job={t.job} label={t.label} />
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
