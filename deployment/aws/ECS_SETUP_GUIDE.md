# 🚀 AWS ECS Deployment Guide

This guide will walk you through deploying your Perfect PO API to AWS ECS using GitHub Actions for automated deployments.

## 🏗️ **Architecture Overview**

```
GitHub Push → GitHub Actions → Build Docker → Push to ECR → Deploy to ECS → Load Balancer → Your API
     ↓              ↓              ↓              ↓              ↓              ↓
  Trigger      Build Image    Store Image    Run Container   Route Traffic   Access API
```

## 📋 **Prerequisites**

### **AWS Setup**
- ✅ AWS account with appropriate permissions
- ✅ AWS CLI configured with credentials
- ✅ IAM user with CloudFormation, ECS, ECR permissions

### **GitHub Setup**
- ✅ GitHub repository with your code
- ✅ GitHub Actions enabled
- ✅ Repository secrets configured

## 🚀 **Step-by-Step Deployment**

### **Step 1: Deploy AWS Infrastructure**

#### **1.1 Install AWS CLI (if not already installed)**
```bash
# macOS
brew install awscli

# Ubuntu/Debian
sudo apt-get install awscli

# Windows
# Download from AWS website
```

#### **1.2 Configure AWS Credentials**
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your default region (e.g., us-east-1)
# Enter your output format (json)
```

#### **1.3 Deploy Infrastructure**
```bash
cd deployment/aws
chmod +x deploy-infrastructure.sh
./deploy-infrastructure.sh dev
```

**This will create:**
- ✅ ECS Cluster
- ✅ ECR Repository
- ✅ VPC and Networking
- ✅ Load Balancer
- ✅ IAM Roles
- ✅ Security Groups

### **Step 2: Set Up AWS Secrets Manager**

#### **2.1 Create Secrets**
```bash
# MongoDB URI
aws secretsmanager create-secret \
    --name "perfect-po-dev-mongodb-uri" \
    --description "MongoDB connection string for development" \
    --secret-string "mongodb+srv://maor:Mvnu3GxLmlDm251O@allshoes-dev.gvdqclc.mongodb.net/?retryWrites=true&w=majority&appName=AllShoes-Dev"

# JWT Secret
aws secretsmanager create-secret \
    --name "perfect-po-dev-jwt-secret" \
    --description "JWT secret key for development" \
    --secret-string "your_super_secret_jwt_key_here"

# Keepa API Key
aws secretsmanager create-secret \
    --name "perfect-po-dev-keepa-api-key" \
    --description "Keepa API key for development" \
    --secret-string "your_keepa_api_key_here"
```

### **Step 3: Configure GitHub Secrets**

#### **3.1 Go to Your GitHub Repository**
- Navigate to `Settings` → `Secrets and variables` → `Actions`
- Click `New repository secret`

#### **3.2 Add Required Secrets**
```
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
```

### **Step 4: Update Configuration Files**

#### **4.1 Update ECS Task Definition**
Edit `deployment/aws/ecs-task-definition.json`:
- Replace `ACCOUNT_ID` with your actual AWS account ID
- Update region if different from `us-east-1`

#### **4.2 Update GitHub Actions Workflow**
Edit `.github/workflows/deploy-ecs.yml`:
- Update `AWS_REGION` if different
- Update ECS cluster and service names if needed

### **Step 5: Deploy Your Application**

#### **5.1 Push to GitHub**
```bash
git add .
git commit -m "Add ECS deployment configuration"
git push origin main
```

#### **5.2 Monitor Deployment**
- Go to `Actions` tab in your GitHub repository
- Watch the deployment workflow run
- Check for any errors or issues

## 🔧 **Configuration Details**

### **Environment Variables**
The ECS task definition uses these environment variables:
- `ENVIRONMENT`: Set to your deployment environment (dev/staging/prod)
- `AWS_REGION`: AWS region for your deployment

### **Secrets (from AWS Secrets Manager)**
- `MONGODB_URI`: Your MongoDB Atlas connection string
- `JWT_SECRET_KEY`: Secret key for JWT token generation
- `KEEPA_API_KEY`: Your Keepa API key
- `AWS_ACCESS_KEY_ID`: AWS access key for S3/SQS access
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for S3/SQS access

### **Port Configuration**
- **Container Port**: 8000 (FastAPI application)
- **Load Balancer Port**: 80 (HTTP)
- **Health Check Path**: `/health`

## 📱 **Accessing Your API**

### **After Successful Deployment**
Your API will be available at the Load Balancer DNS name:
```
http://your-load-balancer-dns-name
```

### **Endpoints Available**
- **API**: `http://your-lb-dns/`
- **Health Check**: `http://your-lb-dns/health`
- **API Docs**: `http://your-lb-dns/docs`
- **OpenAPI**: `http://your-lb-dns/openapi.json`

## 🔍 **Monitoring and Troubleshooting**

### **Check ECS Service Status**
```bash
aws ecs describe-services \
    --cluster perfect-po-dev-cluster \
    --services perfect-po-dev-api-service \
    --region us-east-1
```

### **View Container Logs**
```bash
# Get log group name
aws logs describe-log-groups --log-group-name-prefix "/ecs/perfect-po-dev"

# View recent logs
aws logs tail "/ecs/perfect-po-dev-api" --follow
```

### **Check Load Balancer Health**
```bash
# Get target group health
aws elbv2 describe-target-health \
    --target-group-arn your-target-group-arn \
    --region us-east-1
```

## 💰 **Cost Estimation**

### **Development Environment**
- **ECS Fargate**: ~$15-25/month (512 CPU, 1GB RAM)
- **Load Balancer**: ~$16/month
- **Data Transfer**: ~$1-5/month
- **ECR Storage**: ~$1-3/month
- **Total**: **~$35-50/month**

### **Production Environment**
- **ECS Fargate**: ~$30-50/month (1024 CPU, 2GB RAM)
- **Load Balancer**: ~$16/month
- **Data Transfer**: ~$5-15/month
- **ECR Storage**: ~$2-5/month
- **Total**: **~$55-90/month**

## 🚀 **Next Steps After Deployment**

### **1. Test Your API**
```bash
# Test health endpoint
curl http://your-load-balancer-dns/health

# Test API documentation
curl http://your-load-balancer-dns/docs
```

### **2. Set Up Custom Domain (Optional)**
- Configure Route 53 for your domain
- Set up SSL certificate with ACM
- Update load balancer listener for HTTPS

### **3. Set Up Monitoring**
- Configure CloudWatch alarms
- Set up log aggregation
- Monitor performance metrics

### **4. Scale Your Application**
- Adjust ECS service desired count
- Set up auto-scaling policies
- Configure load balancer rules

## 🎉 **Success!**

Your Perfect PO API is now running on AWS ECS with:
- ✅ **Automated deployments** via GitHub Actions
- ✅ **Scalable infrastructure** with Fargate
- ✅ **Load balancing** for high availability
- ✅ **Secrets management** for security
- ✅ **Monitoring and logging** built-in

**Happy deploying! 🚀**
