#!/bin/bash

# AWS ECS Infrastructure Deployment Script
# This script deploys the complete ECS infrastructure for Perfect PO API

set -e

# Configuration
ENVIRONMENT=${1:-dev}
STACK_NAME="perfect-po-api-${ENVIRONMENT}"
REGION=${AWS_REGION:-us-east-1}

echo "🚀 Deploying Perfect PO API ECS Infrastructure..."
echo "Environment: ${ENVIRONMENT}"
echo "Stack Name: ${STACK_NAME}"
echo "Region: ${REGION}"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    echo "   Visit: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
    exit 1
fi

# Check AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ AWS CLI and credentials configured"

# Check if stack already exists
if aws cloudformation describe-stacks --stack-name $STACK_NAME --region $REGION &> /dev/null; then
    echo "📝 Stack ${STACK_NAME} already exists. Updating..."
    OPERATION="update-stack"
else
    echo "🆕 Stack ${STACK_NAME} does not exist. Creating..."
    OPERATION="create-stack"
fi

# Deploy infrastructure
echo "🏗️  Deploying infrastructure with CloudFormation..."

if [ "$OPERATION" = "create-stack" ]; then
    aws cloudformation create-stack \
        --stack-name $STACK_NAME \
        --template-body file://ecs-infrastructure.yaml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION
    
    echo "⏳ Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete \
        --stack-name $STACK_NAME \
        --region $REGION
else
    aws cloudformation update-stack \
        --stack-name $STACK_NAME \
        --template-body file://ecs-infrastructure.yaml \
        --parameters ParameterKey=Environment,ParameterValue=$ENVIRONMENT \
        --capabilities CAPABILITY_NAMED_IAM \
        --region $REGION
    
    echo "⏳ Waiting for stack update to complete..."
    aws cloudformation wait stack-update-complete \
        --stack-name $STACK_NAME \
        --region $REGION
fi

# Get stack outputs
echo "📊 Getting stack outputs..."
STACK_OUTPUTS=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --region $REGION \
    --query 'Stacks[0].Outputs')

# Extract important values
CLUSTER_NAME=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="ClusterName") | .OutputValue')
SERVICE_NAME=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="ServiceName") | .OutputValue')
LOAD_BALANCER_DNS=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="LoadBalancerDNS") | .OutputValue')
ECR_REPO_URI=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="ECRRepositoryURI") | .OutputValue')
VPC_ID=$(echo "$STACK_OUTPUTS" | jq -r '.[] | select(.OutputKey=="VPCId") | .OutputValue')

echo ""
echo "🎉 Infrastructure deployed successfully!"
echo ""
echo "📋 Stack Information:"
echo "  - Stack Name: ${STACK_NAME}"
echo "  - Environment: ${ENVIRONMENT}"
echo "  - Region: ${REGION}"
echo ""
echo "🏗️  Resources Created:"
echo "  - ECS Cluster: ${CLUSTER_NAME}"
echo "  - ECS Service: ${SERVICE_NAME}"
echo "  - Load Balancer: ${LOAD_BALANCER_DNS}"
echo "  - ECR Repository: ${ECR_REPO_URI}"
echo "  - VPC: ${VPC_ID}"
echo ""
echo "🔧 Next Steps:"
echo "1. Set up secrets in AWS Secrets Manager:"
echo "   - perfect-po-${ENVIRONMENT}-mongodb-uri"
echo "   - perfect-po-${ENVIRONMENT}-jwt-secret"
echo "   - perfect-po-${ENVIRONMENT}-keepa-api-key"
echo ""
echo "2. Update GitHub repository secrets:"
echo "   - AWS_ACCESS_KEY_ID"
echo "   - AWS_SECRET_ACCESS_KEY"
echo ""
echo "3. Push to GitHub to trigger deployment:"
echo "   git push origin main"
echo ""
echo "4. Monitor deployment in GitHub Actions"
echo ""
echo "📱 Your API will be available at:"
echo "  http://${LOAD_BALANCER_DNS}"
echo ""
echo "�� Happy deploying!"
