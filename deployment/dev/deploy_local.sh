#!/bin/bash

# Local Development Deployment Script for Perfect PO API
# This script deploys the local development environment with localhost MongoDB

set -e

echo "🧪 Deploying Perfect PO API Local Development Environment..."
echo "Environment: local"
echo "Database: localhost MongoDB"
echo ""

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if .env.local exists
if [ ! -f .env.local ]; then
    echo "❌ .env.local file not found. Creating from template..."
    cp env.local.template .env.local
    echo "⚠️  Please edit .env.local with your local development values before continuing"
    echo "   Key values to set:"
    echo "   - KEEPA_API_KEY (your Keepa API key)"
    echo "   - AWS credentials (for S3 access)"
    echo "   - JWT_SECRET_KEY (change from default)"
    echo "   - MONGODB_URI (already set to localhost)"
    echo ""
    read -p "Press Enter after editing .env.local to continue..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs nginx uploads mongo-init

# Set proper permissions
echo "🔒 Setting proper permissions..."
chmod 600 .env.local

# Load environment variables
echo "📋 Loading environment variables..."
set -a
source .env.local
set +a

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.local.yml down --remove-orphans || true

# Build and start services
echo "🔨 Building and starting local development services..."
docker-compose -f docker-compose.local.yml up -d --build

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
    docker-compose -f docker-compose.local.yml logs api
    exit 1
fi

# Check MongoDB
if docker exec perfect-po-mongodb-local mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    echo "✅ MongoDB is healthy"
else
    echo "❌ MongoDB health check failed"
    docker-compose -f docker-compose.local.yml logs mongodb
    exit 1
fi

# Check Redis
if docker exec perfect-po-redis-local redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    docker-compose -f docker-compose.local.yml logs redis
    exit 1
fi

# Check Nginx
if curl -f http://localhost &> /dev/null; then
    echo "✅ Nginx is healthy"
else
    echo "❌ Nginx health check failed"
    docker-compose -f docker-compose.local.yml logs nginx
    exit 1
fi

# Check MongoDB Express
if curl -f http://localhost:8081 &> /dev/null; then
    echo "✅ MongoDB Express is healthy"
else
    echo "⚠️  MongoDB Express health check failed"
    docker-compose -f docker-compose.local.yml logs mongo-express
fi

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.local.yml ps

# Show logs
echo ""
echo "📋 Recent logs:"
docker-compose -f docker-compose.local.yml logs --tail=20

# Show access information
echo ""
echo "🎉 Local development environment deployed successfully!"
echo ""
echo "📱 Access Information:"
echo "  - API: http://localhost"
echo "  - API Docs: http://localhost/docs"
echo "  - Health Check: http://localhost/health"
echo "  - Dev Status: http://localhost/dev/status"
echo "  - Direct API: http://localhost:8000"
echo "  - MongoDB Express: http://localhost:8081"
echo ""
echo "🗄️  Database:"
echo "  - MongoDB: localhost:27017"
echo "  - Database: perfect_po_dev"
echo "  - Username: admin"
echo "  - Password: dev_password"
echo ""
echo "🔧 Management Commands:"
echo "  - View logs: docker-compose -f docker-compose.local.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.local.yml down"
echo "  - Restart services: docker-compose -f docker-compose.local.yml restart"
echo "  - Update: git pull && ./deploy_local.sh"
echo ""
echo "🐛 Local Development Features:"
echo "  - Hot reload enabled (code changes auto-restart)"
echo "  - Debug mode enabled"
echo "  - Verbose logging"
echo "  - Local MongoDB with MongoDB Express"
echo "  - More lenient rate limiting"
echo ""
echo "🔒 Security Notes:"
echo "  - Local development only - not for production"
echo "  - Weak passwords (safe for local dev)"
echo "  - HTTP only (no SSL in local dev)"
echo "  - Debug mode enabled"
echo "  - CORS is permissive"
echo ""
echo "📚 Next Steps:"
echo "1. Test the API endpoints"
echo "2. Upload a test catalog"
echo "3. Test product enrichment"
echo "4. Verify all functionality works"
echo "5. When ready for remote dev: cd ../ && ./deploy.sh"
echo ""
echo "🌐 For Remote Development:"
echo "  - Use the main deployment script: ./deploy.sh"
echo "  - Choose option 1 for remote development"
echo "  - Uses your MongoDB Atlas cluster"
