"""validate task."""

import pandas as pd
import pandera.pandas as pa
from prefect import task

from schemas.trips import trips_schema

MAX_INVALID_FRACTION = 0.05


@task
def validate(df: pd.DataFrame) -> pd.DataFrame:
    """Gate: validate df against trips_schema; drop invalid rows if under 5%, otherwise fail."""
    # TODO(human): validate with lazy=True and catch pa.errors.SchemaErrors.
    # TODO(human): from the failure cases, count the distinct invalid rows and decide: drop or raise.
    raise NotImplementedError
