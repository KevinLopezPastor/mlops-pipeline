"""train task."""

import logging

import pandas as pd
from lightgbm import LGBMRegressor
from prefect import task

from .features import TARGET
from .params import load_params

logger = logging.getLogger(__name__)

TIMESTAMP = "tpep_pickup_datetime"


@task
def train(df: pd.DataFrame) -> tuple[LGBMRegressor, pd.DataFrame, pd.Series]:
    """Split by pickup time, fit LightGBM on the early part, return the model and the held-out X, y."""
    params = load_params()["train"]

    cutoff = pd.to_datetime(params["cutoff_date"])
    train_df = df[df[TIMESTAMP] < cutoff]
    test_df = df[df[TIMESTAMP] >= cutoff]

    if train_df.empty or test_df.empty:
        raise ValueError(
            f"Empty split on cutoff_date={params['cutoff_date']}: "
            f"{len(train_df)} train rows, {len(test_df)} test rows."
        )

    feature_cols = [c for c in df.columns if c not in (TARGET, TIMESTAMP)]
    X_train, y_train = train_df[feature_cols], train_df[TARGET]
    X_test, y_test = test_df[feature_cols], test_df[TARGET]

    logger.info("Train rows: %d, Test rows: %d", len(train_df), len(test_df))
    model = LGBMRegressor(**params["lgbm"])
    # No eval_set: test_df is strictly for held-out evaluation, not training/early stopping tuning.
    model.fit(X_train, y_train)

    return model, X_test, y_test
