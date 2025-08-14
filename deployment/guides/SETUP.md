# Perfect PO API - Setup Guide

This guide will help you set up and run the Perfect PO API locally.

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose (for easy setup)
- MongoDB (included in Docker setup)
- AWS account with S3 and SQS access (for production features)

## Quick Start with Docker

1. **Clone and navigate to the project:**
   ```bash
   cd perfect-po-api
   ```

2. **Start the services:**
   ```bash
   docker-compose up -d
   ```

3. **Access the API:**
   - API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - MongoDB Express: http://localhost:8081

## Manual Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up Environment Variables

Copy the environment template and configure it:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# Database Configuration
MONGODB_URL=mongodb://localhost:27017/perfect_po_db

# AWS Configuration (optional for local development)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
S3_BUCKET_NAME=perfect-po-catalogs
SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/your-account/your-queue

# JWT Configuration
JWT_SECRET_KEY=your_super_secret_jwt_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=30

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### 3. Start MongoDB

**Option A: Using Docker**
```bash
docker run -d -p 27017:27017 --name mongodb mongo:6.0
```

**Option B: Local Installation**
- Install MongoDB Community Edition
- Start the MongoDB service

### 4. Run the Application

```bash
python run.py
```

Or using uvicorn directly:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/me` - Get current user info

### Catalogs
- `POST /catalogs/upload` - Upload catalog file
- `GET /catalogs/` - List user catalogs
- `GET /catalogs/{catalog_id}` - Get specific catalog
- `PUT /catalogs/{catalog_id}` - Update catalog
- `DELETE /catalogs/{catalog_id}` - Delete catalog

### Enrichment
- `POST /catalogs/{catalog_id}/enrich` - Trigger enrichment
- `GET /catalogs/{catalog_id}/enrichment-status` - Check enrichment status

## Testing

Run the test suite:

```bash
pytest tests/
```

## File Upload Formats

The API supports the following file formats:
- **CSV**: Comma-separated values
- **JSON**: JSON array or object with 'items' key
- **Excel**: .xlsx files (basic support)

## Development

### Project Structure
```
perfect-po-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection
│   ├── auth/                # Authentication utilities
│   ├── models/              # Pydantic models
│   ├── routers/             # API route handlers
│   └── services/            # Business logic
├── tests/                   # Test files
├── requirements.txt          # Python dependencies
├── Dockerfile               # Container configuration
├── docker-compose.yml       # Development services
└── README.md               # Project documentation
```

### Adding New Features

1. **Models**: Add new Pydantic models in `app/models/`
2. **Services**: Add business logic in `app/services/`
3. **Routes**: Add new endpoints in `app/routers/`
4. **Tests**: Add corresponding tests in `tests/`

## Production Deployment

### Environment Variables
- Set `DEBUG=false`
- Configure proper CORS origins
- Use strong JWT secrets
- Set up proper AWS credentials

### Security Considerations
- Use HTTPS in production
- Implement rate limiting
- Add request validation
- Set up proper logging and monitoring

### Scaling
- Use multiple API instances behind a load balancer
- Implement database connection pooling
- Set up Redis for caching
- Use message queues for async processing

## Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check connection string in `.env`
   - Verify network connectivity

2. **AWS Credentials Error**
   - Verify AWS credentials in `.env`
   - Check AWS region configuration
   - Ensure proper IAM permissions

3. **Port Already in Use**
   - Change port in `.env` file
   - Kill existing processes using the port

4. **Import Errors**
   - Ensure you're in the correct directory
   - Check Python path
   - Verify all dependencies are installed

### Logs

Check application logs for detailed error information:
```bash
docker-compose logs api
```

## Support

For issues and questions:
1. Check the logs for error details
2. Verify configuration settings
3. Test individual components
4. Check the API documentation at `/docs`

