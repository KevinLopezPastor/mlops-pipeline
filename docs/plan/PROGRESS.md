# Week 1 progress

## Done when

- [ ] `make pipeline` on a clean clone registers a model with the same metrics
- [x] MLflow run tagged with the DVC data hash and git commit
  (run `6777263f602e47b9807abffbd427f1f1`, tags `lineage.dvc_data_hash` and `lineage.git_commit`, confirmed in the MLflow UI; re-check with
  `curl -s "http://localhost:5000/api/2.0/mlflow/runs/get?run_id=6777263f602e47b9807abffbd427f1f1" | grep -o '"lineage[^}]*'`)
- [ ] Bad data fails at the Pandera gate
  (partly: `uv run python -m scripts.probe_validate` shows 20% bad rows and a missing column both raise; the end-to-end "bad file" test is Friday's)
- [ ] CI green, archify PNG in the README

## Stretch ideas (parked)

- Offline mode: `docker-compose.offline.yml` override with RustFS (maintained S3-compatible store) plus a
  bucket-init container, selected with `make up-offline`. Only `.env` differs (artifact URI, endpoint,
  credentials). One branch, no long-lived second branch. See "Decisions" in week-01.md for why not MinIO.

- LightGBM `objective="huber"` (or `l1`): the target has a heavy tail (p99.9 = 117 min, max 1499), and the default L2 loss
  chases it while the registry compares on MAE. Try after the baseline is registered.

## Sessions

<!-- /checkpoint adds a new entry here, newest first -->

### 2026-10-25 (late night): Thu wrap-up (decision recorded, Prefect UI confirmed)

**Done**
- MAE-over-RMSE decision written into "Decisions" in [week-01.md](week-01.md) and the Thursday log committed (`9ee22b6`, `887799e`).
- Prefect UI confirmed by Kevin: a long-running `prefect server start` shows `training-flow` and its five task runs.
- [.env.example](../../.env.example): optional, commented `PREFECT_API_URL` for a persistent local server (not committed yet).
- Thu "Done when" progress: MLflow run carries the DVC hash and git commit tags (box ticked above).

**Who wrote what**
- Kevin: ran and verified the MLflow run page and the Prefect UI; decided the notebook lives in `notebooks/`.
- Claude: the `week-01.md` decision paragraph, the `.env.example` lines, this log.

**Open**
- Task logs in the flow output: confirm `get_current_settings().logging.extra_loggers` is `'taxi'` (the `.env` line had a trailing space), then check that
  `Validation gate dropped 225 invalid rows` appears in a `make pipeline` run.
- The Friday row in `week-01.md` still says RMSE; the Decisions section explains why it is MAE.
- Uncommitted: `.env.example`. Check `git diff .gitignore` and `git status --short` before Friday's first registered run so `lineage.git_dirty` is `False`.

**Next step**
- Fri block: read the MLflow registry and aliases docs, then write the `register` promotion rule in [src/taxi/register.py](../../src/taxi/register.py) (Kevin).
  Decide first: improvement margin (absolute or relative, in `params.yaml`), what happens when no champion exists, and how to get from the
  `@champion` alias to the run holding its MAE. Then pytest per task, starting with `validate` (cases from `scripts/probe_validate.py`) and the empty-split guard.

### 2026-10-25 (night): Thu block done (`features`, `train`, `evaluate`, MLflow-logged flow)

**Done** (last commit `dc64923`)
- [src/taxi/features.py](../../src/taxi/features.py): 7 inputs (pickup hour and weekday, fixed `CategoricalDtype` zones 1 to 265, vendor, rate code,
  passenger count); native NaN kept (751,815 rows) as `Int8`/category. Post-trip columns (`trip_distance`, fares, tips, tolls, totals) excluded as leakage.
- [src/taxi/train.py](../../src/taxi/train.py): time split at `train.cutoff_date` (2024-03-01): 5,972,080 train / 3,582,473 test rows; LightGBM, seeded;
  empty-split guard; no `eval_set` (the test period is the held-out score).
- [src/taxi/evaluate.py](../../src/taxi/evaluate.py): `mae` (primary, `PRIMARY_METRIC`), `rmse_capped` (trips up to `evaluate.duration_cap_min` = 120), `rmse_raw`.
  Baseline run: MAE 5.4802, RMSE capped 6.9655, RMSE raw 31.0753 (mean baseline: 9.21 / 12.77 / 32.94).
- [flows/training_flow.py](../../flows/training_flow.py) + [src/taxi/lineage.py](../../src/taxi/lineage.py): one MLflow run per flow run, tags `lineage.dvc_data_hash`,
  `lineage.git_commit`, `lineage.git_dirty`, `primary_metric`; `params.yaml` flattened into run params; `make pipeline` ran end to end in about 50 s.

**Design decisions**
- Registry compares on **MAE**, not RMSE as written in the plan: the target has a heavy tail (median 12.5 min, p99.9 117, max 1499), so raw RMSE
  barely moves (6% better than the mean baseline) while MAE improves 40%. The cap for the secondary RMSE is a fixed param, never a per-test-set quantile.
- The schema cap stays at 1500 min: the gate decides what is physically possible, the metric decides what is scored.

**Who wrote what**
- Kevin: feature choices and leakage reasoning, fixed zone categories and NaN policy, the split rule and hyperparameters, the empty-split guard,
  the three metrics, the MAE decision, the run tags, params flattening and metric logging in the flow.
- Claude scaffolded: stubs and `TODO(human)` for each task, `lineage.py`, the flow skeleton, the `make pipeline` target, `params.yaml` keys, and
  (at Kevin's request) the `ingest` column pruning.

**Lessons**
- Peak memory is a design constraint: `ingest` of all 20 columns peaked at 3.6 GB and the pipeline was OOM-killed (exit 137) in WSL (8 GB shared with the stack).
  Reading 6 columns plus the dropoff time, computing the target per file and concatenating narrow frames cut the `ingest` peak to 1.5 GB (pipeline peak 3.1 GB, in `validate`).
  Metrics were bit-identical before and after.
- A process killed with SIGKILL loses buffered stdout when piped; use `python -u` when measuring.
- MLflow's active run is per thread, so tasks are called directly in the flow, never `.submit()`.
- `python -m flows.training_flow`, not a path: `schemas` is a top-level package that needs the repo root on `sys.path`.
- Float summation order changes the last digit of a metric between libraries, so "same metrics" means equal to a tolerance.

**Open**
- Task logs did not appear in the flow output; `.env` has `PREFECT_LOGGING_EXTRA_LOGGERS=taxi ` with a trailing space. Check `get_current_settings().logging.extra_loggers`.
- `week-01.md` still says RMSE for the promotion rule; update "Decisions" with the MAE reasoning.
- Swap was at 1.6 of 2 GB during the run: little memory headroom. `validate` is the peak (second coercion pass after the drop).
- Uncommitted: `.gitignore`; untracked `nbk_taxi.ipynb` (ignore it, move it, or delete it) so the registered run has `lineage.git_dirty = False`.
- `dvc.yaml`: decide whether `dvc repro` owns any stage or Prefect owns all of them.
- Friday: pytest per task, including the end-to-end "bad file fails at the gate" test; `taxi` imports `schemas` from the repo root, which CI must respect.

**Next step**
- Fri block: `register` (promote to `@champion` only if MAE beats the current champion; Kevin writes the rule and decides how to compare with a tolerance),
  log the model in the flow, then pytest for each task (`validate` cases from `scripts/probe_validate.py`, the empty-split guard).

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
