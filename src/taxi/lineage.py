"""Run lineage: which data version and which code produced a model."""

import subprocess
from pathlib import Path

import yaml

DVC_FILE = Path("data/raw.dvc")


def dvc_data_hash(path: Path = DVC_FILE) -> str:
    """md5 of the tracked data directory, as recorded in the .dvc file."""
    with path.open() as f:
        return yaml.safe_load(f)["outs"][0]["md5"]


def git_commit() -> str:
    """Full SHA of HEAD."""
    return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()


def git_dirty() -> bool:
    """True if tracked files have uncommitted changes, so HEAD alone does not describe the code that ran."""
    out = subprocess.check_output(
        ["git", "status", "--porcelain", "--untracked-files=no"], text=True
    )
    return bool(out.strip())
