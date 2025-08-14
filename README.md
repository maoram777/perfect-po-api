# Perfect PO API

A comprehensive API for managing product catalogs, enrichment, and offer generation.

## 🚀 **Latest Deployment Status**
- **Infrastructure**: ✅ ECS Service Active
- **Next**: Trigger deployment with latest fixes

## Features

- **Catalog Management**: Upload and manage product catalogs
- **Product Enrichment**: Automatically enrich products with external data
- **Offer Generation**: Generate competitive offers based on enriched data
- **User Authentication**: Secure JWT-based authentication
- **File Processing**: Support for CSV, JSON, and Excel files

## Quick Start

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd perfect-po-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run the development server**
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Environment Variables

- `MONGODB_URL` - MongoDB connection string
- `JWT_SECRET_KEY` - JWT signing secret
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `KEEPA_API_KEY` - Keepa API key for product enrichment

## Deployment

This project includes automated deployment to AWS ECS via GitHub Actions.

### Prerequisites

- AWS account with appropriate permissions
- GitHub repository secrets configured
- Docker and Docker Compose (for local development)

### Deployment Process

1. **Push to main branch** triggers automatic deployment
2. **Builds Docker image** and pushes to ECR
3. **Deploys to ECS** with latest code
4. **Health checks** ensure successful deployment

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.
