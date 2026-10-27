"""Load pipeline parameters from params.yaml."""

from pathlib import Path

import yaml

PARAMS_PATH = Path("params.yaml")


def load_params(path: Path = PARAMS_PATH) -> dict:
    """Read params.yaml; tasks call this at run time so tests and reruns see the current values."""
    with path.open() as f:
        return yaml.safe_load(f)
