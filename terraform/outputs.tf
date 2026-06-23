output "websocket_url" {
  description = "WebSocket URL for the chatbot API — used in frontend app.js"
  value       = "${aws_apigatewayv2_stage.dev.invoke_url}"
}

output "cloudfront_url" {
  description = "Public HTTPS URL for the chat UI"
  value       = "https://${aws_cloudfront_distribution.frontend.domain_name}"
}

output "s3_bucket_name" {
  description = "S3 bucket name for deploying frontend files"
  value       = aws_s3_bucket.frontend.bucket
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (needed for cache invalidation after deploy)"
  value       = aws_cloudfront_distribution.frontend.id
}

output "lambda_function_name" {
  description = "Lambda function name (for testing directly in AWS Console)"
  value       = aws_lambda_function.chat_handler.function_name
}

output "dynamodb_table_name" {
  description = "DynamoDB session table name"
  value       = aws_dynamodb_table.sessions.name
}
