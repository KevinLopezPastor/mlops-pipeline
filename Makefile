SHELL := bash
AWS_PROFILE_NAME := ml-roadmap

# Short-lived SSO credentials from the host profile, exported into this shell only (never written to disk).
AWS_ENV := eval "$$(aws configure export-credentials --profile $(AWS_PROFILE_NAME) --format env)"

.PHONY: up down pipeline

up:
	$(AWS_ENV) && docker compose up -d --build

# Compose validates the AWS variables on every command, so down needs them too.
down:
	$(AWS_ENV) && docker compose down

# -m, not a script path: it puts the repo root on sys.path, which `schemas` (imported by validate) needs.
# Run `make up` first; the MLflow server proxies artifacts, so the client needs no AWS credentials.
pipeline:
	uv run python -m flows.training_flow
