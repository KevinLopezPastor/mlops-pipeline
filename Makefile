SHELL := bash
AWS_PROFILE_NAME := ml-roadmap

# Short-lived SSO credentials from the host profile, exported into this shell only (never written to disk).
AWS_LOG := aws sso login --profile $(AWS_PROFILE_NAME) --no-browser
AWS_ENV := eval "$$(aws configure export-credentials --profile $(AWS_PROFILE_NAME) --format env)"

PREFECT_URL := http://127.0.0.1:4200
# Exported so every recipe talks to the local server; without it Prefect falls back to a temporary
# SQLite server that times out on a cold start.
export PREFECT_API_URL := $(PREFECT_URL)/api

.PHONY: up down pipeline prefect-up prefect-down test lint

up:
	$(AWS_LOG) && $(AWS_ENV) && docker compose up -d --build

# Compose validates the AWS variables on every command, so down needs them too.
down:
	$(AWS_LOG) && $(AWS_ENV) && docker compose down

# -m, not a script path: it puts the repo root on sys.path, which `schemas` (imported by validate) needs.
# Run `make up` first; the MLflow server proxies artifacts, so the client needs no AWS credentials.
pipeline: prefect-up
	uv run python -m flows.training_flow

# Idempotent: starts a detached local Prefect server only if nothing answers on the health endpoint.
prefect-up:
	@curl -sf $(PREFECT_URL)/api/health >/dev/null || { \
		echo "Starting Prefect server (log: .prefect-server.log)"; \
		nohup uv run prefect server start > .prefect-server.log 2>&1 & \
		for i in $$(seq 1 60); do \
			curl -sf $(PREFECT_URL)/api/health >/dev/null && exit 0; sleep 1; \
		done; \
		echo "Prefect server did not come up in 60 s; see .prefect-server.log"; exit 1; }

# Run from the repo root: tasks read params.yaml relative to the working directory.
test:
	uv run pytest -q

# Same two checks CI runs: lint rules, then formatting (check only, never rewrites files).
lint:
	uv run ruff check .
	uv run ruff format --check .

# The [p] keeps pkill from matching its own command line.
prefect-down:
	-pkill -f '[p]refect server start'
