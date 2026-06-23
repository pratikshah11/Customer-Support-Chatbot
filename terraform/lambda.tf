# Package the Lambda function code
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.root}/../backend"
  output_path = "${path.root}/../backend/lambda_package.zip"
}

# IAM role for Lambda execution
resource "aws_iam_role" "lambda_exec" {
  name = "${local.name_prefix}-lambda-exec"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Attach AWS managed policy for basic Lambda execution (CloudWatch Logs)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Attach Bedrock access policy
resource "aws_iam_role_policy_attachment" "lambda_bedrock" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.bedrock_access.arn
}

# DynamoDB read/write policy for sessions table
data "aws_iam_policy_document" "dynamodb_access" {
  statement {
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem"
    ]
    resources = [aws_dynamodb_table.sessions.arn]
  }
}

resource "aws_iam_policy" "dynamodb_access" {
  name        = "${local.name_prefix}-dynamodb-access"
  description = "Allow Lambda to read/write session data in DynamoDB"
  policy      = data.aws_iam_policy_document.dynamodb_access.json
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.dynamodb_access.arn
}

# API Gateway Management API policy (to send messages back to WebSocket clients)
data "aws_iam_policy_document" "apigw_management" {
  statement {
    effect    = "Allow"
    actions   = ["execute-api:ManageConnections"]
    resources = ["arn:aws:execute-api:${var.aws_region}:*:*/${var.environment}/*/@connections/*"]
  }
}

resource "aws_iam_policy" "apigw_management" {
  name        = "${local.name_prefix}-apigw-management"
  description = "Allow Lambda to push messages to WebSocket connections"
  policy      = data.aws_iam_policy_document.apigw_management.json
}

resource "aws_iam_role_policy_attachment" "lambda_apigw" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = aws_iam_policy.apigw_management.arn
}

# Lambda function
resource "aws_lambda_function" "chat_handler" {
  function_name    = "${local.name_prefix}-chat-handler"
  role             = aws_iam_role.lambda_exec.arn
  handler          = "handler.lambda_handler"
  runtime          = "python3.12"
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_mb

  environment {
    variables = {
      BEDROCK_MODEL_ID  = var.bedrock_model_id
      DYNAMODB_TABLE    = aws_dynamodb_table.sessions.name
      SESSION_TTL_HOURS = tostring(var.session_ttl_hours)
      AWS_ACCOUNT_ID    = data.aws_caller_identity.current.account_id
      ENVIRONMENT       = var.environment
    }
  }
}

# Get current account ID for ARN construction
data "aws_caller_identity" "current" {}

# CloudWatch log group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${aws_lambda_function.chat_handler.function_name}"
  retention_in_days = 7
}

# Allow API Gateway to invoke Lambda
resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.chat_handler.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.chatbot_ws.execution_arn}/*/*"
}
