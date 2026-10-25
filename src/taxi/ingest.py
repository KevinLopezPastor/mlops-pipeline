"""ingest task."""

import logging
from pathlib import Path

import pandas as pd
from prefect import task

logger = logging.getLogger(__name__)

RAW_DIR = Path("data/raw")


@task
def ingest(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Read the yellow taxi Parquet files and return one DataFrame with the target column."""
    logger.info("Scanning for yellow taxi Parquet files in: %s", raw_dir)

    list_of_files = []

    for path in sorted(raw_dir.glob("yellow_tripdata_*.parquet")):
        logger.info("Processing file: %s", path.name)
        df = pd.read_parquet(path)
        list_of_files.append(df)

    if not list_of_files:
        error_msg = f"No files found in {raw_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    df_concatenated = pd.concat(list_of_files, ignore_index=True)
    df_concatenated["duration_min"] = (
        df_concatenated["tpep_dropoff_datetime"]
        - df_concatenated["tpep_pickup_datetime"]
    ).dt.total_seconds() / 60

    logger.info("Successfully ingested %s total rows.", len(df_concatenated))
    return df_concatenated
