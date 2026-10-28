SHELL := bash
AWS_PROFILE_NAME := ml-roadmap

# Short-lived SSO credentials from the host profile, exported into this shell only (never written to disk).
AWS_LOG := aws sso login --profile $(AWS_PROFILE_NAME) --no-browser
AWS_ENV := eval "$$(aws configure export-credentials --profile $(AWS_PROFILE_NAME) --format env)"

PREFECT_URL := http://127.0.0.1:4200
# Exported so every recipe talks to the local server; without it Prefect falls back to a temporary
# SQLite server that times out on a cold start.
export PREFECT_API_URL := $(PREFECT_URL)/api

.PHONY: up down pipeline reproduce demo smoke prefect-up prefect-down test lint

up:
	$(AWS_LOG) && $(AWS_ENV) && docker compose up -d --build

# Compose validates the AWS variables on every command, so down needs them too.
down:
	$(AWS_LOG) && $(AWS_ENV) && docker compose down

# DVC decides whether the `training` stage must run (dvc.yaml); it then runs the flow below.
# Needs data/raw (`dvc pull`) and `make up`; the MLflow server proxies artifacts, so no AWS credentials here.
# DVC skips an unchanged stage; `make pipeline ARGS=--force` re-runs it.
pipeline: prefect-up
	uv run dvc repro $(ARGS)

# For a fresh clone: pull the data version pinned in data/raw.dvc, then always run the flow and register a
# model. Unlike `pipeline`, it never skips on dvc.lock and never rewrites data/raw.dvc, so git_dirty stays False.
# Needs `make up` and an AWS profile for the DVC remote (`aws sso login --profile ml-roadmap`).
reproduce: prefect-up
	uv run dvc pull
	uv run python -m flows.training_flow

# The 1-minute demo, in three beats. Needs `make up`, a fresh SSO session and a clean git tree.
# 1. A bad file is rejected at the Pandera gate. 2. The real data trains and registers. 3. The lineage tags.
demo: prefect-up
	@test -z "$$(git status --porcelain)" || { echo "Working tree is not clean: lineage.git_dirty would be True."; exit 1; }
	@echo "== 1/3  Bad data (20% negative durations) must stop at the gate =="
	@bad=$$(mktemp -d) && log=$$(mktemp) && uv run python scripts/make_bad_sample.py $$bad && \
		if RAW_DIR=$$bad uv run python -m flows.training_flow > $$log 2>&1; then \
			echo "UNEXPECTED: the gate let bad data through"; rm -rf $$bad $$log; exit 1; \
		elif grep -q "exceeds allowed fraction" $$log; then \
			grep "exceeds allowed fraction" $$log | tail -n 1; \
			echo "Rejected at the gate, nothing reached training."; rm -rf $$bad $$log; \
		else echo "Failed, but not at the gate:"; tail -n 20 $$log; rm -rf $$bad $$log; exit 1; fi
	@echo "== 2/3  Real data: dvc pull, train, evaluate, register =="
	@$(MAKE) --no-print-directory reproduce
	@echo "== 3/3  Lineage of that run =="
	@uv run python scripts/show_lineage.py

# The flow without DVC, for CI: RAW_DIR and MLFLOW_TRACKING_URI come from the environment.
# -m, not a script path: it puts the repo root on sys.path, which `schemas` (imported by validate) needs.
smoke: prefect-up
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
