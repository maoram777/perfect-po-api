#!/bin/bash
# Deploy Perfect PO API to AWS App Runner
# Prerequisites: Accept App Runner service terms in AWS Console first

set -e

PROFILE="allshoes"
REGION="us-east-1"
ECR_REPOSITORY="perfect-po-api"
AWS_ACCOUNT_ID="259886476792"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
# Use timestamp-based tag to ensure App Runner detects the new image
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
IMAGE_TAG="${TIMESTAMP}"
LATEST_TAG="latest"

echo "🚀 Deploying Perfect PO API to AWS App Runner..."
echo "Profile: $PROFILE"
echo "Region: $REGION"
echo ""

# Step 1: Build and push Docker image to ECR
echo "📦 Step 1: Building and pushing Docker image to ECR..."
echo ""

# Get ECR login token
echo "   Authenticating with ECR..."
aws ecr get-login-password --profile $PROFILE --region $REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

# Check if repository exists, create if not
echo "   Checking ECR repository..."
if ! aws ecr describe-repositories --profile $PROFILE --region $REGION --repository-names $ECR_REPOSITORY &>/dev/null; then
    echo "   Creating ECR repository: $ECR_REPOSITORY"
    aws ecr create-repository --profile $PROFILE --region $REGION --repository-name $ECR_REPOSITORY
fi

# Build Docker image (no cache to ensure latest code is included)
echo "   Building Docker image (no cache)..."
echo "   This ensures all latest code changes are included..."
docker build --no-cache -t $ECR_REPOSITORY:$IMAGE_TAG -t $ECR_REPOSITORY:$LATEST_TAG .

# Quick verification that main.py was copied
echo "   Verifying app/main.py exists in image..."
if docker run --rm $ECR_REPOSITORY:$IMAGE_TAG test -f app/main.py; then
    echo "   ✓ app/main.py found in image"
else
    echo "   ⚠️  Warning: app/main.py not found in image"
fi

# Tag images for ECR (both timestamp and latest)
echo "   Tagging images for ECR..."
docker tag $ECR_REPOSITORY:$IMAGE_TAG $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
docker tag $ECR_REPOSITORY:$LATEST_TAG $ECR_REGISTRY/$ECR_REPOSITORY:$LATEST_TAG

# Push images to ECR
echo "   Pushing images to ECR (tag: $IMAGE_TAG and latest)..."
docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG
docker push $ECR_REGISTRY/$ECR_REPOSITORY:$LATEST_TAG

echo "✅ Docker image pushed successfully!"
echo ""

# Step 2: Update App Runner service
echo "🔄 Step 2: Updating App Runner service..."
echo ""

# Check if service already exists
SERVICE_EXISTS=$(aws apprunner list-services --profile $PROFILE --region $REGION --query "ServiceSummaryList[?ServiceName=='perfect-po-api'].ServiceName" --output text 2>/dev/null || echo "")

if [ ! -z "$SERVICE_EXISTS" ]; then
    echo "⚠️  Service 'perfect-po-api' already exists. Updating..."
    SERVICE_ARN=$(aws apprunner list-services --profile $PROFILE --region $REGION --query "ServiceSummaryList[?ServiceName=='perfect-po-api'].ServiceArn" --output text)
    
    # Create temporary update config with the new image tag to force App Runner to use the new image
    echo "   Using image tag: $IMAGE_TAG to force new deployment..."
    if [ -f "apprunner-update-config.json" ]; then
        # Update the ImageIdentifier with the new timestamp tag
        jq --arg IMAGE_TAG "$IMAGE_TAG" --arg ECR_REGISTRY "$ECR_REGISTRY" --arg REPO "$ECR_REPOSITORY" \
           '.SourceConfiguration.ImageRepository.ImageIdentifier = "\($ECR_REGISTRY)/\($REPO):\($IMAGE_TAG)"' \
           apprunner-update-config.json > /tmp/apprunner-update-${IMAGE_TAG}.json
        aws apprunner update-service --profile $PROFILE --region $REGION --service-arn "$SERVICE_ARN" --cli-input-json file:///tmp/apprunner-update-${IMAGE_TAG}.json
        rm /tmp/apprunner-update-${IMAGE_TAG}.json
    else
        # Fallback: remove ServiceName and update image tag
        echo "⚠️  apprunner-update-config.json not found, using apprunner-config.json..."
        jq --arg IMAGE_TAG "$IMAGE_TAG" --arg ECR_REGISTRY "$ECR_REGISTRY" --arg REPO "$ECR_REPOSITORY" \
           'del(.ServiceName) | .SourceConfiguration.ImageRepository.ImageIdentifier = "\($ECR_REGISTRY)/\($REPO):\($IMAGE_TAG)"' \
           apprunner-config.json > /tmp/apprunner-update-temp.json
        aws apprunner update-service --profile $PROFILE --region $REGION --service-arn "$SERVICE_ARN" --cli-input-json file:///tmp/apprunner-update-temp.json
        rm /tmp/apprunner-update-temp.json
    fi
    echo "✅ Service update initiated with new image tag: $IMAGE_TAG"
else
    echo "🆕 Creating new App Runner service..."
    aws apprunner create-service --profile $PROFILE --region $REGION --cli-input-json file://apprunner-config.json
    echo "✅ Service creation initiated"
fi

echo ""
echo "⏳ Waiting for service to be ready..."
echo "   This may take a few minutes..."

# Wait for service to be running
SERVICE_ARN=$(aws apprunner list-services --profile $PROFILE --region $REGION --query "ServiceSummaryList[?ServiceName=='perfect-po-api'].ServiceArn" --output text)

if [ -z "$SERVICE_ARN" ]; then
    echo "❌ Could not find service ARN. Please check the service status in AWS Console."
    exit 1
fi

# Poll for service status
MAX_ATTEMPTS=60
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    STATUS=$(aws apprunner describe-service --profile $PROFILE --region $REGION --service-arn "$SERVICE_ARN" --query "Service.Status" --output text)
    
    if [ "$STATUS" == "RUNNING" ]; then
        echo "✅ Service is RUNNING!"
        break
    elif [ "$STATUS" == "CREATE_FAILED" ] || [ "$STATUS" == "UPDATE_FAILED" ]; then
        echo "❌ Service creation/update failed. Status: $STATUS"
        echo "   Check AWS Console for details."
        exit 1
    fi
    
    echo "   Status: $STATUS (attempt $((ATTEMPT+1))/$MAX_ATTEMPTS)"
    sleep 10
    ATTEMPT=$((ATTEMPT+1))
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo "⏰ Timeout waiting for service to be ready. Check AWS Console for status."
    exit 1
fi

# Get the service URL
SERVICE_URL=$(aws apprunner describe-service --profile $PROFILE --region $REGION --service-arn "$SERVICE_ARN" --query "Service.ServiceUrl" --output text)

echo ""
echo "🎉 Deployment complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📍 Public URL: $SERVICE_URL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Service Details:"
echo "   Service Name: perfect-po-api"
echo "   Service ARN: $SERVICE_ARN"
echo "   Status: RUNNING"
echo ""
echo "🔍 Test the API:"
echo "   curl $SERVICE_URL/health"
echo "   curl $SERVICE_URL/docs"
echo ""


