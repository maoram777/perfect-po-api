# Accepting AWS App Runner Subscription

## Quick Steps to Accept App Runner Subscription

The subscription acceptance is a **one-time requirement** that must be done through the AWS Console. After accepting, you can use the CLI/script to deploy.

### Method 1: Via AWS Console (Recommended)

1. **Open AWS App Runner Console:**
   - Go to: https://console.aws.amazon.com/apprunner/
   - Make sure you're in the `us-east-1` region
   - Make sure you're using the correct AWS account (259886476792)

2. **Accept Service Terms:**
   - If you see a prompt to "Get started" or "Subscribe", click it
   - Review and accept the service terms
   - This is a one-time action

3. **Verify Subscription:**
   - After accepting, you should be able to see the App Runner dashboard
   - You don't need to create a service manually - just accept the terms

4. **Run Deployment Script:**
   ```bash
   ./deploy-apprunner.sh
   ```

### Method 2: Via AWS CLI (Alternative)

Try this command to see if it triggers the subscription:

```bash
aws apprunner list-services --profile allshoes --region us-east-1
```

If it still shows the subscription error, you must use Method 1 (Console).

### Verification

After accepting, verify with:

```bash
aws apprunner list-services --profile allshoes --region us-east-1
```

If this command runs without errors, the subscription is active and you can proceed with deployment.


