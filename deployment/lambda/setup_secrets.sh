#!/bin/bash

# Setup AWS Secrets Manager for Product Enrichment Lambda
# This script creates the necessary secrets for the Lambda function

set -e

# Configuration
ENVIRONMENT=${1:-dev}
REGION=${2:-us-east-1}

echo "🔐 Setting up AWS Secrets Manager for Product Enrichment..."
echo "Environment: ${ENVIRONMENT}"
echo "Region: ${REGION}"

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured. Please run 'aws configure' first."
    exit 1
fi

# Function to create secret
create_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3
    
    echo "Creating secret: ${secret_name}"
    
    # Check if secret already exists
    if aws secretsmanager describe-secret --secret-id "${secret_name}" --region "${REGION}" &> /dev/null; then
        echo "Secret ${secret_name} already exists. Updating..."
        aws secretsmanager update-secret \
            --secret-id "${secret_name}" \
            --secret-string "${secret_value}" \
            --description "${description}" \
            --region "${REGION}"
    else
        echo "Creating new secret: ${secret_name}"
        aws secretsmanager create-secret \
            --name "${secret_name}" \
            --secret-string "${secret_value}" \
            --description "${description}" \
            --region "${REGION}"
    fi
    
    echo "✅ Secret ${secret_name} created/updated successfully"
}

# Function to prompt for secret value
prompt_for_secret() {
    local prompt_text=$1
    local secret_name=$2
    local is_required=${3:-true}
    
    echo ""
    echo "${prompt_text}"
    if [ "${is_required}" = "true" ]; then
        echo "(Required)"
    else
        echo "(Optional - press Enter to skip)"
    fi
    
    read -s secret_value
    echo ""
    
    if [ "${is_required}" = "true" ] && [ -z "${secret_value}" ]; then
        echo "❌ ${secret_name} is required. Please provide a value."
        exit 1
    fi
    
    echo "${secret_value}"
}

echo ""
echo "📝 Please provide the following secret values:"
echo ""

# Get MongoDB connection string
echo "🔍 MongoDB Connection String"
echo "Format: mongodb://username:password@host:port/database"
echo "Example: mongodb://user:pass@cluster.mongodb.net:27017/perfect-po"
mongodb_uri=$(prompt_for_secret "Enter MongoDB connection string:" "mongodb-connection-string")

# Get Keepa API key
echo "🔑 Keepa API Key"
echo "Get your API key from: https://keepa.com/#!api"
keepa_api_key=$(prompt_for_secret "Enter Keepa API key:" "keepa-api-key")

# Create secrets
echo ""
echo "🚀 Creating secrets in AWS Secrets Manager..."

# Create MongoDB connection string secret
create_secret \
    "${ENVIRONMENT}-mongodb-connection-string" \
    "${mongodb_uri}" \
    "MongoDB connection string for ${ENVIRONMENT} environment"

# Create Keepa API key secret
create_secret \
    "${ENVIRONMENT}-keepa-api-key" \
    "${keepa_api_key}" \
    "Keepa API key for ${ENVIRONMENT} environment"

echo ""
echo "✅ All secrets created successfully!"
echo ""
echo "📋 Secret Names:"
echo "  - ${ENVIRONMENT}-mongodb-connection-string"
echo "  - ${ENVIRONMENT}-keepa-api-key"
echo ""
echo "🔧 Next Steps:"
echo "1. Update your Lambda function environment variables to use these secret names"
echo "2. Deploy the Lambda function with: ./deploy_lambda.sh ${ENVIRONMENT} ${REGION}"
echo "3. Test the secrets are accessible from Lambda"
echo ""
echo "📚 Secret Management:"
echo "  - View secrets: aws secretsmanager list-secrets --region ${REGION}"
echo "  - Update secrets: aws secretsmanager update-secret --secret-id SECRET_NAME --secret-string NEW_VALUE"
echo "  - Delete secrets: aws secretsmanager delete-secret --secret-id SECRET_NAME"
echo ""
echo "🔒 Security Notes:"
echo "  - Secrets are encrypted at rest using AWS KMS"
echo "  - Access is controlled via IAM policies"
echo "  - Consider enabling automatic rotation for production secrets"
