# IAM policy for Bedrock model access
data "aws_iam_policy_document" "bedrock_access" {
  statement {
    effect = "Allow"
    actions = [
      "bedrock:InvokeModel",
      "bedrock:InvokeModelWithResponseStream"
    ]
    resources = [
      "arn:aws:bedrock:*::foundation-model/*",
      "arn:aws:bedrock:*:${data.aws_caller_identity.current.account_id}:inference-profile/*"
    ]
  }
}

resource "aws_iam_policy" "bedrock_access" {
  name        = "${local.name_prefix}-bedrock-access"
  description = "Allow Lambda to invoke Bedrock Llama model"
  policy      = data.aws_iam_policy_document.bedrock_access.json
}
