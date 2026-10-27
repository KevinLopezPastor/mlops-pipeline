"""Cut the committed CI sample from the real Parquet files.

Run once from the repo root (needs `dvc pull` first), then commit the output:

    uv run python scripts/make_smoke_sample.py

Output keeps the TLC file names, so `ingest` reads it unchanged through RAW_DIR.
"""

from pathlib import Path

import pandas as pd

SRC_DIR = Path("data/raw")
OUT_DIR = Path("tests/data/smoke")
FRACTION = 0.01
SEED = 42


def sample(df: pd.DataFrame) -> pd.DataFrame:
    """Return about FRACTION of one month's rows reproducibly.
    
    Note on gate testing:
    The real dataset has ~0.0024% invalid rows, meaning a 1% sample yields 0-2 invalid rows
    in total. This smoke dataset is meant to verify that the end-to-end pipeline runs cleanly.
    Explicit failure paths (e.g. max_invalid_fraction threshold breaches) are covered by
    `tests/test_gate_e2e.py` and `tests/test_validate.py`.
    """
    return df.sample(frac=FRACTION, random_state=SEED).reset_index(drop=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in sorted(SRC_DIR.glob("yellow_tripdata_*.parquet")):
        # Same columns ingest reads: keeps the committed files small.
        df = pd.read_parquet(path, columns=_columns())
        out = sample(df)
        out.to_parquet(OUT_DIR / path.name, index=False)
        print(f"{path.name}: {len(df):,} -> {len(out):,} rows")


def _columns() -> list[str]:
    from taxi.ingest import DROPOFF
    from taxi.params import load_params

    return [*load_params()["ingest"]["columns"], DROPOFF]


if __name__ == "__main__":
    main()