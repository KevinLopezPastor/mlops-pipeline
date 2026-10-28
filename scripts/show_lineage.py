"""Print the lineage tags and MAE of the newest finished run, for `make demo`.

A run that failed at the gate is also recorded in MLflow (status FAILED), so it is filtered out.
"""

import os

import mlflow

EXPERIMENT = "nyc-taxi-duration"
TAGS = ["lineage.git_commit", "lineage.git_dirty", "lineage.dvc_data_hash", "promoted"]


def main() -> None:
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000"))
    runs = mlflow.search_runs(
        experiment_names=[EXPERIMENT],
        filter_string="attributes.status = 'FINISHED'",
        order_by=["attributes.start_time DESC"],
        max_results=1,
        output_format="list",
    )
    run = runs[0]
    print(f"run {run.info.run_id}")
    for tag in TAGS:
        print(f"  {tag:24} {run.data.tags.get(tag)}")
    print(f"  {'mae':24} {run.data.metrics.get('mae')}")


if __name__ == "__main__":
    main()
