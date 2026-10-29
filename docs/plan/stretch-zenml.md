# Stretch: swap Prefect for ZenML on a branch

From "Stretch" in [week-01.md](week-01.md): swap Prefect for ZenML on a branch and write half a page comparing the two.
Branch: `stretch-zenml` (never merged into `main`; the comparison page is the deliverable, plus the branch as evidence).

**Rule for the swap:** only the orchestration changes. Task logic in `src/taxi/*`, `params.yaml`, the Pandera schema, the MLflow registry and the
MAE promotion rule stay as they are, so the two runs are comparable. Success = same metrics on the same data (MAE 5.4802, RMSE capped 6.9655,
RMSE raw 31.0753, to a tolerance) and a green `make test`.

## What is verified and what is not

Verified in the ZenML docs (docs.zenml.io, core concepts and the MLflow experiment tracker page):
- `@step` and `@pipeline` decorators; a pipeline can only call steps; running a pipeline is calling its function.
- Step outputs are written to the artifact store and loaded by the next step (not passed in memory); materializers serialize them.
- A stack needs an orchestrator and an artifact store; the default local stack runs without a server. A ZenML server is only needed for remote
  components, collaboration and the dashboard.
- MLflow: `zenml integration install mlflow -y`, `zenml experiment-tracker register <name> --flavor=mlflow`, then a stack with `-e <name>`.
  The local scenario needs a local artifact store; a remote MLflow server uses a ZenML secret for credentials.

Not verified (check in Step 0, do not assume):
- Whether `zenml integration install mlflow` pins `mlflow` below `3.17.2` (our registry code uses MLflow 3 aliases).
- Whether steps share one MLflow run per pipeline run when using the tracker, or get one each.
- Whether the local orchestrator runs steps in one process, and the peak memory of passing a 9.5 M-row DataFrame as an artifact.
- Cache invalidation rules (the core-concepts page does not explain them).

**Step 0 result (2026-10-29, scratch venv, Python 3.12):**
- `zenml==0.98.0` and `mlflow==3.17.2` install together. The mlflow integration requires `mlflow>=2.1.1,<4`, `python-rapidjson<1.15`, `numpy<3.0`, `pandas>=2.0.0`: no downgrade.
- Plain `zenml` is not enough for the local store (`ModuleNotFoundError: sqlalchemy_utils`); use `zenml[local]`. It moves `sqlalchemy` from 2.1.6 to 2.0.55 and caps `pydantic` at 2.12.5 (repo lock: 2.14.1, held up by Prefect).
- A two-step pipeline passed a pandas 3.1 DataFrame (`int64`, `datetime64[us]`, nullable `Int32`) through the artifact store with dtypes intact. Steps expose `.entrypoint`.
- Still open: MLflow run scope, process model, peak memory, cache rules.

## Mapping, from this repo to ZenML

| Today (Prefect) | On the branch (ZenML) | Notes |
| --- | --- | --- |
| `@flow training_flow` in `flows/training_flow.py` | `@pipeline` in the same module name | Keep `python -m flows.training_flow` so `dvc.yaml` `cmd` and the Makefile do not change. |
| Six `@task` in `src/taxi/*` | Six `@step` | `ingest`, `validate`, `features`, `train`, `evaluate`, `register`. |
| DataFrames passed in memory | DataFrames written to the artifact store | The biggest behavioural change: serialization cost and peak memory (our `ingest` peak is 1.5 GB). |
| One `mlflow.start_run()` around all tasks | Decision for Kevin, see Step 3 | Lineage tags and params must end up on one run. |
| `taxi.*` stdlib logging forwarded by `PREFECT_LOGGING_EXTRA_LOGGERS` | ZenML captures step logs | Re-check that the gate's log line still appears. |
| Prefect server (`make prefect-up`) | `zenml init` and the default local stack | No server process. |
| Tests call `task.fn(...)` (18 call sites) | `step.entrypoint(...)` | Verify the name in the installed version. |
| `prefect` dependency | `zenml` dependency | Remove `prefect` on the branch; check `mlflow` and `pydantic` pins. |

## Steps

One step at a time, each with a check. Estimated 3 to 4 hours.

0. **Spike the dependency.** Without touching the repo, in a scratch venv: `uv pip install zenml "mlflow==3.17.2"` and read what resolves, then
   `zenml integration requirements mlflow`. Check: the resolver output. If it forces MLflow below 3.x, do not use the integration; call `mlflow` directly in a step.
1. **Branch and dependencies.** `pyproject.toml`: add `zenml`, remove `prefect`; `uv sync` from WSL only. Check: `uv run zenml version`.
2. **Local stack.** `zenml init`, default stack, no server. Check: `uv run zenml stack describe`.
3. **Decide the MLflow run scope (Kevin).** Option A: the ZenML MLflow experiment tracker component. Option B: no integration; one `mlflow.start_run()` inside a
   single wrapper step or in the pipeline's entry code, tags and params as today. B keeps `lineage.*` identical to the Prefect version; A shows what the integration gives.
   Recommendation: B first, A only if time is left.
4. **Convert the tasks.** Swap `@task` for `@step` in the six modules; the bodies do not change. Add type hints where ZenML needs them for materializers
   (a `pandas.DataFrame` is supported; the `(model, X_test, y_test)` tuple from `train` may need named outputs). Check: `uv run python -c "import taxi.ingest"`.
5. **Wire the pipeline.** Replace `flows/training_flow.py` with a `@pipeline` calling the six steps in order. Check: `make smoke` on the committed 1% sample
   (`RAW_DIR=tests/data/smoke`, SQLite tracking). Expect MAE 6.2526 and 3 rows dropped, the numbers in the Saturday log.
6. **Gate failure path.** Run the 20% bad sample (`scripts/make_bad_sample.py`). Check: the run fails at `validate`, `features` never starts, and the failure is visible in ZenML.
7. **Tests.** Update the 18 `.fn(...)` call sites; `make test` must give 13 passed. Check: `make lint && make test`.
8. **Full data.** `make reproduce`-style run on the 9.5 M rows. Record wall time and peak memory (as in Thursday's lessons: `python -u`, `/usr/bin/time -v`).
   Check: MAE 5.4802 to a tolerance.
9. **Failure mode and caching.** Run twice and note what ZenML caches; change one param and note what re-runs. Compare with DVC's skip.
10. **Write the page** (below), commit the branch, link it from `PROGRESS.md`. No PR to `main`.

Who writes what: Kevin writes the steps' wiring and the MLflow run-scope decision (Step 3 to 5); Claude scaffolds the dependency change,
the `zenml init` and Makefile targets, and the test edits.

## What to measure (fill in on the branch)

| Measure | Prefect (main) | ZenML (branch) |
| --- | --- | --- |
| Lines changed in `src/taxi` (excluding the decorator swap) | 0 | |
| `make smoke` wall time (1% sample) | about 35 s in CI | |
| Full-data wall time | about 50 to 60 s | |
| Peak memory, full data | 3.1 GB (in `validate`) | |
| New concepts you had to learn | | |
| What a bad-data failure looks like in the UI or CLI | | |
| Same metrics (MAE 5.4802) | yes | |

## The half page (write after Step 9, about 300 words)

Skeleton. Each bullet gets one or two sentences of evidence from the table, not from opinion:

1. **What each one is for.** Prefect: general workflow orchestration (retries, deployments, observability). ZenML: an ML-specific pipeline framework with
   artifacts and stacks as first-class concepts.
2. **Programming model.** Tasks that pass Python objects versus steps that pass versioned artifacts. Cost and benefit on a 9.5 M-row DataFrame.
3. **Lineage.** Our hand-written `lineage.*` tags versus what ZenML records itself. Which one answers "which data and code made this model" better.
4. **Infrastructure.** A Prefect server process versus a stack; what each needs to go beyond a laptop.
5. **Fit with MLflow and DVC.** Whether the registry and the DVC stage stayed untouched, or whether ZenML wanted to own them.
6. **Testing and failure behaviour.** The 18 `.fn` call sites, and what the gate failure looks like.
7. **Verdict.** For this project, which one and why; for what kind of team the other one wins.

Do not write the verdict before the measurements exist.
