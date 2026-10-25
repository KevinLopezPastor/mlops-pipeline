"""Prefect flow wiring the tasks inside one MLflow run."""

import os
from typing import Any

import mlflow
from prefect import flow

from taxi.evaluate import PRIMARY_METRIC, evaluate
from taxi.features import features
from taxi.ingest import ingest
from taxi.lineage import dvc_data_hash, git_commit, git_dirty
from taxi.params import load_params
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


@flow
def training_flow() -> dict[str, float]:
    """ingest -> validate -> features -> train -> evaluate; register joins on Friday."""
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment(EXPERIMENT)

    # Tasks are called directly, not .submit(): MLflow's active run is per thread, so a task
    # moved to another thread would log to no run at all.
    with mlflow.start_run():
        # Tag the run with lineage tracking
        mlflow.set_tags(
            {
                "lineage.dvc_data_hash": dvc_data_hash(),
                "lineage.git_commit": git_commit(),
                "lineage.git_dirty": str(git_dirty()),
                "primary_metric": PRIMARY_METRIC,
            }
        )
        # Log params.yaml flattened (e.g. train.lgbm.n_estimators)
        raw_params = load_params()
        flat_params = _flatten_dict(raw_params)
        mlflow.log_params(flat_params)

        df = ingest()
        df = validate(df)
        df = features(df)
        model, X_test, y_test = train(df)
        metrics = evaluate(model, X_test, y_test)

        # Log metrics to MLflow; PRIMARY_METRIC ("mae") determines model quality for register
        mlflow.log_metrics(metrics)

        # Friday: log the model and let `register` decide on @champion.

    return metrics


if __name__ == "__main__":
    training_flow()
