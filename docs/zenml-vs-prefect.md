# Prefect or ZenML for this pipeline

I swapped Prefect 3 for ZenML 0.98 on the branch `stretch-zenml`: same six steps, same MLflow registry and MAE rule, default local stack, one machine (WSL), one run per measurement. Details are in [stretch-zenml.md](plan/stretch-zenml.md).

**What each is for.** Prefect schedules and monitors Python work (retries, deployments, a UI). ZenML treats an ML pipeline as versioned artifacts moving between steps, run on a stack of swappable components.

**Programming model.** Prefect tasks pass Python objects in memory. ZenML steps pass artifacts through an artifact store, and that cost me one real bug: the default pandas materializer dropped the categorical dtypes, so the model trained on numbers and MAE came out 7.2438 instead of 6.2526. A 56-line custom materializer fixed it, and the full-data metrics then matched exactly (5.4802, 225 rows dropped). Peak memory was 2.79 GB against 3.1 GB on Prefect, so serialization did not raise it.

**Speed.** 3 m 01 s against about one minute. About 30 s is fixed startup (a run with all steps cached still took 32 s); I did not find the rest.

**Fit with MLflow and DVC.** Neither needed to change. But a pipeline body only wires steps, so logging the model had to move into a seventh step, `track`.

**Caching.** ZenML's cache key covers step inputs and code, not `data/raw` or `params.yaml`. With caching on, a changed data file and a changed hyperparameter were both ignored, and `track` and `register` were replayed from an earlier run, leaving MLflow runs with no metrics or model but `promoted=True`. I left caching off; DVC already does this job with the right inputs.

**Testing and failure.** Tests changed by renaming 18 `.fn` calls to `.entrypoint`; 13 pass. A bad file fails at the gate in both; ZenML lists the run as failed with `validate` failed and later steps absent, with a longer traceback.

**Verdict.** For this project, Prefect: one machine, one DataFrame-heavy flow, and DVC and MLflow already own versioning, so ZenML's artifacts duplicate them and added a bug, a slower run and a cache hazard. ZenML would win for a team that needs to move the same pipeline between orchestrators and clouds, and wants artifact lineage and a stack abstraction without building them. I did not test a remote stack, the MLflow tracker component or the ZenML server, so that side of the argument is untested.
