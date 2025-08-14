# Local Enrichment Testing Guide

This guide shows you how to test the local enrichment functionality without needing SQS/Lambda.

## 🚀 Quick Start

### 1. Start the API
```bash
# Option A: Using Docker (recommended)
docker-compose up -d

# Option B: Direct Python
python run.py
```

### 2. Test the Enrichment Flow
```bash
python test_enrichment.py
```

## 🔧 Configuration

### File Upload Formats

The API supports the following file formats:
- **CSV**: Comma-separated values
- **JSON**: JSON array or object with 'items' key
- **Excel**: .xlsx and .xls files with full parsing support
- **Flexible Field Mapping**: Automatically maps common catalog field names

### Excel File Support
- Full Excel parsing using pandas and openpyxl
- Automatic column detection and mapping
- Handles various field naming conventions
- Processes large files efficiently

### Environment Variables
Make sure your `.env` file includes:

```bash
# AWS Configuration (for S3 file storage)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=perfect-po-catalogs

# External APIs (for enrichment)
AMAZON_API_KEY=your_amazon_api_key
AMAZON_API_SECRET=your_amazon_api_secret
KEEPA_API_KEY=your_keepa_api_key

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here
```

## 📋 Testing Steps

### 1. Register and Login
- Register a new user at `POST /auth/register`
- Login at `POST /auth/login` to get JWT token

### 2. Upload Catalog
- Upload a catalog file at `POST /catalogs/upload`
- Supported formats: CSV, JSON, Excel

### 3. Check Available Providers
- Get enrichment providers at `GET /catalogs/providers`
- Currently available: `amazon`, `keepa`

### 4. Trigger Enrichment
- Enrich with Amazon: `POST /catalogs/{id}/enrich?provider=amazon`
- Enrich with Keepa: `POST /catalogs/{id}/enrich?provider=keepa`

### 5. View Results
- Check products at `GET /products`
- Get summary at `GET /products/catalog/{id}/summary`

## 🔍 How It Works

### Local Enrichment Service
The system now includes a `LocalEnrichmentService` that:

1. **Processes catalogs immediately** (no SQS/Lambda needed)
2. **Supports multiple providers** (Amazon, Keepa, etc.)
3. **Saves enriched data** directly to MongoDB
4. **Provides real-time progress** updates

### Provider System
Each enrichment provider:
- Implements the `EnrichmentProvider` base class
- Handles its own API calls and data formatting
- Can be easily added/configured

### Mock Data (for testing)
Currently uses mock data for demonstration:
- Simulates API delays
- Returns realistic-looking enriched data
- Easy to replace with real API calls

## 🛠️ Customization

### Adding New Providers
1. Create a new class inheriting from `EnrichmentProvider`
2. Implement the `enrich_item` method
3. Add to the `providers` dict in `LocalEnrichmentService`

### Example Provider
```python
class CustomAPIProvider(EnrichmentProvider):
    def __init__(self):
        super().__init__("custom_api")
        self.api_key = settings.custom_api_key
    
    async def enrich_item(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        # Your enrichment logic here
        pass
```

### Real API Integration
Replace the mock methods in providers:
- `_call_amazon_api()` - Call actual Amazon API
- `_call_keepa_api()` - Call actual Keepa API
- Add proper error handling and rate limiting

## 📊 Monitoring

### Enrichment Status
- `uploaded` - Catalog uploaded, ready for enrichment
- `processing` - Enrichment in progress
- `completed` - All items enriched successfully
- `partially_completed` - Some items failed
- `error` - Enrichment process failed

### Progress Tracking
- Real-time updates during processing
- Batch processing with configurable batch sizes
- Detailed error reporting for failed items

## 📊 Catalog Analysis

Before testing enrichment, analyze your catalog files to understand their structure:

```bash
python analyze_catalog.py
```

This script will:
- Analyze all Excel files in `app/catalog_examples/`
- Show column structure and data types
- Identify missing data and unique values
- Provide recommendations for enrichment setup

## 🧪 Testing Scenarios

### 1. Basic Enrichment
```bash
# Test with default Amazon provider
curl -X POST "http://localhost:8000/catalogs/{id}/enrich" \
  -H "Authorization: Bearer {token}"
```

### 2. Provider Selection
```bash
# Test with specific provider
curl -X POST "http://localhost:8000/catalogs/{id}/enrich?provider=keepa" \
  -H "Authorization: Bearer {token}"
```

### 3. Error Handling
- Test with invalid catalog ID
- Test with unsupported provider
- Test with corrupted catalog data

## 🔄 Production Migration

When ready for production:

1. **Replace mock providers** with real API implementations
2. **Enable SQS/Lambda** for async processing
3. **Add rate limiting** and error handling
4. **Implement retry logic** for failed enrichments
5. **Add monitoring** and alerting

## 📚 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string in `.env`

2. **AWS Credentials Error**
   - Verify AWS credentials in `.env`
   - Check AWS region configuration

3. **Enrichment Fails**
   - Check provider configuration
   - Verify API keys are valid
   - Check logs for detailed errors

### Debug Mode
Enable debug logging in `.env`:
```bash
DEBUG=true
```

### Logs
Check application logs for detailed information:
```bash
docker-compose logs api
```

## 🎯 Next Steps

1. **Test the current implementation** with mock data
2. **Integrate real APIs** (Amazon, Keepa, etc.)
3. **Add more providers** as needed
4. **Implement offer generation** based on enriched data
5. **Add performance monitoring** and optimization
