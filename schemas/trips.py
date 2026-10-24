"""Pandera schema for NYC TLC yellow taxi trips (the validation gate)."""

import pandera.pandas as pa

trips_schema = pa.DataFrameSchema({
    "duration_min": pa.Column(float, checks=pa.Check.in_range(0, 1500), nullable=False),
    "PULocationID": pa.Column(dtype=pa.Int32, coerce=True, checks=pa.Check.in_range(1, 265), nullable=False),
    "DOLocationID": pa.Column(dtype=pa.Int32, coerce=True, checks=pa.Check.in_range(1, 265), nullable=False),
})

