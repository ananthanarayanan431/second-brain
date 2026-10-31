# Second Brain web

Next.js (App Router) + React + Tailwind CSS, managed with pnpm.

- `/` home page: what Second Brain is, what works today, and what is coming.
- `/app` the application: ask with citations, search, and teach it new sources.

## Run it

From the repo root:

```bash
make services   # Postgres, Memgraph, Inngest
make app        # FastAPI backend on :8000
make web        # this app on http://localhost:3001
```

The browser only calls `/api/*`; Next.js forwards those requests to the backend
(`BACKEND_URL`, default `http://localhost:8000`), so the backend needs no CORS setup.

Search and ask need `OPENAI_API_KEY` (embeddings) and the API key for `LLM_PROVIDER`
in the repo's `.env`.

## Checks

```bash
make web-check   # tsc + eslint
make web-build   # production build
```
