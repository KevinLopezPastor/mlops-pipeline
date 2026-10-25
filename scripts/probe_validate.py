"""Throwaway probe for the validate gate; replaced by tests/test_validate.py on Friday."""

import pandas as pd

from src.taxi.validate import validate


def make_df(n: int = 200) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "duration_min": [10.0] * n,
            "PULocationID": [1] * n,
            "DOLocationID": [2] * n,
        }
    )


def expect_raises(name: str, df: pd.DataFrame) -> None:
    try:
        validate.fn(df)
    except ValueError as exc:
        print(f"PASS {name}: raised {type(exc).__name__}")
    else:
        print(f"FAIL {name}: did not raise")


clean = make_df()
out = validate.fn(clean)
print(
    "PASS clean" if len(out) == 200 else "FAIL clean",
    "| zone dtype:",
    out["PULocationID"].dtype,
)

few_bad = make_df()
few_bad.loc[[3, 7], "duration_min"] = -1.0
out = validate.fn(few_bad)
print(
    "PASS few bad"
    if len(out) == 198 and out["duration_min"].min() >= 0
    else "FAIL few bad",
    f"| rows: {len(out)}",
)

many_bad = make_df()
many_bad.loc[:39, "duration_min"] = -1.0  # 20%
expect_raises("20% bad", many_bad)

expect_raises("missing column", make_df().drop(columns=["PULocationID"]))
