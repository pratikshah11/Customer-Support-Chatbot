#!/usr/bin/env bash
# deploy.sh — Full deployment: Terraform apply + frontend sync to S3
# Run from the project root: ./scripts/deploy.sh
#
# Prerequisites:
#   - AWS CLI configured (aws configure)
#   - Terraform installed
#   - Already ran: terraform init (first time only)

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERRAFORM_DIR="$PROJECT_ROOT/terraform"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo ""
echo "🚀 Deploying Customer Support Chatbot"
echo "======================================"
echo ""

# Step 1: Package Lambda
echo "📦 Step 1: Packaging Lambda function..."
bash "$PROJECT_ROOT/scripts/package_lambda.sh"
echo ""

# Step 2: Terraform init (idempotent — safe to run every time)
echo "⚙️  Step 2: Initializing Terraform..."
cd "$TERRAFORM_DIR"
terraform init -input=false
echo ""

# Step 3: Terraform plan
echo "📋 Step 3: Planning infrastructure changes..."
terraform plan -input=false
echo ""

# Step 4: Terraform apply
echo "🏗️  Step 4: Applying infrastructure..."
terraform apply -input=false -auto-approve
echo ""

# Step 5: Get outputs
echo "📤 Step 5: Reading Terraform outputs..."
WEBSOCKET_URL=$(terraform output -raw websocket_url)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)
S3_BUCKET=$(terraform output -raw s3_bucket_name)
CLOUDFRONT_ID=$(terraform output -raw cloudfront_distribution_id)

echo "   WebSocket URL: $WEBSOCKET_URL"
echo "   CloudFront URL: $CLOUDFRONT_URL"
echo "   S3 Bucket: $S3_BUCKET"
echo ""

# Step 6: Inject WebSocket URL into frontend app.js
echo "🔧 Step 6: Injecting WebSocket URL into frontend..."
cd "$FRONTEND_DIR"
sed "s|%%WEBSOCKET_URL%%|$WEBSOCKET_URL|g" app.js > app_deploy.js
echo "   WebSocket URL injected."
echo ""

# Step 7: Sync frontend to S3
echo "☁️  Step 7: Syncing frontend to S3..."
aws s3 sync "$FRONTEND_DIR" "s3://$S3_BUCKET/" \
  --exclude "*.sh" \
  --exclude "app.js" \
  --delete

# Upload the version of app.js with the URL injected
aws s3 cp app_deploy.js "s3://$S3_BUCKET/app.js"
rm -f app_deploy.js
echo "   Frontend synced."
echo ""

# Step 8: Invalidate CloudFront cache
echo "🔄 Step 8: Invalidating CloudFront cache..."
aws cloudfront create-invalidation \
  --distribution-id "$CLOUDFRONT_ID" \
  --paths "/*" \
  --query "Invalidation.Id" \
  --output text
echo "   Cache invalidated."
echo ""

echo "======================================"
echo "✅ Deployment complete!"
echo ""
echo "   🌐 Chat UI:      $CLOUDFRONT_URL"
echo "   🔌 WebSocket:    $WEBSOCKET_URL"
echo ""
echo "   Note: CloudFront may take 1-2 minutes to propagate."
echo "   Open the URL above in your browser to test the chatbot."
echo ""
