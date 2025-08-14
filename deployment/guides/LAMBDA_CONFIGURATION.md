# 🔐 Lambda Configuration & Secrets Management

## 📋 Overview

Lambda functions don't use `.env` files like traditional applications. Instead, they use AWS-native configuration methods for security and scalability.

## 🔧 **Configuration Methods**

### 1. **Environment Variables** (Non-sensitive data)
```yaml
# In template.yaml
Environment:
  Variables:
    ENVIRONMENT: dev
    BATCH_SIZE: 20
    AWS_REGION: us-east-1
```

**Use for:**
- ✅ Configuration values
- ✅ Feature flags
- ✅ Environment names
- ❌ API keys
- ❌ Database passwords
- ❌ Connection strings

### 2. **AWS Secrets Manager** (Sensitive data - RECOMMENDED)
```python
# In Lambda function
import boto3

secrets_client = boto3.client('secretsmanager')
secret_value = secrets_client.get_secret_value(SecretId='secret-name')
```

**Use for:**
- ✅ API keys (Keepa, etc.)
- ✅ Database credentials
- ✅ Connection strings
- ✅ Passwords
- ✅ Private keys

### 3. **AWS Systems Manager Parameter Store** (Alternative)
```python
# In Lambda function
import boto3

ssm_client = boto3.client('ssm')
parameter = ssm_client.get_parameter(Name='/app/mongodb-uri', WithDecryption=True)
```

**Use for:**
- ✅ Configuration values
- ✅ Non-sensitive secrets
- ✅ Hierarchical configuration

## 🚀 **Our Implementation**

### **Secret Names Pattern**
```
{environment}-{secret-type}
Examples:
- dev-mongodb-connection-string
- dev-keepa-api-key
- prod-mongodb-connection-string
- prod-keepa-api-key
```

### **Lambda Function Logic**
```python
def get_secret(secret_name: str) -> str:
    """Retrieve secret from AWS Secrets Manager."""
    try:
        response = secrets_client.get_secret_value(SecretId=secret_name)
        if 'SecretString' in response:
            return response['SecretString']
        else:
            return response['SecretBinary'].decode('utf-8')
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        return None

# Usage in functions
environment = os.environ.get('ENVIRONMENT', 'dev')
mongodb_uri = get_secret(f"{environment}-mongodb-connection-string") or MONGODB_URI
keepa_api_key = get_secret(f"{environment}-keepa-api-key") or KEEPA_API_KEY
```

## 🔐 **Setting Up Secrets**

### **Step 1: Run Setup Script**
```bash
# Set up secrets for dev environment
./setup_secrets.sh dev us-east-1

# Set up secrets for production
./setup_secrets.sh prod us-east-1
```

### **Step 2: Manual Secret Creation**
```bash
# MongoDB connection string
aws secretsmanager create-secret \
    --name "dev-mongodb-connection-string" \
    --secret-string "mongodb://user:pass@host:port/db" \
    --description "MongoDB connection for dev environment"

# Keepa API key
aws secretsmanager create-secret \
    --name "dev-keepa-api-key" \
    --secret-string "your-keepa-api-key" \
    --description "Keepa API key for dev environment"
```

### **Step 3: View/Update Secrets**
```bash
# List all secrets
aws secretsmanager list-secrets --region us-east-1

# Update a secret
aws secretsmanager update-secret \
    --secret-id "dev-mongodb-connection-string" \
    --secret-string "new-connection-string"

# Delete a secret
aws secretsmanager delete-secret --secret-id "dev-mongodb-connection-string"
```

## 📊 **Environment Variables vs Secrets**

| Aspect | Environment Variables | AWS Secrets Manager |
|--------|---------------------|-------------------|
| **Security** | ❌ Visible in console | ✅ Encrypted at rest |
| **Cost** | ✅ Free | 💰 $0.40 per 10K API calls |
| **Rotation** | ❌ Manual | ✅ Automatic (optional) |
| **Audit** | ❌ Limited | ✅ Full audit trail |
| **Access Control** | ❌ Basic IAM | ✅ Fine-grained IAM |
| **Latency** | ✅ Instant | ⏱️ ~100ms first call |

## 🔒 **Security Best Practices**

### **1. IAM Permissions**
```yaml
# In template.yaml - Least privilege access
Policies:
  - SecretsManagerReadWrite:
      SecretArn: !Sub "arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:secret:*"
```

### **2. Secret Naming Convention**
```
{environment}-{service}-{purpose}
Examples:
- dev-mongodb-connection-string
- prod-keepa-api-key
- staging-redis-password
```

### **3. Environment Separation**
- **dev**: Development secrets
- **staging**: Staging secrets  
- **prod**: Production secrets
- **Never mix environments!**

### **4. Secret Rotation**
```bash
# Enable automatic rotation (production only)
aws secretsmanager rotate-secret \
    --secret-id "prod-keepa-api-key" \
    --rotation-rules AutomaticallyAfterDays=90
```

## 💰 **Cost Optimization**

### **Secrets Manager Pricing**
- **Storage**: $0.40 per secret per month
- **API Calls**: $0.05 per 10,000 API calls
- **Rotation**: $0.10 per rotation

### **Cost Estimation (1000 Lambda invocations)**
```
Storage: $0.40/month (2 secrets)
API Calls: $0.005 (1000 calls)
Total: ~$0.41/month
```

## 🔄 **Migration from .env Files**

### **Phase 1: Parallel Setup**
1. Keep existing `.env` files
2. Set up AWS Secrets Manager
3. Test Lambda with secrets

### **Phase 2: Gradual Migration**
1. Update Lambda to use secrets
2. Remove environment variables
3. Test thoroughly

### **Phase 3: Cleanup**
1. Remove `.env` files from Lambda
2. Update documentation
3. Monitor costs

## 🧪 **Testing Secrets**

### **Local Testing**
```bash
# Test secret retrieval locally
python3 -c "
import boto3
client = boto3.client('secretsmanager')
try:
    secret = client.get_secret_value(SecretId='dev-mongodb-connection-string')
    print('✅ Secret accessible')
except Exception as e:
    print(f'❌ Secret error: {e}')
"
```

### **Lambda Testing**
```python
# Add to Lambda function for testing
def test_secrets():
    """Test function to verify secrets are accessible."""
    try:
        mongodb_uri = get_secret(f"{os.environ.get('ENVIRONMENT', 'dev')}-mongodb-connection-string")
        keepa_key = get_secret(f"{os.environ.get('ENVIRONMENT', 'dev')}-keepa-api-key")
        
        logger.info(f"MongoDB URI accessible: {'Yes' if mongodb_uri else 'No'}")
        logger.info(f"Keepa API key accessible: {'Yes' if keepa_key else 'No'}")
        
        return {
            "mongodb": bool(mongodb_uri),
            "keepa": bool(keepa_key)
        }
    except Exception as e:
        logger.error(f"Secret test failed: {e}")
        return {"error": str(e)}
```

## 📚 **Troubleshooting**

### **Common Issues**

1. **Secret Not Found**
   ```bash
   # Check secret exists
   aws secretsmanager describe-secret --secret-id "dev-mongodb-connection-string"
   ```

2. **Permission Denied**
   ```bash
   # Check IAM permissions
   aws iam get-user
   aws iam list-attached-user-policies --user-name YOUR_USERNAME
   ```

3. **Lambda Can't Access Secrets**
   ```bash
   # Check Lambda execution role
   aws lambda get-function --function-name dev-product-enrichment
   ```

4. **Secret Value is Empty**
   ```bash
   # Verify secret has content
   aws secretsmanager get-secret-value --secret-id "dev-mongodb-connection-string"
   ```

## 🎯 **Next Steps**

1. **Set up secrets**: `./setup_secrets.sh dev us-east-1`
2. **Deploy Lambda**: `./deploy_lambda.sh dev us-east-1`
3. **Test secrets**: Verify Lambda can access secrets
4. **Monitor costs**: Check AWS billing for Secrets Manager usage

---

**🔐 This approach provides enterprise-grade security for your Lambda functions!**
