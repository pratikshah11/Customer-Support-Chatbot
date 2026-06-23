# Customer Support Chatbot

A serverless AI-powered customer support chatbot built on AWS using **Amazon Bedrock (Meta Llama 3.1 8B Instruct)**, **Terraform** for infrastructure-as-code, and **Python** for the backend.

## Architecture

```
User → CloudFront (HTTPS) → S3 (Web UI)
                     ↓ WebSocket
User → API Gateway (WebSocket) → Lambda (Python) → Bedrock (Llama 3.1)
                                       ↕
                                 DynamoDB (Session Memory)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI Model | Amazon Bedrock — Meta Llama 3.1 8B Instruct |
| Backend | AWS Lambda (Python 3.12) |
| API | API Gateway WebSocket |
| Session Memory | DynamoDB |
| Frontend Hosting | S3 + CloudFront |
| IaC | Terraform |

## Project Structure

```
├── terraform/          # Infrastructure as Code
├── backend/            # Python Lambda function
├── frontend/           # HTML/CSS/JS chat UI
├── scripts/            # Deployment scripts
└── tests/              # Unit tests
```

## Prerequisites

- AWS CLI configured (`aws configure`)
- Terraform installed (`brew install hashicorp/tap/terraform`)
- Python 3.x installed

## Quick Deploy

```bash
# One command to deploy everything
./scripts/deploy.sh
```

This will:
1. Package the Python backend as a zip
2. Run `terraform apply` to create all AWS resources
3. Sync the frontend files to S3
4. Inject the WebSocket URL into the frontend
5. Invalidate the CloudFront cache
6. Print the chatbot URL

## Running Tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install boto3 pytest
pytest tests/ -v
```

## Configuration

Edit [`terraform/terraform.tfvars`](terraform/terraform.tfvars) to change:
- `bedrock_model_id` — swap to a different Bedrock model
- `session_ttl_hours` — how long session history is kept
- `lambda_timeout` — adjust if model is slow
- `aws_region` — deployment region

Edit [`backend/config.py`](backend/config.py) to customize:
- `SYSTEM_PROMPT` — the chatbot's persona and behavior
- `MAX_TOKENS` — max response length
- `TEMPERATURE` — response creativity (0=deterministic, 1=creative)
- `MAX_CONVERSATION_TURNS` — how many turns of history to keep

## Cleanup

To delete all AWS resources (stops all billing):

```bash
cd terraform && terraform destroy
```

## Estimated Cost

~$2-4/month at demo usage levels (well within AWS free tier limits for Lambda, DynamoDB, and API Gateway).
