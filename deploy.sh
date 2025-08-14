#!/bin/bash

# Main Deployment Script for Perfect PO API
# This script helps you choose between local, remote development and production deployments

set -e

echo "🚀 Perfect PO API - Deployment Script"
echo "======================================"
echo ""

# Check if running from the right directory
if [ ! -d "deployment" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   Current directory: $(pwd)"
    echo "   Expected: /path/to/perfect-po-api"
    exit 1
fi

# Function to show deployment options
show_options() {
    echo "🎯 Choose your deployment option:"
    echo ""
    echo "1. 🏠 Local Development Environment (Recommended to start)"
    echo "   - Development on your local machine"
    echo "   - Hot reload, debug mode, local MongoDB, MongoDB Express"
    echo "   - Cost: Free (local resources)"
    echo "   - Security: Local only, weak passwords"
    echo ""
    echo "2. 🧪 Remote Development Environment (Team development)"
    echo "   - Testing and development on EC2"
    echo "   - Hot reload, debug mode, MongoDB Atlas cluster"
    echo "   - Cost: $11-20/month (t3.small + Atlas)"
    echo "   - Security: HTTP only, weak passwords"
    echo ""
    echo "3. 🚀 Production Environment"
    echo "   - Live production deployment"
    echo "   - SSL, strict security, monitoring"
    echo "   - Cost: $21-60/month (t3.medium + SSL)"
    echo "   - Security: HTTPS, strong passwords"
    echo ""
    echo "4. ⚡ AWS Lambda & SQS Setup"
    echo "   - Asynchronous product enrichment"
    echo "   - Scalable, serverless, cost-effective"
    echo "   - Cost: Pay-per-use ($5-20/month)"
    echo ""
    echo "5. 📚 View Documentation"
    echo "   - Read deployment guides"
    echo "   - View architecture diagrams"
    echo "   - Check prerequisites"
    echo ""
    echo "6. ❌ Exit"
    echo ""
}

# Function to deploy local development environment
deploy_local() {
    echo "🏠 Deploying Local Development Environment..."
    echo ""
    
    if [ ! -d "deployment/dev" ]; then
        echo "❌ Error: Development deployment files not found"
        exit 1
    fi
    
    cd deployment/dev
    
    if [ ! -x "deploy_local.sh" ]; then
        echo "❌ Error: deploy_local.sh is not executable"
        echo "   Running: chmod +x deploy_local.sh"
        chmod +x deploy_local.sh
    fi
    
    echo "🚀 Starting local development deployment..."
    echo "   This will deploy to your local machine with localhost MongoDB"
    echo ""
    
    read -p "Press Enter to continue with local development deployment..."
    
    ./deploy_local.sh
}

# Function to deploy remote development environment
deploy_dev() {
    echo "🧪 Deploying Remote Development Environment..."
    echo ""
    
    if [ ! -d "deployment/dev" ]; then
        echo "❌ Error: Development deployment files not found"
        exit 1
    fi
    
    cd deployment/dev
    
    if [ ! -x "deploy_dev.sh" ]; then
        echo "❌ Error: deploy_dev.sh is not executable"
        echo "   Running: chmod +x deploy_dev.sh"
        chmod +x deploy_dev.sh
    fi
    
    echo "🚀 Starting remote development deployment..."
    echo "   This will deploy to your EC2 instance with MongoDB Atlas"
    echo ""
    
    read -p "Press Enter to continue with remote development deployment..."
    
    ./deploy_dev.sh
}

# Function to deploy production environment
deploy_prod() {
    echo "🚀 Deploying Production Environment..."
    echo ""
    
    if [ ! -d "deployment/prod" ]; then
        echo "❌ Error: Production deployment files not found"
        exit 1
    fi
    
    cd deployment/prod
    
    if [ ! -x "deploy_ec2.sh" ]; then
        echo "❌ Error: deploy_ec2.sh is not executable"
        echo "   Running: chmod +x deploy_ec2.sh"
        chmod +x deploy_ec2.sh
    fi
    
    echo "🚀 Starting production deployment..."
    echo "   This will deploy to a new EC2 instance with SSL"
    echo ""
    
    read -p "Enter your domain name (e.g., api.yourdomain.com): " DOMAIN
    read -p "Press Enter to continue with production deployment..."
    
    ./deploy_ec2.sh production "$DOMAIN"
}

# Function to deploy Lambda
deploy_lambda() {
    echo "⚡ Deploying AWS Lambda & SQS..."
    echo ""
    
    if [ ! -d "deployment/lambda" ]; then
        echo "❌ Error: Lambda deployment files not found"
        exit 1
    fi
    
    cd deployment/lambda
    
    if [ ! -x "deploy_lambda.sh" ]; then
        echo "❌ Error: deploy_lambda.sh is not executable"
        echo "   Running: chmod +x deploy_lambda.sh"
        chmod +x deploy_lambda.sh
    fi
    
    echo "⚡ Starting Lambda deployment..."
    echo "   This will set up SQS, Lambda, and DynamoDB"
    echo ""
    
    read -p "Press Enter to continue with Lambda deployment..."
    
    ./deploy_lambda.sh
}

# Function to show documentation
show_docs() {
    echo "📚 Available Documentation:"
    echo ""
    
    if [ -d "deployment/guides" ]; then
        echo "📖 Quick Start Guides:"
        echo "   - deployment/guides/REMOTE_DEV_QUICKSTART.md"
        echo "   - deployment/guides/EC2_DEPLOYMENT_GUIDE.md"
        echo "   - deployment/guides/DEPLOYMENT_CHECKLIST.md"
        echo ""
        echo "🏗️ Architecture Guides:"
        echo "   - deployment/guides/SQS_LAMBDA_ARCHITECTURE.md"
        echo "   - deployment/guides/LAMBDA_CONFIGURATION.md"
        echo ""
        echo "📋 Main Deployment Guide:"
        echo "   - deployment/README.md"
        echo ""
        
        read -p "Press Enter to view main deployment guide..."
        cat deployment/README.md
    else
        echo "❌ Documentation directory not found"
    fi
}

# Main menu loop
while true; do
    show_options
    
    read -p "Enter your choice (1-6): " choice
    
    case $choice in
        1)
            deploy_local
            break
            ;;
        2)
            deploy_dev
            break
            ;;
        3)
            deploy_prod
            break
            ;;
        4)
            deploy_lambda
            break
            ;;
        5)
            show_docs
            ;;
        6)
            echo "👋 Goodbye!"
            exit 0
            ;;
        *)
            echo "❌ Invalid choice. Please enter 1-6."
            echo ""
            ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    echo ""
done

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📚 Next steps:"
echo "   - Check the deployment logs above"
echo "   - Test your endpoints"
echo "   - Read the documentation in deployment/guides/"
echo ""
echo "🚀 Happy deploying!"
