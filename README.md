# 💬 AI-Powered Customer Support Chatbot

A production-ready, serverless, AI-powered customer support chatbot built on AWS. This application leverages generative AI (**Meta Llama 3.1 8B Instruct** via Amazon Bedrock) to deliver contextual responses, dynamically maintaining conversation history in Amazon DynamoDB.

The entire infrastructure is automated and managed using **Terraform** (Infrastructure as Code), and the backend is implemented in **Python**.

---

## 🏗️ Architecture Overview

The system is designed with a high-performance, cost-effective serverless architecture:

```
User ──► CloudFront (HTTPS) ──► S3 (Web UI)
                 │
                 ▼ (WebSocket)
User ──► API Gateway ──► Lambda (Python) ──► Bedrock (Llama 3.1)
                              │
                              ▼
                        DynamoDB (Session Memory)
```

1. **Frontend Hosting**: Stored in a private Amazon S3 bucket, served securely and globally with low latency via Amazon CloudFront.
2. **WebSocket API**: Handled by AWS API Gateway WebSocket API to enable real-time bi-directional messaging.
3. **Serverless Compute**: AWS Lambda functions process incoming messages, coordinate Bedrock calls, and manage history.
4. **Contextual Memory**: Conversation state and message history are persisted in DynamoDB with automatic Time-to-Live (TTL) expiry to optimize costs.
5. **AI Inference**: Converses with Meta Llama 3.1 on Amazon Bedrock using the Converse API.

---

## 🛠️ Technology Stack

| Layer | Component & Technology | Purpose |
| :--- | :--- | :--- |
| **Frontend** | HTML5 / Vanilla CSS3 / JavaScript | Responsive UI with real-time feedback |
| **Hosting** | Amazon S3 + Amazon CloudFront | Secure, fast, and serverless web hosting |
| **API Layer** | Amazon API Gateway (WebSocket) | Persistent connection for two-way chat |
| **Compute** | AWS Lambda (Python 3.12) | On-demand execution of message handler |
| **Database** | Amazon DynamoDB | Key-value store for session history (with TTL) |
| **AI Model** | Amazon Bedrock (Meta Llama 3.1 8B) | LLM powering context-aware support |
| **IaC** | Terraform | Replicable infrastructure deployment |

---

## 📂 Project Structure

```text
├── terraform/          # Infrastructure as Code (AWS Resources)
├── backend/            # Python Lambda function code & dependencies
├── frontend/           # Static HTML/CSS/JS web interface
├── scripts/            # Build and deployment helper shell scripts
└── tests/              # Pytest suite for backend validation
```

---

## 🚀 Getting Started & Deployment

Follow these steps to deploy the chatbot to your AWS account.

### 📋 Prerequisites

Before you start, ensure you have:
1. **AWS CLI** configured on your local machine:
   ```bash
   aws configure
   ```
2. **Terraform** installed:
   - macOS: `brew install hashicorp/tap/terraform`
   - Windows/Linux: [Terraform Installation Guide](https://developer.hashicorp.com/terraform/downloads)
3. **Python 3.12+** installed on your machine.

---

### ⚡ Quick Deploy (Recommended)

A single helper script packages the Python application, initializes Terraform, creates the AWS resources, syncs the frontend to S3, and invalidates CloudFront.

Run this command from the root directory:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

**What the script does under the hood:**
1. Packages Python dependencies and code into `backend/lambda_package.zip`.
2. Provisions Bedrock model access, API Gateway, Lambda, DynamoDB, S3, and CloudFront via `terraform apply`.
3. Injects the newly created WebSocket URL dynamically into the frontend bundle (`frontend/app.js`).
4. Uploads static files to the secure S3 Bucket and triggers a CloudFront invalidation.
5. Outputs the final public CloudFront URL for you to open in your browser!

---

### 🧪 Running Tests

To validate the backend logic locally, you can use the test suite:

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install test dependencies
pip install boto3 pytest

# 3. Execute tests
pytest tests/ -v
```

---

## ⚙️ Configuration & Customization

You can customize the behavior of both the AI model and the deployment infrastructure:

### 🔧 Infrastructure Variables (`terraform/terraform.tfvars`)
- `aws_region`: The AWS Region to deploy resources (defaults to `us-east-1`).
- `bedrock_model_id`: Swap the default Meta Llama 3.1 model for Titan, Claude, or other Bedrock models.
- `session_ttl_hours`: Time-to-Live (TTL) for session history in DynamoDB (defaults to 24 hours).
- `lambda_timeout`: Max timeout in seconds for Bedrock responses (defaults to 60s).

### 🤖 Chatbot Persona & Behavior (`backend/config.py`)
- `SYSTEM_PROMPT`: Edit this block of text to change the chatbot's instructions, tone, constraints, and business rules.
- `MAX_TOKENS`: Adjust response lengths (defaults to 1024).
- `TEMPERATURE`: Set creativity (0.0 for factual/precise, 1.0 for creative/varied).
- `MAX_CONVERSATION_TURNS`: The number of message exchanges kept in Bedrock memory.

---

## 🧹 Cleanup & Resource Destruction

To teardown the AWS infrastructure and prevent any unwanted charges, navigate to the `terraform/` directory and destroy the resources:

```bash
cd terraform
terraform destroy
```

---

## 💰 Estimated Cost Breakdown

At demo and development usage levels:
- **AWS Lambda**: Free Tier covers up to 1M requests/month.
- **Amazon DynamoDB**: Free Tier covers up to 25GB of storage.
- **Amazon API Gateway**: WebSocket connections are free for the first 1M messages/connection minutes per month.
- **Amazon Bedrock**: Pay-per-token pricing (~$2-4/month for demo workloads).
