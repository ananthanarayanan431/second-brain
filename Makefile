.DEFAULT_GOAL := help
.PHONY: help install start services app stop logs reset nuke db-clear \
	migrate migration downgrade db-current mcp calibrate replay \
	format lint test check

-include .env
export

# Compose reads .env from infra/ by default; pass the repo-root .env only when
# it exists, so every target still works before you have copied .env.example.
COMPOSE := docker compose -f infra/docker-compose.yml $(if $(wildcard .env),--env-file .env)
REPO_DIR := $(shell pwd)
LAB_PORT ?= 8000

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies (uv sync)
	uv sync

# --- Running ---------------------------------------------------------------

start: services migrate app ## Start services, apply migrations, run the app

services: ## Start Postgres, Memgraph, and Inngest; wait until healthy
	$(COMPOSE) up -d --wait

app: ## Run the FastAPI app with reload on LAB_PORT
	uv run python -m uvicorn second_brain.main:app --reload --port $(LAB_PORT)

mcp: ## Run the second-brain MCP server (stdio)
	uv run second-brain-mcp

stop: ## Stop the containers (data is kept)
	$(COMPOSE) down

logs: ## Follow container logs
	$(COMPOSE) logs -f

# Destructive: drops the named volumes.
reset: ## Stop the containers and DELETE their volumes
	$(COMPOSE) down -v

# More destructive than `reset`: also kills any stray app process left
# holding $(LAB_PORT). uvicorn --reload's actual worker process can survive
# a plain `pkill -f uvicorn` (its argv doesn't match the reloader's) and can
# even lose the "second_brain.main:app" string entirely once Python's
# multiprocessing re-execs it as a generic "spawn_main(...)" bootstrap — so
# this matches on the repo's own path (present in the worker's venv
# interpreter path either way) instead of any command-line string, and only
# ever targets processes rooted under this checkout. Use this when
# start/reset leave things in a weird state, not for routine teardown.
nuke: ## reset, plus kill stray app processes from this repo on LAB_PORT
	$(COMPOSE) down -v --remove-orphans
	@for pid in $$(lsof -ti:$(LAB_PORT) 2>/dev/null); do \
		if ps -p "$$pid" -o command= 2>/dev/null | grep -qF "$(REPO_DIR)"; then \
			echo "Killing stray process on :$(LAB_PORT) rooted in this repo: $$pid"; \
			kill -9 "$$pid"; \
		fi; \
	done

# --- Database --------------------------------------------------------------

migrate: ## Apply all Alembic migrations (upgrade head)
	uv run alembic upgrade head

migration: ## Autogenerate a migration: make migration MSG="add x column"
	@test -n "$(MSG)" || { echo 'Usage: make migration MSG="describe the change"'; exit 1; }
	uv run alembic revision --autogenerate -m "$(MSG)"
	@echo "Review the generated file in alembic/versions/ before running 'make migrate'."

downgrade: ## Roll back the most recent migration
	uv run alembic downgrade -1

db-current: ## Show the applied revision and whether models match the database
	uv run alembic current
	uv run alembic check

# Destructive: deletes every row from every app table (not the schema —
# migrations stay applied) and empties Memgraph, without tearing down the
# containers. Faster than `reset` when you just want a clean corpus mid-session.
db-clear: ## DELETE all rows in Postgres and all nodes in Memgraph
	$(COMPOSE) exec -T postgres psql -U "$${POSTGRES_USER:-second_brain}" -d "$${POSTGRES_DB:-second_brain}" -c \
		"DO \$$\$$ DECLARE r RECORD; BEGIN FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename <> 'alembic_version') LOOP EXECUTE 'TRUNCATE TABLE ' || quote_ident(r.tablename) || ' RESTART IDENTITY CASCADE'; END LOOP; END \$$\$$;"
	$(COMPOSE) exec -T memgraph sh -c "echo 'MATCH (n) DETACH DELETE n;' | mgconsole" || true

# --- Scripts ---------------------------------------------------------------

calibrate: ## Calibrate the LLM judges: make calibrate MODE=live (default offline)
	uv run python scripts/calibrate_judges.py --mode $(or $(MODE),offline)

replay: ## Replay backfill: make replay ARGS="--verify" (or --all, --slug <slug>)
	uv run python scripts/replay_backfill.py $(or $(ARGS),--verify)

# --- Quality ---------------------------------------------------------------

format: ## Format and auto-fix lint issues
	uv run ruff format .
	uv run ruff check --fix .

lint: ## Lint, check formatting, and type-check
	uv run ruff check .
	uv run ruff format --check .
	uv run mypy

test: ## Run the test suite
	uv run pytest

check: lint test ## lint + test (run before committing)
