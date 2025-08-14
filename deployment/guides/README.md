# Perfect PO API - Catalog Management System

A Python FastAPI-based system for managing product catalogs with automatic enrichment and offer generation.

## Features

- **User Authentication**: JWT-based authentication system
- **Catalog Management**: Upload and manage product catalogs
- **S3 Integration**: Store catalog files in user-specific folders
- **Data Enrichment**: Enrich line items via local service or SQS/Lambda pipeline
- **Multiple Enrichment Providers**: Support for Amazon API, Keepa API, and more
- **Product Database**: MongoDB storage for enriched products
- **Offer Generation**: AI-powered offer generation based on catalog data

## Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  FastAPI    │───▶│   MongoDB   │
│             │    │   Server    │    │             │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │     S3      │
                   │  (Catalogs) │
                   └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │     SQS     │
                   └─────────────┘
                          │
                          ▼
                   ┌─────────────┐
                   │   Lambda    │
                   │(Enrichment) │
                   └─────────────┘
```

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. Run the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

4. Access the API documentation:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## API Endpoints

- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `POST /catalogs/upload` - Upload catalog file
- `POST /catalogs/{catalog_id}/enrich` - Trigger enrichment (with provider selection)
- `GET /catalogs/providers` - Get available enrichment providers
- `GET /catalogs` - List user catalogs
- `GET /products` - List enriched products
- `GET /products/catalog/{catalog_id}/summary` - Get catalog products summary
- `POST /offers/generate` - Generate offers based on enriched products
- `GET /offers` - List user offers
- `GET /offers/{offer_id}` - Get specific offer
- `PUT /offers/{offer_id}` - Update offer
- `DELETE /offers/{offer_id}` - Delete offer
- `GET /offers/catalog/{catalog_id}/summary` - Get catalog offers summary

## File Upload Formats

The API supports the following file formats:
- **CSV**: Comma-separated values
- **JSON**: JSON array or object with 'items' key
- **Excel**: .xlsx and .xls files with full parsing support
- **Flexible Field Mapping**: Automatically maps common catalog field names

## Catalog Analysis

Use the included analysis script to understand your catalog structure:
```bash
python analyze_catalog.py
```

This will analyze your Excel files and provide insights for enrichment setup.

## Environment Variables

- `MONGODB_URL` - MongoDB connection string
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `AWS_REGION` - AWS region
- `S3_BUCKET_NAME` - S3 bucket for catalogs
- `SQS_QUEUE_URL` - SQS queue for enrichment
- `JWT_SECRET_KEY` - JWT signing secret
- `JWT_ALGORITHM` - JWT algorithm (HS256)
