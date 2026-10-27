# Week 1: Reproducible pipelines and experiment tracking

**Repo:** `mlops-reproducible-pipeline`. Goal: anyone can clone it, run one command, and get the
exact same registered model, with lineage from data version to model version.

Problem for all of Phase 1: predict NYC taxi trip duration from the public
[NYC TLC trip records](https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page)
(yellow taxi, Jan to Mar 2024 for this week).

## Sources

- [MLflow docs](https://mlflow.org/docs/latest/): tracking, model registry, aliases (`@champion`, `@challenger`), `mlflow.models.evaluate`.
- [DVC docs](https://dvc.org/doc): `dvc.yaml` pipelines, S3 remotes, `dvc repro`.
- [Prefect docs](https://docs.prefect.io/): flows, tasks, caching, retries, deployments.
- [Pandera docs](https://pandera.readthedocs.io/): DataFrame schemas as validation gates.
- [Hidden Technical Debt in Machine Learning Systems](https://papers.nips.cc/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html) (Sculley et al., 2015).

## Day by day (about 15 hours)

| Day | Hours | Work |
| --- | --- | --- |
| Mon | 2 | Read MLflow registry and aliases docs; run `docker compose` with MLflow and Postgres, artifacts in a real S3 bucket (Terraform). |
| Tue | 2 | Read DVC and Prefect basics; download Jan to Mar 2024 yellow taxi Parquet; track it with DVC on an S3 remote. |
| Wed | 2.5 | Write `ingest` and `validate` tasks; a Pandera schema rejects negative durations and out-of-range zones. |
| Thu | 2.5 | Write `features`, `train` (LightGBM) and `evaluate` tasks; log params, metrics and the DVC data hash to MLflow. |
| Fri | 2 | `register` task promotes to `@champion` only if MAE beats the current champion (see "Decisions"); add pytest for each task. |
| Sat | 2.5 | GitHub Actions: lint, tests, and a smoke run of the flow on a 1% sample. Generate the archify diagram. |
| Sun | 1.5 | README, demo GIF, publish, LinkedIn post. |

## Repo layout

```
mlops-reproducible-pipeline/
├── flows/training_flow.py      # Prefect flow wiring the tasks
├── src/taxi/{ingest,validate,features,train,evaluate,register}.py
├── schemas/trips.py            # Pandera schema
├── data/.gitignore             # data lives in DVC
├── dvc.yaml  params.yaml
├── docker-compose.yml          # MLflow + Postgres (artifacts in S3)
├── infra/                      # Terraform: S3 bucket for MLflow artifacts and the DVC remote
├── tests/
├── docs/architecture.html      # archify
└── Makefile                    # make up / pipeline / test / demo
```

## Archify diagram

Show: the S3 data store versioned by DVC, the six Prefect tasks in order, the Pandera gate
with its failure path, MLflow tracking and registry, and the champion promotion decision.
Follow-up prompt: "Highlight the path a new data version takes to become @champion."

## Decisions

**Real S3 instead of MinIO (2026-10-22).** The plan originally used MinIO as the local S3-compatible
store. We dropped it for three reasons:

1. MinIO stopped publishing official community images in late 2025; `minio/minio` and `minio/mc`
   no longer resolve on Docker Hub, quay.io or ghcr.io.
2. The only working option, `bitnamilegacy/minio`, is a frozen archive with no security patches that
   Bitnami can delete at any time. A public repo whose "clone and run" depends on it can break with no warning.
3. We need the S3 bucket anyway for the DVC remote, so one bucket (prefixes `mlflow/` and `dvc/`),
   created with Terraform, gives one storage story and matches production (S3 plus IAM).

Cost: a clone now needs an AWS account and profile (`ml-roadmap`), so it is no longer fully offline.
An offline mode with a maintained S3 stand-in (RustFS) is parked as a stretch idea in PROGRESS.md.

**MAE instead of RMSE for champion promotion (2026-10-25).** The Friday row says `register` promotes on RMSE.
It promotes on MAE instead, for these reasons:

1. The target has a heavy tail: on the March test set the median trip is 12.5 min, p99.9 is 117 min and the max is 1,499 min.
   A few multi-hour trips (mostly meters left running) dominate a squared-error metric, and no feature known at request time can predict them.
2. On that test set the model is 40% better than the mean baseline on MAE (5.48 vs 9.21 min) but only 6% better on raw RMSE (31.08 vs 32.94 min).
   Raw RMSE would make a good model look barely better than a constant, and it could flip a promotion on a handful of outlier trips.
3. MAE scores every trip with no filtering, so the comparison does not depend on which trips are left out.

RMSE stays as a secondary diagnostic, computed on trips up to a **fixed** cap (`evaluate.duration_cap_min` = 120 min in `params.yaml`; 6.97 min vs 12.77 for the baseline).
The cap is never a quantile of the test set: that would change with the data and make champion and challenger incomparable.
The Pandera cap on `duration_min` stays at 1,500 min, because the gate decides what is physically possible and the metric decides what is scored.

Known mismatch: LightGBM trains on L2 loss (the conditional mean) while MAE rewards the median. An `l1` or `huber` objective is parked in PROGRESS.md.

**One DVC stage wraps the whole flow (2026-10-27).** `dvc.yaml` has a single stage, `training`, whose command is the Prefect flow.
DVC decides whether to run it; Prefect and MLflow decide how it runs and where the model goes.

1. The six Prefect tasks stay as the plan describes them. Splitting the data steps into their own DVC stage would leave Prefect with three.
2. `deps` are `data/raw`, the flow, `src/taxi` and `schemas`; `params` are the `validate`, `ingest`, `train` and `evaluate` groups.
   `register.*` is left out: it changes the promotion decision, not the trained model. Changing it needs `make pipeline ARGS=--force`.
3. `make pipeline` runs `dvc repro`, which skips an unchanged stage (no Prefect run, no MLflow run, no registry version).
   CI has no `data/raw`, so the smoke job calls `make smoke`, the flow without DVC, on the committed 1% sample.
4. The MLflow lineage tags stay as they are (git commit, `git_dirty`, hash of `data/raw.dvc`, params logged flat). `dvc.lock` is written after the stage
   finishes, so a tag computed inside the flow would show the previous run's hashes. The committed `dvc.lock` is the receipt that ties inputs to the commit.

Cost: DVC sees the flow as a black box, so it caches nothing between tasks, and the stage has side effects outside DVC (a registry version).

## Done when

- [ ] `make pipeline` on a clean clone registers a model with the same metrics as yours.
- [ ] The MLflow run shows the DVC data hash and git commit as tags.
- [ ] A bad data file fails at the Pandera gate and does not reach training.
- [ ] CI is green and the README shows the archify PNG.

**Stretch:** swap Prefect for ZenML on a branch and write half a page comparing the two.
