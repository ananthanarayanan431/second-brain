---
name: ci-cd-and-automation
description: Automates CI/CD pipeline setup for any language (Node.js, Python, Go, Java/Kotlin, .NET, Rust, and others). Use when setting up or modifying build and deployment pipelines. Use when you need to automate quality gates, configure test runners in CI, or establish deployment strategies.
---

# CI/CD and Automation

## Overview

Automate quality gates so that no change reaches production without passing tests, lint, type checking, and build. CI/CD is the enforcement mechanism for every other skill — it catches what humans and agents miss, and it does so consistently on every single change.

**Shift Left:** Catch problems as early in the pipeline as possible. A bug caught in linting costs minutes; the same bug caught in production costs hours. Move checks upstream — static analysis before tests, tests before staging, staging before production.

**Faster is Safer:** Smaller batches and more frequent releases reduce risk, not increase it. A deployment with 3 changes is easier to debug than one with 30. Frequent releases build confidence in the release process itself.

### Works with any language

The pipeline, gates, and deployment practices in this skill are language-agnostic. The YAML and code snippets use Node.js and npm **only as examples**; they are not a requirement to use Node.

When setting up CI:

1. **Detect the stack** from the manifest files in the repo: `package.json` (Node), `pyproject.toml` / `requirements.txt` (Python), `go.mod` (Go), `pom.xml` / `build.gradle(.kts)` (Java/Kotlin), `*.csproj` / `*.sln` (.NET), `Cargo.toml` (Rust). A repo can contain several; give each its own job.
2. **Use that ecosystem's tools** for every gate, from [language-reference.md](language-reference.md). Never introduce npm or a Node toolchain into a project because an example here uses it.
3. **Keep the gates identical across languages.** Lint, type/static check, tests, build, and dependency audit are required in every language; only the commands change.
4. **Prefer one command entrypoint** (`make ci`, `just ci`, a `package.json` script, a Gradle task) that runs the same checks locally and in CI, so the workflow YAML stays thin and developers and agents can reproduce CI exactly.

## When to Use

- Setting up a new project's CI pipeline
- Adding or modifying automated checks
- Configuring deployment pipelines
- When a change should trigger automated verification
- Debugging CI failures

## The Quality Gate Pipeline

Every change goes through these gates before merge:

```
Pull Request Opened
    │
    ▼
┌───────────────────────┐
│  LINT + FORMAT         │  style and common bugs, formatting check (no rewrite)
│   ↓ pass               │
│  TYPE / STATIC CHECK   │  type checker, or compiler with warnings as errors
│   ↓ pass               │
│  UNIT TESTS            │  with coverage
│   ↓ pass               │
│  BUILD                 │  produce the deployable artifact
│   ↓ pass               │
│  INTEGRATION           │  API/DB tests against real services
│   ↓ pass               │
│  E2E (optional)        │  browser or end-to-end tests
│   ↓ pass               │
│  DEPENDENCY AUDIT      │  fail on high/critical known vulnerabilities
│   ↓ pass               │
│  ARTIFACT SIZE (opt.)  │  bundle, image, or binary size budget
└───────────────────────┘
    │
    ▼
  Ready for review
```

The exact tool for each gate depends on the language. See [language-reference.md](language-reference.md) for Node.js/TypeScript, Python, Go, Java/Kotlin, .NET, and Rust.

**No gate can be skipped.** If lint fails, fix lint — don't disable the rule. If a test fails, fix the code — don't skip the test.

## GitHub Actions Configuration

The workflows below show a Node.js project **as an example**. For any other language, keep the same job structure and swap the setup step and gate commands for the ones in [language-reference.md](language-reference.md), which also has a language-neutral workflow template.

### Basic CI Pipeline

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
    branches: [main]
  push:
    branches: [main]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Lint
        run: npm run lint

      - name: Type check
        run: npx tsc --noEmit

      - name: Test
        run: npm test -- --coverage

      - name: Build
        run: npm run build

      - name: Security audit
        run: npm audit --audit-level=high
```

### With Database Integration Tests

```yaml
  integration:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: testdb
          POSTGRES_USER: ci_user
          POSTGRES_PASSWORD: ${{ secrets.CI_DB_PASSWORD }}
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - name: Run migrations
        run: npx prisma migrate deploy
        env:
          DATABASE_URL: postgresql://ci_user:${{ secrets.CI_DB_PASSWORD }}@localhost:5432/testdb
      - name: Integration tests
        run: npm run test:integration
        env:
          DATABASE_URL: postgresql://ci_user:${{ secrets.CI_DB_PASSWORD }}@localhost:5432/testdb
```

> **Note:** Even for CI-only test databases, use GitHub Secrets for credentials rather than hardcoding values. This builds good habits and prevents accidental reuse of test credentials in other contexts.

### E2E Tests

```yaml
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '22'
          cache: 'npm'
      - run: npm ci
      - name: Install Playwright
        run: npx playwright install --with-deps chromium
      - name: Build
        run: npm run build
      - name: Run E2E tests
        run: npx playwright test
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
```

## Feeding CI Failures Back to Agents

The power of CI with AI agents is the feedback loop. When CI fails:

```
CI fails
    │
    ▼
Copy the failure output
    │
    ▼
Feed it to the agent:
"The CI pipeline failed with this error:
[paste specific error]
Fix the issue and verify locally before pushing again."
    │
    ▼
Agent fixes → pushes → CI runs again
```

**Key patterns:**

```
Lint failure  → Agent runs the project's lint autofix, reviews the diff, and commits
                (e.g. `npm run lint -- --fix`, `ruff check --fix`, `golangci-lint run --fix`,
                 `cargo clippy --fix`, `dotnet format`, `./gradlew spotlessApply`)
Type error    → Agent reads the error location and fixes the type
Test failure  → Agent follows debugging-and-error-recovery skill
Build error   → Agent checks config and dependencies
Audit failure → Agent upgrades the vulnerable dependency to a fixed version, then re-runs tests
```

## Deployment Strategies

### Preview Deployments

Every PR gets a preview deployment for manual testing:

```yaml
# Deploy preview on PR (Vercel/Netlify/etc.)
deploy-preview:
  runs-on: ubuntu-latest
  if: github.event_name == 'pull_request'
  steps:
    - uses: actions/checkout@v4
    - name: Deploy preview
      run: npx vercel --token=${{ secrets.VERCEL_TOKEN }}
```

### Feature Flags

Feature flags decouple deployment from release. Deploy incomplete or risky features behind flags so you can:

- **Ship code without enabling it.** Merge to main early, enable when ready.
- **Roll back without redeploying.** Disable the flag instead of reverting code.
- **Canary new features.** Enable for 1% of users, then 10%, then 100%.
- **Run A/B tests.** Compare behavior with and without the feature.

```typescript
// Simple feature flag pattern
if (featureFlags.isEnabled('new-checkout-flow', { userId })) {
  return renderNewCheckout();
}
return renderLegacyCheckout();
```

**Flag lifecycle:** Create → Enable for testing → Canary → Full rollout → Remove the flag and dead code. Flags that live forever become technical debt — set a cleanup date when you create them.

### Staged Rollouts

```
PR merged to main
    │
    ▼
  Staging deployment (auto)
    │ Manual verification
    ▼
  Production deployment (manual trigger or auto after staging)
    │
    ▼
  Monitor for errors (15-minute window)
    │
    ├── Errors detected → Rollback
    └── Clean → Done
```

### Rollback Plan

Every deployment should be reversible:

```yaml
# Manual rollback workflow
name: Rollback
on:
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to rollback to'
        required: true

jobs:
  rollback:
    runs-on: ubuntu-latest
    steps:
      - name: Rollback deployment
        run: |
          # Deploy the specified previous version
          npx vercel rollback ${{ inputs.version }}
```

## Environment Management

```
.env.example       → Committed (template for developers)
.env                → NOT committed (local development)
.env.test           → Committed (test environment, no real secrets)
CI secrets          → Stored in GitHub Secrets / vault
Production secrets  → Stored in deployment platform / vault
```

CI should never have production secrets. Use separate secrets for CI testing.

## Automation Beyond CI

### Build Cop Role

Designate someone responsible for keeping CI green. When the build breaks, the Build Cop's job is to fix or revert — not the person whose change caused the break. This prevents broken builds from accumulating while everyone assumes someone else will fix it.

### PR Checks

- **Required reviews:** At least 1 approval before merge
- **Required status checks:** CI must pass before merge
- **Branch protection:** No force-pushes to main
- **Auto-merge:** If all checks pass and approved, merge automatically

## CI Optimization

When the pipeline exceeds 10 minutes, apply these strategies in order of impact:

```
Slow CI pipeline?
├── Cache dependencies
│   └── Use the setup action's built-in cache (npm, pip/uv, Go modules, Maven/Gradle,
│       NuGet) or actions/cache for anything else (e.g. Cargo target/)
├── Run jobs in parallel
│   └── Split lint, typecheck, test, build into separate parallel jobs
├── Only run what changed
│   └── Use path filters to skip unrelated jobs (e.g., skip e2e for docs-only PRs)
├── Use matrix builds
│   └── Shard test suites across multiple runners
├── Optimize the test suite
│   └── Remove slow tests from the critical path, run them on a schedule instead
└── Use larger runners
    └── GitHub-hosted larger runners or self-hosted for CPU-heavy builds
```

**Example: caching and parallelism**
```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      - run: npm ci
      - run: npm run lint

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      - run: npm ci
      - run: npx tsc --noEmit

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '22', cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "CI is too slow" | Optimize the pipeline (see CI Optimization below), don't skip it. A 5-minute pipeline prevents hours of debugging. |
| "This change is trivial, skip CI" | Trivial changes break builds. CI is fast for trivial changes anyway. |
| "The test is flaky, just re-run" | Flaky tests mask real bugs and waste everyone's time. Fix the flakiness. |
| "We'll add CI later" | Projects without CI accumulate broken states. Set it up on day one. |
| "Manual testing is enough" | Manual testing doesn't scale and isn't repeatable. Automate what you can. |

## Red Flags

- No CI pipeline in the project
- CI failures ignored or silenced
- Tests disabled in CI to make the pipeline pass
- Production deploys without staging verification
- No rollback mechanism
- Secrets stored in code or CI config files (not secrets manager)
- Long CI times with no optimization effort

## Verification

After setting up or modifying CI:

- [ ] All quality gates are present (lint, types, tests, build, audit)
- [ ] Every gate uses the project's own language tooling (no example toolchain copied in by mistake)
- [ ] Each language in the repo has its own job, and CI runs the same commands developers run locally
- [ ] Pipeline runs on every PR and push to main
- [ ] Failures block merge (branch protection configured)
- [ ] CI results feed back into the development loop
- [ ] Secrets are stored in the secrets manager, not in code
- [ ] Deployment has a rollback mechanism
- [ ] Pipeline runs in under 10 minutes for the test suite