#!/bin/bash

# EC2 Deployment Script for Perfect PO API
# This script deploys the FastAPI application on EC2 using Docker Compose

set -e

# Configuration
ENVIRONMENT=${1:-production}
DOMAIN=${2:-localhost}
REGION=${3:-us-east-1}

echo "🚀 Deploying Perfect PO API on EC2..."
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

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ .env.prod file not found. Creating from template..."
    cp env.prod.template .env.prod
    echo "⚠️  Please edit .env.prod with your production values before continuing"
    echo "   Key values to set:"
    echo "   - MONGO_ROOT_PASSWORD"
    echo "   - JWT_SECRET_KEY"
    echo "   - KEEPA_API_KEY"
    echo "   - AWS credentials"
    echo ""
    read -p "Press Enter after editing .env.prod to continue..."
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p logs nginx/ssl uploads mongo-init

# Generate self-signed SSL certificate (for development)
if [ ! -f nginx/ssl/cert.pem ] || [ ! -f nginx/ssl/key.pem ]; then
    echo "🔐 Generating self-signed SSL certificate..."
    sudo mkdir -p nginx/ssl
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=${DOMAIN}"
    sudo chown -R $USER:$USER nginx/ssl/
    echo "✅ SSL certificate generated"
fi

# Set proper permissions
echo "🔒 Setting proper permissions..."
chmod 600 .env.prod
chmod 600 nginx/ssl/*.pem

# Load environment variables
echo "📋 Loading environment variables..."
set -a
source .env.prod
set +a

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# Build and start services
echo "🔨 Building and starting services..."
docker-compose -f docker-compose.prod.yml up -d --build

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
    docker-compose -f docker-compose.prod.yml logs api
    exit 1
fi

# Check MongoDB
if docker exec perfect-po-mongodb mongosh --eval "db.adminCommand('ping')" &> /dev/null; then
    echo "✅ MongoDB is healthy"
else
    echo "❌ MongoDB health check failed"
    docker-compose -f docker-compose.prod.yml logs mongodb
    exit 1
fi

# Check Redis
if docker exec perfect-po-redis redis-cli ping | grep -q "PONG"; then
    echo "✅ Redis is healthy"
else
    echo "❌ Redis health check failed"
    docker-compose -f docker-compose.prod.yml logs redis
    exit 1
fi

# Check Nginx
if curl -f http://localhost &> /dev/null; then
    echo "✅ Nginx is healthy"
else
    echo "❌ Nginx health check failed"
    docker-compose -f docker-compose.prod.yml logs nginx
    exit 1
fi

# Show service status
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.prod.yml ps

# Show logs
echo ""
echo "📋 Recent logs:"
docker-compose -f docker-compose.prod.yml logs --tail=20

# Show access information
echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📱 Access Information:"
echo "  - API: https://${DOMAIN}"
echo "  - API Docs: https://${DOMAIN}/docs"
echo "  - Health Check: https://${DOMAIN}/health"
echo "  - MongoDB Express: http://${DOMAIN}:8081 (if enabled)"
echo ""
echo "🔧 Management Commands:"
echo "  - View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "  - Stop services: docker-compose -f docker-compose.prod.yml down"
echo "  - Restart services: docker-compose -f docker-compose.prod.yml restart"
echo "  - Update: git pull && ./deploy_ec2.sh"
echo ""
echo "🔒 Security Notes:"
echo "  - Change default passwords in .env.prod"
echo "  - Use proper SSL certificates for production"
echo "  - Configure firewall rules"
echo "  - Enable AWS CloudWatch monitoring"
echo ""
echo "📚 Next Steps:"
echo "1. Test the API endpoints"
echo "2. Configure your domain DNS"
echo "3. Set up monitoring and alerts"
echo "4. Configure backup strategies"
