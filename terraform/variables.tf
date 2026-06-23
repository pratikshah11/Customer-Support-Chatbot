variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Prefix for all resource names"
  type        = string
  default     = "chatbot"
}

variable "environment" {
  description = "Deployment environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "bedrock_model_id" {
  description = "Bedrock model ID to use for chat"
  type        = string
  default     = "us.meta.llama3-1-8b-instruct-v1:0"
}

variable "session_ttl_hours" {
  description = "Number of hours to keep session history in DynamoDB"
  type        = number
  default     = 24
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 60
}

variable "lambda_memory_mb" {
  description = "Lambda function memory in MB"
  type        = number
  default     = 256
}
