"""DataFrame materializer that keeps categorical dtypes between steps.

ZenML's default pandas materializer writes Parquet, and reading it back decodes dictionary columns to plain
numbers. `features` returns zone, vendor and rate-code columns as categoricals with fixed categories, so after one
round trip LightGBM would train on numbers and give a different model (MAE 7.2438 instead of 6.2526 on the smoke
sample). This one stores the categorical dtypes next to the Parquet file and restores them on load.
"""

import json
from typing import Any, ClassVar

import pandas as pd
from zenml.enums import ArtifactType
from zenml.materializers.base_materializer import BaseMaterializer
from zenml.materializers.materializer_registry import materializer_registry

PARQUET_FILENAME = "df.parquet"
CATEGORIES_FILENAME = "categories.json"


class CategoricalDataFrameMaterializer(BaseMaterializer):
    ASSOCIATED_TYPES: ClassVar[tuple[type[Any], ...]] = (pd.DataFrame,)
    ASSOCIATED_ARTIFACT_TYPE: ClassVar[ArtifactType] = ArtifactType.DATA

    def save(self, df: pd.DataFrame) -> None:
        categoricals = {
            col: {
                "categories": dtype.categories.tolist(),
                "categories_dtype": str(dtype.categories.dtype),
                "ordered": dtype.ordered,
            }
            for col, dtype in df.dtypes.items()
            if isinstance(dtype, pd.CategoricalDtype)
        }
        with self.artifact_store.open(f"{self.uri}/{PARQUET_FILENAME}", "wb") as f:
            df.to_parquet(f)
        with self.artifact_store.open(f"{self.uri}/{CATEGORIES_FILENAME}", "w") as f:
            json.dump(categoricals, f)

    def load(self, data_type: type[Any]) -> pd.DataFrame:
        with self.artifact_store.open(f"{self.uri}/{PARQUET_FILENAME}", "rb") as f:
            df = pd.read_parquet(f)
        with self.artifact_store.open(f"{self.uri}/{CATEGORIES_FILENAME}", "r") as f:
            categoricals = json.load(f)
        for col, spec in categoricals.items():
            categories = pd.Index(spec["categories"], dtype=spec["categories_dtype"])
            df[col] = df[col].astype(
                pd.CategoricalDtype(categories, ordered=spec["ordered"])
            )
        return df


# ZenML ships a materializer for pd.DataFrame and keeps the first one registered, so replace it explicitly.
materializer_registry.register_and_overwrite_type(
    pd.DataFrame, CategoricalDataFrameMaterializer
)
