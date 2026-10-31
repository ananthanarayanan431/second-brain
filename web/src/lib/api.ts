import type {
  AskResponse,
  Health,
  JobStatus,
  QueuedJob,
  SearchMode,
  SearchResponse,
  SourceProvenance,
} from "./types";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const UNREACHABLE =
  "Can’t reach the Neramind backend. Start it with `make app` (and `make services`).";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    throw new ApiError(UNREACHABLE, 0);
  }
  if (!res.ok) {
    throw new ApiError(await errorMessage(res), res.status);
  }
  return (await res.json()) as T;
}

async function errorMessage(res: Response): Promise<string> {
  const detail = detailFrom(await res.text().catch(() => ""));
  if (detail) return detail;
  if (res.status >= 500) {
    // Either FastAPI crashed on this request or the proxy could not reach it;
    // the status badge in the header tells the two apart.
    return (
      `The backend returned an error (${res.status}). If it is running, check its logs: ` +
      "search and ask need OPENAI_API_KEY for embeddings and an API key for LLM_PROVIDER."
    );
  }
  return `Request failed (${res.status}).`;
}

function detailFrom(text: string): string | null {
  try {
    const body: unknown = JSON.parse(text);
    if (body && typeof body === "object" && "detail" in body) {
      const detail = (body as { detail: unknown }).detail;
      return typeof detail === "string" ? detail : JSON.stringify(detail);
    }
  } catch {
    // not JSON
  }
  return null;
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const api = {
  health: () => request<Health>("/health"),
  ask: (question: string) => request<AskResponse>("/ask", post({ question })),
  search: (q: string, mode: SearchMode, limit = 10) =>
    request<SearchResponse>(`/search?${new URLSearchParams({ q, mode, limit: String(limit) })}`),
  source: (id: string) => request<SourceProvenance>(`/sources/${encodeURIComponent(id)}`),
  addPublication: (feedUrl: string) =>
    request<QueuedJob>("/publications", post({ feed_url: feedUrl })),
  addArticle: (url: string) => request<QueuedJob>("/articles", post({ url })),
  job: (eventId: string) => request<JobStatus>(`/jobs/${encodeURIComponent(eventId)}`),
};
