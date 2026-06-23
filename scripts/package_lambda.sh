#!/usr/bin/env bash
# package_lambda.sh — Zips the backend Python code for Lambda deployment
# Run from the project root: ./scripts/package_lambda.sh

set -e  # Exit on any error

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
OUTPUT_ZIP="$BACKEND_DIR/lambda_package.zip"

echo "📦 Packaging Lambda function..."

# Remove old package if exists
rm -f "$OUTPUT_ZIP"

# Create zip from the backend directory
# Excluding the zip itself, __pycache__, and test files
cd "$BACKEND_DIR"
zip -r "$OUTPUT_ZIP" . \
  --exclude "*.pyc" \
  --exclude "__pycache__/*" \
  --exclude "lambda_package.zip" \
  --exclude ".pytest_cache/*" \
  --exclude "tests/*"

echo "✅ Lambda package created: $OUTPUT_ZIP"
echo "   Size: $(du -sh "$OUTPUT_ZIP" | cut -f1)"
