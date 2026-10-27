output "bucket_name" {
  description = "Paste into .env as MLFLOW_BUCKET and use as the DVC remote bucket."
  value       = module.pipeline_bucket.bucket_name
}

output "bucket_arn" {
  description = "Bucket ARN, for scoping an IAM policy for the MLflow server later."
  value       = module.pipeline_bucket.bucket_arn
}
