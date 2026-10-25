# src/taxi/evaluate.py
"""evaluate task."""

import logging

import pandas as pd
from lightgbm import LGBMRegressor
from prefect import task
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from .params import load_params

logger = logging.getLogger(__name__)

# The metric `register` compares champion and challenger on (lower is better).
PRIMARY_METRIC = "mae"


@task
def evaluate(
    model: LGBMRegressor, X_test: pd.DataFrame, y_test: pd.Series
) -> dict[str, float]:
    """Score the model on the held-out period; return {"mae", "rmse_capped", "rmse_raw"} in minutes.

    Note: 'rmse_capped' uses boolean masking to exclude actual trip durations above `duration_cap_min`
    rather than clipping values at the threshold.
    """
    cap = load_params()["evaluate"]["duration_cap_min"]

    pred = model.predict(X_test)

    mae = float(mean_absolute_error(y_test, pred))
    rmse_raw = float(root_mean_squared_error(y_test, pred))

    # Masking vs Clipping:
    # We choose masking over clipping because clipping artificially compresses residuals for extreme outliers
    # (e.g. 1,500 min trips treated as 120 min), distorting the loss shape.
    # Masking evaluates the model's true error specifically on the domain of typical trips (< cap min).
    #
    # Trade-offs / Consequences:
    # 1. Test set size shrinks slightly based on ground-truth values above `cap`.
    # 2. Nonsensical predictions on extreme long-tail trips (> cap) are ignored by this metric.
    #    MAE remains our PRIMARY_METRIC to ensure every trip is scored and penalized fairly.
    mask = y_test <= cap
    rmse_capped = float(root_mean_squared_error(y_test[mask], pred[mask]))

    excluded_count = int((~mask).sum())
    total_count = len(y_test)
    excluded_pct = (excluded_count / total_count) * 100 if total_count > 0 else 0.0

    logger.info(
        "Evaluation metrics — MAE: %.4f | RMSE Capped (<=%.0f min): %.4f | RMSE Raw: %.4f "
        "(Excluded %d trips above %.0f min, %.2f%% of test set)",
        mae,
        cap,
        rmse_capped,
        rmse_raw,
        excluded_count,
        cap,
        excluded_pct,
    )

    return {
        "mae": mae,
        "rmse_raw": rmse_raw,
        "rmse_capped": rmse_capped,
    }
