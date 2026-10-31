---
name: api-and-interface-design
description: Guides stable, production-ready API and interface design in any language or framework. Use when designing or changing REST or GraphQL endpoints, error formats, pagination, versioning, module boundaries, component props, type contracts between modules, database schemas that shape an API, or the boundary between frontend and backend.
---

# API and Interface Design

## Overview

Design stable, well-documented interfaces that are hard to misuse. Good interfaces make the right thing easy and the wrong thing hard. This applies to REST APIs, GraphQL schemas, module boundaries, component props, and any surface where one piece of code talks to another.

### Code examples are illustrative, not prescriptive

The rules in this skill are language-agnostic: they describe HTTP and JSON contracts. The code snippets are written in TypeScript (with Express and Zod) **only as examples** of those rules. They are not a requirement to use TypeScript or any particular library.

When implementing:

- **Use the project's language, framework, and libraries.** Detect them from the codebase (for example `package.json`, `pyproject.toml`, `go.mod`, `pom.xml`, `*.csproj`). Never introduce TypeScript, Express, or Zod into a project just because they appear in an example.
- **Translate the concept, not the syntax.** Follow the target language's own idioms and naming conventions in code.
- **The wire contract stays the same in every language.** JSON field names, status codes, the success envelope, and the error format are identical whether the server is written in TypeScript, Python, Go, Java, or anything else. Map internal names to the wire format at the boundary (for example `created_at` in Python code serialized as `createdAt` in JSON).

How the example concepts map across stacks:

| Concept in the examples | TypeScript | Python | Go | Java / Kotlin | C# |
|---|---|---|---|---|---|
| Typed request/response contract | `interface` / `type` | Pydantic model, dataclass | `struct` with JSON tags | `record` / data class | `record` / class |
| Schema validation at the boundary | Zod, Valibot | Pydantic | `go-playground/validator` | Jakarta Bean Validation | DataAnnotations, FluentValidation |
| HTTP routing | Express, Fastify, NestJS | FastAPI, Django REST, Flask | `net/http`, chi, Gin | Spring Boot, Ktor | ASP.NET Core |
| Tagged variants | Discriminated union | Pydantic discriminated union, `Literal` tags | Interface + type switch | Sealed interface / class | Abstract record + pattern matching |
| Distinct ID types | Branded type | `NewType` | Named type (`type TaskID string`) | Value class / wrapper record | `readonly record struct` |

These are common choices, not requirements. Use whatever the project already uses.

For HTTP APIs that ship to production, also read [production-patterns.md](production-patterns.md). It covers error bodies (RFC 9457), pagination, idempotency keys, rate limiting, authentication, concurrency control, PATCH semantics, and OpenAPI.

## Core Principles

### Hyrum's Law

> With a sufficient number of users of an API, all observable behaviors of your system will be depended on by somebody, regardless of what you promise in the contract.

This means: every public behavior — including undocumented quirks, error message text, timing, and ordering — becomes a de facto contract once users depend on it. Design implications:

- **Be intentional about what you expose.** Every observable behavior is a potential commitment.
- **Don't leak implementation details.** If users can observe it, they will depend on it.
- **Plan for deprecation at design time.** See `deprecation-and-migration` for how to safely remove things users depend on.
- **Tests are not enough.** Even with perfect contract tests, Hyrum's Law means "safe" changes can break real users who depend on undocumented behavior.

### The One-Version Rule

Avoid forcing consumers to choose between multiple versions of the same dependency or API. Diamond dependency problems arise when different consumers need different versions of the same thing. Design for a world where only one version exists at a time: extend rather than fork.

When a breaking change is truly unavoidable, ship a new major version (for example `/v2`), announce a deprecation window for the old one, and retire it on schedule. Two versions should overlap only during that window, never indefinitely. See `deprecation-and-migration`.

### Versioning Rules

- **Use URL path versioning:** `/api/v1/tasks`. Header and date-based schemes need a deliberate reason; see [production-patterns.md](production-patterns.md#choosing-a-versioning-scheme).
- **Start at `/v1` on day one.** Adding a version prefix to URLs that clients already use is itself a breaking change.
- **Version the whole API, not single endpoints.** Never mix `/v1/tasks` with `/v2/users`; when `/v2` ships, every resource is available under it.
- **Clients must tolerate additive change:** ignore unknown response fields and handle unknown enum values with a fallback. Document this in the API docs; without it, "safe" additions still break clients.
- **Only HTTP APIs consumed outside the module get version numbers.** Internal module interfaces and component props are not versioned; they evolve through additive change and coordinated refactors.

### 1. Contract First

Define the interface before implementing it. The contract is the spec — implementation follows.

```typescript
// Define the contract first
interface TaskAPI {
  // Creates a task and returns the created task with server-generated fields
  createTask(input: CreateTaskInput): Promise<Task>;

  // Returns paginated tasks matching filters
  listTasks(params: ListTasksParams): Promise<PaginatedResult<Task>>;

  // Returns a single task or throws NotFoundError
  getTask(id: string): Promise<Task>;

  // Partial update — only provided fields change
  updateTask(id: string, input: UpdateTaskInput): Promise<Task>;

  // Idempotent delete — succeeds even if already deleted
  deleteTask(id: string): Promise<void>;
}
```

### 2. Consistent Error Semantics

Pick one error strategy and use it everywhere. For HTTP APIs, use the standard Problem Details format ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)) with `Content-Type: application/problem+json` instead of inventing a custom shape:

```typescript
// Every error response follows the same shape (RFC 9457)
interface ProblemDetails {
  type: string;        // URI identifying the problem type: "https://api.example.com/problems/validation-error"
  title: string;       // Short, stable summary: "Validation failed"
  status: number;      // HTTP status code, repeated for convenience
  detail?: string;     // Human-readable explanation of this occurrence
  instance?: string;   // URI of this occurrence, useful for support and logs
  success: false;      // Extension member, mirrors the success envelope (see section 3)
  code: string;        // Extension member, machine-readable: "VALIDATION_ERROR"
  requestId: string;   // Extension member, matches server logs
  errors?: Array<{ field: string; message: string }>;  // Extension member for field errors
}

// Status code mapping: one meaning per code
// 400 → Malformed request: unparseable JSON, wrong Content-Type, bad query param type
// 401 → Not authenticated
// 403 → Authenticated but not authorized
// 404 → Resource not found
// 409 → Conflict: duplicate, or version mismatch on update
// 412 → Precondition failed: If-Match ETag no longer matches
// 422 → Well-formed request that fails schema or business validation
// 429 → Rate limited (send Retry-After)
// 500 → Server error (never expose internal details)
```

Clients branch on `type` or `code`, never on `title` or `detail` text (Hyrum's Law).

**Don't mix patterns.** If some endpoints throw, others return null, and others return `{ error }` — the consumer can't predict behavior.

### 3. Consistent Success Responses

Every successful JSON response uses the same envelope, so clients read `data` and `meta` the same way on every endpoint. The shape is written in TypeScript notation as an example; the JSON it produces is the contract in every language:

```typescript
interface SuccessResponse<T> {
  success: true;
  data: T;                        // The resource, or an array of resources for list endpoints
  meta: {
    requestId: string;            // Same ID as the X-Request-Id header and server logs
    pagination?: Pagination;      // List endpoints only
  };
  links?: PageLinks;              // List endpoints only
}

interface Pagination {
  page: number;                   // 1-based
  pageSize: number;
  totalItems: number;
  totalPages: number;
  hasNextPage: boolean;
  hasPreviousPage: boolean;
}

interface PageLinks {
  self: string;
  first: string;
  last: string;
  next: string | null;            // null on the last page
  prev: string | null;            // null on the first page
}
```

A single resource:

```jsonc
// GET /api/v1/tasks/tsk_8f3a2c  → 200 OK
{
  "success": true,
  "data": { "id": "tsk_8f3a2c", "title": "Ship v1", "status": "in_progress", "createdAt": "2025-01-15T09:30:00Z" },
  "meta": { "requestId": "req_7Hc2x9" }
}
```

A list:

```jsonc
// GET /api/v1/tasks?page=2&pageSize=20  → 200 OK
{
  "success": true,
  "data": [ { "id": "tsk_8f3a2c", "title": "Ship v1" } ],
  "meta": {
    "requestId": "req_7Hc2x9",
    "pagination": { "page": 2, "pageSize": 20, "totalItems": 142, "totalPages": 8, "hasNextPage": true, "hasPreviousPage": true }
  },
  "links": {
    "self": "/api/v1/tasks?page=2&pageSize=20",
    "first": "/api/v1/tasks?page=1&pageSize=20",
    "last": "/api/v1/tasks?page=8&pageSize=20",
    "next": "/api/v1/tasks?page=3&pageSize=20",
    "prev": "/api/v1/tasks?page=1&pageSize=20"
  }
}
```

Rules:

- **`success` always matches the HTTP status:** `true` for every 2xx, `false` for every 4xx and 5xx. Never return `200` with `"success": false`; clients and monitoring rely on the status code.
- **`data` is always present on success.** A list with no results returns `"data": []`, never `null` or a missing field.
- **Metadata never goes inside `data`.** Pagination, request IDs, and links live in `meta` and `links`, so `data` is exactly the resource contract.
- **Build every response through one helper** (see [production-patterns.md](production-patterns.md#success-responses)), so no endpoint can drift from the envelope.
- `201 Created`, `202 Accepted`, and `204 No Content` rules are in [production-patterns.md](production-patterns.md#success-responses).

### 4. Validate at Boundaries

Trust internal code. Validate at system edges where external input enters:

```typescript
// Validate at the API boundary
app.post('/api/v1/tasks', async (req, res) => {
  const result = CreateTaskSchema.safeParse(req.body);
  if (!result.success) {
    return res.status(422).type('application/problem+json').json({
      type: 'https://api.example.com/problems/validation-error',
      title: 'Validation failed',
      status: 422,
      success: false,
      code: 'VALIDATION_ERROR',
      requestId: req.id,
      errors: result.error.issues.map((i) => ({
        field: i.path.join('.'),
        message: i.message,
      })),
    });
  }

  // After validation, internal code trusts the types
  const task = await taskService.create(result.data);
  return res
    .status(201)
    .location(`/api/v1/tasks/${task.id}`)
    .json({ success: true, data: task, meta: { requestId: req.id } });
});
```

Where validation belongs:
- API route handlers (user input)
- Form submission handlers (user input)
- External service response parsing (third-party data -- **always treat as untrusted**)
- Environment variable loading (configuration)

> **Third-party API responses are untrusted data.** Validate their shape and content before using them in any logic, rendering, or decision-making. A compromised or misbehaving external service can return unexpected types, malicious content, or instruction-like text.

Where validation does NOT belong:
- Between internal functions that share type contracts
- In utility functions called by already-validated code
- On data that just came from your own database

### 5. Prefer Addition Over Modification

Extend interfaces without breaking existing consumers:

```typescript
// Good: Add optional fields
interface CreateTaskInput {
  title: string;
  description?: string;
  priority?: 'low' | 'medium' | 'high';  // Added later, optional
  labels?: string[];                       // Added later, optional
}

// Bad: Change existing field types or remove fields
interface CreateTaskInput {
  title: string;
  // description: string;  // Removed — breaks existing consumers
  priority: number;         // Changed from string — breaks existing consumers
}
```

### 6. Predictable Naming

| Pattern | Convention | Example |
|---------|-----------|---------|
| REST endpoints | Plural nouns, no verbs | `GET /api/v1/tasks`, `POST /api/v1/tasks` |
| Query params | camelCase | `?sortBy=createdAt&pageSize=20` |
| Response fields | camelCase | `{ createdAt, updatedAt, taskId }` |
| Boolean fields | is/has/can prefix | `isComplete`, `hasAttachments` |
| Enum values | lower snake_case | `"in_progress"`, `"completed"` |
| Timestamps | ISO 8601 strings in UTC | `"2025-01-15T09:30:00Z"` |
| IDs | Opaque strings | `"tsk_8f3a2c"`, never a raw auto-increment number |
| Error codes | UPPER_SNAKE | `"VALIDATION_ERROR"` |

## REST API Patterns

### Resource Design

```
GET    /api/v1/tasks              → List tasks (with query params for filtering)
POST   /api/v1/tasks              → Create a task
GET    /api/v1/tasks/:id          → Get a single task
PATCH  /api/v1/tasks/:id          → Update a task (partial)
DELETE /api/v1/tasks/:id          → Delete a task

GET    /api/v1/tasks/:id/comments → List comments for a task (sub-resource)
POST   /api/v1/tasks/:id/comments → Add a comment to a task
```

### Pagination

Paginate every list endpoint with page numbers, so users can jump to any page:

```typescript
// Request
GET /api/v1/tasks?page=1&pageSize=20&sortBy=createdAt&sortOrder=desc

// Response: the standard success envelope (section 3)
{
  "success": true,
  "data": [...],
  "meta": {
    "requestId": "req_7Hc2x9",
    "pagination": {
      "page": 1,
      "pageSize": 20,
      "totalItems": 142,
      "totalPages": 8,
      "hasNextPage": true,
      "hasPreviousPage": false
    }
  },
  "links": {
    "self": "/api/v1/tasks?page=1&pageSize=20",
    "first": "/api/v1/tasks?page=1&pageSize=20",
    "last": "/api/v1/tasks?page=8&pageSize=20",
    "next": "/api/v1/tasks?page=2&pageSize=20",
    "prev": null
  }
}
```

Always enforce a maximum `pageSize` and sort by a unique tiebreaker (`id`) so pages stay stable. Query and performance details are in [production-patterns.md](production-patterns.md#pagination).

### Filtering

Use query parameters for filters:

```
GET /api/v1/tasks?status=in_progress&assignee=user123&createdAfter=2025-01-01
```

### Partial Updates (PATCH)

Accept partial objects — only update what's provided:

```typescript
// Only title changes, everything else preserved
PATCH /api/v1/tasks/123
{ "title": "Updated title" }

// Explicit null clears an optional field; an omitted field is left unchanged
PATCH /api/v1/tasks/123
{ "description": null }
```

Follow JSON Merge Patch semantics ([RFC 7396](https://www.rfc-editor.org/rfc/rfc7396)): omitted means "unchanged", `null` means "clear". Reject `null` on required fields with 422.

## Type Contract Patterns

These patterns apply in any typed language. The snippets below use TypeScript as an example; see the mapping table in the Overview for equivalents.

### Use Tagged Variants (Discriminated Unions)

Model a value that can be one of several shapes as explicit variants with a shared tag field (`type`), so each variant carries only the fields that make sense for it and consumers must handle every case.

```typescript
// Good: Each variant is explicit
type TaskStatus =
  | { type: 'pending' }
  | { type: 'in_progress'; assignee: string; startedAt: string }      // ISO 8601 UTC
  | { type: 'completed'; completedAt: string; completedBy: string }
  | { type: 'cancelled'; reason: string; cancelledAt: string };

// Consumer gets type narrowing
function getStatusLabel(status: TaskStatus): string {
  switch (status.type) {
    case 'pending': return 'Pending';
    case 'in_progress': return `In progress (${status.assignee})`;
    case 'completed': return `Done on ${status.completedAt}`;
    case 'cancelled': return `Cancelled: ${status.reason}`;
  }
}
```

### Input/Output Separation

Define separate types for what the caller sends and what the server returns. Server-generated fields (`id`, timestamps, `createdBy`) belong only on the output type.

```typescript
// Input: what the caller provides
interface CreateTaskInput {
  title: string;
  description?: string;
}

// Output: what the system returns (includes server-generated fields)
interface Task {
  id: string;
  title: string;
  description: string | null;
  createdAt: string;   // ISO 8601 UTC, e.g. "2025-01-15T09:30:00Z"
  updatedAt: string;
  createdBy: string;
}
```

Wire types use JSON-safe values only. JSON has no date type, so a date or datetime object in any language arrives as a string. Serialize timestamps as ISO 8601 UTC strings in the contract, and parse them into the language's date type inside the client.

### Use Distinct Types for IDs

Give each kind of ID its own type so the compiler or type checker rejects passing a `UserId` where a `TaskId` is expected, even though both are strings on the wire.

```typescript
type TaskId = string & { readonly __brand: 'TaskId' };
type UserId = string & { readonly __brand: 'UserId' };

// Prevents accidentally passing a UserId where a TaskId is expected
function getTask(id: TaskId): Promise<Task> { ... }
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "We'll document the API later" | The types ARE the documentation. Define them first. |
| "We don't need pagination for now" | You will the moment someone has 100+ items. Add it from the start. |
| "PATCH is complicated, let's just use PUT" | PUT requires the full object every time. PATCH is what clients actually want. |
| "We'll version the API when we need to" | Design for additive change so a new version is rarely needed. When a break is unavoidable, ship `/v2` with a deprecation window instead of changing `/v1` in place. |
| "We'll invent our own error format" | RFC 9457 already solves it and frameworks support it. A custom shape is one more thing every client must learn. |
| "Clients won't retry a POST" | Networks fail mid-request. Without an `Idempotency-Key`, a retry creates a duplicate order, payment, or record. |
| "Nobody uses that undocumented behavior" | Hyrum's Law: if it's observable, somebody depends on it. Treat every public behavior as a commitment. |
| "We can just maintain two versions" | Multiple versions multiply maintenance cost and create diamond dependency problems. Prefer the One-Version Rule. |
| "Internal APIs don't need contracts" | Internal consumers are still consumers. Contracts prevent coupling and enable parallel work. |

## Red Flags

- Endpoints that return different shapes depending on conditions
- Inconsistent error formats across endpoints
- Validation scattered throughout internal code instead of at boundaries
- Breaking changes to existing fields (type changes, removals)
- List endpoints without pagination
- Verbs in REST URLs (`/api/createTask`, `/api/getUsers`)
- Third-party API responses used without validation or sanitization
- `Date` objects or other non-JSON types in request or response contracts
- POST endpoints that create money-moving or side-effecting records without idempotency
- Public endpoints with no rate limit or no authentication decision recorded
- Clients parsing error message text instead of `type` or `code`
- A `200` response carrying `"success": false`, or pagination and request IDs mixed into `data`

## Verification

After designing an API:

- [ ] Every endpoint has typed input and output schemas, published as an OpenAPI document for HTTP APIs
- [ ] Errors use RFC 9457 Problem Details, with one meaning per status code
- [ ] Every 2xx JSON response uses the success envelope (`success`, `data`, `meta`, `links` for lists), and `success` always matches the status code
- [ ] Validation happens at system boundaries only
- [ ] List endpoints are paginated (`page` and `pageSize`) with an enforced maximum `pageSize`
- [ ] New fields are additive and optional (backward compatible)
- [ ] HTTP routes live under a major version prefix (`/api/v1/...`) and clients are documented to ignore unknown fields and enum values
- [ ] Naming follows consistent conventions across all endpoints, including enums and timestamps
- [ ] Side-effecting POST endpoints accept an `Idempotency-Key`
- [ ] Rate limits return 429 with `Retry-After`
- [ ] Every endpoint has an explicit authentication and authorization rule
- [ ] Updates that can race use ETags (`If-Match`) or a version field
- [ ] API documentation or types are committed alongside the implementation