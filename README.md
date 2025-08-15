# Perfect PO API

A comprehensive API for managing product catalogs, pricing optimization, and inventory management.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- MongoDB
- Docker (for containerized deployment)

### Local Development
```bash
# Clone the repository
git clone https://github.com/maoram777/perfect-po-api.git
cd perfect-po-api

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Run the application
uvicorn app.main:app --reload
```

## 📚 API Documentation

### Health Check
- **GET** `/health` - API health status

### Authentication
- **POST** `/auth/login` - User login
- **POST** `/auth/register` - User registration

### Products
- **GET** `/products` - List all products
- **POST** `/products` - Create new product
- **GET** `/products/{id}` - Get product by ID
- **PUT** `/products/{id}` - Update product
- **DELETE** `/products/{id}` - Delete product

### Catalogs
- **GET** `/catalogs` - List all catalogs
- **POST** `/catalogs` - Create new catalog
- **GET** `/catalogs/{id}` - Get catalog by ID
- **PUT** `/catalogs/{id}` - Update catalog
- **DELETE** `/catalogs/{id}` - Delete catalog

## 🔧 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `MONGODB_URL` | MongoDB connection string | ✅ | - |
| `JWT_SECRET_KEY` | JWT signing secret | ✅ | - |
| `KEEPA_API_KEY` | Keepa API key | ✅ | - |
| `AWS_ACCESS_KEY_ID` | AWS access key | ✅ | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | ✅ | - |
| `AWS_REGION` | AWS region | ❌ | `us-east-1` |
| `ENVIRONMENT` | Environment name | ❌ | `dev` |
| `DEBUG` | Debug mode | ❌ | `false` |

## 🚀 Deployment

### AWS ECS Deployment

The application is configured for deployment to AWS ECS using GitHub Actions.

#### Prerequisites
- AWS account with appropriate permissions
- GitHub repository secrets configured
- Infrastructure deployed via CloudFormation

#### Deployment Process
1. **Infrastructure Setup**: Deploy ECS infrastructure using CloudFormation
2. **GitHub Secrets**: Configure `ENV_FILE_DEV` secret with environment variables
3. **Automatic Deployment**: Push to main branch triggers GitHub Actions deployment
4. **ECS Deployment**: Application deploys to ECS Fargate with load balancer

#### Infrastructure Components
- **ECS Cluster**: `perfect-po-dev-cluster`
- **ECS Service**: `perfect-po-dev-api-service`
- **Load Balancer**: Application Load Balancer with health checks
- **ECR Repository**: `perfect-po-dev-api`
- **IAM Roles**: Execution and task roles with appropriate permissions

## 📝 Development Notes

- **Triggering Deployment**: This comment triggers a new deployment! 🚀
