"""ingest task."""

from pathlib import Path

import pandas as pd
from prefect import task

RAW_DIR = Path("data/raw")


@task
def ingest(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Read the yellow taxi Parquet files and return one DataFrame with the target column."""
    # TODO(human): read every yellow_tripdata_*.parquet in raw_dir and concatenate them.
    # TODO(human): add the target `duration_min` (minutes between pickup and dropoff).
    raise NotImplementedError
