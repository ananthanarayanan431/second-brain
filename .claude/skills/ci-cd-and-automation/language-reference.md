# CI Gate Commands by Language

Read the section for the project's language. Every language runs the same gates from `SKILL.md`; only the tools change. Tools listed here are common, well-maintained defaults: if the project already uses a different tool for a gate, keep the project's tool.

In workflow snippets, `@<latest>` means: use the action's current release, pinned to its full commit SHA.

## Contents

- [Language-neutral workflow template](#language-neutral-workflow-template)
- [Node.js / TypeScript](#nodejs--typescript)
- [Python](#python)
- [Go](#go)
- [Java / Kotlin](#java--kotlin)
- [.NET (C#, F#)](#net-c-f)
- [Rust](#rust)
- [Repos with more than one language](#repos-with-more-than-one-language)

## Language-neutral workflow template

The workflow only sets up the toolchain and calls the project's own commands. The commands live in the repo (a `Makefile`, `justfile`, `package.json` scripts, or build-tool tasks), so developers and agents run exactly what CI runs.

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
      - uses: actions/checkout@<latest>

      # Toolchain setup: copy the "Setup" step for the project's language below

      - name: Install dependencies (from the lockfile)
        run: make install
      - name: Lint and format check
        run: make lint
      - name: Type / static check
        run: make typecheck
      - name: Test
        run: make test
      - name: Build
        run: make build
      - name: Dependency audit
        run: make audit
```

```makefile
# Makefile: one target per gate. Fill each with the commands for the project's language.
.PHONY: install lint typecheck test build audit ci
install:   ; <install from lockfile>
lint:      ; <lint> && <format check>
typecheck: ; <type checker or compiler with warnings as errors>
test:      ; <tests with coverage>
build:     ; <build the deployable artifact>
audit:     ; <dependency vulnerability scan, failing on high/critical>
ci: install lint typecheck test build audit
```

## Node.js / TypeScript

| Gate | Command |
|---|---|
| Setup | `actions/setup-node@<latest>` with `node-version-file: .nvmrc` (or `node-version`) and `cache: npm` |
| Install | `npm ci` (pnpm: `pnpm install --frozen-lockfile`, Yarn: `yarn install --immutable`) |
| Lint + format | `npm run lint`, `npx prettier --check .` |
| Type check | `npx tsc --noEmit` (TypeScript projects) |
| Test | `npm test -- --coverage` |
| Build | `npm run build` |
| Audit | `npm audit --audit-level=high` |
| Artifact size | `size-limit` (frontend bundles) |
| Lint autofix | `npm run lint -- --fix` (the `--` is required, or npm swallows `--fix`) |

## Python

| Gate | Command |
|---|---|
| Setup | `actions/setup-python@<latest>` with `python-version-file: pyproject.toml` and `cache: pip`; or `astral-sh/setup-uv@<latest>` with `enable-cache: true` for uv projects |
| Install | `pip install -r requirements.txt` (pinned), or `uv sync --locked` |
| Lint + format | `ruff check .`, `ruff format --check .` |
| Type check | `mypy .` or `pyright` |
| Test | `pytest --cov` |
| Build | `python -m build` or `uv build` for packages; container image build for services |
| Audit | `pip-audit` (with uv: `uv run --with pip-audit pip-audit`) |
| Lint autofix | `ruff check --fix .`, `ruff format .` |

With uv, prefix tool commands with `uv run` (for example `uv run pytest --cov`) so they use the locked environment.

## Go

| Gate | Command |
|---|---|
| Setup | `actions/setup-go@<latest>` with `go-version-file: go.mod` (module caching is on by default) |
| Install | `go mod download` |
| Lint + format | `test -z "$(gofmt -l .)"` (fails if any file is unformatted), `golangci-lint run` via `golangci/golangci-lint-action@<latest>` |
| Static check | `go vet ./...` (the compiler is the type checker) |
| Test | `go test -race -coverprofile=coverage.out ./...` |
| Build | `go build ./...` |
| Audit | `go run golang.org/x/vuln/cmd/govulncheck@latest ./...` |
| Lint autofix | `gofmt -w .`, `golangci-lint run --fix` |

## Java / Kotlin

| Gate | Maven | Gradle |
|---|---|---|
| Setup | `actions/setup-java@<latest>` with `distribution: temurin`, `java-version`, `cache: maven` | `actions/setup-java@<latest>` plus `gradle/actions/setup-gradle@<latest>` |
| Install | `./mvnw -B -ntp dependency:go-offline` | resolved by the build |
| Lint + format | `./mvnw -B spotless:check` (plus Checkstyle if used) | `./gradlew spotlessCheck` (Kotlin: ktlint or detekt) |
| Static check | compiler with `-Werror`; SpotBugs or Error Prone if configured | same |
| Test | `./mvnw -B verify` with JaCoCo for coverage | `./gradlew test jacocoTestReport` |
| Build | `./mvnw -B package` | `./gradlew build` |
| Audit | OWASP dependency-check: `./mvnw org.owasp:dependency-check-maven:check -DfailBuildOnCVSS=7` | `./gradlew dependencyCheckAnalyze` with `failBuildOnCVSS = 7` |
| Lint autofix | `./mvnw spotless:apply` | `./gradlew spotlessApply` |

Always use the wrapper (`./mvnw`, `./gradlew`) so CI uses the project's pinned build-tool version. OWASP dependency-check downloads the NVD database; configure an NVD API key as a secret and cache the data directory, or the audit step will be slow.

## .NET (C#, F#)

| Gate | Command |
|---|---|
| Setup | `actions/setup-dotnet@<latest>` with `global-json-file: global.json` (or `dotnet-version`); `cache: true` requires `packages.lock.json` |
| Install | `dotnet restore --locked-mode` |
| Lint + format | `dotnet format --verify-no-changes` |
| Static check | `dotnet build --no-restore -warnaserror` (analyzers run during build) |
| Test | `dotnet test --no-build --collect:"XPlat Code Coverage"` |
| Build | `dotnet publish -c Release --no-restore` |
| Audit | NuGet Audit during restore, with high and critical findings as errors (see below) |
| Lint autofix | `dotnet format` |

`dotnet list package --vulnerable` always exits 0, so it cannot fail a CI step by itself. Instead, let NuGet Audit fail the restore. In `Directory.Build.props`:

```xml
<Project>
  <PropertyGroup>
    <NuGetAudit>true</NuGetAudit>
    <NuGetAuditMode>all</NuGetAuditMode>             <!-- include transitive packages -->
    <WarningsAsErrors>$(WarningsAsErrors);NU1903;NU1904</WarningsAsErrors>  <!-- high, critical -->
  </PropertyGroup>
</Project>
```

## Rust

| Gate | Command |
|---|---|
| Setup | `dtolnay/rust-toolchain@stable` with `components: rustfmt, clippy`; cache with `Swatinem/rust-cache@<latest>` |
| Install | `cargo fetch --locked` |
| Lint + format | `cargo fmt --all --check`, `cargo clippy --all-targets --all-features -- -D warnings` |
| Static check | covered by the compiler and Clippy |
| Test | `cargo test --locked` (coverage: `cargo llvm-cov`) |
| Build | `cargo build --release --locked` |
| Audit | `cargo audit` (install with `cargo install cargo-audit --locked`) or `cargo deny check advisories` |
| Lint autofix | `cargo fmt --all`, `cargo clippy --fix` |

## Repos with more than one language

- Give each language its own job (for example `backend` for Python, `frontend` for TypeScript), each with its own setup and gates. Use `paths` filters so a frontend-only change does not run backend jobs, but keep required checks passing for skipped jobs.
- Add one cross-language audit that reads every lockfile in the repo: OSV-Scanner (`google/osv-scanner`), run as `osv-scanner scan source -r .` or through its GitHub Action. It covers npm, PyPI, Go, Maven, NuGet, crates.io, and more.
- Services that ship as containers can share one final gate in any language: build the image and scan it before deploy.
