"""Prefect flow wiring the tasks inside one MLflow run."""

import logging
import os
from typing import Any

import mlflow
from prefect import flow

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

# PREFECT_LOGGING_EXTRA_LOGGERS gives `taxi` Prefect's handlers but no level, so INFO is dropped by default.
logging.getLogger("taxi").setLevel(logging.INFO)


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
def training_flow() -> dict[str, Any]:
    """ingest -> validate -> features -> train -> evaluate -> register."""
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

        # 1. Log model using MLflow 3 signature (name= instead of artifact_path=)
        model_info = mlflow.lightgbm.log_model(
            lgb_model=model,
            name="model",
        )

        # 2. Register model and evaluate champion promotion against previous runs
        is_promoted = register(model_uri=model_info.model_uri, metrics=metrics)

        # 3. Record outcome inside the with block so it is attached while the run is active
        mlflow.set_tag("promoted", str(is_promoted))

    return {
        "metrics": metrics,
        "is_promoted": is_promoted,
    }


if __name__ == "__main__":
    training_flow()
