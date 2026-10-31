# Production Patterns for HTTP APIs

Read this when an HTTP API will be used by real clients in production. `SKILL.md` covers the design principles; this file covers the operational patterns that keep an API correct under retries, load, concurrent edits, and change.

Everything here is language-agnostic. HTTP and JSON examples are the contract itself. Code snippets (TypeScript, SQL) are **examples only**; implement them with the project's own language, framework, and database tooling, as described in `SKILL.md` under "Code examples are illustrative, not prescriptive".

## Contents

- [Error responses (RFC 9457)](#error-responses-rfc-9457)
- [Success responses](#success-responses)
- [Pagination](#pagination)
- [Idempotency keys](#idempotency-keys)
- [Rate limiting](#rate-limiting)
- [Authentication and authorization](#authentication-and-authorization)
- [Concurrency control (ETags)](#concurrency-control-etags)
- [PATCH semantics](#patch-semantics)
- [Versioning and deprecation](#versioning-and-deprecation)
- [OpenAPI contract](#openapi-contract)
- [Request tracing](#request-tracing)

## Error responses (RFC 9457)

Every error uses `Content-Type: application/problem+json`:

```http
HTTP/1.1 422 Unprocessable Content
Content-Type: application/problem+json

{
  "type": "https://api.example.com/problems/validation-error",
  "title": "Validation failed",
  "status": 422,
  "detail": "2 fields are invalid.",
  "instance": "/api/v1/tasks",
  "success": false,
  "code": "VALIDATION_ERROR",
  "requestId": "req_7Hc2x9",
  "errors": [
    { "field": "title", "message": "Required" },
    { "field": "dueDate", "message": "Must be an ISO 8601 date" }
  ]
}
```

Rules:

- `type` and `code` are stable identifiers. Never change them once published.
- `title` is stable per `type`. `detail` may vary per occurrence.
- Never put stack traces, SQL, internal hostnames, or secrets in any field. Log them server-side under the same `requestId`.
- Use one central error handler or middleware so every endpoint produces this shape.
- Always include `"success": false` so clients can check one field on every response, success or error.

## Success responses

Every 2xx response with a body uses the envelope from `SKILL.md` section 3: `success`, `data`, `meta`, and (for lists) `links`.

### Status codes and bodies

| Situation | Status | Body | Headers |
|---|---|---|---|
| Read one resource | `200 OK` | Envelope, `data` is the object | `ETag` |
| Read a list | `200 OK` | Envelope, `data` is an array (may be `[]`), plus `meta.pagination` and `links` | |
| Create | `201 Created` | Envelope, `data` is the created resource with server-generated fields | `Location: /api/v1/tasks/tsk_8f3a2c` |
| Update (PATCH/PUT) | `200 OK` | Envelope, `data` is the full updated resource | New `ETag` |
| Delete | `204 No Content` | **No body** (no envelope) | |
| Long-running work accepted | `202 Accepted` | Envelope, `data` is a job: `{ "id", "status": "pending", "statusUrl" }` | `Location` of the job |
| Action with no resource to return (for example "resend email") | `202 Accepted` or `204 No Content` | Envelope if 202, nothing if 204 | |

Rules:

- `204` responses have no body at all, so they carry no envelope. Clients treat `204` as success without parsing.
- Return the **full** resource after create and update, so clients do not need a follow-up GET.
- Non-JSON responses (file downloads, CSV exports, redirects) are not wrapped; they use the right `Content-Type` and status only.
- `meta` may grow over time (for example `meta.warnings`, `meta.deprecation`). Clients must ignore unknown `meta` fields.

### One response helper

Build every success and error response in one place so no endpoint drifts from the contract. The example below uses TypeScript and Express **for illustration only**; write the equivalent in the project's framework (for example a FastAPI response model and helper, a Go `respond` package, or a Spring `ResponseEntity` factory):

```typescript
// http/respond.ts
export function ok<T>(res: Response, data: T, status: 200 | 201 | 202 = 200) {
  return res.status(status).json({
    success: true,
    data,
    meta: { requestId: res.locals.requestId },
  });
}

export function paginated<T>(
  req: Request, res: Response, data: T[],
  { page, pageSize, totalItems }: { page: number; pageSize: number; totalItems: number },
) {
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const url = (p: number) => {
    const u = new URL(req.originalUrl, 'http://local');
    u.searchParams.set('page', String(p));
    u.searchParams.set('pageSize', String(pageSize));
    return `${u.pathname}${u.search}`;
  };
  return res.status(200).json({
    success: true,
    data,
    meta: {
      requestId: res.locals.requestId,
      pagination: {
        page, pageSize, totalItems, totalPages,
        hasNextPage: page < totalPages,
        hasPreviousPage: page > 1,
      },
    },
    links: {
      self: url(page),
      first: url(1),
      last: url(totalPages),
      next: page < totalPages ? url(page + 1) : null,
      prev: page > 1 ? url(page - 1) : null,
    },
  });
}

export function noContent(res: Response) {
  return res.status(204).end();
}
```

Whatever the language, the helper must:

- Wrap every 2xx JSON body in the envelope (`success`, `data`, `meta`, and `links` for lists).
- Take `requestId` from the request context, never generate a second one.
- Keep every existing filter and sort parameter in the page links, so following `next` returns the next page of the **same** query.
- Be the only place in the codebase that writes a success response body.

## Pagination

Use page-number pagination so users can jump to any page.

```http
GET /api/v1/tasks?page=35&pageSize=20&sortBy=createdAt&sortOrder=desc
```

```json
{
  "success": true,
  "data": [],
  "meta": {
    "requestId": "req_7Hc2x9",
    "pagination": { "page": 35, "pageSize": 20, "totalItems": 1420, "totalPages": 71, "hasNextPage": true, "hasPreviousPage": true }
  },
  "links": {
    "self": "/api/v1/tasks?page=35&pageSize=20&sortBy=createdAt&sortOrder=desc",
    "first": "/api/v1/tasks?page=1&pageSize=20&sortBy=createdAt&sortOrder=desc",
    "last": "/api/v1/tasks?page=71&pageSize=20&sortBy=createdAt&sortOrder=desc",
    "next": "/api/v1/tasks?page=36&pageSize=20&sortBy=createdAt&sortOrder=desc",
    "prev": "/api/v1/tasks?page=34&pageSize=20&sortBy=createdAt&sortOrder=desc"
  }
}
```

Rules:

- `page` starts at 1. Enforce a default `pageSize` (for example 20) and a maximum (for example 100). Return 400 for a non-positive or non-numeric `page` or `pageSize`.
- A `page` beyond `totalPages` returns `200` with an empty `data` array, not 404.
- Always sort by a unique tiebreaker after the requested sort (usually `id`), so rows with equal sort values do not move between pages:
  `ORDER BY created_at DESC, id DESC LIMIT :pageSize OFFSET (:page - 1) * :pageSize`
- Back the sort with a composite index on `(sort_column, id)`.
- If deep pages get slow on large tables, select only the ids with `OFFSET` first, then join back for the full rows (a "deferred join"):
  `SELECT t.* FROM tasks t JOIN (SELECT id FROM tasks ORDER BY created_at DESC, id DESC LIMIT :pageSize OFFSET :offset) p ON p.id = t.id ORDER BY t.created_at DESC, t.id DESC`
- Run the `COUNT(*)` for `totalItems` with the same filters as the page query. On very large tables, consider caching the count briefly.

## Idempotency keys

Any POST that creates a record or causes a side effect (payment, email, order) must be safe to retry.

```http
POST /api/v1/payments
Idempotency-Key: 5f1c2a8e-4b6d-4e2f-9a31-0c7d8e9f1a2b
```

Server behavior:

1. Look up the key, scoped to the authenticated caller.
2. **Not seen:** process the request, then store the key with a hash of the request body and the response (status + body).
3. **Seen with the same body hash:** return the stored response. Do not process again.
4. **Seen with a different body hash:** return 422; the client reused a key for a different request.
5. **Still in progress:** return 409 so the client retries later.
6. Expire keys after a fixed window (24 hours is common).

PUT and DELETE are idempotent by definition and do not need a key.

## Rate limiting

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/problem+json
Retry-After: 30
RateLimit-Policy: "default";q=100;w=60
RateLimit: "default";r=0;t=30
```

- Limit per authenticated identity (API key, user, or tenant), falling back to IP for anonymous traffic.
- Always send `Retry-After` on 429 so clients back off correctly.
- `RateLimit-Policy` / `RateLimit` follow the IETF RateLimit header fields draft; use them, or the widely used `X-RateLimit-Limit` / `X-RateLimit-Remaining` / `X-RateLimit-Reset`, but pick one and use it consistently.
- Apply tighter limits to expensive or abuse-prone endpoints (login, search, exports).

## Authentication and authorization

- Decide auth for every endpoint explicitly. Default to "authenticated required"; mark public endpoints as exceptions.
- Send credentials in the `Authorization` header (`Bearer <token>`), never in the URL, where they leak into logs and browser history.
- Authenticate (who are you, 401) separately from authorize (may you do this, 403).
- Check ownership on every resource access, not only on list endpoints. `GET /api/v1/tasks/:id` must verify the caller can see that task (prevents IDOR).
- Return 404 instead of 403 when revealing that a resource exists would itself leak information.

## Concurrency control (ETags)

Prevent lost updates when two clients edit the same resource:

```http
GET /api/v1/tasks/tsk_8f3a2c
ETag: "v7"

PATCH /api/v1/tasks/tsk_8f3a2c
If-Match: "v7"
```

- If the current version is still `"v7"`, apply the change and return the new `ETag`.
- If it changed, return **412 Precondition Failed** and let the client re-fetch and retry.
- A numeric `version` column incremented on every write is the simplest ETag source.
- Optionally return 428 Precondition Required when a client omits `If-Match` on a resource that requires it.

## PATCH semantics

Use JSON Merge Patch ([RFC 7396](https://www.rfc-editor.org/rfc/rfc7396)), `Content-Type: application/merge-patch+json`:

| Request body | Meaning |
|---|---|
| Field omitted | Leave unchanged |
| `"field": "value"` | Set to value |
| `"field": null` | Clear the field (422 if the field is required) |

Validate the merged result, not only the patch, so cross-field rules still hold. If clients need array element operations (insert at index, move), use JSON Patch (RFC 6902) instead and document it.

## Versioning and deprecation

### Choosing a versioning scheme

| Scheme | Example | Strengths | Weaknesses | Use when |
|---|---|---|---|---|
| **URL path** (default) | `/api/v1/tasks` | Visible in logs, links, and browser; trivial to route, cache, and test | Version appears in every URL | Almost always. The default for this project. |
| Header / media type | `Accept: application/vnd.app.v2+json` | Clean, stable URLs | Invisible in logs and links; harder to test with a browser or curl; caches need `Vary: Accept` | A strong existing convention requires it |
| Date-based | `Api-Version: 2025-01-15` | Fine-grained, per-client pinning (Stripe style) | Needs a version-transform layer and per-account pinning; heavy to maintain | Large public API with many external integrators and frequent changes |

Pick one scheme for the whole API and never mix them.

### Version rules

- Only the **major** version appears in the URL (`/v1`, `/v2`). Never `/v1.2`; minor and patch changes are additive by definition and ship without a new version.
- Start at `/v1` on day one, even for internal or early-stage APIs.
- Version the whole API surface together. When `/v2` ships, every resource is reachable under `/v2`, even unchanged ones (they can share handlers).
- Unversioned paths (`/api/tasks`) must not exist; return 404, or redirect only if clients were already using them.

### What clients must tolerate

State these in the API documentation so additive change stays non-breaking:

- **Unknown fields** in responses are ignored, never rejected (no strict "additional properties forbidden" parsing on the client).
- **Unknown enum values** fall back to a safe default (for example display "Unknown status") instead of crashing.
- **Field order** in JSON objects carries no meaning.
- **New optional request parameters** may appear; existing calls keep working without them.

### What counts as breaking

- Additive changes (new optional fields, new endpoints, new enum values clients are told to tolerate) never need a new version. (new optional fields, new endpoints, new enum values clients are told to tolerate) never need a new version.
- Breaking changes need a new major version, for example `/v2`. These include: removing or renaming a field, endpoint, or enum value; changing a field's type or format; making an optional request field required; tightening validation; changing default values, status codes, error `type`/`code` values, or pagination behavior; and changing authentication requirements.

### Retiring a version

- Announce deprecation with the `Deprecation` and `Sunset` response headers and a `Link` to migration docs:

```http
Deprecation: @1735689600
Sunset: Wed, 31 Dec 2025 23:59:59 GMT
Link: <https://api.example.com/docs/migrate-v2>; rel="deprecation"
```

- Monitor traffic on the old version and retire it on the announced date. See the `deprecation-and-migration` skill.

## OpenAPI contract

- Keep an OpenAPI 3.1 document as the source of truth for HTTP APIs, either written first or generated from code (FastAPI, zod-to-openapi, NestJS Swagger).
- Commit it to the repo and review changes to it like code.
- Run a breaking-change check in CI (for example `oasdiff breaking`) against the main branch's spec.
- Generate client types or SDKs from the spec instead of hand-writing them.

## Request tracing

- Accept or generate a request ID for every request and return it in a response header (for example `X-Request-Id`) and in error bodies.
- Propagate W3C `traceparent` to downstream services when distributed tracing is in place.
- Log the request ID with every log line for that request, so a client's error report maps to server logs.
