// Response shapes of the FastAPI backend (second_brain/main.py).

export type Health = {
  status: "ok" | "degraded";
  database: string;
  inngest: string;
  memgraph: string;
  articles: number;
  passages: number;
  claims: number;
  topics: number;
};

export type Citation = {
  citation_idx: number;
  passage_id: string;
  title: string;
  author: string | null;
  url: string;
  claim_id?: string;
  claim_type?: string | null;
};

export type AskResponse = {
  answer: string;
  citations: Citation[];
  as_of: string;
  snapshot_id: string;
  latency_ms: number;
};

export type SearchMode = "hybrid" | "sparse" | "dense";

export type SearchResult = {
  passage_id: string;
  text: string;
  title: string;
  author: string | null;
  url: string;
  published_at: string | null;
  rank?: number;
  claim_id?: string;
  claim_text?: string;
  claim_type?: string;
};

export type SearchResponse = { mode: SearchMode; results: SearchResult[] };

export type QueuedJob = { event_id: string; trace_url: string; status: string };

export type JobStatus = {
  status: string;
  articles_done: number | null;
  articles_total: number | null;
  run_status: string | null;
  failures: unknown[];
  trace_url: string;
};

export type SourceProvenance = {
  kind: "claim" | "passage";
  id: string;
  article: { title: string; url: string; published_at: string };
  publication: { name: string; slug: string; homepage: string };
  author: string;
  verbatim_quote: string;
  claim_text?: string;
  claim_type?: string;
  confidence?: number;
  validity: { valid_from: string; valid_to: string | null; is_active: boolean };
};
