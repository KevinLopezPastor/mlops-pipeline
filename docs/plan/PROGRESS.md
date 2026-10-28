# Week 1 progress

## Done when

- [x] `make pipeline` on a clean clone registers a model with the same metrics
  (2026-10-28, fresh `git clone` in `/tmp/clean-clone`, `dvc pull`: MAE 5.4802, RMSE capped 6.9655, RMSE raw 31.0753. `make pipeline` skips there because
  `dvc.lock` is satisfied, so the clone path is `make reproduce`, which always runs the flow. The path for a stranger with their own bucket is untested)
- [x] MLflow run tagged with the DVC data hash and git commit
  (2026-10-28, run `ea83057131704d3e9fe6e2302f5c843b` from a clean commit: `lineage.git_commit` `a1e32d2`, `lineage.git_dirty` `False`,
  `lineage.dvc_data_hash` `1e82f1da…dir`; MAE 5.4802, same as the baseline. The older run `198b9c9a…` carries a dead SHA.
  A first `--force` run (`b2e6d44f…`) had `git_dirty` `True`: `dvc repro --force` rewrote `data/raw.dvc` before the flow started; `git checkout data/raw.dvc` fixed it)
- [x] Bad data fails at the Pandera gate
  (`tests/test_gate_e2e.py`: a Parquet file with 20% negative durations passes `ingest` and is rejected by `validate`; 1% bad rows are dropped;
  `tests/test_validate.py` covers the missing column)
- [x] CI green, archify PNG in the README
  (CI is green on `main` since 2026-10-27, run `40577558675`; the README shows `docs/architecture.png` at the top since 2026-10-28.
  Confirm CI on the Sunday PR before the final tick. The PNG is a page screenshot with the toolbar and cut-off cards; the viewer's Export gives a cleaner one)

## Stretch ideas (parked)

- Offline mode: `docker-compose.offline.yml` override with RustFS (maintained S3-compatible store) plus a
  bucket-init container, selected with `make up-offline`. Only `.env` differs (artifact URI, endpoint,
  credentials). One branch, no long-lived second branch. See "Decisions" in week-01.md for why not MinIO.

- LightGBM `objective="huber"` (or `l1`): the target has a heavy tail (p99.9 = 117 min, max 1499), and the default L2 loss
  chases it while the registry compares on MAE. Try after the baseline is registered.

## Sessions

### 2026-10-28: Sun block (AWS Deployment fixed, lineage run, clean-clone proof, README, `make demo`); no demo GIF

**Done** (branch `week-01-mlflow-stack`, last commit `1640143`; PR to `main` opened after this entry)
- `AWS Deployment` fixed: the role `GitHubActionsDeployRole` trusted the old repo. The repo uses immutable subjects (`use_immutable_subject`), so the claim is
  `repo:KevinLopezPastor@137914994/mlops-pipeline@1436065944:ref:refs/heads/main`. [infra/github_oidc.tf](../../infra/github_oidc.tf) imports the role and the OIDC provider
  and pins that exact claim with `StringEquals`; the workflow authenticates as `GitHubActions`.
- Lineage box ticked for good: run `ea83057131704d3e9fe6e2302f5c843b` (`lineage.git_commit` `a1e32d2`, `git_dirty` `False`, data hash `1e82f1da…dir`, MAE 5.4802).
  The first attempt (`b2e6d44f…`) had `git_dirty` `True` because `dvc repro --force` rewrote `data/raw.dvc` before the flow started.
- Clean-clone proof in `/tmp/clean-clone`: `make pipeline` skipped (the stage matches `dvc.lock`), so I added `make reproduce` (`dvc pull`, then the flow, no skip, no rewrite
  of `data/raw.dvc`). Metrics identical: MAE 5.4802, RMSE capped 6.9655, RMSE raw 31.0753.
- [README.md](../../README.md): architecture PNG, CI badge, tasks, gate outcomes, MAE decision, lineage tags, quick start, command table, credential-expiry note.
- `make demo` ([Makefile](../../Makefile), [scripts/make_bad_sample.py](../../scripts/make_bad_sample.py), [scripts/show_lineage.py](../../scripts/show_lineage.py)):
  gate rejection on a 20% bad copy of the 1% sample, then `make reproduce` on the full data, then the lineage tags. Beat 1 prints one line and only claims "rejected at the gate" if
  the log contains `exceeds allowed fraction`. Ran green end to end.

**Who wrote what**
- Kevin: chose Terraform for the role, option B (`make reproduce`), full data and AWS for the demo, gate beat first, the 1% sample for the bad file, and the fallback decision.
- Claude scaffolded: `github_oidc.tf`, `make reproduce` and `make demo`, the two scripts, the README (written in full at Kevin's request), this log.

**Lessons**
- A trust policy for GitHub OIDC must match the claim the repo emits. With immutable subjects the claim holds numeric owner and repo IDs, so a new repo never matches an old policy.
  Read the claim from `gh api repos/OWNER/REPO/actions/oidc/customization/sub`.
- `dvc repro` skips an unchanged stage, so a fresh clone with a committed `dvc.lock` registers nothing. `--force` also rewrites `data/raw.dvc` first, which makes `git_dirty` `True`.
- A failed flow leaves a `FAILED` run in MLflow; "latest run" scripts must filter on `FINISHED`.
- Injected SSO credentials expire after about an hour. The MLflow server then fails the model upload with `ExpiredToken` and the client retries, so the flow looks frozen at `log_model`.
  `docker compose logs` needs the AWS variables; `docker logs <container>` does not.
- vhs needs ttyd 1.7.2 or newer and, in WSL, `libnss3` for its downloaded Chromium. The recording stalled twice at `log_model` inside vhs; the cause is not found (the first stall was expired credentials).

**Open**
- Demo GIF not recorded (vhs stalls at `log_model`; `docs/demo.tape` removed in `1640143`). Fallback: ScreenToGif, then one README line under the PNG.
- The stranger path (own bucket, `terraform apply`, `download_data.sh`, `dvc push`, `make reproduce`) is untested; re-downloaded TLC files may hash differently from `1e82f1da…`.
- `dvc pull` prints `M data/raw/ 3 files modified` on every run (data on `/mnt/d`); the hash is unchanged. Probably cosmetic.
- `github-trust-policy.json` in the repo root is the old policy with the dead repo name; Terraform owns the role now. Delete it.
- `.dvc/config` names the private bucket (account ID visible in a public repo).
- Registry clutter: `nyc-taxi-duration-lgbm` has 12+ versions, one `@champion`; the registry story for the demo is not clean.
- Stretch (parked): mount `~/.aws` read-only with `AWS_PROFILE` so boto3 refreshes SSO credentials itself; raise the 60 s wait in `prefect-up`.
- LinkedIn post (Kevin).

**Next step**
- Merge the PR once CI is green, record the GIF with ScreenToGif (run `make down && make up` first), add it to the README, then publish and post.

<!-- /checkpoint adds a new entry here, newest first -->

### 2026-10-27: Sat block done (smoke sample, CI green, one DVC stage, architecture diagram); history rewritten for the new repo

**Done** (in `main` through PR #3, merge commit `fdba3be`; this log is `8c2e7a6` on the branch, not in `main` until a PR is opened)
- `make lint` ([Makefile](../../Makefile)): `ruff check .` and `ruff format --check .`. Green locally on the first run; red in CI later (see Lessons).
- [src/taxi/ingest.py](../../src/taxi/ingest.py): `RAW_DIR` env var (default `data/raw`).
- [scripts/make_smoke_sample.py](../../scripts/make_smoke_sample.py): seeded 1% sample per month into `tests/data/smoke/` (95,547 rows, 2.0 MB, committed).
- Local smoke run (`RAW_DIR=tests/data/smoke MLFLOW_TRACKING_URI=sqlite:////tmp/smoke_mlflow.db make pipeline`): 59,721 train / 35,823 test rows,
  gate dropped 3 rows, MAE 6.2526, v1 auto-promoted to `@champion`. `mlruns/` added to `.gitignore`.
- [.github/workflows/ci.yml](../../.github/workflows/ci.yml): `lint`, `test`, then `smoke` (`make smoke` on the sample, SQLite tracking).
  First green run on PR #3 (run `40576819499`: lint 9 s, test 32 s, smoke 35 s), and green on `main` after the merge (run `40577558675`, 1 m 14 s).
  The smoke job printed the same numbers as the local run (MAE 6.2526, RMSE capped 9.0614, RMSE raw 28.8327, 3 rows dropped, v1 `@champion`).
- [dvc.yaml](../../dvc.yaml) and `dvc.lock`: one stage, `training`, wraps the flow (deps `data/raw`, the flow, `src/taxi`, `schemas`; params `validate`, `ingest`, `train`,
  `evaluate`). `make pipeline` runs `dvc repro`; a second run printed `Stage 'training' didn't change, skipping`. `make smoke` runs the flow without DVC (CI has no `data/raw`).
  `.dvcignore` skips `__pycache__`. Decision and cost written in "Decisions" in [week-01.md](week-01.md); lineage tags unchanged because `dvc.lock` is written after the run.
- [docs/architecture.html](../architecture.html) and [docs/architecture.png](../architecture.png): archify diagram with the path of a new data version to `@champion`
  drawn as thick green arrows. Source links are pinned to `46e8ed6`. The PNG is a page screenshot (toolbar included, cards cut off); the viewer's Export gives a cleaner one.
- History rewrite: 8 commits had the corporate email as author and in `pyproject.toml` `authors`; all commits now use `kevinlopez.ind@gmail.com`.
  Every hash changed. `origin` = `KevinLopezPastor/mlops-pipeline`. `.claude/` untracked in a follow-up commit (it stays in older history; no secrets in it).

**Who wrote what**
- Kevin: the sampling rule (`sample()`, seed 42), the decisions (real 1% sample in git, `RAW_DIR`, rewrite the history, option C with its param groups, lineage tags unchanged),
  the review of the diagram (the unclear node text and the broken links).
- Claude scaffolded: `make lint` and `make smoke`, the `RAW_DIR` line, the sampling script skeleton, `ci.yml`, `dvc.yaml` and `.dvcignore`, the diagram, the `filter-branch` rewrite,
  the decision paragraph in `week-01.md`, this log.

**Lessons**
- A SQLite tracking URI only holds metadata; artifacts go to `./mlruns` unless the experiment sets `artifact_location`, which is stored in the `experiments` table at creation.
- A commit hash covers author, parents and content, so changing one email changes every descendant. Lineage tags that store a SHA go stale; rewrite before the first public push.
- `.gitignore` only affects untracked files. `.claude/` stayed on GitHub until `git rm --cached` removed it; a merged PR is a snapshot, so commits pushed after the merge need a new PR.
- `git rev-list --all` also walks `refs/remotes/*` and checkpoint refs, so a scan with it is not a check of what a push will send. Push named branches, never `--all`.
- `sed -i` in Git Bash stripped CRLF from this file; restore line endings or the diff shows every line.
- Windows `uv` on the WSL-built `.venv` fails with "Access is denied" while rebuilding it. Run `uv` from WSL only.
- CI caught what local lint could not: `scripts/make_smoke_sample.py` was added after the last `make lint` and had trailing whitespace and no final newline. Run `make lint && make test` before every push.
- A 1% sample of real data still had 3 invalid rows, so the smoke run reaches the gate's drop path (not its failure path, which the tests cover).
- Archify pins every source link to a commit; a commit that is not on GitHub gives a 404 that looks like a wrong repo. Push before sharing the diagram. `meta.views` is retired in archify 3.2,
  so a highlighted path is authored with edge variants and a card.
- DVC re-runs the stage only for the param groups listed in `dvc.yaml`; `register.*` is left out, so changing it needs `make pipeline ARGS=--force`.

**Open**
- `AWS Deployment` (`.github/workflows/deploy.yml`, OIDC, not in the plan) fails on every push to `main` since the first merge (latest `40577558486`). Probably the role's trust policy
  names the old repo; read the log (`gh run view 40577558486 --log-failed`), then fix the trust policy or remove the workflow.
- Record the run id of the first `dvc repro` run and check its tags (`lineage.git_commit` should be `be72c2f`, `lineage.git_dirty` `False`); the old run `198b9c9a…` carries a dead SHA.
- Old GitHub repo `KevinLopezPastor/mlops-reproducible-pipeline`: confirm it is deleted (`delete_repo` scope missing in `gh`; the web UI works), then `refs/original` and the checkpoint refs are local only.
- Hash map old to new, for the older entries below (they use the new hashes): `3b34154` to `ac61fbd`, `4ec17d0` to `010e259`, `44c528b` to `5e710c8`, `7620afc` to `cf9174c`,
  `dc64923` to `c792665`, `887799e` to `9982d94`, `9ee22b6` to `0077294`, `6213abc` to `8fda985`, `e8b9856` to `9f8ad9b`.
- `make demo` does not exist yet (CLAUDE.md lists it); the clean-clone box needs `dvc pull` and an AWS profile in a second directory.
- Registry clutter: `nyc-taxi-duration-lgbm` v1 (failed run, no alias), v3, v4 (rejected), plus the Monday smoke models; `.env.example` `PREFECT_API_URL` line is redundant.
- Parked ideas: a pre-push hook for `make lint && make test`; `astral-sh/setup-uv@v6` warns about Node 20 (check for v7); the PNG for the README from the viewer's Export.

**Next step**
- Sun block: prove the clean clone (fresh directory, `git clone`, `dvc pull`, `make up`, `make pipeline`; compare the metrics), then the README with the archify PNG at the top,
  a `make demo` target and the demo GIF, publish and the LinkedIn post. Resolve the `AWS Deployment` question first, because a red badge on the README undoes the green CI.
### 2026-10-26: Fri block done (`register`, flow wiring, pytest for every task)

**Done** (committed in `9f8ad9b`)
- [src/taxi/register.py](../../src/taxi/register.py): registers a version, tags it `mae` (`repr` of the float), promotes `@champion` if there is none
  (`register.auto_promote_first`) or if `new < champ * (1 - register.relative_margin)` (strict, 1% relative). Champion found through
  `get_registered_model(...).aliases`, not through an exception.
- [flows/training_flow.py](../../flows/training_flow.py): `mlflow.lightgbm.log_model(name="model")`, `register(...)`, run tag `promoted`; `taxi` logger set to INFO.
- Registry checked by hand: v2 is `@champion` (mae 5.480241473956837); v3 and v4, same MAE, were registered and rejected.
- Tests, 13 passing (about 78 s): `test_validate` (4), `test_train` (2, empty split), `test_register` (6, throwaway SQLite registry), `test_gate_e2e` (1).
  `make test`; `pythonpath = ["."]` in [pyproject.toml](../../pyproject.toml). `scripts/probe_validate.py` removed.
- `make pipeline` now starts a detached Prefect server if none answers (`prefect-up`); `make prefect-down` stops it.
- "Bad data fails at the Pandera gate" ticked above.
- First run from a clean commit: run `198b9c9a7b634eac878ab06546697379` (`merciful-rat-495`), tags `lineage.git_commit` = `e8b9856...` (pre-rewrite SHA, now `9f8ad9b`),
  `lineage.git_dirty` = `False`, `lineage.dvc_data_hash` = `1e82f1da5851bbfa0ab1bdc3752a9797.dir`, `promoted` = `False`; MAE 5.480241473956837,
  RMSE capped 6.9655, RMSE raw 31.0753, identical to Thursday's baseline (1.3 min). The lineage box above now points at this run.

**Who wrote what**
- Kevin: the three register decisions (relative 1%, auto-promote the first, `mae` tag as the single source), the body of `register`, the flow wiring
  (`log_model`, `register`, `promoted` tag), the six `register` cases, the empty-split test, the bad-file test.
- Claude scaffolded: `register` stub and `params.yaml` keys, `prefect-up`/`test` targets, `tests/conftest.py`, the SQLite registry fixtures, the
  `write_trips` helper. At Kevin's request: the alias-map lookup, the `taxi` logger level, the fixes to five test issues.

**Lessons**
- MLflow 3.17 answers a missing alias with `INVALID_PARAMETER_VALUE`, not `RESOURCE_DOES_NOT_EXIST`; read the `aliases` map instead of parsing errors.
  (Claude gave the wrong code in the first review.)
- `PREFECT_LOGGING_EXTRA_LOGGERS` copies Prefect's handlers to the logger but sets no level; INFO from `taxi.*` needs `setLevel` in the flow.
- `register_model` in MLflow 3 needs an `MLmodel` file or a logged model; a bare `runs:/.../model` URI fails. `log_model` runs `uv export` on the
  project (about 15 s) unless `pip_requirements` is given.
- `ModelVersion.version` is an `int` from the SQL store and a `str` from REST; `aliases` values are strings.
- Prefect's server is a process, not a service: it died with the shell, and the flow then fell back to a temporary SQLite server that timed out.
  Piping a run into `head` kills it with SIGPIPE.
- `PREFECT_API_URL` from the profile was visible to `prefect config view` but not to `python -m`; the Makefile now exports it.

**Open**
- `dvc.yaml`: does `dvc repro` own any stage, or does Prefect own all of them? (Kevin's answer was ambiguous; decide before Sunday's README.)
- Registry clutter: `nyc-taxi-duration-lgbm` v1 (failed run, no alias), v3 and v4 (rejected); the Monday smoke models are still there.
- `make lint` target for CI (`ruff check`, `ruff format --check`); `.env.example` `PREFECT_API_URL` line is now redundant.
- Tests take about 78 s, mostly imports and one `log_model` per registry test; check the time in CI.
- The "clean clone" box is not provable yet: it needs `dvc pull` of the data and an AWS profile on a second machine or directory (Sunday).
- A checked run must be newer than the commit: the first UI check was a stale run (`8fda985`, dirty) from before `9f8ad9b`.

**Next step**
- Sat block: GitHub Actions (lint, `make test`, smoke run of the flow on a 1% sample; the tests need no AWS or MLflow server), then the archify diagram.

### 2026-10-25 (late night): Thu wrap-up (decision recorded, Prefect UI confirmed)

**Done**
- MAE-over-RMSE decision written into "Decisions" in [week-01.md](week-01.md) and the Thursday log committed (`0077294`, `9982d94`).
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

**Done** (last commit `c792665`)
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

**Done** (committed in `5e710c8` and `cf9174c`)
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
- Tue closed: `dvc push` done, `dvc status -c` reports cache and remote in sync. DVC setup committed in `010e259`
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

**Done** (nothing committed yet; last commit is `ac61fbd`)
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
