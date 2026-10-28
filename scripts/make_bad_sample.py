"""Write a copy of the committed smoke sample with some trips ending before they start, for `make demo`.

    uv run python scripts/make_bad_sample.py <out_dir>

The demo points RAW_DIR at <out_dir>, so the validate gate sees a file it must reject.
"""

import sys
from pathlib import Path

import pandas as pd

SRC_DIR = Path("tests/data/smoke")
BAD_FRACTION = 0.20  # the gate fails at max_invalid_fraction = 0.05 (params.yaml)
SEED = 42


def main(out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for src in sorted(SRC_DIR.glob("*.parquet")):
        df = pd.read_parquet(src)
        bad = df.sample(frac=BAD_FRACTION, random_state=SEED).index
        # Dropoff 5 minutes before pickup gives a negative duration_min, which the schema rejects.
        df.loc[bad, "tpep_dropoff_datetime"] = df.loc[
            bad, "tpep_pickup_datetime"
        ] - pd.Timedelta(minutes=5)
        df.to_parquet(out_dir / src.name)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
