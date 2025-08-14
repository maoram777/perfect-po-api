#!/bin/bash

# Product Enrichment Lambda Deployment Script
# This script deploys the SQS and Lambda infrastructure for product enrichment

set -e

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}
STACK_NAME="product-enrichment-${ENVIRONMENT}"

echo "🚀 Deploying Product Enrichment Infrastructure..."
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"
echo "Stack Name: ${STACK_NAME}"

# Check if SAM CLI is installed
if ! command -v sam &> /dev/null; then
    echo "❌ SAM CLI is not installed. Please install it first:"
    echo "   https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html"
    exit 1
fi

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Create deployment package
echo "📦 Creating Lambda deployment package..."

# Create temporary directory for packaging
PACKAGE_DIR="lambda_package"
rm -rf $PACKAGE_DIR
mkdir -p $PACKAGE_DIR

# Copy Lambda function
cp lambda_enrichment_function.py $PACKAGE_DIR/

# Install dependencies
pip install -r lambda_requirements.txt -t $PACKAGE_DIR/

# Remove unnecessary files to reduce package size
cd $PACKAGE_DIR
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type d -name "*.dist-info" -exec rm -rf {} +
find . -type d -name "tests" -exec rm -rf {} +
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete

# Create ZIP package
zip -r ../lambda_package.zip .
cd ..

# Clean up package directory
rm -rf $PACKAGE_DIR

echo "✅ Lambda package created: lambda_package.zip"

# Deploy with SAM
echo "🚀 Deploying with SAM..."

sam deploy \
    --template-file template.yaml \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        Environment=$ENVIRONMENT \
        BatchSize=20 \
        LambdaTimeout=900 \
        LambdaMemory=1024 \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --no-fail-on-empty-changeset

echo "✅ Deployment completed successfully!"

# Get stack outputs
echo "📊 Stack Outputs:"
aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs' \
    --output table

echo ""
echo "🎉 Product Enrichment Infrastructure deployed!"
echo ""
echo "Next steps:"
echo "1. Update your .env file with the SQS queue URL from the outputs above"
echo "2. Test the SQS service with the sqs_enrichment_service.py"
echo "3. Monitor the Lambda function in CloudWatch"
echo ""
echo "To test the deployment:"
echo "python3 sqs_enrichment_service.py"
