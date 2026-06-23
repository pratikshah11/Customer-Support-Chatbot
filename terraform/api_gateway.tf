# WebSocket API Gateway
resource "aws_apigatewayv2_api" "chatbot_ws" {
  name                       = "${local.name_prefix}-websocket-api"
  protocol_type              = "WEBSOCKET"
  route_selection_expression = "$request.body.action"
}

# Lambda integration
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id             = aws_apigatewayv2_api.chatbot_ws.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.chat_handler.invoke_arn
  integration_method = "POST"
}

# $connect route — triggered when a client connects
resource "aws_apigatewayv2_route" "connect" {
  api_id    = aws_apigatewayv2_api.chatbot_ws.id
  route_key = "$connect"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# $disconnect route — triggered when a client disconnects
resource "aws_apigatewayv2_route" "disconnect" {
  api_id    = aws_apigatewayv2_api.chatbot_ws.id
  route_key = "$disconnect"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# sendMessage route — the main chat route
resource "aws_apigatewayv2_route" "send_message" {
  api_id    = aws_apigatewayv2_api.chatbot_ws.id
  route_key = "sendMessage"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# $default route — fallback for unmatched routes
resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.chatbot_ws.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"
}

# Deploy the API stage
resource "aws_apigatewayv2_stage" "dev" {
  api_id      = aws_apigatewayv2_api.chatbot_ws.id
  name        = var.environment
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit   = 100
    throttling_rate_limit    = 50
    data_trace_enabled       = false
    logging_level            = "OFF"
  }
}
