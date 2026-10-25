"""ingest task."""

import logging
from pathlib import Path

import pandas as pd
from prefect import task

from .params import load_params

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")
PICKUP = "tpep_pickup_datetime"
DROPOFF = "tpep_dropoff_datetime"


@task
def ingest(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Read the yellow taxi Parquet files and return one DataFrame with the target column."""
    logger.info("Scanning for yellow taxi Parquet files in: %s", raw_dir)

    # Only the columns the pipeline uses, plus the dropoff time needed for the target. Loading all 20
    # columns of 9.5M rows peaked at 3.6 GB, which WSL (8 GB, shared with the MLflow stack) cannot afford.
    columns = load_params()["ingest"]["columns"]

    list_of_files = []

    for path in sorted(raw_dir.glob("yellow_tripdata_*.parquet")):
        logger.info("Processing file: %s", path.name)
        df = pd.read_parquet(path, columns=[*columns, DROPOFF])
        # Target per file, then drop the dropoff time: the concat below then copies narrow frames.
        df["duration_min"] = (df[DROPOFF] - df[PICKUP]).dt.total_seconds() / 60
        list_of_files.append(df.drop(columns=DROPOFF))

    if not list_of_files:
        error_msg = f"No files found in {raw_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    df_concatenated = pd.concat(list_of_files, ignore_index=True)
    del list_of_files

    logger.info("Successfully ingested %s total rows.", len(df_concatenated))
    return df_concatenated
