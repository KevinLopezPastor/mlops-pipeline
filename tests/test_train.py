"""train: the time split must refuse an empty train or test side."""

import pandas as pd
import pytest

from taxi.features import TARGET
from taxi.params import load_params
from taxi.train import TIMESTAMP, train


@pytest.mark.parametrize(
    "offset_days",
    [
        # All rows strictly before cutoff -> test_df is empty
        [-30, -15, -1],
        # All rows on or after cutoff -> train_df is empty
        [0, 15, 30],
    ],
    ids=["empty_test", "empty_train"],
)
def test_empty_split_raises(offset_days: list[int]) -> None:
    """Ensure train.fn raises ValueError when either train_df or test_df is empty."""
    params = load_params()["train"]
    cutoff_str = params["cutoff_date"]
    cutoff_dt = pd.Timestamp(cutoff_str)

    timestamps = [cutoff_dt + pd.Timedelta(days=d) for d in offset_days]

    df = pd.DataFrame(
        {
            TIMESTAMP: timestamps,
            TARGET: [10.0, 15.0, 20.0],
            "feature_a": [1, 2, 3],
        }
    )

    with pytest.raises(ValueError, match=rf"Empty split on cutoff_date={cutoff_str}"):
        train.fn(df)
