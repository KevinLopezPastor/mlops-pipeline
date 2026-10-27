"""A bad data file must fail at the validate gate, before features and train can run."""

from pathlib import Path

import pandas as pd
import pytest

from taxi.ingest import ingest
from taxi.validate import validate


def write_trips(raw_dir: Path, rows: int, bad_rows: int) -> None:
    """Write a tiny yellow_tripdata Parquet file whose first `bad_rows` trips end before they start."""
    pickup = pd.Timestamp("2024-01-15 08:00")
    dropoff = [pickup - pd.Timedelta(minutes=5)] * bad_rows + [
        pickup + pd.Timedelta(minutes=10)
    ] * (rows - bad_rows)
    pd.DataFrame(
        {
            "tpep_pickup_datetime": [pickup] * rows,
            "tpep_dropoff_datetime": dropoff,
            "PULocationID": [1] * rows,
            "DOLocationID": [2] * rows,
            "VendorID": [1] * rows,
            "RatecodeID": [1] * rows,
            "passenger_count": [1] * rows,
        }
    ).to_parquet(raw_dir / "yellow_tripdata_2024-01.parquet")


def test_bad_file_fails_at_the_gate(tmp_path):
    # 1. File with 20% bad rows (above max_invalid_fraction tolerance of 0.05)
    write_trips(tmp_path, rows=200, bad_rows=40)

    # 2. Ingest is a pure data reader; it must not clean data or raise validation errors.
    df = ingest.fn(tmp_path)
    # ingest drops the dropoff time after computing the target, so the bad trips show up in duration_min.
    assert (df["duration_min"] < 0).sum() == 40

    # 3. Validation gate must raise ValueError when bad row fraction exceeds threshold (20% >= 5%).
    with pytest.raises(ValueError, match="exceeds allowed fraction"):
        validate.fn(df)

    # 4. Contrast case: minor invalid fraction (2 bad rows out of 200 = 1% < 5%) passes gate with bad rows removed.
    # Own directory, so this case does not depend on the file written above.
    small = tmp_path / "small"
    small.mkdir()
    write_trips(small, rows=200, bad_rows=2)
    df_cleaned = validate.fn(ingest.fn(small))

    assert len(df_cleaned) == 198
    assert df_cleaned["duration_min"].min() >= 0
