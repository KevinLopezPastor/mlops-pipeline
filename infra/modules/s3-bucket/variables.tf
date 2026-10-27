variable "name_prefix" {
  description = "Bucket name prefix. The AWS account id is appended to make the name globally unique."
  type        = string
}

variable "force_destroy" {
  description = "Allow terraform destroy to delete a non-empty bucket. Keep false outside learning projects."
  type        = bool
  default     = false
}

variable "versioning_enabled" {
  description = "Keep previous versions of overwritten or deleted objects."
  type        = bool
  default     = true
}

variable "tags" {
  description = "Tags applied to the bucket."
  type        = map(string)
  default     = {}
}
