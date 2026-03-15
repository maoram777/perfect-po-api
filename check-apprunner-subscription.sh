#!/bin/bash
# Check if App Runner subscription is active

PROFILE="allshoes"
REGION="us-east-1"

echo "🔍 Checking App Runner subscription status..."
echo ""

# Try to list services - if this works, subscription is active
if aws apprunner list-services --profile $PROFILE --region $REGION &>/dev/null; then
    echo "✅ App Runner subscription is ACTIVE!"
    echo "   You can now run: ./deploy-apprunner.sh"
    exit 0
else
    ERROR=$(aws apprunner list-services --profile $PROFILE --region $REGION 2>&1)
    
    if echo "$ERROR" | grep -q "SubscriptionRequiredException"; then
        echo "❌ App Runner subscription is NOT active"
        echo ""
        echo "📋 To activate:"
        echo "   1. Open: https://console.aws.amazon.com/apprunner/"
        echo "   2. Make sure you're in region: $REGION"
        echo "   3. Accept the service terms (one-time action)"
        echo "   4. Run this script again to verify"
        echo ""
        echo "📄 See ACCEPT_APP_RUNNER_SUBSCRIPTION.md for detailed instructions"
        exit 1
    else
        echo "❌ Error checking subscription:"
        echo "$ERROR"
        exit 1
    fi
fi



