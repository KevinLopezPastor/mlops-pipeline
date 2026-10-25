"""features task."""

import logging

import pandas as pd
from prefect import task

logger = logging.getLogger(__name__)

TARGET = "duration_min"
ZONE_CATEGORICAL_DTYPE = pd.CategoricalDtype(
    categories=list(range(1, 266)), ordered=False
)


@task
def features(df: pd.DataFrame) -> pd.DataFrame:
    """Turn the validated trips into model inputs; keep TARGET so train can split on time."""
    # 1. Fast-fail structural checks on critical coordinates
    critical_cols = ["PULocationID", "DOLocationID", "tpep_pickup_datetime"]
    for col in critical_cols:
        if df[col].isna().any():
            raise ValueError(
                f"Feature extraction failed: Null values detected in critical col '{col}'."
            )

    # 2. Track missing data metrics natively for LightGBM ingestion
    missing_passenger_mask = df["passenger_count"].isna()
    missing_ratecode_mask = df["RatecodeID"].isna()

    logger.info(
        "Missing value summary: Found %s missing passenger counts and %s missing RatecodeIDs. Retaining as Native NaN.",
        missing_passenger_mask.sum(),
        missing_ratecode_mask.sum(),
    )

    # 3. Explicitly construct feature matrix with strict contracts
    features_df = pd.DataFrame()

    # Core Metadata Columns
    features_df["tpep_pickup_datetime"] = df["tpep_pickup_datetime"]
    features_df["duration_min"] = df["duration_min"]

    # Time-series Signals
    features_df["pickup_hour"] = df["tpep_pickup_datetime"].dt.hour.astype("int8")
    features_df["pickup_weekday"] = df["tpep_pickup_datetime"].dt.weekday.astype("int8")

    # Spatial Bounds (Guarantees category alignment between large-scale training and single-row inference)
    features_df["PULocationID"] = df["PULocationID"].astype(ZONE_CATEGORICAL_DTYPE)
    features_df["DOLocationID"] = df["DOLocationID"].astype(ZONE_CATEGORICAL_DTYPE)

    # Vendor and rate code categories come from the data on purpose: LightGBM stores the training
    # categories in the model and remaps them at predict time, so single-row inference stays safe.
    features_df["VendorID"] = df["VendorID"].astype("category")
    features_df["RatecodeID"] = df["RatecodeID"].astype("category")
    features_df["passenger_count"] = df["passenger_count"].astype("Int8")

    # Calculate model input feature footprint explicitly to eliminate magic numbers
    meta_cols = {"tpep_pickup_datetime", "duration_min"}
    feature_cols = [col for col in features_df.columns if col not in meta_cols]

    logger.info(
        "Feature extraction complete. Engineered %s inputs for training pipeline.",
        len(feature_cols),
    )

    return features_df
