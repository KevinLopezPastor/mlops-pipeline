"""register: promotion rule against a throwaway SQLite registry (no server, no S3)."""

import mlflow
import pytest
from mlflow import MlflowClient
from sklearn.linear_model import LinearRegression

from taxi.register import register

MODEL_NAME = "test-model"


@pytest.fixture
def registry(tmp_path, monkeypatch):
    """Point MLflow at a SQLite store under tmp_path; never at the real server on localhost:5000."""
    uri = f"sqlite:///{tmp_path / 'mlflow.db'}"
    monkeypatch.setenv("MLFLOW_TRACKING_URI", uri)
    previous = mlflow.get_tracking_uri()
    mlflow.set_tracking_uri(uri)
    # The default artifact root of a SQLite store is ./mlruns in the cwd; keep it inside tmp_path.
    experiment_id = mlflow.create_experiment(
        "test", artifact_location=(tmp_path / "artifacts").as_uri()
    )
    mlflow.set_experiment(experiment_id=experiment_id)
    yield uri
    mlflow.set_tracking_uri(previous)


@pytest.fixture
def make_model_uri(registry):
    """Return a factory: each call logs a tiny real model in a new run and returns its model URI."""
    uris: list[str] = []

    def _make() -> str:
        # Logged once per test: every `register` call on the same URI creates a new version of it.
        if not uris:
            with mlflow.start_run():
                info = mlflow.sklearn.log_model(
                    LinearRegression().fit([[0.0], [1.0]], [0.0, 1.0]),
                    name="model",
                    pip_requirements=["scikit-learn"],
                )
            uris.append(info.model_uri)
        return uris[0]

    return _make


@pytest.fixture
def set_register_params(monkeypatch):
    """Return a setter for the `register` section of params.yaml, so tests check the rule, not the file."""

    def _set(**overrides) -> None:
        cfg = {
            "model_name": MODEL_NAME,
            "primary_metric": "mae",
            "auto_promote_first": True,
            "relative_margin": 0.01,
            **overrides,
        }
        monkeypatch.setattr("taxi.register.load_params", lambda: {"register": cfg})

    return _set


def test_first_model_becomes_champion(make_model_uri, set_register_params):
    """Worked example: the first registered model is promoted and tagged."""
    set_register_params()

    promoted = register.fn(make_model_uri(), {"mae": 5.0})

    champion = MlflowClient().get_model_version_by_alias(MODEL_NAME, "champion")
    assert promoted is True
    assert int(champion.version) == 1
    assert champion.tags["mae"] == "5.0"


def test_first_model_not_promoted_when_auto_promote_disabled(
    make_model_uri, set_register_params
):
    """When auto_promote_first=False, the first model is registered but no champion alias is set."""
    set_register_params(auto_promote_first=False)

    promoted = register.fn(make_model_uri(), {"mae": 5.0})

    client = MlflowClient()
    reg_model = client.get_registered_model(MODEL_NAME)
    assert promoted is False
    assert "champion" not in reg_model.aliases


def test_challenger_promoted_when_beating_margin(make_model_uri, set_register_params):
    """Challenger clearly outperforming champion past relative margin moves @champion pointer."""
    set_register_params(relative_margin=0.01)
    uri = make_model_uri()

    # Seed initial champion (version 1 with MAE 5.0; required threshold for v2: < 4.95)
    register.fn(uri, {"mae": 5.0})

    promoted = register.fn(uri, {"mae": 4.5})

    champion = MlflowClient().get_model_version_by_alias(MODEL_NAME, "champion")
    assert promoted is True
    assert int(champion.version) == 2
    assert champion.tags["mae"] == "4.5"


def test_challenger_rejected_when_within_or_at_margin_boundary(
    make_model_uri, set_register_params
):
    """Challenger meeting or underperforming strict threshold < champ * (1 - margin) is rejected."""
    set_register_params(relative_margin=0.01)
    uri = make_model_uri()

    # Seed champion (version 1 with MAE 10.0; threshold is strictly < 9.9)
    register.fn(uri, {"mae": 10.0})

    # Equal MAE loses
    promoted_equal = register.fn(uri, {"mae": 10.0})
    assert promoted_equal is False

    # Exact threshold boundary loses due to strict inequality (<); same expression as register.py, so no float luck
    threshold = 10.0 * (1.0 - 0.01)
    promoted_exact_boundary = register.fn(uri, {"mae": threshold})
    assert promoted_exact_boundary is False

    champion = MlflowClient().get_model_version_by_alias(MODEL_NAME, "champion")
    assert int(champion.version) == 1


def test_missing_mae_tag_on_champion_raises_value_error(
    make_model_uri, set_register_params
):
    """If current champion exists but lacks primary metric tag, register raises ValueError."""
    set_register_params()
    uri = make_model_uri()

    register.fn(uri, {"mae": 5.0})

    # Simulate missing tag state on champion
    client = MlflowClient()
    client.delete_model_version_tag(MODEL_NAME, version="1", key="mae")

    with pytest.raises(ValueError, match="missing the required metric tag 'mae'"):
        register.fn(uri, {"mae": 4.0})


def test_missing_primary_metric_raises_key_error_without_registering(
    make_model_uri, set_register_params
):
    """Passing metrics missing primary_metric key raises KeyError before creating model version."""
    set_register_params(primary_metric="mae")

    with pytest.raises(KeyError, match="Primary metric 'mae' not found"):
        register.fn(make_model_uri(), {"rmse_raw": 10.0})

    # Nothing was registered, not even an empty registered model.
    assert list(MlflowClient().search_registered_models()) == []
