"""Monday smoke test: tracking -> S3 artifacts -> registry -> alias -> load by alias."""

import mlflow
from mlflow import MlflowClient
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

TRACKING_URI = "http://localhost:5000"
MODEL_NAME = "smoke_model_test_2"

mlflow.set_tracking_uri(TRACKING_URI)
mlflow.set_experiment("smoke_test_2")

with mlflow.start_run() as run:
    model = LinearRegression(fit_intercept=True)
    model.fit([[1], [2], [3]], [1, 2, 3])
    mlflow.log_param("fit_intercept", model.fit_intercept)
    y_pred = model.predict([[1], [2], [3]])
    error = mean_squared_error([1, 2, 3], y_pred)
    mlflow.log_metric("mse", error)
    info = mlflow.sklearn.log_model(
        model, name=MODEL_NAME, registered_model_name=MODEL_NAME
    )


client = MlflowClient()
version = info.registered_model_version
client.set_registered_model_tag(name=MODEL_NAME, key="git_commit", value="abc123")
client.set_registered_model_alias(MODEL_NAME, "champion", version)
client.set_model_version_tag(MODEL_NAME, version, "git_commit", "abc123")

# Get the model version using a model URI
model_uri = f"models:/{MODEL_NAME}@champion"
model_x = mlflow.sklearn.load_model(model_uri)

prediction = model_x.predict([[4]])
print(f"Prediction for [[4]]: {prediction[0]}")
