"""validate task."""

import logging

import pandas as pd
import pandera.pandas as pa
from prefect import task

from schemas.trips import trips_schema

logger = logging.getLogger(__name__)

MAX_INVALID_FRACTION = 0.05


@task
def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Gate: validate df against trips_schema; drop invalid rows if under 5%, otherwise fail."""
    try:
        # Capture the coerced frame returned by Pandera to preserve explicit dtypes (e.g., Int32)
        df_coerced = trips_schema.validate(df, lazy=True)
        
    except pa.errors.SchemaErrors as exc:
        # A null index indicates structural/schema-level failures (e.g., missing columns)
        if exc.failure_cases["index"].isna().any():
            failed_targets = exc.failure_cases["column"].unique().tolist()
            logger.error(
                "Schema-level validation failed structurally. Missing or incorrect targets: %s",
                failed_targets
            )
            raise ValueError(
                "Schema-level validation failed (e.g., missing or altered columns). "
                "Data structure is fundamentally invalid."
            ) from exc

        # Count invalid individual rows for data-level failures
        invalid_row_indices = exc.failure_cases["index"].dropna().unique()
        invalid_rows = len(invalid_row_indices)
        total_rows = df.shape[0]
        invalid_fraction = invalid_rows / total_rows if total_rows > 0 else 0

        if invalid_fraction < MAX_INVALID_FRACTION:
            logger.info(
                "Validation gate dropped %s invalid rows (%.2f%% of total dataset).",
                invalid_rows,
                invalid_fraction * 100
            )
            # Re-validate the dropped/reset frame to enforce the schema's coerced dtypes on clean rows.
            df_coerced = trips_schema.validate(df.drop(index=invalid_row_indices).reset_index(drop=True), lazy=True)
        else:
            logger.error(
                "Validation gate failed: %s invalid rows out of %s total rows. "
                "Invalid fraction (%.2f%%) exceeds the allowed max threshold (%.2f%%).",
                invalid_rows,
                total_rows,
                invalid_fraction * 100,
                MAX_INVALID_FRACTION * 100
            )
            raise ValueError(f"Invalid data exceeds allowed fraction: {invalid_fraction:.2%}")

    return df_coerced
