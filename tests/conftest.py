"""Test-session setup; runs before any test module imports prefect."""

import os

# `taxi` has Prefect's API log handler (PREFECT_LOGGING_EXTRA_LOGGERS in .env). Tasks run via `.fn` outside a
# flow run, so that handler warns on every log call; the records still reach the console and caplog.
os.environ.setdefault("PREFECT_LOGGING_TO_API_WHEN_MISSING_FLOW", "ignore")
