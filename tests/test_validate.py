"""validate gate: drop a few bad rows, fail on many bad rows or a broken structure."""

import pandas as pd
import pytest

from taxi.validate import validate


def make_df(n: int = 200) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "duration_min": [10.0] * n,
            "PULocationID": [1] * n,
            "DOLocationID": [2] * n,
        }
    )


def test_clean_frame_passes_and_zones_are_int32():
    out = validate.fn(make_df())

    assert len(out) == 200
    assert out["PULocationID"].dtype == "int32"


def test_few_bad_rows_are_dropped():
    df = make_df()
    df.loc[[3, 7], "duration_min"] = -1.0

    out = validate.fn(df)

    assert len(out) == 198
    assert out["duration_min"].min() >= 0


def test_too_many_bad_rows_raise():
    df = make_df()
    df.loc[:39, "duration_min"] = -1.0  # 20%, above max_invalid_fraction (5%)

    with pytest.raises(ValueError, match="exceeds allowed fraction"):
        validate.fn(df)


def test_missing_column_raises():
    with pytest.raises(ValueError, match="Schema-level"):
        validate.fn(make_df().drop(columns=["PULocationID"]))
