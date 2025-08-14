#!/bin/bash

# Development Deployment Script for Perfect PO API
# This script deploys the development environment on EC2

set -e

# Configuration
ENVIRONMENT=${1:-development}
DOMAIN=${2:-localhost}
REGION=${3:-us-east-1}

echo "🚀 Deploying Perfect PO API Development Environment..."
echo "Environment: ${ENVIRONMENT}"
echo "Domain: ${DOMAIN}"
echo "Region: ${REGION}"

# Check if running on EC2
if ! curl -s http://169.254.169.254/latest/meta-data/instance-id &> /dev/null; then
    echo "⚠️  Warning: This doesn't appear to be running on EC2"
    echo "   Some features may not work correctly"
fi

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo "✅ Docker installed. Please log out and back in, then run this script again."
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Installing Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose installed"
fi

# Check if .env.dev exists
if [ ! -f .env.dev ]; then
    echo "❌ .env.dev file not found. Creating from template..."
    cp env.dev.template .env.dev
    echo "⚠️  Please edit .env.dev with your development values before continuing"
    echo "   Key values to set:"
    echo "   - KEEPA_API_KEY (your Keepa API key)"
    echo "   - AWS credentials (for S3 access)"
    echo "   - JWT_SECRET_KEY (change from default)"
    echo "   - MONGODB_URI (already set to your Atlas cluster)"
    echo ""
    read -p "Press Enter after editing .env.dev to continue..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs nginx uploads

# Set proper permissions
echo "🔒 Setting proper permissions..."
chmod 600 .env.dev

# Load environment variables
echo "📋 Loading environment variables..."
set -a
source .env.dev
set +a

# Verify MongoDB URI is set
if [ -z "$MONGODB_URI" ]; then
    echo "❌ Error: MONGODB_URI is not set in .env.dev"
    echo "   Please check your .env.dev file"
    exit 1
fi

echo "✅ MongoDB URI configured: ${MONGODB_URI:0:50}..."

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.dev.yml down --remove-orphans || true

# Build and start services
echo "🔨 Building and starting development services..."
docker-compose -f docker-compose.dev.yml up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check service health
echo "🏥 Checking service health..."

# Check API health
if curl -f http://localhost/health &> /dev/null; then
    echo "✅ API is healthy"
else
    echo "❌ API health check failed"
    docker-compose -f docker-compose.dev.yml logs api
    exit 1
fi

# Check Redis
if docker exec perfect-po-redis-dev redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    docker-compose -f docker-compose.dev.yml logs redis
    exit 1
fi

# Check Nginx
if curl -f http://localhost &> /dev/null; then
    echo "✅ Nginx is healthy"
else
    echo "❌ Nginx health check failed"
    docker-compose -f docker-compose.dev.yml logs nginx
    exit 1
fi

# Test MongoDB connection through API
echo "🔍 Testing MongoDB connection..."
if curl -f http://localhost/health &> /dev/null; then
    echo "✅ MongoDB connection successful (via API health check)"
else
    echo "⚠️  MongoDB connection test failed - check API logs"
    docker-compose -f docker-compose.dev.yml logs api
fi

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.dev.yml ps

# Show logs
echo ""
echo "📋 Recent logs:"
docker-compose -f docker-compose.dev.yml logs --tail=20

# Show access information
echo ""
echo "🎉 Development environment deployed successfully!"
echo ""
echo "📱 Access Information:"
echo "  - API: http://${DOMAIN}"
echo "  - API Docs: http://${DOMAIN}/docs"
echo "  - Health Check: http://${DOMAIN}/health"
echo "  - Dev Status: http://${DOMAIN}/dev/status"
echo "  - Direct API: http://${DOMAIN}:8000"
echo ""
echo "🗄️  Database:"
echo "  - MongoDB Atlas: ${MONGODB_URI:0:50}..."
echo "  - Database: AllShoes-Dev cluster"
echo ""
echo "🔧 Management Commands:"
echo "  - View logs: docker-compose -f docker-compose.dev.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.dev.yml down"
echo "  - Restart services: docker-compose -f docker-compose.dev.yml restart"
echo "  - Update: git pull && ./deploy_dev.sh"
echo ""
echo "🐛 Development Features:"
echo "  - Hot reload enabled (code changes auto-restart)"
echo "  - Debug mode enabled"
echo "  - Verbose logging"
echo "  - Remote MongoDB Atlas cluster"
echo "  - More lenient rate limiting"
echo ""
echo "🔒 Security Notes:"
echo "  - Development passwords are weak (change for production)"
echo "  - HTTP only (no SSL in dev)"
echo "  - Debug mode enabled"
echo "  - CORS is permissive"
echo "  - Using remote MongoDB Atlas (secure connection)"
echo ""
echo "📚 Next Steps:"
echo "1. Test the API endpoints"
echo "2. Upload a test catalog"
echo "3. Test product enrichment"
echo "4. Verify all functionality works"
echo "5. When ready, deploy to production with: ./deploy_ec2.sh"
