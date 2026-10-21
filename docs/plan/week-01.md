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
| Mon | 2 | Read MLflow registry and aliases docs; run `docker compose` with MLflow, Postgres and MinIO (S3-compatible). |
| Tue | 2 | Read DVC and Prefect basics; download Jan to Mar 2024 yellow taxi Parquet; track it with DVC on an S3 remote. |
| Wed | 2.5 | Write `ingest` and `validate` tasks; a Pandera schema rejects negative durations and out-of-range zones. |
| Thu | 2.5 | Write `features`, `train` (LightGBM) and `evaluate` tasks; log params, metrics and the DVC data hash to MLflow. |
| Fri | 2 | `register` task promotes to `@champion` only if RMSE beats the current champion; add pytest for each task. |
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
├── docker-compose.yml          # MLflow + Postgres + MinIO
├── tests/
├── docs/architecture.html      # archify
└── Makefile                    # make up / pipeline / test / demo
```

## Archify diagram

Show: the S3 or MinIO data store versioned by DVC, the six Prefect tasks in order, the Pandera gate
with its failure path, MLflow tracking and registry, and the champion promotion decision.
Follow-up prompt: "Highlight the path a new data version takes to become @champion."

## Done when

- [ ] `make pipeline` on a clean clone registers a model with the same metrics as yours.
- [ ] The MLflow run shows the DVC data hash and git commit as tags.
- [ ] A bad data file fails at the Pandera gate and does not reach training.
- [ ] CI is green and the README shows the archify PNG.

**Stretch:** swap Prefect for ZenML on a branch and write half a page comparing the two.
