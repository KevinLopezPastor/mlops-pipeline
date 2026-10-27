provider "aws" {
  profile = "ml-roadmap"
  region  = "us-east-1"
}

# One bucket for both MLflow artifacts (prefix mlflow/) and the DVC remote (prefix dvc/).
module "pipeline_bucket" {
  source = "./modules/s3-bucket"

  name_prefix   = "mlops-repro"
  force_destroy = true # learning project only

  tags = {
    project = "mlops-reproducible-pipeline"
  }
}
