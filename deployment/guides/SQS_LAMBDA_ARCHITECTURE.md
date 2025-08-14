# 🚀 SQS & Lambda Architecture for Product Enrichment

## 📋 Overview

This architecture replaces the synchronous product enrichment with a scalable, asynchronous system using AWS SQS and Lambda functions.

## 🏗️ Architecture Components

### 1. **SQS Queue** (`ProductEnrichmentQueue`)
- **Purpose**: Receives product enrichment requests in batches
- **Batch Size**: 20 products per message (configurable)
- **Features**: 
  - Dead Letter Queue (DLQ) for failed messages
  - Long polling for efficiency
  - Message retention: 14 days
  - Visibility timeout: 15 minutes

### 2. **Lambda Function** (`ProductEnrichmentFunction`)
- **Purpose**: Processes enrichment batches asynchronously
- **Runtime**: Python 3.11
- **Timeout**: 15 minutes (configurable)
- **Memory**: 1024 MB (configurable)
- **Concurrency**: Limited to 10 concurrent executions

### 3. **DynamoDB Table** (`EnrichmentStatusTable`)
- **Purpose**: Tracks enrichment progress and status
- **Schema**: 
  - Primary Key: `catalog_id` (Hash)
  - Sort Key: `batch_id` (Range)
  - GSI: `user_id` + `created_at`

## 🔄 Data Flow

```
1. Catalog Upload → Parse Products
2. Create Product Records → Send to SQS (in batches)
3. SQS → Lambda (automatic trigger)
4. Lambda → Process Products → Update MongoDB
5. Lambda → Update DynamoDB Status
6. Real-time Progress Tracking
```

## 📊 Batch Size Recommendations

| Catalog Size | Recommended Batch Size | Reasoning |
|--------------|----------------------|-----------|
| < 100 products | 10-15 | Quick processing, easy debugging |
| 100-500 products | 15-25 | Balanced performance and reliability |
| 500-1000 products | 20-30 | Optimal for most use cases |
| > 1000 products | 25-40 | Maximum efficiency, higher memory usage |

**Current Default**: 20 products per batch

## 🚀 Deployment

### Prerequisites
- AWS CLI configured
- SAM CLI installed
- Python 3.11+
- MongoDB connection string
- Keepa API key

### Quick Deploy
```bash
# Deploy to dev environment
./deploy_lambda.sh dev us-east-1

# Deploy to production
./deploy_lambda.sh prod us-east-1
```

### Manual Deployment
```bash
# 1. Create Lambda package
pip install -r lambda_requirements.txt -t lambda_package/
cp lambda_enrichment_function.py lambda_package/
cd lambda_package && zip -r ../lambda_package.zip . && cd ..

# 2. Deploy with SAM
sam deploy --template-file template.yaml --stack-name product-enrichment-dev
```

## 🔧 Configuration

### Environment Variables
```bash
# Required
MONGODB_URI=mongodb://your-mongodb-connection
KEEPA_API_KEY=your-keepa-api-key

# Optional
AWS_REGION=us-east-1
BATCH_SIZE=20
```

### SAM Template Parameters
```yaml
Environment: dev/staging/prod
BatchSize: 5-50 products per batch
LambdaTimeout: 60-900 seconds
LambdaMemory: 512-3008 MB
```

## 📱 Usage

### 1. **Send Products to SQS**
```python
from sqs_enrichment_service import SQSEnrichmentService

sqs_service = SQSEnrichmentService(
    queue_url="your-sqs-queue-url",
    batch_size=20
)

# Send products for enrichment
result = sqs_service.send_enrichment_batches(
    catalog_id="catalog123",
    user_id="user456",
    products=product_list
)
```

### 2. **Monitor Progress**
```python
# Check DynamoDB for enrichment status
import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('dev-enrichment-status')

response = table.query(
    KeyConditionExpression='catalog_id = :catalog_id',
    ExpressionAttributeValues={':catalog_id': 'catalog123'}
)
```

### 3. **API Integration**
```python
# Update your existing enrichment endpoint
@router.post("/{catalog_id}/enrich")
async def trigger_enrichment(catalog_id: str, provider: str = "keepa"):
    # Instead of synchronous processing:
    # 1. Parse catalog and create products
    # 2. Send products to SQS
    # 3. Return immediate response with tracking ID
    
    sqs_result = sqs_service.send_enrichment_batches(
        catalog_id=catalog_id,
        user_id=current_user.id,
        products=products
    )
    
    return {
        "message": "Enrichment queued successfully",
        "tracking_id": f"enrich_{catalog_id}_{int(time.time())}",
        "total_products": sqs_result["total_products"],
        "total_batches": sqs_result["total_batches"]
    }
```

## 📊 Monitoring & Observability

### CloudWatch Dashboard
- **Lambda Metrics**: Invocations, errors, duration
- **SQS Metrics**: Messages sent/received, queue depth
- **Custom Metrics**: Enrichment success/failure rates

### Logs
- **Lambda Logs**: `/aws/lambda/dev-product-enrichment`
- **Application Logs**: Structured JSON logging
- **Error Tracking**: Detailed error messages with context

### Alarms
```yaml
# Example CloudWatch Alarms
- High Error Rate (>5% errors)
- Long Processing Time (>10 minutes)
- Queue Depth (>100 messages)
- Lambda Throttling
```

## 🔒 Security

### IAM Permissions
- **Least Privilege**: Only necessary SQS/DynamoDB permissions
- **Resource Scoping**: Specific ARNs for each resource
- **Cross-Account**: Support for cross-account deployments

### Data Protection
- **Encryption**: SQS and DynamoDB encryption at rest
- **VPC**: Optional VPC deployment for private resources
- **Secrets**: Environment variables for sensitive data

## 💰 Cost Optimization

### SQS Costs
- **Standard Queue**: $0.40 per million requests
- **Batch Processing**: Reduce API calls with batching
- **Message Retention**: 14 days (configurable)

### Lambda Costs
- **Execution Time**: Pay per 100ms
- **Memory**: Optimize memory allocation
- **Concurrency**: Limit concurrent executions

### Cost Estimation (1000 products)
```
SQS: ~$0.001 (1 message with 20 products)
Lambda: ~$0.50 (50 executions × 10 seconds)
DynamoDB: ~$0.25 (read/write operations)
Total: ~$0.75 per 1000 products
```

## 🚨 Error Handling

### Retry Logic
- **SQS**: Automatic retries with exponential backoff
- **Lambda**: Dead Letter Queue for failed messages
- **API Calls**: Keepa API retry with fallback to mock data

### Failure Scenarios
1. **Keepa API Unavailable** → Fallback to mock data
2. **MongoDB Connection Failed** → Retry with exponential backoff
3. **Lambda Timeout** → Message returns to queue
4. **Invalid Data** → Log error and continue with other products

## 🔄 Migration from Synchronous

### Phase 1: Parallel Deployment
- Deploy SQS/Lambda infrastructure
- Keep existing synchronous enrichment
- Test with small catalogs

### Phase 2: Gradual Migration
- Update enrichment endpoint to use SQS
- Monitor performance and costs
- Validate data consistency

### Phase 3: Full Migration
- Remove synchronous enrichment code
- Optimize batch sizes and timeouts
- Implement advanced monitoring

## 🧪 Testing

### Local Testing
```bash
# Test Lambda function locally
sam local invoke ProductEnrichmentFunction \
  --event events/sqs-event.json \
  --env-vars env.json

# Test SQS service
python3 sqs_enrichment_service.py
```

### Integration Testing
```bash
# Deploy to test environment
./deploy_lambda.sh test us-east-1

# Run end-to-end tests
python3 -m pytest tests/test_enrichment_flow.py
```

## 📚 Additional Resources

- [AWS SQS Developer Guide](https://docs.aws.amazon.com/sqs/)
- [AWS Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [SAM Documentation](https://docs.aws.amazon.com/serverless-application-model/)
- [CloudFormation Reference](https://docs.aws.amazon.com/AWSCloudFormation/)

## 🤝 Support

For issues or questions:
1. Check CloudWatch logs for detailed error information
2. Review Lambda function metrics
3. Verify SQS queue attributes
4. Check DynamoDB table for status updates

---

**🎉 This architecture provides scalable, reliable, and cost-effective product enrichment processing!**
