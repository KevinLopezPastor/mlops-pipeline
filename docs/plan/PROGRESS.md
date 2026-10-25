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

### 2026-10-25 (evening): Wed closed (`validate` done, params and logging settled)

**Done** (committed in `44c528b` and `7620afc`)
- [src/taxi/validate.py](../../src/taxi/validate.py): lazy Pandera validation; null-`index` failures (missing column) always raise;
  drops invalid rows below the threshold and re-validates so the gate returns the coerced frame (`Int32` zones); raises at or above it.
  Real data: 9,554,553 rows, min 0.0, max 1499.43.
- [params.yaml](../../params.yaml) + [src/taxi/params.py](../../src/taxi/params.py): `validate.max_invalid_fraction`, read at call time.
- Logging decision: stdlib `logging.getLogger(__name__)` in every task, `PREFECT_LOGGING_EXTRA_LOGGERS=taxi` in `.env.example`.
  `ingest` switched over, so tasks run as plain functions in tests (no `prefect_test_harness`).
- [scripts/probe_validate.py](../../scripts/probe_validate.py): throwaway probe (clean, few bad, 20% bad, missing column); replaced by pytest Friday.

**Who wrote what**
- Kevin: the `validate` logic and log messages, the decision to use stdlib logging.
- Claude scaffolded: the probe, `params.yaml`, `params.py`, the logger wiring and the `ingest` logger swap (at Kevin's request).

**Lessons**
- `exc.failure_cases.index` is the index of the failure table, not the row labels; the labels are in `failure_cases["index"]`.
- A null `index` in `failure_cases` means a schema-level failure that dropping rows cannot fix.
- `schema.validate(df)` returns the coerced frame; discarding it loses the dtype guarantee.
- WSL git has no identity and no `core.autocrlf`, so `git status` there shows false `M` files. Set `core.autocrlf input` in WSL or use one shell.

**Open**
- `dvc.yaml`: a param is only tracked by DVC if a stage lists it. Decide Thursday whether `dvc repro` owns any stage or Prefect owns all of them.
- Friday tests: end-to-end test that a bad data file fails at the gate; the flow must import `taxi.*`, not `src.taxi.*`, for log forwarding.
- Pick one shell; the shared `.venv` still breaks when Windows `uv` touches a WSL-built one.
- Uncommitted: `.gitattributes` (`*.ipynb text eol=lf`), untracked `nbk_taxi.ipynb`.

**Next step**
- Thu block: `features` (Kevin), `train` (LightGBM), `evaluate`, and log params, metrics and the DVC data hash to MLflow.

### 2026-10-25: Tue (closed), Wed in progress (`ingest` + schema done, `validate` not yet)

**Done**
- Tue closed: `dvc push` done, `dvc status -c` reports cache and remote in sync. DVC setup committed in `4ec17d0`
  ([.dvc/config](../../.dvc/config), [data/raw.dvc](../../data/raw.dvc)).
- Confirmed from Mon: MLflow UI shows version 2 with `@champion` and its tag.
- Layout decided: `src/taxi/` (the scaffold's `src/mlops_reproducible_pipeline/` removed). `module-name = "taxi"` in
  [pyproject.toml](../../pyproject.toml); deps added: `pandera`, `prefect`. Empty task modules in [src/taxi/](../../src/taxi/).
- [src/taxi/ingest.py](../../src/taxi/ingest.py): reads the 3 Parquet files, one concat, adds `duration_min`.
  Ran: 9,554,778 rows, 20 columns. (not committed)
- [schemas/trips.py](../../schemas/trips.py): strict schema (`duration_min` in 0 to 1500, zones 1 to 265, `Int32` coerced). (not committed)
- [src/taxi/validate.py](../../src/taxi/validate.py): stub with `MAX_INVALID_FRACTION = 0.05` and `TODO(human)`. (not committed)

**Design decision (gate behavior)**
- Real data has 225 rows violating the schema (180 negative durations, 22 of them below -1 min, 45 above 1500 min), 0.0024%.
  A strict hard-fail would reject every real month. Rule: drop invalid rows if under 5% of the data, fail the flow at 5% or more.
  Cleaning happens inside the gate, so `ingest` stays a pure reader.

**Who wrote what**
- Kevin: all of `ingest.py` (after 5 review rounds: empty check, single concat, `get_run_logger`), all of `schemas/trips.py`
  (bounds, 1 to 265 zones, dtype fix), the 5% tolerance decision.
- Claude scaffolded: `src/taxi/` layout and empty modules, pyproject changes, the `ingest` and `validate` stubs, the schema stub.

**Lessons**
- `pa.Column(int)` means `int64`; TLC zone IDs are `int32`. Use an exact dtype or `coerce=True`, and know which one a gate should do.
- `get_run_logger()` raises outside a run, so `task.fn()` can't be used as a plain function. Calling the task directly starts a
  temporary Prefect server (noisy `database is locked` telemetry traceback, harmless).
- TLC data has routine sub-minute negative durations (meter noise) and 2,621 zero-minute trips; zones 264 and 265 are "Unknown", valid.
- Windows and WSL share one `.venv` on `D:`; each `uv run` from the other OS deletes and rebuilds it.

**Open**
- `validate` logic not written yet (Kevin).
- Logger vs unit tests: decide `get_run_logger` (needs a Prefect run in tests) or stdlib `logging` before Friday's tests.
- Pick one shell (Windows or WSL), or set `UV_PROJECT_ENVIRONMENT` for WSL. WSL also needs its own `aws sso login`.
- Threshold lives in a constant; `params.yaml` later so DVC tracks it.
- Credential expiry (mount `~/.aws` instead of injecting keys) still undecided from Mon.
- Uncommitted: `ingest.py`, `validate.py`, `schemas/trips.py`, `scripts/smoke_registry.py` change.

**Next step**
- Write `validate` in `src/taxi/validate.py` (lazy validation, count distinct invalid row indices, drop under 5%, raise otherwise,
  schema-level failures always raise). Verify with the two commands: a real run (about 9,554,553 rows, min 0, max at most 1500)
  and a run with 20% rows set to -1 (must fail). Then Thu block: `features`, `train` (LightGBM), `evaluate`.

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
