# Week 1 progress

## Done when

- [ ] `make pipeline` on a clean clone registers a model with the same metrics
- [ ] MLflow run tagged with the DVC data hash and git commit
- [ ] Bad data fails at the Pandera gate
- [ ] CI green, archify PNG in the README

## Stretch ideas (parked)

- Offline mode: `docker-compose.offline.yml` override with RustFS (maintained S3-compatible store) plus a
  bucket-init container, selected with `make up-offline`. Only `.env` differs (artifact URI, endpoint,
  credentials). One branch, no long-lived second branch. See "Decisions" in week-01.md for why not MinIO.

## Sessions

<!-- /checkpoint adds a new entry here, newest first -->

### 2026-10-22: Mon (done), compressing Mon + Tue + Wed into one day

**Done** (nothing committed yet; last commit is `3b34154`)
- Stack: [docker-compose.yml](../../docker-compose.yml) (Postgres + MLflow 3.17.2, proxied artifacts to S3),
  [Dockerfile.mlflow](../../Dockerfile.mlflow), [.env.example](../../.env.example), [Makefile](../../Makefile) (`up`/`down`).
- Infra: [infra/](../../infra/) with a reusable `modules/s3-bucket`; applied, bucket `mlops-repro-435466091082`.
- Smoke test: [scripts/smoke_registry.py](../../scripts/smoke_registry.py) logs, registers, sets `@champion`, loads by
  alias. Ran twice; both model artifact sets are in `s3://mlops-repro-435466091082/mlflow/`.
- Decision: real S3 instead of MinIO (images gone from registries). See "Decisions" in [week-01.md](week-01.md).
- Added deps: `mlflow==3.17.2`, `scikit-learn`; dev: `ruff`, `pytest`.

**Who wrote what**
- Kevin: all of `smoke_registry.py` (params vs metrics, register at log time, alias on the returned version, tag).
- Claude scaffolded: compose, Dockerfile, Terraform module, Makefile, `.env.example`, `scripts/download_data.sh`
  (written, not run yet).

**Lessons**
- SQLAlchemy 2.1 defaults `postgresql://` to psycopg v3; name the driver (`postgresql+psycopg2://`).
- Compose checks required variables on every command, so a bare `docker compose ps` fails without credentials.
- Injected SSO credentials expire after about 1 h; the server then answers 500 (`ExpiredToken`) on artifact upload.
- `ModelInfo.registered_model_version` is the registry version; `mlflow_version` is the library version.

**Open**
- Credential expiry: mount `~/.aws` read-only with `AWS_PROFILE` instead of exporting keys (option B, undecided).
- Pick `src/taxi/` (plan) or the scaffold's `src/mlops_reproducible_pipeline/` before Wednesday.
- Stray untracked files in the repo root (`=`, `exporting`, `naming`, `resolving`, `unpacking`) look like
  accidental output redirects from a `docker build`; delete before committing.
- Not yet confirmed: version 2 shows `@champion` and the tag in the MLflow UI.

**Next step**
- Tue block: `bash scripts/download_data.sh`, then `dvc init` and a DVC S3 remote on
  `s3://mlops-repro-435466091082/dvc` with profile `ml-roadmap`; `dvc add data/raw`; `dvc push`.
