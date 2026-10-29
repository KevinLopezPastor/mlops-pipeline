"""ZenML pipeline wiring the steps inside one MLflow run."""

import os
from typing import Any

import lightgbm as lgb
import mlflow
from zenml import pipeline, step

from taxi.evaluate import PRIMARY_METRIC, evaluate
from taxi.features import features
from taxi.ingest import ingest
from taxi.lineage import dvc_data_hash, git_commit, git_dirty
from taxi.params import load_params
from taxi.register import register
from taxi.train import train
from taxi.validate import validate

TRACKING_URI = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
EXPERIMENT = "nyc-taxi-duration"


def _flatten_dict(
    d: dict[str, Any], parent_key: str = "", sep: str = "."
) -> dict[str, str]:
    """Recursively flatten a nested dictionary for MLflow parameter logging."""
    items: list[tuple[str, str]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else str(k)
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            val_str = str(v)[
                :250
            ]  # Respect MLflow's 250-character parameter value limit
            items.append((new_key, val_str))
    return dict(items)


@step
def track(model: lgb.LGBMRegressor, metrics: dict[str, float]) -> str:
    """Log metrics and the model to the active MLflow run; return the model URI for `register`.

    A pipeline body only wires steps, so this logging cannot sit between them as it did in the
    Prefect flow. The local orchestrator runs steps in this process, so the run opened in `main`
    is the active one here.
    """
    # PRIMARY_METRIC ("mae") determines model quality for register
    mlflow.log_metrics(metrics)
    # MLflow 3 signature: name= instead of artifact_path=
    model_info = mlflow.lightgbm.log_model(lgb_model=model, name="model")
    return model_info.model_uri


# Caching is off until Step 9: the cache key covers code and step inputs, not the contents of data/raw,
# so a cached `ingest` could return stale data.
@pipeline(enable_cache=False)
def training_pipeline() -> None:
    """ingest -> validate -> features -> train -> evaluate -> track -> register."""
    # TODO(human): call the steps in order and pass each output to the next one.
    #   - `train` returns three outputs: unpack them (model, X_test, y_test) like the Prefect flow did.
    #   - `track` needs the model and the metrics, and its output is the `model_uri` that `register` takes.
    #   - A pipeline body is not run with real data: do not use the values for anything but passing them on.
    raise NotImplementedError


def main() -> None:
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    with mlflow.start_run():
        mlflow.set_tags(
            {
                "lineage.dvc_data_hash": dvc_data_hash(),
                "lineage.git_commit": git_commit(),
                "lineage.git_dirty": str(git_dirty()),
                "primary_metric": PRIMARY_METRIC,
            }
        )
        # Log params.yaml flattened (e.g. train.lgbm.n_estimators)
        mlflow.log_params(_flatten_dict(load_params()))

        training_pipeline()

        # TODO(human): set the run tag `promoted` from `register`'s return value, inside this `with`.
        #   Hint: calling a pipeline returns a handle to the run; the docs (Fetch runs and artifacts) show how to
        #   load a step's output from it. Check the attribute names in the installed version (0.98.0).


if __name__ == "__main__":
    main()
