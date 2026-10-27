"""register task."""

import logging

import mlflow
from mlflow import MlflowClient
from prefect import task

from .params import load_params

logger = logging.getLogger(__name__)

CHAMPION_ALIAS = "champion"


@task
def register(model_uri: str, metrics: dict[str, float]) -> bool:
    """Register the logged model as a new version; move @champion to it only if it wins.

    Returns True if the new version became @champion.
    """
    cfg = load_params()["register"]
    client = MlflowClient()
    model_name = cfg["model_name"]
    primary_metric_name = cfg["primary_metric"]

    if primary_metric_name not in metrics:
        raise KeyError(
            f"Primary metric '{primary_metric_name}' not found in evaluation metrics: {list(metrics.keys())}"
        )

    new_score = metrics[primary_metric_name]

    # 1. Register model_uri under cfg["model_name"] and tag the returned version with the primary metric.
    # We use repr() to round-trip the float without precision loss.
    mv = mlflow.register_model(model_uri=model_uri, name=model_name)
    client.set_model_version_tag(
        name=model_name,
        version=mv.version,
        key=primary_metric_name,
        value=repr(new_score),
    )

    # 2. Look up the current champion. A missing alias is read from the model's alias map, not from an
    # exception: MLflow 3.17 answers it with INVALID_PARAMETER_VALUE, which is too broad to catch safely.
    current_champion = None
    champion_version = client.get_registered_model(model_name).aliases.get(
        CHAMPION_ALIAS
    )
    if champion_version is None:
        logger.info(
            "No existing @%s alias found for registered model '%s'.",
            CHAMPION_ALIAS,
            model_name,
        )
    else:
        current_champion = client.get_model_version(model_name, champion_version)

    # If there is no existing champion, apply auto_promote_first decision.
    if current_champion is None:
        auto_promote = cfg["auto_promote_first"]
        if auto_promote:
            logger.info(
                "Promoting initial model version %s to @%s (auto_promote_first=True, %s=%.4f).",
                mv.version,
                CHAMPION_ALIAS,
                primary_metric_name,
                new_score,
            )
            client.set_registered_model_alias(
                name=model_name, alias=CHAMPION_ALIAS, version=mv.version
            )
            return True
        else:
            logger.info(
                "Initial model version %s registered, but auto_promote_first=False; @%s alias not set.",
                mv.version,
                CHAMPION_ALIAS,
            )
            return False

    # 3. Read current champion's primary metric tag and compare against relative margin.
    champ_score_str = current_champion.tags.get(primary_metric_name)
    if champ_score_str is None:
        raise ValueError(
            f"Current champion version {current_champion.version} is missing the required metric tag '{primary_metric_name}'."
        )

    try:
        champ_score = float(champ_score_str)
    except ValueError as e:
        raise ValueError(
            f"Failed to parse metric tag '{primary_metric_name}' value '{champ_score_str}' as float on champion version {current_champion.version}."
        ) from e

    margin = cfg["relative_margin"]
    threshold = champ_score * (1.0 - margin)
    is_winner = new_score < threshold

    logger.info(
        "Promotion decision for model version %s — New %s: %.4f | Champ %s: %.4f | "
        "Required Threshold (< %.4f with margin %.2f%%) | Promoted: %s",
        mv.version,
        primary_metric_name,
        new_score,
        primary_metric_name,
        champ_score,
        threshold,
        margin * 100,
        is_winner,
    )

    # 4. If it wins, set registered model alias to the new version.
    if is_winner:
        client.set_registered_model_alias(
            name=model_name, alias=CHAMPION_ALIAS, version=mv.version
        )
        logger.info("Updated @%s alias to version %s.", CHAMPION_ALIAS, mv.version)

    return is_winner
